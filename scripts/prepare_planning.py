"""Evidence for the separate Saving MTD notebook—not a proposed future network.

Published data were manually transcribed and visually verified from Q4_FY26Report.pdf
PDF pages 2–3 (YTD columns = full FY2025–26). Counts are cross-checked against the
published system total. Special/aggregate services are kept, but not mixed into the
19-current-regular-line screening ranking. No operating-cost savings are invented.

The route-overlap screen reads the bundled current GTFS feed directly: dissolved
route shapes within a 25-metre street buffer, stops served by both routes, and the
trips.block_id values that reveal whether one bus already runs both routes
(interlining). A rename of an interlined pair cannot remove a bus or driver shift,
so only separate-block pairs are cut/merge study candidates.
"""
from pathlib import Path
import csv,json,hashlib,zipfile,math,itertools
from shapely.geometry import LineString,Point
from shapely.ops import unary_union,linemerge,substring
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/network.json').read_text())
source='https://sbmtd.gov/wp-content/uploads/2026/07/Q4_FY26Report.pdf'
network={r['id']:r for r in D['routes']}
rows=[]
with (ROOT/'sources/fy2025-26-route-performance.csv').open() as f:
    for raw in csv.DictReader(f):
        rid=raw['line'];n=network.get(rid)
        rows.append({'id':rid,'name':n['name'] if n else raw['reported_name'],'reportedName':raw['reported_name'],'boardings':int(raw['annual_boardings']),'pph':float(raw['annual_boardings_per_revenue_hour']),'q4Boardings':int(raw['q4_boardings']),'q4Pph':float(raw['q4_boardings_per_revenue_hour']),'scope':raw['scope'],'currentActive':bool(n and n['current'] and n['current']['active'])})
assert sum(r['boardings'] for r in rows)==4524968
assert sum(r['q4Boardings'] for r in rows)==1172298
core=[r for r in rows if r['scope']=='regular' and r['currentActive']]
assert len(core)==19
low=sorted(core,key=lambda r:(r['pph'],r['id']))
high=sorted(core,key=lambda r:(-r['pph'],r['id']))
assert [r['id'] for r in low[:5]]==['19X','23','14','5','3']
assert [r['id'] for r in high[:4]]==['28','27','24X','11']
ucsb=sum(r['boardings'] for r in rows if r['id'] in ['11','24X','27','28'])
assert ucsb==2083620
# Actual shared-terminal starts, not an assumption that either route has 15-minute
# service all along its length. At TC the two already alternate in this sample.
tc=[]
for rid in ['6','11']:
    rec=network[rid]['current']
    for direction in rec['directions']:
        if direction['terminal']=='Transit Center':
            tc.extend({'seconds':t,'line':rid} for t in direction['middayDepartureSeconds'])
tc.sort(key=lambda r:r['seconds'])
gaps=[(b['seconds']-a['seconds'])/60 for a,b in zip(tc,tc[1:])]
assert gaps and min(gaps)==max(gaps)==15

# --- Route overlap screen: duplicated corridors that could be cut or merged ----
# Three independent GTFS signals, all from the sampled current weekday:
#   geometry  - dissolved route shapes within a 25 m street buffer (both directions)
#   stops     - stops served by both routes, so riders could actually switch
#   blocks    - shared trips.block_id values: one bus already runs both routes
# Pairs already interlined on shared blocks are screened out of the candidate list:
# merging their line numbers removes no vehicle assignment or paid driver hour.
OVERLAP_BUFFER_M=25
CANDIDATE_MIN_M=10_000
CANDIDATE_MIN_STOPS=5
CANDIDATE_MAX_SHARED_BLOCKS=1
regular_set={r['id'] for r in core}
active_service=set(D['sources']['current']['active_service_ids'])
def route_key(rid):
    return (1 if rid.endswith('X') else 0, int(rid[:-1]) if rid.endswith('X') else int(rid))
def pair_key(a,b):
    return tuple(sorted((a,b),key=route_key))
with zipfile.ZipFile(ROOT/'sources/current-feed.zip') as zf:
    trip_route={}; trip_block={}; trip_shape={}; shape_routes={}; shape_trip_counts={}
    with zf.open('trips.txt') as fh:
        for t in csv.DictReader(line.decode() for line in fh):
            if t['service_id'] not in active_service or t['route_id'] not in regular_set:
                continue
            trip_route[t['trip_id']]=t['route_id']
            trip_block[t['trip_id']]=t['block_id']
            trip_shape[t['trip_id']]=t['shape_id']
            shape_routes.setdefault(t['shape_id'],set()).add(t['route_id'])
            skey=(t['route_id'],t['direction_id'],t['shape_id'])
            shape_trip_counts[skey]=shape_trip_counts.get(skey,0)+1
    # Local equirectangular metre projection; sub-metre accuracy is not needed
    # for a 25 m street-level buffer at this latitude.
    lat0=34.43
    mx=111_320.0*math.cos(math.radians(lat0)); my=111_320.0
    def project(lon,lat):
        return ((lon+119.7)*mx,(lat-lat0)*my)
    raw_shapes={}
    with zf.open('shapes.txt') as fh:
        for s in csv.DictReader(line.decode() for line in fh):
            raw_shapes.setdefault(s['shape_id'],[]).append(
                (int(s['shape_pt_sequence']),project(float(s['shape_pt_lon']),float(s['shape_pt_lat']))))
    shape_geoms={}; shape_line_geoms={}
    for sid,points in raw_shapes.items():
        points.sort()
        if len(points)<2:
            continue
        line=LineString([p for _,p in points]).simplify(10)
        shape_line_geoms[sid]=line
        for rid in shape_routes.get(sid,()):
            shape_geoms.setdefault(rid,[]).append(line)
    route_geom={rid:unary_union(lines).simplify(5) for rid,lines in shape_geoms.items()}
    assert set(route_geom)==regular_set
    route_buffer={rid:g.buffer(OVERLAP_BUFFER_M) for rid,g in route_geom.items()}
    stop_routes={};shape_stops={}
    with zf.open('stop_times.txt') as fh:
        for st in csv.DictReader(line.decode() for line in fh):
            rid=trip_route.get(st['trip_id'])
            if rid:
                stop_routes.setdefault(st['stop_id'],set()).add(rid)
                shape_stops.setdefault(trip_shape[st['trip_id']],set()).add(st['stop_id'])
route_stops={rid:set() for rid in regular_set}
for stop_id,rids in stop_routes.items():
    for rid in rids:
        route_stops[rid].add(stop_id)
block_routes={}
for trip_id,block in trip_block.items():
    block_routes.setdefault(block,set()).add(trip_route[trip_id])
pair_blocks={}
for rids in block_routes.values():
    for a,b in itertools.combinations(sorted(rids,key=route_key),2):
        pair_blocks[pair_key(a,b)]=pair_blocks.get(pair_key(a,b),0)+1
def midday(rid,field):
    return network[rid]['current'].get(field)
overlap_rows=[]
for a,b in itertools.combinations(sorted(route_geom,key=route_key),2):
    shared_m=route_geom[a].intersection(route_buffer[b]).length
    if shared_m<150:
        continue
    key=pair_key(a,b)
    overlap_rows.append({'a':key[0],'b':key[1],'sharedMeters':round(shared_m),
                         'sharedStops':len(route_stops[a]&route_stops[b]),
                         'sharedBlocks':pair_blocks.get(key,0)})
def as_candidate(row):
    rid_a,rid_b=row['a'],row['b']
    shorter=min(route_geom[rid_a].length,route_geom[rid_b].length)
    return {'a':rid_a,'b':rid_b,'sharedMeters':row['sharedMeters'],'sharedKm':round(row['sharedMeters']/1000,1),
            'pctOfShorter':round(100*row['sharedMeters']/shorter),'sharedStops':row['sharedStops'],
            'middayA':midday(rid_a,'middayTrips'),'middayB':midday(rid_b,'middayTrips'),
            'headwayA':midday(rid_a,'headway'),'headwayB':midday(rid_b,'headway'),
            'sharedBlocks':row['sharedBlocks']}
candidates=sorted((as_candidate(r) for r in overlap_rows
                   if r['sharedMeters']>=CANDIDATE_MIN_M and r['sharedStops']>=CANDIDATE_MIN_STOPS
                   and r['sharedBlocks']<=CANDIDATE_MAX_SHARED_BLOCKS),
                  key=lambda r:(-r['sharedMeters'],r['a'],r['b']))
coordinated=sorted(({'a':r['a'],'b':r['b'],'sharedKm':round(r['sharedMeters']/1000,1),
                     'sharedStops':r['sharedStops'],'sharedBlocks':r['sharedBlocks']}
                    for r in overlap_rows if r['sharedBlocks']>=3),
                   key=lambda r:(-r['sharedBlocks'],-r['sharedKm']))
no_stop_pairs=[{'a':r['a'],'b':r['b'],'sharedKm':round(r['sharedMeters']/1000,1)}
               for r in overlap_rows if r['sharedMeters']>=CANDIDATE_MIN_M and r['sharedStops']==0]
# Pinned findings for this frozen feed; review if the GTFS inputs are replaced.
assert [(r['a'],r['b']) for r in candidates]==[('15X','24X'),('20','19X'),('11','24X'),('7','12X'),
                                                ('11','15X'),('6','12X'),('14','20')]
assert all(r['sharedBlocks']<=1 for r in candidates)
assert [(r['a'],r['b']) for r in coordinated][:2]==[('6','11'),('6','25')]
six_eleven=next(r for r in coordinated if (r['a'],r['b'])==('6','11'))
assert six_eleven['sharedBlocks']==14 and six_eleven['sharedStops']==76
assert {(r['a'],r['b']) for r in no_stop_pairs}=={('7','15X'),('12X','15X')}
# Two deliberately selected, non-express redesign studies replace the generic
# overlap ranking in the public panel. Route 17 is retained as a useful control;
# historic 16 is context only, not current service.
def geometry_paths(g):
    if g.is_empty:
        return []
    if g.geom_type=='MultiLineString':
        g=linemerge(g)
    if g.geom_type=='LineString':
        lines=[g]
    elif g.geom_type in ('MultiLineString','GeometryCollection'):
        lines=[]
        for part in g.geoms:
            if part.geom_type=='LineString':
                lines.append(part)
            else:
                lines.extend(LineString(coords) for coords in _line_parts(part))
    else:
        return []
    return [[[round(y/my+lat0,6),round(x/mx-119.7,6)] for x,y in line.coords]
            for line in lines if len(line.coords)>1]
def _line_parts(g):
    if g.geom_type=='LineString':
        return [g.coords]
    if g.geom_type in ('MultiLineString','GeometryCollection'):
        return [coords for part in g.geoms for coords in _line_parts(part)]
    return []
def main_shape(route_id,direction):
    choices=[(count,sid) for (rid,d,sid),count in shape_trip_counts.items() if rid==route_id and d==direction]
    assert choices
    return max(choices)[1],max(choices)[0]
def stop_point(name,line):
    candidates=[s for s in D['stops']['current'] if s['name']==name]
    assert candidates,name
    return min((Point(project(s['lon'],s['lat'])) for s in candidates),key=line.distance)
def segment(line,start_name,end_name):
    start=line.project(stop_point(start_name,line));end=line.project(stop_point(end_name,line))
    part=substring(line,min(start,end),max(start,end))
    coords=list(part.coords)
    return LineString(coords if start<=end else coords[::-1])
def join_segments(*segments):
    coords=[]
    for line in segments:
        points=list(line.coords)
        gap=math.dist(coords[-1],points[0]) if coords else 0
        if gap>100:
            raise ValueError(f'Proposal segments do not connect at the named junction: {gap:.1f} m gap')
        if coords and gap<2:
            points=points[1:]
        coords.extend(points)
    return LineString(coords)
# Simplified single 4/5 line in both directions: keep Route 4's
# Transit Center -> Carrillo/Meigs -> Cliff approach, then continue on Route 5's
# Cliff -> Mesa -> La Cumbre segment. Do not add Route 17's SBCC branch to the
# merged line; show Route 17's current SBCC path separately on the map.
r4_out=shape_line_geoms[main_shape('4','0')[0]]
r5_out,route5_primary_trip_count=main_shape('5','0')
r5_line=shape_line_geoms[r5_out]
route45_path=join_segments(r4_out,segment(r5_line,'Cliff & Loma Alta','State & La Cumbre 156'))
# Single 14/20 line in both directions: North Jameson -> Transit Center ->
# Via Real/Carpinteria. Use Route 14's TC-to-North-Jameson shape in reverse and
# Route 20's Via-Real-to-TC shape in reverse; the lines meet at TC without
# retracing their shared downtown/coastal geometry.
r14_tc_to_north=shape_line_geoms[main_shape('14','0')[0]]
r20_tc_to_viareal=shape_line_geoms[main_shape('20','0')[0]]
r14_to_tc=segment(r14_tc_to_north,'North Jameson & Sheffield','Transit Center')
r20_from_tc=segment(r20_tc_to_viareal,'Transit Center','Via Real & Mark')
assert r14_to_tc.intersection(r20_from_tc).length<25
route1420_path=join_segments(r14_to_tc,r20_from_tc)
def proposal_stop_coords(path,ids):
    chosen=[s for s in D['stops']['current'] if ids.intersection(s['routes'])
            and path.distance(Point(project(s['lon'],s['lat'])))<=OVERLAP_BUFFER_M]
    return [[s['lat'],s['lon']] for s in chosen]
def pair_evidence(a,b,proposed_path,route5_pattern=False):
    row=next(r for r in overlap_rows if (r['a'],r['b'])==pair_key(a,b))
    x,y=network[a]['current'],network[b]['current']
    coords=proposal_stop_coords(proposed_path,{a,b})
    return {'a':a,'b':b,'sharedMeters':row['sharedMeters'],'sharedKm':round(row['sharedMeters']/1000,1),
            'sharedStops':row['sharedStops'],'sharedBlocks':row['sharedBlocks'],
            'middayA':x.get('middayTrips'),'middayB':y.get('middayTrips'),
            'dayTripsA':x.get('dayTrips'),'dayTripsB':y.get('dayTrips'),
            'headwayA':x.get('headway'),'headwayB':y.get('headway'),
            'proposedLengthKm':round(proposed_path.length/1000,1),
            'proposedRouteStops':len(coords),'proposedPaths':geometry_paths(proposed_path),
            'proposedStopCoords':coords,
            'patternShape':r5_out if route5_pattern else None,
            'patternTrips':route5_primary_trip_count if route5_pattern else None}
proposals={'route45':pair_evidence('4','5',route45_path,True),
           'route1420':pair_evidence('14','20',route1420_path),
           'keep17':{'id':'17','name':network['17']['name'],'dayTrips':network['17']['current']['dayTrips'],
                     'middayTrips':network['17']['current']['middayTrips'],'headway':network['17']['current']['headway'],
                     'sharedBlocksWith4':pair_blocks.get(pair_key('4','17'),0)},
           'historic16':{'id':'16','name':network['16']['name'],'active':False,
                         'dayTrips':network['16']['historic']['dayTrips'],
                         'middayTrips':network['16']['historic']['middayTrips'],
                         'headway':network['16']['historic']['headway'],
                         'note':'2019 historical service; absent from the October 2026 current feed.'}}
assert proposals['route45']['sharedKm']==5.3 and proposals['route45']['sharedStops']==14 and proposals['route45']['sharedBlocks']==0
assert proposals['route45']['patternShape']=='shp-5-51' and proposals['route45']['patternTrips']==11
assert proposals['route45']['proposedLengthKm']==17.1 and proposals['route45']['proposedRouteStops']==59
assert proposals['route1420']['sharedKm']==11.5 and proposals['route1420']['sharedStops']==23 and proposals['route1420']['sharedBlocks']==0
assert proposals['route1420']['proposedLengthKm']==38.9 and proposals['route1420']['proposedRouteStops']==119
assert route1420_path.distance(stop_point('Transit Center',route1420_path))<25
assert proposals['route1420']['proposedPaths']
assert proposals['route45']['proposedPaths'] and proposals['route1420']['proposedPaths']
assert proposals['keep17']['sharedBlocksWith4']==4 and proposals['historic16']['active'] is False
overlaps={'method':{'bufferMeters':OVERLAP_BUFFER_M,'minSharedMeters':CANDIDATE_MIN_M,
                    'minSharedStops':CANDIDATE_MIN_STOPS,'maxSharedBlocks':CANDIDATE_MAX_SHARED_BLOCKS,
                    'geometryBasis':'Current GTFS shapes for trips active on October 15, 2026, dissolved by line in a local metre projection; shared length is route geometry inside a 25-metre buffer, including both directions and loops.',
                    'stopBasis':'Stops served by both lines in stop_times.txt on the sampled weekday; a shared freeway alignment without shared stops is not rider-substitutable.',
                    'blockBasis':'trips.block_id values used by both lines; a shared block means one bus and one driver already run both routes (interlining).',
                    'caveat':'Screening output, not a cut list. Candidate pairs still need trip-level loads, vehicle/crew costing, access and Title VI review, and a reversible trial.'},
          'candidates':candidates,'coordinated':coordinated,'noSharedStops':no_stop_pairs,'proposals':proposals}
P={'asOf':'2026-10-15','period':'FY2025–26','periodStart':'2025-07-01','periodEnd':'2026-06-30','dateCaveat':'These full-year averages end June 30, 2026 and predate the August 2026 reductions. They are a screening baseline—not measured post-cut performance, trip-level demand or a cut list.',
'sources':{
'performance':{'title':'MTD FY2025–26 system ridership and productivity','url':source,'boardingsPage':2,'productivityPage':3,'localFile':'sources/Q4-FY26-ridership.pdf','sha256':hashlib.sha256((ROOT/'sources/Q4-FY26-ridership.pdf').read_bytes()).hexdigest(),'extraction':'Manual transcription of all nonzero fixed-route records, visually verified against rendered PDF pages 2–3. YTD columns are full fiscal-year figures; all boarding counts sum to the published system totals.'},
'budget':{'title':'FY2026–27 budget executive summary','url':'https://sbmtd.gov/wp-content/uploads/2026/05/20260602-Agenda-Packet.pdf#page=23','date':'2026-06-02','page':23,'localFile':'sources/20260602-budget-packet.pdf','sha256':hashlib.sha256((ROOT/'sources/20260602-budget-packet.pdf').read_bytes()).hexdigest(),'status':'Published FY2026–27 budget; not a newly estimated deficit'},
'campus':{'title':'UCSB student pass fee staff proposal','url':'https://sbmtd.gov/wp-content/uploads/2026/07/20260721-Board-Packet-v2-1.pdf#page=19','date':'2026-07-21','pages':[19,20,24],'localFile':'sources/20260721-annual-packet.pdf','sha256':hashlib.sha256((ROOT/'sources/20260721-annual-packet.pdf').read_bytes()).hexdigest(),'status':'Published staff proposal to pursue a Spring 2027 student vote; no new revenue is assumed or booked'}},
'system':{'annualBoardings':4524968,'annualRevenueHours':174453,'pph':25.9,'ucsbLineBoardings':ucsb,'ucsbLineShare':ucsb/4524968,'boosterPph':64.8,'boosterBoardings':174761,'temporaryReliefBudget':4935532,'reliefPercentOfOperatingRevenue':14,'budgetFiscalYear':'FY2026–27','reliefExhaustionForecast':'FY2028–29','currentCampusQuarterlyFee':18.76,'staffProposedCampusQuarterlyFee':45,'campusProposalBallot':'Spring 2027'},
'rows':rows,'regularIds':[r['id'] for r in core],'lowProductivityIds':[r['id'] for r in low[:5]],'highProductivityIds':[r['id'] for r in high[:5]],
'sharedTrunk':{'lines':['6','11'],'terminal':'Transit Center','direction':'Toward Goleta / UCSB','departures':tc,'combinedGapMin':15,'combinedGapMax':15,'combinedTypicalGap':15,'caveat':'These routes already alternate 15-minute departures from Transit Center in the sampled midday window. This is not a guarantee at every shared stop, not a proposed merge, and not a new saving.'},
'overlaps':overlaps,
'limits':['Line averages cannot identify the least-used individual trips. Request stop/trip-level boardings, loads and transfer counts.','Headway is not ridership. Low frequency does not establish low demand.','Renaming or combining route numbers does not by itself reduce buses, driver shifts or costs.','Any reduction needs vehicle-block/crew costing, accessibility and Title VI/equity review, and protected essential connections.','Seasonal line 33, timed Amtrak services and the aggregate school-booster record are preserved in the source export but excluded from the comparable 19-line ranking.'],
'planningStatus':'All options are independent study concepts, except the specifically attributed published staff funding proposal. No future network, automatic cut list or quantified savings plan is asserted.'}
(ROOT/'data/planning.json').write_text(json.dumps(P,separators=(',',':')))
with (ROOT/'data/route-performance-fy2025-26.csv').open('w',newline='') as f:
    cols=['line','current_name','reported_name','annual_boardings','annual_boardings_per_revenue_hour','q4_boardings','q4_boardings_per_revenue_hour','scope','active_2026_10_15','period_start','period_end','source_url','boardings_pdf_page','productivity_pdf_page']
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
    for r in rows:w.writerow({'line':r['id'],'current_name':r['name'],'reported_name':r['reportedName'],'annual_boardings':r['boardings'],'annual_boardings_per_revenue_hour':r['pph'],'q4_boardings':r['q4Boardings'],'q4_boardings_per_revenue_hour':r['q4Pph'],'scope':r['scope'],'active_2026_10_15':r['currentActive'],'period_start':'2025-07-01','period_end':'2026-06-30','source_url':source,'boardings_pdf_page':2,'productivity_pdf_page':3})
print('Planning evidence: 19 comparable lines; 24 published records; all boardings reconcile. Lowest PPH:',[(r['id'],r['pph']) for r in low[:5]])
print('6/11 TC departures already alternate every 15 min. UCSB-line share:',round(100*P['system']['ucsbLineShare'],2),'%. No savings estimate produced.')
print('Overlap screen:',len(candidates),'separate-block cut/merge candidates;',len(coordinated),'pairs already interlined on shared blocks; freeway-only exclusions:',[(r['a'],r['b']) for r in no_stop_pairs])
