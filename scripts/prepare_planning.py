"""Evidence for the separate Saving MTD notebook—not a proposed future network.

Published data were manually transcribed and visually verified from Q4_FY26Report.pdf
PDF pages 2–3 (YTD columns = full FY2025–26). Counts are cross-checked against the
published system total. Special/aggregate services are kept, but not mixed into the
19-current-regular-line screening ranking. No operating-cost savings are invented.
"""
from pathlib import Path
import csv,json,hashlib
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
P={'asOf':'2026-10-15','period':'FY2025–26','periodStart':'2025-07-01','periodEnd':'2026-06-30','dateCaveat':'These full-year averages end June 30, 2026 and predate the August 2026 reductions. They are a screening baseline—not measured post-cut performance, trip-level demand or a cut list.',
'sources':{
'performance':{'title':'MTD FY2025–26 system ridership and productivity','url':source,'boardingsPage':2,'productivityPage':3,'localFile':'sources/Q4-FY26-ridership.pdf','sha256':hashlib.sha256((ROOT/'sources/Q4-FY26-ridership.pdf').read_bytes()).hexdigest(),'extraction':'Manual transcription of all nonzero fixed-route records, visually verified against rendered PDF pages 2–3. YTD columns are full fiscal-year figures; all boarding counts sum to the published system totals.'},
'budget':{'title':'FY2026–27 budget executive summary','url':'https://sbmtd.gov/wp-content/uploads/2026/05/20260602-Agenda-Packet.pdf#page=23','date':'2026-06-02','page':23,'localFile':'sources/20260602-budget-packet.pdf','sha256':hashlib.sha256((ROOT/'sources/20260602-budget-packet.pdf').read_bytes()).hexdigest(),'status':'Published FY2026–27 budget; not a newly estimated deficit'},
'campus':{'title':'UCSB student pass fee staff proposal','url':'https://sbmtd.gov/wp-content/uploads/2026/07/20260721-Board-Packet-v2-1.pdf#page=19','date':'2026-07-21','pages':[19,20,24],'localFile':'sources/20260721-annual-packet.pdf','sha256':hashlib.sha256((ROOT/'sources/20260721-annual-packet.pdf').read_bytes()).hexdigest(),'status':'Published staff proposal to pursue a Spring 2027 student vote; no new revenue is assumed or booked'}},
'system':{'annualBoardings':4524968,'annualRevenueHours':174453,'pph':25.9,'ucsbLineBoardings':ucsb,'ucsbLineShare':ucsb/4524968,'boosterPph':64.8,'boosterBoardings':174761,'temporaryReliefBudget':4935532,'reliefPercentOfOperatingRevenue':14,'budgetFiscalYear':'FY2026–27','reliefExhaustionForecast':'FY2028–29','currentCampusQuarterlyFee':18.76,'staffProposedCampusQuarterlyFee':45,'campusProposalBallot':'Spring 2027'},
'rows':rows,'regularIds':[r['id'] for r in core],'lowProductivityIds':[r['id'] for r in low[:5]],'highProductivityIds':[r['id'] for r in high[:5]],
'sharedTrunk':{'lines':['6','11'],'terminal':'Transit Center','direction':'Toward Goleta / UCSB','departures':tc,'combinedGapMin':15,'combinedGapMax':15,'combinedTypicalGap':15,'caveat':'These routes already alternate 15-minute departures from Transit Center in the sampled midday window. This is not a guarantee at every shared stop, not a proposed merge, and not a new saving.'},
'limits':['Line averages cannot identify the least-used individual trips. Request stop/trip-level boardings, loads and transfer counts.','Headway is not ridership. Low frequency does not establish low demand.','Renaming or combining route numbers does not by itself reduce buses, driver shifts or costs.','Any reduction needs vehicle-block/crew costing, accessibility and Title VI/equity review, and protected essential connections.','Seasonal line 33, timed Amtrak services and the aggregate school-booster record are preserved in the source export but excluded from the comparable 19-line ranking.'],
'planningStatus':'All options are independent study concepts, except the specifically attributed published staff funding proposal. No future network, automatic cut list or quantified savings plan is asserted.'}
(ROOT/'data/planning.json').write_text(json.dumps(P,separators=(',',':')))
with (ROOT/'data/route-performance-fy2025-26.csv').open('w',newline='') as f:
    cols=['line','current_name','reported_name','annual_boardings','annual_boardings_per_revenue_hour','q4_boardings','q4_boardings_per_revenue_hour','scope','active_2026_10_15','period_start','period_end','source_url','boardings_pdf_page','productivity_pdf_page']
    w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
    for r in rows:w.writerow({'line':r['id'],'current_name':r['name'],'reported_name':r['reportedName'],'annual_boardings':r['boardings'],'annual_boardings_per_revenue_hour':r['pph'],'q4_boardings':r['q4Boardings'],'q4_boardings_per_revenue_hour':r['q4Pph'],'scope':r['scope'],'active_2026_10_15':r['currentActive'],'period_start':'2025-07-01','period_end':'2026-06-30','source_url':source,'boardings_pdf_page':2,'productivity_pdf_page':3})
print('Planning evidence: 19 comparable lines; 24 published records; all boardings reconcile. Lowest PPH:',[(r['id'],r['pph']) for r in low[:5]])
print('6/11 TC departures already alternate every 15 min. UCSB-line share:',round(100*P['system']['ucsbLineShare'],2),'%. No savings estimate produced.')
