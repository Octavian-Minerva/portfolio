"""One-shot interaction test for site.js: sticky header, reading progress, section highlight,
theme toggle (and that the choice persists), copy buttons, print layout. Loads ../site from disk."""
import glob, mimetypes, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, '..', 'site')
SHOTS = os.path.join(HERE, '..', 'shots')
ORIGIN = 'https://portfolio.test'
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('text/javascript', '.js')


def answer(route):
    u = route.request.url
    if not u.startswith(ORIGIN):
        return route.abort()
    path = u[len(ORIGIN):].split('#')[0].split('?')[0].lstrip('/') or 'index.html'
    f = os.path.join(SITE, path)
    if os.path.isfile(f):
        return route.fulfill(status=200, body=open(f, 'rb').read(), content_type=mimetypes.guess_type(f)[0])
    return route.fulfill(status=404, body=b'')


fails = []
def check(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond: fails.append(msg)


EXE = glob.glob('/opt/pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell')[0]
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, color_scheme='light')
    ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=ORIGIN)
    ctx.route('**/*', answer)
    pg = ctx.new_page(); errs = []
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    pg.goto(ORIGIN + '/index.html'); pg.wait_for_load_state('load')
    check(pg.is_visible('.theme-toggle'), 'theme toggle is shown once the script runs')
    pg.evaluate("window.scrollTo({top: document.getElementById('skills').offsetTop + 200, behavior: 'instant'})"); pg.wait_for_timeout(400)
    top = pg.evaluate("document.querySelector('.site-head').getBoundingClientRect().top")
    check(abs(top) < 1, f'header stays at the top while scrolled (top={top})')
    check(pg.evaluate("document.querySelector('.site-head').classList.contains('scrolled')"), 'header gains its shadow when scrolled')
    p = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.progress')).getPropertyValue('--p'))")
    check(0 < p < 1, f'progress line reflects scroll position (p={p})')
    cur = pg.evaluate("[...document.querySelectorAll('.nav a.is-current')].map(a => a.textContent)")
    check(cur == ['Skills'], f'nav highlights the section in view ({cur})')
    bg0 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    pg.click('.theme-toggle'); pg.wait_for_timeout(400)
    bg1 = pg.evaluate("getComputedStyle(document.body).backgroundColor")
    check(pg.evaluate("document.documentElement.dataset.theme") == 'dark' and bg0 != bg1, f'toggle switches to dark ({bg0} -> {bg1})')
    check(pg.get_attribute('.theme-toggle', 'aria-label') == 'Switch to light theme', 'toggle label updates')
    pg.screenshot(path=os.path.join(SHOTS, 'interaction-dark-scrolled.png'))
    pg.reload(); pg.wait_for_load_state('load')
    check(pg.evaluate("document.documentElement.dataset.theme") == 'dark', 'theme choice persists after reload')
    pg.click('.theme-toggle')
    pg.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'})"); pg.wait_for_timeout(400)
    btn = pg.locator('.copy').first
    check(btn.is_visible(), 'copy buttons are shown')
    btn.click(); pg.wait_for_timeout(200)
    clip = pg.evaluate("navigator.clipboard.readText()")
    check(clip == 'ryan.ogrady77@gmail.com', f'copy puts the address on the clipboard ({clip})')
    check(btn.text_content() == 'Copied', 'copy button confirms')
    pg.emulate_media(media='print')
    check(not pg.is_visible('.site-head'), 'header is hidden when printing')
    pg.pdf(path=os.path.join(SHOTS, 'print-preview.pdf'), format='A4')
    check(not errs, f'no console errors {errs}')
    b.close()
print('ALL INTERACTION TESTS PASSED' if not fails else f'{len(fails)} FAILED')
sys.exit(1 if fails else 0)
