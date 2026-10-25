"""Build the curated, self-contained project bundle.

Includes the published app, the hand-written sources, the original GTFS/PDF
inputs and the audit trail. Excludes prior revisions and research scratch.
Refuses to package unless the recorded browser suite passed and the
independent audit is still a pass.
"""
from pathlib import Path
import json, sys, zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'Santa-Barbara-Transit-Atlas.html', 'index.html', 'README.md', 'NOTICE.md',
    'LICENSE', 'requirements.txt', 'pyproject.toml', '.gitattributes',
    'data/route-comparison.csv', 'data/route-performance-fy2025-26.csv', 'data/network.json',
    'data/planning.json', 'data/provenance.json', 'data/calculation-log.txt',
    'scripts/prepare_data.py', 'scripts/prepare_planning.py', 'scripts/build_atlas.py',
    'scripts/package_project.py', 'scripts/check_links.py',
    '.github/workflows/atlas.yml', '.github/workflows/link-check.yml', '.gitignore',
    'sources/historic-feed-20190819.zip', 'sources/current-feed.zip',
    'sources/fy2025-26-route-performance.csv', 'sources/Q4-FY26-ridership.pdf',
    'sources/20260721-annual-packet.pdf', 'sources/20260602-budget-packet.pdf',
    'assets/index.template.html', 'assets/app.js', 'assets/app.css', 'assets/contrast.css',
    'assets/saving-tab.html', 'assets/saving.js', 'assets/saving.css',
    'assets/leaflet.js', 'assets/leaflet.css', 'assets/leaflet-license.txt',
    'assets/manrope.ttf', 'assets/manrope-license.txt',
    'assets/basemap.webp', 'assets/basemap-bounds.json', 'assets/basemap-source.json',
    'assets/preview.png',
    'tests/test_atlas.py', 'tests/test_accessibility.py', 'tests/test-report.json',
    'tests/timetable-fingerprint.json',
    'tests/axe/axe.min.js', 'tests/axe/LICENSE', 'tests/axe/README.md',
    'Accuracy-Check.md', 'accuracy-check/audit_atlas.py',
    'accuracy-check/independent-audit.json', 'accuracy-check/before-corrections.json',
    'accuracy-check/corrections.json', 'accuracy-check/live-source-check.json',
    'accuracy-check/source-links.json', 'accuracy-check/source-departures.csv',
]


def fail(message):
    print('package: ' + message, file=sys.stderr)
    raise SystemExit(1)


missing = [name for name in FILES if not (ROOT / name).is_file()]
if missing:
    fail('missing files: ' + ', '.join(missing))

report = json.loads((ROOT / 'tests/test-report.json').read_text())
if report.get('version') != 2 or report.get('errors'):
    fail('tests/test-report.json is not a clean version-2 report; run tests/test_atlas.py first')
audit = json.loads((ROOT / 'accuracy-check/independent-audit.json').read_text())
if audit.get('result') != 'pass':
    fail('accuracy-check/independent-audit.json is not a pass')

out = ROOT / 'Santa-Barbara-Transit-Atlas-Project.zip'
tmp = out.with_suffix('.zip.tmp')
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for name in FILES:
        archive.write(ROOT / name, 'Santa-Barbara-Transit-Atlas/' + name)
tmp.replace(out)
print('Packaged', len(FILES), 'files;', out.stat().st_size, 'bytes;',
      len(report['checks']), 'browser checks recorded.')
