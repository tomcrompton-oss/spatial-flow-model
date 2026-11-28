"""Check that the site's embedded players look the same after a change to the viewer (web/).

Each player embedded in the site's pages (an iframe of viewer/index.html?player&run=...) is drawn twice: by the viewer
in web/ as it is now, and by a base copy of it (web/ at a git ref, HEAD by default). The two plots are compared pixel by
pixel. Spinning bodies and falling space move on a separate layer, so they are not compared.

    python3 scripts/check_players.py                       # web/ now against HEAD's, in headless Chrome
    python3 scripts/check_players.py --base main           # against main's viewer
    python3 scripts/check_players.py --only kerrPaths      # only players whose address has this in it
    python3 scripts/check_players.py --serve               # serve the check page, to open in a browser

It serves a folder holding the docs, web/, the base copy and scripts/check_players.html, and opens the check page in
Chrome without a window (--dump-dom), or, with --serve, prints the page's address and waits. It prints each player that
differs, and exits with 1 if any do.
"""
import argparse
import functools
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 'google-chrome', 'chromium', 'chromium-browser']
PLAYER = re.compile(r'viewer/index\.html\?player&(?:amp;)?((?:run|state)=[^"\s<>]+)')


def players(only):
    """the players embedded in the pages, by their query (run=... or state=...), with run addresses made absolute
    (a page's ../runs/x is the site's runs folder, docs/runs here)"""
    found = set()
    for page in (ROOT / 'docs').rglob('*.md'):
        for query in PLAYER.findall(page.read_text(errors='ignore')):
            if not query.endswith('.json') and not query.startswith('state='):
                continue   #the pages' example, run=../runs/<name>/<view>.full.json
            query = html.unescape(query).replace('run=../runs/', 'run=/docs/runs/')
            if not only or only in query:
                found.add(query)
    return sorted(found)


def base_copy(ref, folder):
    """web/index.html and web/viewer.js as they are at a git ref"""
    folder.mkdir()
    for name in ('index.html', 'viewer.js'):
        text = subprocess.run(['git', '-C', str(ROOT), 'show', f'{ref}:web/{name}'], capture_output=True, check=True).stdout
        (folder / name).write_bytes(text)


def serve(folder, port):
    handler = functools.partial(QuietHandler, directory=str(folder))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def chrome():
    for name in CHROME:
        if os.path.exists(name) or shutil.which(name):
            return name
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--base', default='HEAD', help='the git ref whose web/ viewer is the base (default HEAD)')
    parser.add_argument('--only', help='only players whose address contains this')
    parser.add_argument('--port', type=int, default=8790)
    parser.add_argument('--serve', action='store_true', help='serve the check page and wait, instead of running Chrome')
    parser.add_argument('--budget', type=int, default=600000, help="Chrome's virtual time budget, in ms")
    args = parser.parse_args()

    runs = players(args.only)
    if not runs:
        sys.exit('no players found')
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / 'docs').symlink_to(ROOT / 'docs')
        (folder / 'runs').symlink_to(ROOT / 'docs' / 'runs')   #a state= player's runs, ../runs/... from the viewer
        (folder / 'web').symlink_to(ROOT / 'web')
        (folder / 'check.html').symlink_to(ROOT / 'scripts' / 'check_players.html')
        base_copy(args.base, folder / 'base')
        (folder / 'runs.json').write_text(json.dumps(runs))
        server = serve(folder, args.port)
        url = f'http://127.0.0.1:{args.port}/check.html'
        print(f'{len(runs)} players; base: web/ at {args.base}')
        if args.serve or not chrome():
            if not args.serve:
                print('Chrome not found: open the page in a browser instead.')
            print('Open', url, '(Ctrl-C to stop)')
            try:
                threading.Event().wait()
            except KeyboardInterrupt:
                pass
            return
        with tempfile.TemporaryDirectory() as profile:
            dom = subprocess.run([chrome(), '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=1400,900',
                                  f'--user-data-dir={profile}', f'--virtual-time-budget={args.budget}', '--dump-dom', url],
                                 capture_output=True, text=True, timeout=1800).stdout
        server.shutdown()
    found = re.search(r'<pre id="result"[^>]*>(.*?)</pre>', dom, re.S)
    if not found or not found.group(1).strip():
        sys.exit('the check page did not finish: try a larger --budget, or --serve and a browser')
    results = json.loads(html.unescape(found.group(1)))
    bad = [r for r in results if r.get('differ') or r.get('error') or r.get('errors')]
    for r in results:
        if r in bad:
            what = r.get('error') or ('sizes differ' if r.get('differ') == -1 else f"{r['differ']} of {r['total']} pixels differ")
            print(f"DIFFERS  {r['run']}: {what}" + (f"  ({'; '.join(r['errors'])})" if r.get('errors') else ''))
    print(f'{len(results)} players checked, {len(bad)} differ or failed.')
    if bad:
        print('To see them side by side: python3 scripts/check_players.py --serve' + (f' --base {args.base}' if args.base != 'HEAD' else ''))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
