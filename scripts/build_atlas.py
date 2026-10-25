"""Build a self-contained offline atlas: two factual networks + a planning notebook.

Reads the hand-written sources in assets/ and data/, and writes the same bytes
to index.html (static-host entry) and Santa-Barbara-Transit-Atlas.html
(offline copy). No network access; every asset is inlined.
"""
from pathlib import Path
import base64, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'


def fail(message):
    print('build: ' + message, file=sys.stderr)
    raise SystemExit(1)


def require(*paths):
    missing = [str(p.relative_to(ROOT)) for p in paths if not p.is_file()]
    if missing:
        fail('missing input files: ' + ', '.join(missing))


require(*(A / name for name in (
    'app.css', 'saving.css', 'contrast.css', 'app.js', 'saving.js',
    'index.template.html', 'saving-tab.html', 'leaflet.css', 'leaflet.js',
    'manrope.ttf', 'basemap.webp', 'basemap-bounds.json')),
    ROOT / 'data/network.json', ROOT / 'data/planning.json',
    ROOT / 'data/route-comparison.csv', ROOT / 'data/route-performance-fy2025-26.csv')


def uri(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()


def csv_b64(path):
    """Embed a CSV, normalising checkout line endings.

    Without this the build is byte-identical on a fresh clone but differs in a
    Windows or CRLF working tree, which fails the CI stale-build check.
    """
    return base64.b64encode(path.read_bytes().replace(b'\r\n', b'\n')).decode()


css = ((A / 'app.css').read_text() + '\n' + (A / 'saving.css').read_text() + '\n'
       + (A / 'contrast.css').read_text()).replace('/*FONT_URI*/', uri(A / 'manrope.ttf', 'font/ttf'))
js = (A / 'app.js').read_text().replace('/*CSV_B64*/', csv_b64(ROOT / 'data/route-comparison.csv'))
saving_js = (A / 'saving.js').read_text().replace(
    '/*PERFORMANCE_CSV_B64*/', csv_b64(ROOT / 'data/route-performance-fy2025-26.csv'))

payload = json.loads((ROOT / 'data/network.json').read_text())
payload['planning'] = json.loads((ROOT / 'data/planning.json').read_text())
if 'cutFactor' in payload['meta'] or 'cutMethod' in payload['meta']:
    fail('network.json still carries the retired modeled-column keys (cutFactor/cutMethod)')

template = (A / 'index.template.html').read_text()
replacements = {
    '/*LEAFLET_CSS*/': (A / 'leaflet.css').read_text(),
    '/*APP_CSS*/': css,
    '/*SAVING_TAB*/': (A / 'saving-tab.html').read_text(),
    '/*LEAFLET_JS*/': re.sub(r'//# sourceMappingURL=.*', '', (A / 'leaflet.js').read_text()),
    '/*DATA_JSON*/': json.dumps(payload, separators=(',', ':')).replace('</', '<\\/'),
    '/*BASEMAP_URI*/': uri(A / 'basemap.webp', 'image/webp'),
    '/*BASEMAP_BOUNDS*/': (A / 'basemap-bounds.json').read_text(),
    '/*APP_JS*/': js,
    '/*SAVING_JS*/': saving_js,
}
for key, value in replacements.items():
    template = template.replace(key, value)

leftover = [key for key in replacements if key in template]
if leftover:
    fail('placeholders left unfilled: ' + ', '.join(leftover))
if 'data-mode="cut"' in template:
    fail('template still contains the retired cut-scenario mode')

for name in ('Santa-Barbara-Transit-Atlas.html', 'index.html'):
    tmp = ROOT / (name + '.tmp')
    tmp.write_text(template)
    tmp.replace(ROOT / name)
print('Built offline atlas and live-preview index:', len(template.encode()), 'bytes')
