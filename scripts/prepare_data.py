"""Reproducible SBMTD comparison from original GTFS ZIPs; no API key required."""
from pathlib import Path
from datetime import datetime
import csv, io, json, zipfile, hashlib, statistics
from collections import defaultdict, Counter
from shapely.geometry import LineString
from shapely.ops import unary_union, linemerge

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data'
OUT.mkdir(exist_ok=True)
START, END = 10*3600, 14*3600
FILES = {
    'historic': {'file': 'historic-feed-20190819.zip', 'date': '20191015', 'url': 'https://openmobilitydata-data.s3-us-west-1.amazonaws.com/public/feeds/santa-barbara-mtd/1156/20190819/gtfs.zip'},
    'current': {'file': 'current-feed.zip', 'date': '20261015', 'url': 'https://www.sbmtd.gov/google_transit/feed.zip'},
}

def seconds(value):
    h, m, s = map(int, value.split(':'))
    return h*3600 + m*60 + s

def clean_num(x):
    return round(x, 3) if x is not None else None

def geometry_paths(geoms):
    if not geoms: return []
    # Dissolve duplicate geometries shared by trip patterns within a line.
    g = unary_union(geoms)
    if g.geom_type == 'MultiLineString':
        g = linemerge(g)
    g = g.simplify(0.000025, preserve_topology=True)
    lines = [g] if g.geom_type == 'LineString' else list(g.geoms)
    return [[[round(y, 6), round(x, 6)] for x,y in line.coords] for line in lines if line.geom_type == 'LineString' and len(line.coords)>1]

networks = {}
source_manifest = {}
all_shapes_raw = {}
for period, spec in FILES.items():
    raw = (ROOT/'sources'/spec['file']).read_bytes()
    z = zipfile.ZipFile(io.BytesIO(raw))
    def rows(name, z=z):
        return list(csv.DictReader(io.StringIO(z.read(name+'.txt').decode('utf-8-sig')))) if name+'.txt' in z.namelist() else []
    info = rows('feed_info')[0]
    day = spec['date']
    dow = datetime.strptime(day,'%Y%m%d').strftime('%A').lower()
    active = {c['service_id'] for c in rows('calendar') if c[dow]=='1' and c['start_date']<=day<=c['end_date']}
    for c in rows('calendar_dates'):
        if c['date'] == day:
            if c['exception_type']=='1': active.add(c['service_id'])
            else: active.discard(c['service_id'])
    rt = rows('routes')
    route_names = {r['route_id']: r['route_short_name'].upper() for r in rt}
    trips = rows('trips')
    by_trip = {t['trip_id']:t for t in trips}
    active_trips = {t['trip_id']:t for t in trips if t['service_id'] in active}
    times = defaultdict(list)
    for st in rows('stop_times'):
        if st['trip_id'] in active_trips:
            times[st['trip_id']].append(st)
    for a in times.values(): a.sort(key=lambda x:int(x['stop_sequence']))
    shapes = defaultdict(list)
    for pt in rows('shapes'):
        shapes[pt['shape_id']].append((int(pt['shape_pt_sequence']),float(pt['shape_pt_lon']),float(pt['shape_pt_lat'])))
    shape_lines = {}
    for sid, pts in shapes.items():
        pts.sort()
        if len(pts)>1: shape_lines[sid] = LineString([(x,y) for _,x,y in pts])
    stopdata = {s['stop_id']:s for s in rows('stops')}
    network = {'date':day,'feedStart':info['feed_start_date'],'feedEnd':info['feed_end_date'],'version':info.get('feed_version',''),'routes':{},'stops':[]}
    stop_routes = defaultdict(set)
    by_route = defaultdict(list)
    all_by_route = defaultdict(list)
    for t in trips: all_by_route[t['route_id']].append(t)
    for t in active_trips.values(): by_route[t['route_id']].append(t)
    for r in rt:
        key = route_names[r['route_id']]
        rs = by_route[r['route_id']]
        allrs = all_by_route[r['route_id']]
        # Shapes are exact GTFS paths; use only patterns scheduled on comparison day,
        # except for inactive routes, whose source-feed paths remain available to inspect.
        used_shapes = sorted({t.get('shape_id') for t in (rs or allrs) if t.get('shape_id') in shape_lines})
        paths = geometry_paths([shape_lines[s] for s in used_shapes])
        directions = defaultdict(list)
        day_durations, departures, midday_times = [], [], []
        stop_count=set()
        for t in rs:
            st = times.get(t['trip_id'],[])
            if not st: continue
            # GTFS pickup_type=1 means boarding is prohibited. Frequency must be
            # based on first boardable departure, not a terminal drop-off-only stop.
            boardable = [s for s in st if s.get('pickup_type','')!='1' and s.get('departure_time')]
            if not boardable: continue
            dep = seconds(boardable[0]['departure_time'])
            arr = seconds(st[-1]['arrival_time'])
            tripdir = t.get('direction_id','') or '0'
            directions[tripdir].append((dep,t.get('trip_headsign',''),t['trip_id'],boardable[0]['stop_id']))
            departures.append(dep)
            day_durations.append(max(0,arr-dep)/3600)
            if START<=dep<END: midday_times.append(dep)
            for s in st:
                stop_routes[s['stop_id']].add(key)
                stop_count.add(s['stop_id'])
        all_gaps=[]
        dir_info=[]
        for d,ts in sorted(directions.items()):
            ts.sort()
            # Include intervals overlapping the sample via their midpoint. This
            # avoids discarding the first/last interval merely at the window edge.
            gs=[(b[0]-a[0])/60 for a,b in zip(ts,ts[1:]) if START <= (a[0]+b[0])/2 < END and b[0]>a[0]]
            all_gaps.extend(gs)
            mid=[a[0] for a in ts if START<=a[0]<END]
            hs=Counter(x[1] for x in ts).most_common()
            dir_info.append({'id':d,'headsign':hs[0][0] if hs else '', 'headway':clean_num(statistics.median(gs)) if gs and len(mid)>=2 else None,'gapMin':clean_num(min(gs)) if gs and len(mid)>=2 else None,'gapMax':clean_num(max(gs)) if gs and len(mid)>=2 else None,'middayTrips':len(mid),'dayTrips':len(ts),'first':ts[0][0],'last':ts[-1][0],'terminal':stopdata.get(ts[0][3],{}).get('stop_name',''),'middayDepartureSeconds':mid})
        core = len(key)<4 and key not in ('90','91','92')
        kind = 'regular' if core else ('amtrak' if key in ('90','91','92') else ('standby' if key=='1001' else 'booster'))
        n_mid=len(midday_times)
        # At least two midday departures in one direction are required to present
        # a typical frequency, so sparse college/school trips aren't misrepresented.
        regular_midday = max([x['middayTrips'] for x in dir_info] or [0]) >= 2
        headway = statistics.median(all_gaps) if all_gaps and regular_midday else None
        obj={'id':key,'gtfsId':r['route_id'],'name':r['route_long_name'],'kind':kind,'paths':paths,'active':bool(departures),'dayTrips':len(departures),'middayTrips':n_mid,'headway':clean_num(headway),'gapMin':clean_num(min(all_gaps)) if all_gaps and headway else None,'gapMax':clean_num(max(all_gaps)) if all_gaps and headway else None,'first':min(departures) if departures else None,'last':max(departures) if departures else None,'directions':dir_info,'stopCount':len(stop_count),'scheduledTripHours':clean_num(sum(day_durations)),'middayDepartureSeconds':sorted(midday_times)}
        network['routes'][key]=obj
        if core:
            print(period,key,r['route_long_name'],'active',obj['active'],'day',obj['dayTrips'],'mid',n_mid,'h',headway,'range',obj['gapMin'],obj['gapMax'])
    for sid, keys in stop_routes.items():
        s=stopdata.get(sid)
        if s:
            network['stops'].append({'id':sid,'name':s['stop_name'],'lat':round(float(s['stop_lat']),6),'lon':round(float(s['stop_lon']),6),'routes':sorted(keys)})
    networks[period]=network
    source_manifest[period]={'url':spec['url'],'file':spec['file'],'sha1':hashlib.sha1(raw).hexdigest(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'feed_info':info,'sample_date':day,'active_service_ids':sorted(active)}

# Source-specific annotations; absent route IDs are not treated as formal agency
# cancellation declarations.
notes={
'1':'Weekday intervals went from 15 to 20 minutes in August 2026.',
'2':'Weekday intervals went from 15 to 20 minutes in August 2026.',
'10':'Cathedral Oaks ran 12 trips on the 2019 weekday, all outside midday. It is missing from today’s timetable.',
'16':'The City College line from 2019 is gone. Other MTD routes still serve SBCC.',
'19X':'This Carpinteria–SBCC express is new since 2019. It runs six college-oriented trips on the comparison weekday.',
'28':'In 2019, the guide advertised a bus every 10 minutes while UCSB was in session. Today’s midday timetable has longer, uneven gaps.',
'30':'This was the Downtown Shuttle. Today’s seasonal Downtown–Waterfront line 33 is a different route, with no October weekday trips.',
'34':'This was the Waterfront Shuttle. Seasonal line 33 is a separate route and has no trips on the October comparison weekday.',
'36':'The Seaside Shuttle is gone from the fixed-route timetable. Carpinteria now also has The Wave, which you book on demand.',
'37':'The Crosstown Shuttle is missing from today’s timetable. The dark dashes show its 2019 route.',
'33':'This is a seasonal shuttle. There are no trips on October 15, 2026.',
'1001':'Carp Standby appears in the source data, with no scheduled trips on the 2019 comparison date.'
}
all_ids=set(networks['historic']['routes'])|set(networks['current']['routes'])
def sort_key(s):
    return (int(''.join(c for c in s if c.isdigit()) or '99999'), s)
route_summary=[]
for key in sorted(all_ids,key=sort_key):
    h=networks['historic']['routes'].get(key)
    c=networks['current']['routes'].get(key)
    route_summary.append({'id':key,'name':(c or h)['name'],'historicName':h['name'] if h else None,'kind':(c or h)['kind'],'note':notes.get(key,''),'historic':h,'current':c})

D={'meta':{'asOf':'2026-10-15','historicDate':'2019-10-15','currentDate':'2026-10-15','windowStart':START,'windowEnd':END,'windowLabel':'Weekday daytime · 10 am–2 pm','historicLabel':'Fall 2019','currentLabel':'October 2026','historicBasis':'A real pre-pandemic high-service benchmark, not a proven all-time maximum or a best-of-every-line composite.','frequencyMethod':'Median of positive, consecutive first-boardable-stop departure gaps, separately by direction and then pooled, whose midpoint falls from 10:00 to 14:00. At least two departures within the window in a direction are required. Both directions are shown in details.'},'sources':source_manifest,'routes':route_summary,'stops':{k:v['stops'] for k,v in networks.items()}}
(OUT/'network.json').write_text(json.dumps(D,separators=(',',':')))
(OUT/'provenance.json').write_text(json.dumps({'retrieved_as_of_local_date':'2026-10-15','sources':source_manifest,'methods':D['meta']},indent=2))
cols=['line','name','type','historic_active','historic_day_trips','historic_midday_trips_both_directions','historic_typical_midday_headway_min','historic_midday_gap_min','historic_midday_gap_max','current_active','current_day_trips','current_midday_trips_both_directions','current_typical_midday_headway_min','current_midday_gap_min','current_midday_gap_max','note']
with (OUT/'route-comparison.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
    for r in route_summary:
        h,c=r['historic'] or {},r['current'] or {}
        w.writerow({'line':r['id'],'name':r['name'],'type':r['kind'],'historic_active':h.get('active',False),'historic_day_trips':h.get('dayTrips',0),'historic_midday_trips_both_directions':h.get('middayTrips',0),'historic_typical_midday_headway_min':h.get('headway'),'historic_midday_gap_min':h.get('gapMin'),'historic_midday_gap_max':h.get('gapMax'),'current_active':c.get('active',False),'current_day_trips':c.get('dayTrips',0),'current_midday_trips_both_directions':c.get('middayTrips',0),'current_typical_midday_headway_min':c.get('headway'),'current_midday_gap_min':c.get('gapMin'),'current_midday_gap_max':c.get('gapMax'),'note':r['note']})
# Exact archives and useful numbers for verification.
for period in ('historic','current'):
    rr=[r[period] for r in route_summary if r['kind']=='regular' and r[period] and r[period]['active']]
    print('TOTAL',period,'regular lines',len(rr),'midday trips',sum(r['middayTrips'] for r in rr),'<=15 min',sum(r['headway'] is not None and r['headway']<=15 for r in rr))
assert source_manifest['historic']['sha1']=='9babdd55bd0af8e510597e6906d896365f24cfcb'
assert networks['historic']['routes']['1']['headway']==15
assert networks['current']['routes']['1']['headway']==20
assert networks['historic']['routes']['28']['headway']==10
assert networks['current']['routes']['33']['active'] is False
assert len(route_summary)==48
print('Wrote',(OUT/'network.json').relative_to(ROOT),(OUT/'network.json').stat().st_size,'bytes')
