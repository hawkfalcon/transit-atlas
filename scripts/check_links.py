"""Check every external link embedded in the built atlas.

Sources move: MTD re-posts PDFs, archive buckets rotate, and the GTFS feed URL
drifts. This script pulls the URLs out of the committed index.html, requests
each one and reports what changed. It is run weekly by
.github/workflows/link-check.yml, not by the pull-request checks, so a remote
outage never blocks a code change.

Usage:
    python scripts/check_links.py            # check the built index.html
    python scripts/check_links.py --all      # also check links in docs/*.md

Exit status is 1 when a URL is gone (404/410) or the server errors repeatedly.
403/429 are reported as warnings: several agencies block automated clients
while still serving the page to a browser.
"""
import json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = 'Mozilla/5.0 (compatible; transit-atlas link check; +https://github.com/hawkfalcon/transit-atlas)'
TIMEOUT = 25
RETRIES = 2
IGNORE = ('http://127.0.0.1', 'http://localhost', 'https://hawkfalcon.github.io')


LINK_PATTERNS = (
    r'href="(https?://[^"]+)"',        # anchors in the page
    r'"url":"(https?://[^"]+)"',       # source records in the embedded data payload
    r'"source_url":"(https?://[^"]+)"',
)


def urls_from(text):
    """Collect user-facing links, not URLs that merely appear in vendor code.

    Fragment-only variants (PDF #page=) collapse to one request; the fragment
    is still reported so a moved page number is easy to spot.
    """
    found = {}
    for pattern in LINK_PATTERNS:
        for raw in re.findall(pattern, text):
            url = raw.rstrip('.,;:')
            if url.startswith(IGNORE):
                continue
            found.setdefault(urllib.parse.urldefrag(url)[0], url)
    return found


def probe(url):
    """Return (status, note). status is an int or None."""
    for attempt in range(RETRIES + 1):
        for method in ('HEAD', 'GET'):
            request = urllib.request.Request(url, method=method, headers={'User-Agent': UA})
            if method == 'GET':
                request.add_header('Range', 'bytes=0-1024')
            try:
                with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                    return response.status, ''
            except urllib.error.HTTPError as error:
                if method == 'HEAD' and error.code in (403, 405, 501):
                    continue  # many static hosts refuse HEAD; retry with GET
                if error.code in (403, 429):
                    return error.code, 'blocked automated client'
                if attempt < RETRIES and error.code >= 500:
                    break
                return error.code, ''
            except Exception as error:  # DNS, TLS, timeout
                if method == 'HEAD':
                    continue
                if attempt < RETRIES:
                    break
                return None, type(error).__name__
        time.sleep(2 * (attempt + 1))
    return None, 'unreachable'


def main():
    sources = [ROOT / 'index.html']
    if '--all' in sys.argv:
        sources += list(ROOT.glob('*.md'))
    urls = {}
    for path in sources:
        urls.update(urls_from(path.read_text(encoding='utf-8')))
    print(f'{len(urls)} external URLs from {", ".join(p.name for p in sources)}\n')

    results, failures, warnings = [], [], []
    for key in sorted(urls):
        url, status, note = urls[key], None, ''
        status, note = probe(url)
        ok = status is not None and status < 400
        if status in (403, 429):
            warnings.append(url)
        elif not ok:
            failures.append(url)
        results.append({'url': url, 'status': status, 'note': note, 'ok': ok or status in (403, 429)})
        label = 'ok  ' if ok else ('warn' if status in (403, 429) else 'FAIL')
        print(f'  {label} {status if status else "---"}  {url}' + (f'  ({note})' if note else ''))

    (ROOT / 'tests/link-report.json').write_text(json.dumps(
        {'checked': len(urls), 'failures': failures, 'warnings': warnings, 'results': results}, indent=2))
    print(f'\n{len(urls)} checked · {len(failures)} broken · {len(warnings)} blocked')
    if failures:
        print('\nBroken:')
        for url in failures:
            print(f'  {url}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
