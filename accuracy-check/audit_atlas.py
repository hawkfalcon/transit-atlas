"""Independent accuracy audit. Reads original ZIPs/PDFs; never imports the production calculators.
Run from any directory: python accuracy-check/audit_atlas.py
Needs Shapely and PyMuPDF. Does not edit the app or re-download sources.
"""
from pathlib import Path
from datetime import date
from collections import defaultdict
from statistics import median
import csv,io,json,zipfile,math,hashlib,re
import pymupdf
from shapely.geometry import LineString,MultiLineString

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'accuracy-check'
D=json.loads((ROOT/'data/network.json').read_text());P=json.loads((ROOT/'data/planning.json').read_text())
profiles={r['id']:r for r in D['routes']}
report={'checked_local_date':'2026-10-24','method':'Separate parser of original GTFS ZIPs; direct PDF word-coordinate extraction; no production functions imported.','source_integrity':[],'metric_differences':[],'direction_differences':[],'geometry':[],'stops':[],'performance_differences':[],'summary':{},'source_warnings':[]}
trip_export=[];tc=[];all_ids=set()

def time_seconds(s):
    a=s.split(':');return int(a[0])*3600+int(a[1])*60+int(a[2])
def same(a,b):
    return abs(a-b)<.0011 if isinstance(a,(int,float)) and isinstance(b,(int,float)) else a==b
def project(lon,lat):return (lon*111320*math.cos(math.radians(34.43)),lat*110950)
def check_fields(diffs,key,expected,actual):
    for field,x in expected.items():
        if not same(x,actual.get(field)):diffs.append({'record':key,'field':field,'expected':x,'actual':actual.get(field)})

for period,filename,iso in [('historic','historic-feed-20190819.zip','2019-10-15'),('current','current-feed.zip','2026-10-15')]:
    raw=(ROOT/'sources'/filename).read_bytes();source=D['sources'][period]
    report['source_integrity'].append({'period':period,'sha1':hashlib.sha1(raw).hexdigest(),'sha256_matches':hashlib.sha256(raw).hexdigest()==source['sha256'],'bytes_match':len(raw)==source['bytes']})
    z=zipfile.ZipFile(io.BytesIO(raw))
    def table(name, z=z):
        return list(csv.DictReader(io.StringIO(z.read(name+'.txt').decode('utf-8-sig')))) if name+'.txt' in z.namelist() else []
    calendars=table('calendar');exceptions=table('calendar_dates')
    def services(iso_day, calendars=calendars, exceptions=exceptions):
        day=date.fromisoformat(iso_day);key=day.strftime('%Y%m%d');wd=('monday','tuesday','wednesday','thursday','friday','saturday','sunday')[day.weekday()]
        selected=set()
        for c in calendars:
            if c[wd]=='1' and c['start_date']<=key<=c['end_date']:selected.add(c['service_id'])
        for e in exceptions:
            if e['date']==key:
                if e['exception_type']=='1':selected.add(e['service_id'])
                elif e['exception_type']=='2':selected.discard(e['service_id'])
        return selected
    active=services(iso);routes=table('routes');trips=table('trips');by_id={t['trip_id']:t for t in trips}
    assert sorted(active)==source['active_service_ids']
    assert not table('frequencies'),'Frequency-based trips would need expansion.'
    first={};last={};trip_stops=defaultdict(set)
    for st in table('stop_times'):
        tid=st['trip_id']
        if by_id[tid]['service_id'] not in active:continue
        seq=int(st['stop_sequence']);trip_stops[tid].add(st['stop_id'])
        if st.get('arrival_time') and (tid not in last or seq>last[tid][0]):last[tid]=(seq,time_seconds(st['arrival_time']))
        if st.get('pickup_type','0')!='1' and st.get('departure_time') and (tid not in first or seq<first[tid][0]):first[tid]=(seq,time_seconds(st['departure_time']),st['stop_id'])
    stops={s['stop_id']:s for s in table('stops')}
    shapes=defaultdict(list)
    for pt in table('shapes'):shapes[pt['shape_id']].append((int(pt['shape_pt_sequence']),float(pt['shape_pt_lon']),float(pt['shape_pt_lat'])))
    shape_geometry={sid:LineString([project(x,y) for _,x,y in sorted(pts)]) for sid,pts in shapes.items() if len(pts)>1}
    by_route=defaultdict(list)
    for t in trips:by_route[t['route_id']].append(t)
    period_metrics={};expected_stop_routes=defaultdict(set)
    for route in routes:
        rid=route['route_short_name'].upper();all_ids.add(rid);stored=profiles[rid][period]
        scheduled=[t for t in by_route[route['route_id']] if t['service_id'] in active]
        valid=[t for t in scheduled if t['trip_id'] in first]
        dirs=defaultdict(list);durations=[];all_stops=set()
        for t in valid:
            tid=t['trip_id'];_,sec,stop=first[tid]
            dirs[t.get('direction_id') or '0'].append((sec,tid,stop))
            durations.append(max(0,last[tid][1]-sec)/3600);all_stops.update(trip_stops[tid])
            for sid in trip_stops[tid]:expected_stop_routes[sid].add(rid)
            trip_export.append({'period':period,'date':iso,'line':rid,'trip_id':tid,'direction':t.get('direction_id') or '0','first_boardable_stop':stops[stop]['stop_name'],'departure':f'{sec//3600:02}:{sec//60%60:02}:{sec%60:02}','midday':36000<=sec<50400})
            if period=='current' and rid in ('6','11') and stops[stop]['stop_name']=='Transit Center' and 36000<=sec<50400:tc.append((sec,rid))
        all_gaps=[];dir_window=[];ds={d['id']:d for d in stored['directions']}
        for direction,starts in dirs.items():
            starts.sort();seconds=[s[0] for s in starts]
            windows=[t for t in seconds if 36000<=t<50400]
            gaps=[(b-a)/60 for a,b in zip(seconds,seconds[1:]) if a<b and 72000<=a+b<100800]
            all_gaps+=gaps;dir_window.append(len(windows))
            regular=len(windows)>=2 and bool(gaps)
            expected={'dayTrips':len(starts),'middayTrips':len(windows),'first':min(seconds),'last':max(seconds),'middayDepartureSeconds':windows,'headway':round(median(gaps),3) if regular else None,'gapMin':round(min(gaps),3) if regular else None,'gapMax':round(max(gaps),3) if regular else None}
            check_fields(report['direction_differences'],f'{period}/{rid}/{direction}',expected,ds[direction])
        seconds=sorted(first[t['trip_id']][1] for t in valid)
        regular=max(dir_window,default=0)>=2 and bool(all_gaps)
        expected={'name':route['route_long_name'],'gtfsId':route['route_id'],'active':bool(valid),'dayTrips':len(valid),'middayTrips':sum(36000<=t<50400 for t in seconds),'headway':round(median(all_gaps),3) if regular else None,'gapMin':round(min(all_gaps),3) if regular else None,'gapMax':round(max(all_gaps),3) if regular else None,'first':min(seconds) if seconds else None,'last':max(seconds) if seconds else None,'stopCount':len(all_stops),'scheduledTripHours':round(sum(durations),3),'middayDepartureSeconds':[s for s in seconds if 36000<=s<50400]}
        check_fields(report['metric_differences'],f'{period}/{rid}',expected,stored)
        period_metrics[rid]=expected
        used={t['shape_id'] for t in (scheduled or by_route[route['route_id']]) if t.get('shape_id') in shape_geometry}
        displayed=[LineString([project(lon,lat) for lat,lon in path]) for path in stored['paths'] if len(path)>1]
        if used:
            original=MultiLineString([shape_geometry[sid] for sid in used]);exported=MultiLineString(displayed)
            dist=original.hausdorff_distance(exported)
            report['geometry'].append({'period':period,'line':rid,'source_shape_count':len(used),'displayed_path_count':len(displayed),'hausdorff_distance_m':round(dist,4),'within_3_2_m':dist<=3.2})
        else:assert not displayed
    core=[(rid,v) for rid,v in period_metrics.items() if profiles[rid]['kind']=='regular' and v['active']]
    report['summary'][period]={'regular_lines':len(core),'midday_departures':sum(v['middayTrips'] for _,v in core),'frequent_lines':[rid for rid,v in core if v['headway'] is not None and v['headway']<=15],'route_records':len(routes),'active_route_records':sum(v['active'] for v in period_metrics.values())}
    exported_ids={s['id'] for s in D['stops'][period]}
    mismatches=[f'missing:{sid}' for sid in set(expected_stop_routes)-exported_ids]
    for s in D['stops'][period]:
        original=stops[s['id']]
        if s['lat']!=round(float(original['stop_lat']),6) or s['lon']!=round(float(original['stop_lon']),6) or set(s['routes'])!=expected_stop_routes[s['id']]:mismatches.append(s['id'])
    report['stops'].append({'period':period,'checked':len(D['stops'][period]),'mismatches':mismatches})
    if period=='current':
        seasonal=next((r for r in routes if r['route_short_name']=='33'),None)
        active_oct_weekdays=[]
        for n in range(1,32):
            dd=f'2026-10-{n:02}'
            if date.fromisoformat(dd).weekday()<5 and any(t['service_id'] in services(dd) for t in by_route[seasonal['route_id']]):active_oct_weekdays.append(dd)
        report['summary']['seasonal_33_october_weekdays_with_trips']=active_oct_weekdays
assert all_ids==set(profiles)
base=report['summary']['historic']['midday_departures'];now=report['summary']['current']['midday_departures']
report['summary']['decline_departures']=base-now;report['summary']['decline_percent']=100*(base-now)/base
report['summary']['missing_2019_regular_routes']=[r['id'] for r in D['routes'] if r['kind']=='regular' and (r['historic'] or {}).get('active') and not (r['current'] or {}).get('active')]
tc.sort();report['summary']['6_11_tc_gaps_min']=sorted(set((b[0]-a[0])/60 for a,b in zip(tc,tc[1:])));assert report['summary']['6_11_tc_gaps_min']==[15]
report['summary']['tc_departures']=[{'line':rid,'seconds':sec} for sec,rid in tc]

for key,src in P['sources'].items():
    raw=(ROOT/src['localFile']).read_bytes()
    report['source_integrity'].append({'source':key,'sha256_matches':hashlib.sha256(raw).hexdigest()==src['sha256']})

# Re-extract numerical cells directly from original PDF text coordinates, not the transcription CSV.
pdf=pymupdf.open(ROOT/'sources/Q4-FY26-ridership.pdf')
def pdf_values(page_number):
    words=pdf[page_number-1].get_text('words');result={}
    for x0,y0,_,_,text,*_ in words:
        rid=text.upper()
        if not (95<y0<550):continue
        if not ((45<x0<73 and re.fullmatch(r'\d{1,2}X?',rid)) or (rid=='BOOSTER' and 70<x0<85)):continue
        if rid=='BOOSTER':rid='BOOSTERS'
        cells=[(a,t) for a,b,c,d,t,*_ in words if abs(b-y0)<1.1]
        q=[t for a,t in cells if 235<a<290 and re.fullmatch(r'[\d,]+(?:\.\d+)?',t)]
        annual=[t for a,t in cells if 400<a<460 and re.fullmatch(r'[\d,]+(?:\.\d+)?',t)]
        if q and annual:result[rid]={'q4':float(q[0].replace(',','')),'annual':float(annual[0].replace(',',''))}
    return result
counts=pdf_values(2);pph=pdf_values(3)
for row in P['rows']:
    rid=row['id']
    check_fields(report['performance_differences'],rid,{'boardings':int(counts[rid]['annual']),'q4Boardings':int(counts[rid]['q4']),'pph':pph[rid]['annual'],'q4Pph':pph[rid]['q4']},row)
report['summary']['performance_rows_checked']=len(P['rows'])
report['summary']['annual_fixed_route_boardings']=sum(int(counts[r['id']]['annual']) for r in P['rows'])
report['summary']['q4_fixed_route_boardings']=sum(int(counts[r['id']]['q4']) for r in P['rows'])
regular=[r for r in P['rows'] if r['id'] in P['regularIds']]
report['summary']['lowest_pph']=[{'line':r['id'],'pph':r['pph']} for r in sorted(regular,key=lambda r:r['pph'])[:5]]
report['summary']['highest_pph']=[{'line':r['id'],'pph':r['pph']} for r in sorted(regular,key=lambda r:-r['pph'])[:5]]
report['summary']['ucsb_route_boardings']=sum(counts[rid]['annual'] for rid in ['11','24X','27','28'])
report['summary']['ucsb_route_boarding_share']=report['summary']['ucsb_route_boardings']/report['summary']['annual_fixed_route_boardings']
budget=pymupdf.open(ROOT/'sources/20260602-budget-packet.pdf')[22].get_text()
campus=pymupdf.open(ROOT/'sources/20260721-annual-packet.pdf')
report['financial_checks']={'budget_4935532': '$4,935,532' in budget,'budget_14_percent':'14%' in budget,'relief_exhaustion_FY2028_29':'2028-29' in budget,'fee_18_76':'$18.76' in campus[19].get_text(),'proposed_fee_45':'$45.00' in campus[23].get_text(),'proposed_vote_spring_2027':'Spring 2027' in campus[23].get_text(),'annual_COLA_0_to_4_percent':'4%' in campus[23].get_text()}
report['summary']['geometry_max_difference_m']=max(g['hausdorff_distance_m'] for g in report['geometry'])
report['summary']['geometry_profiles_checked']=len(report['geometry'])
report['result']='pass' if not (report['metric_differences'] or report['direction_differences'] or report['performance_differences'] or any(not x['within_3_2_m'] for x in report['geometry']) or any(x['mismatches'] for x in report['stops']) or not all(report['financial_checks'].values()) or any(not s['sha256_matches'] for s in report['source_integrity'])) else 'corrections-needed'
OUT.mkdir(exist_ok=True)
(OUT/'independent-audit.json').write_text(json.dumps(report,indent=2))
with (OUT/'source-departures.csv').open('w',newline='',encoding='utf-8') as f:
    # LF endings so a fresh run reproduces the committed file byte for byte.
    w=csv.DictWriter(f,fieldnames=list(trip_export[0]),lineterminator='\n');w.writeheader();w.writerows(trip_export)
print(json.dumps({k:v for k,v in report.items() if k not in ('geometry',)},indent=2))
