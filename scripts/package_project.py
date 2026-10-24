"""Curated, reproducible bundle. Excludes prior revisions and research scratch files."""
from pathlib import Path
import zipfile,json,shutil
ROOT=Path(__file__).resolve().parents[1]
files=[
'Santa-Barbara-Transit-Atlas.html','index.html','README.md','NOTICE.md','requirements.txt',
'data/route-comparison.csv','data/route-performance-fy2025-26.csv','data/network.json','data/planning.json','data/provenance.json','data/calculation-log.txt',
'scripts/prepare_data.py','scripts/prepare_planning.py','scripts/build_atlas.py','scripts/package_project.py',
'sources/historic-feed-20190819.zip','sources/current-feed.zip','sources/fy2025-26-route-performance.csv','sources/Q4-FY26-ridership.pdf','sources/20260721-annual-packet.pdf','sources/20260602-budget-packet.pdf',
'assets/index.template.html','assets/app.js','assets/app.css','assets/saving-tab.html','assets/saving.js','assets/saving.css',
'assets/leaflet.js','assets/leaflet.css','assets/leaflet-license.txt','assets/manrope.ttf','assets/manrope-license.txt','assets/basemap.webp','assets/basemap-bounds.json','assets/basemap-source.json',
 'tests/test_atlas.py','tests/test-report.json','tests/timetable-fingerprint.json',
'Accuracy-Check.md','accuracy-check/audit_atlas.py','accuracy-check/independent-audit.json','accuracy-check/before-corrections.json','accuracy-check/corrections.json','accuracy-check/live-source-check.json','accuracy-check/source-links.json','accuracy-check/source-departures.csv']
report=json.loads((ROOT/'tests/test-report.json').read_text())
assert report['version']==2 and not report['errors']
assert json.loads((ROOT/'accuracy-check/independent-audit.json').read_text())['result']=='pass'
for name in files:assert (ROOT/name).is_file(),name
out=ROOT/'Santa-Barbara-Transit-Atlas-Project.zip';tmp=ROOT/'Santa-Barbara-Transit-Atlas-Project.zip.tmp'
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in files:z.write(ROOT/name,'Santa-Barbara-Transit-Atlas/'+name)
tmp.replace(out)
shutil.copyfile(out,ROOT/'SBMTD-Atlas-Project.zip')
print('Packaged',len(files),'files;',out.stat().st_size,'bytes;',len(report['checks']),'browser checks recorded.')
