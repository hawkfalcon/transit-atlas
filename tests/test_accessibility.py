"""Accessibility regression tests: axe-core audit plus keyboard focus indicators.

Runs the same checks that fixed the pre-publication defects: WCAG 2.x colour
contrast, accessible names, target size, landmarks/roles, and a visible focus
indicator on every tab stop. The browser under test is the built index.html
served at http://127.0.0.1:8000/ (see README, "Tests and package").

Set PLAYWRIGHT_CHROMIUM_EXECUTABLE to use a local Chromium build.
"""
from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AXE = (ROOT / 'tests/axe/axe.min.js').read_text()
AXE_VERSION = '4.14.0'
URL = 'http://127.0.0.1:8000/'
TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']
VIEWPORTS = [(1440, 960, False), (390, 844, True)]
EXECUTABLE = os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')

report = {'version': 1, 'axe': AXE_VERSION, 'tags': TAGS, 'views': [], 'focus': [], 'violations': []}
failures = []


def audit(page, label):
    """Return axe violations for the current document."""
    found = page.evaluate(
        """async (tags) => {
          const r = await axe.run(document, {runOnly: {type: 'tag', values: tags}});
          return r.violations.map(v => ({
            id: v.id, impact: v.impact, help: v.help,
            nodes: v.nodes.map(n => ({target: n.target.join(' '), summary: n.failureSummary}))
          }));
        }""",
        TAGS,
    )
    report['views'].append({'view': label, 'violations': len(found)})
    for v in found:
        for n in v['nodes']:
            report['violations'].append(
                {'view': label, 'id': v['id'], 'impact': v['impact'], 'target': n['target']}
            )
        failures.append(f'{label}: {v["id"]} ({v["impact"]}) — {v["help"]}')
        print(f'  {label}: {v["id"]} ({v["impact"]})')
        for n in v['nodes'][:5]:
            print(f'     {n["target"]}\n       {n["summary"].replace(chr(10), " ")[:160]}')


def focus_ring(page):
    """Every tab stop, including repeated rows, must keep a visible indicator."""
    stops = []
    for _ in range(45):
        page.keyboard.press('Tab')
        info = page.evaluate(
            """() => {
              const e = document.activeElement;
              if (!e || e === document.body || e === document.documentElement) return null;
              const c = getComputedStyle(e);
              const outline = c.outlineStyle !== 'none' && parseFloat(c.outlineWidth) >= 2;
              return {
                tag: e.tagName,
                id: e.id || '',
                cls: String(e.className || '').slice(0, 40),
                ring: outline || c.boxShadow !== 'none'
              };
            }"""
        )
        if info:
            stops.append(info)
    missing = [s for s in stops if not s['ring']]
    distinct = []
    for s in stops:
        key = (s['tag'], s['id'], s['cls'], s['ring'])
        if key not in [(d['tag'], d['id'], d['cls'], d['ring']) for d in distinct]:
            distinct.append(s)
    report['focus'].append({'tabStops': len(stops), 'distinctKinds': len(distinct), 'withoutIndicator': len(missing)})
    print(f'  tab stops checked: {len(stops)} ({len(distinct)} distinct), without visible indicator: {len(missing)}')
    for s in missing[:6]:
        print(f'     {s["tag"]}#{s["id"]}.{s["cls"]}')
    if missing:
        failures.append(f'{len(missing)} tab stop(s) have no visible focus indicator')
    return stops


with sync_playwright() as p:
    launch = {'headless': True, 'args': ['--no-sandbox', '--disable-dev-shm-usage']}
    if EXECUTABLE:
        launch['executable_path'] = EXECUTABLE
    browser = p.chromium.launch(**launch)
    for width, height, mobile in VIEWPORTS:
        ctx = browser.new_context(
            viewport={'width': width, 'height': height},
            is_mobile=mobile,
            has_touch=mobile,
            reduced_motion='reduce',
        )
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(URL, wait_until='networkidle')
        page.wait_for_function('window.ATLAS && window.ATLAS_SAVING')
        page.evaluate('document.fonts.ready')
        page.add_script_tag(content=AXE)

        device = 'mobile' if mobile else 'desktop'
        print(f'{device} {width}x{height}')
        audit(page, f'{device} / network')
        if not mobile:
            focus_ring(page)

        page.locator('#savingTab').click()
        page.wait_for_timeout(400)
        page.evaluate('document.fonts.ready')
        audit(page, f'{device} / saving')

        if errors:
            failures.append(f'{device}: JavaScript errors: {errors[:2]}')
        ctx.close()
    browser.close()

report['failures'] = failures
(ROOT / 'tests/accessibility-report.json').write_text(json.dumps(report, indent=2))
print(f'\naxe-core {AXE_VERSION} · {len(report["views"])} view audits · '
      f'{sum(v["violations"] for v in report["views"])} violations · {len(failures)} failures')
if failures:
    for f in failures:
        print('FAIL:', f)
    raise SystemExit(1)
print('All accessibility checks passed.')
