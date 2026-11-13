# Checks the built site in ../site/ and screenshots every page into ../../shots/ (desktop 1440 and phone 390).
# Run: .venv/bin/python check_site.py          (uses the Playwright Chromium in /opt/pw-browsers)
#      .venv/bin/python check_site.py --online (also fetches external links to check they resolve)
# Static checks: broken internal links and anchors, missing images, missing or empty alt text, em dashes in
# visible text and attributes, duplicate ids, one h1 per page, lang attribute, placeholder count.
# Browser checks: no external requests, no console errors, no horizontal overflow, WCAG AA text contrast,
# skip link is the first Tab stop and every Tab stop shows a visible focus outline.
import glob, os, re, sys, urllib.request
from html.parser import HTMLParser
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, '..', 'site'))
SHOTS = os.path.abspath(os.path.join(HERE, '..', 'shots'))
PAGES = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SITE, '*.html')))
problems, notes = [], []

class Page(HTMLParser):
    VOID = {'img', 'meta', 'link', 'br', 'hr', 'input', 'source'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.imgs, self.ids, self.text, self.attrs_text = [], [], [], [], []
        self.h1 = 0; self.lang = None; self.stack = []; self.placeholders = []
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'html': self.lang = a.get('lang')
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'h1': self.h1 += 1
        if 'data-placeholder' in a: self.placeholders.append(a['data-placeholder'])
        for k in ('href', 'src'):
            if k in a and tag != 'img' or (tag == 'img' and k == 'src' and k in a): self.links.append((tag, a[k]))
        if tag == 'img':
            self.imgs.append(a)
            for s in (a.get('srcset') or '').split(','):
                if s.strip(): self.links.append(('img', s.strip().split(' ')[0]))
        for k in ('alt', 'title', 'aria-label', 'content'):
            if a.get(k): self.attrs_text.append(a[k])
        if tag not in self.VOID: self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag: pass
    def handle_data(self, d):
        if not any(t in ('style', 'script') for t in self.stack): self.text.append(d)

parsed = {}
for name in PAGES:
    p = Page(); p.feed(open(os.path.join(SITE, name), encoding='utf-8').read()); parsed[name] = p

external = set()
for name, p in parsed.items():
    if p.lang != 'en-AU': problems.append(f'{name}: <html lang> is {p.lang!r}, expected en-AU')
    if p.h1 != 1: problems.append(f'{name}: {p.h1} h1 elements (expected 1)')
    dup = {i for i in p.ids if p.ids.count(i) > 1}
    if dup: problems.append(f'{name}: duplicate ids {sorted(dup)}')
    for tag, url in p.links:
        if url.startswith(('http://', 'https://')): external.add(url); continue
        if url.startswith(('mailto:', 'tel:')): continue
        path, _, frag = url.partition('#'); path = path.split('?')[0]
        if path.startswith('/'): target = os.path.join(SITE, path.lstrip('/') or 'index.html')
        else: target = os.path.join(SITE, path) if path else os.path.join(SITE, name)
        if os.path.isdir(target): target = os.path.join(target, 'index.html')
        if not os.path.exists(target):
            problems.append(f'{name}: broken {"image" if tag == "img" else "link"} {url}'); continue
        if frag and target.endswith('.html'):
            tp = parsed.get(os.path.basename(target))
            if tp and frag not in tp.ids and frag != 'top': problems.append(f'{name}: missing anchor #{frag} in {os.path.basename(target)}')
    for a in p.imgs:
        if 'alt' not in a: problems.append(f'{name}: img without alt: {a.get("src")}')
        elif not a['alt'].strip(): problems.append(f'{name}: empty alt (decorative?) on {a.get("src")}')
        if not a.get('width') or not a.get('height'): problems.append(f'{name}: img without width/height: {a.get("src")}')
    visible = ' '.join(p.text) + ' ' + ' '.join(p.attrs_text)
    if '—' in visible: problems.append(f'{name}: em dash in visible text: ' + re.findall(r'.{0,30}—.{0,30}', visible)[0])
    if '--' in visible: problems.append(f'{name}: double hyphen in visible text')
    if "'" in ' '.join(p.text) or '"' in ' '.join(p.text): notes.append(f'{name}: straight quote in visible text')
    notes.append(f'{name}: {len(p.placeholders)} placeholder box(es)')

unique_ph = sorted({x for p in parsed.values() for x in p.placeholders})

if '--online' in sys.argv:
    for url in sorted(external):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, method='GET', headers={'User-Agent': 'Mozilla/5.0'}), timeout=15)
            notes.append(f'external {r.status}: {url}')
        except Exception as e:
            problems.append(f'external link failed: {url} ({e})')
else:
    notes.append('external links not fetched (run with --online): ' + ', '.join(sorted(external)))

# ------------------------------------------------------------------ browser checks and screenshots
CONTRAST_JS = r"""() => {
  const lum = c => { const [r,g,b] = c.map(v => { v/=255; return v <= .03928 ? v/12.92 : Math.pow((v+.055)/1.055, 2.4) }); return .2126*r+.7152*g+.0722*b };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,\/]+/).filter(Boolean).map(Number); return {c:p.slice(0,3), a:p.length>3?p[3]:1} };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const b = parse(getComputedStyle(e).backgroundColor); if (b && b.a > .5) return b.c;
      if (getComputedStyle(e).backgroundImage !== 'none' && e !== document.documentElement) return null } return [250,248,244] };
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const n = walker.currentNode; if (!n.textContent.trim()) continue;
    const el = n.parentElement; if (seen.has(el)) continue; seen.add(el);
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || cs.display === 'none' || el.closest('[aria-hidden=true]')) continue;
    const r = el.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    const fg = parse(cs.color), bg = bgOf(el); if (!fg || !bg) continue;
    const L1 = lum(fg.c), L2 = lum(bg); const ratio = (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
    const size = parseFloat(cs.fontSize), bold = parseInt(cs.fontWeight) >= 700;
    const need = (size >= 24 || (bold && size >= 18.66)) ? 3 : 4.5;
    if (ratio < need) out.push(`${ratio.toFixed(2)} < ${need}: "${n.textContent.trim().slice(0,40)}" (${cs.color} on rgb(${bg}))`);
  }
  return out;
}"""

import mimetypes
from playwright.sync_api import sync_playwright
# No server: Playwright intercepts requests to a made-up origin and answers them from ../site on disk,
# the way Netlify would (including 404.html for unknown paths). Anything else counts as an external request.
ORIGIN = 'https://portfolio.test'
mimetypes.add_type('font/woff2', '.woff2')
def serve(route, ext):
    u = route.request.url
    if not u.startswith(ORIGIN): ext.append(u); return route.abort()
    path = u[len(ORIGIN):].split('#')[0].split('?')[0].lstrip('/') or 'index.html'
    f = os.path.join(SITE, path)
    if os.path.isfile(f):
        return route.fulfill(status=200, body=open(f, 'rb').read(), content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
    return route.fulfill(status=404, body=open(os.path.join(SITE, '404.html'), 'rb').read(), content_type='text/html; charset=utf-8')
os.makedirs(SHOTS, exist_ok=True)
EXE = glob.glob('/opt/pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell')[0]
shots = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    for mode, vp, scale in (('desktop', {'width': 1440, 'height': 900}, 1), ('phone', {'width': 390, 'height': 844}, 2), ('dark', {'width': 1440, 'height': 900}, 1)):
        ctx = b.new_context(viewport=vp, device_scale_factor=scale, is_mobile=(mode == 'phone'), has_touch=(mode == 'phone'),
                            color_scheme='dark' if mode == 'dark' else 'light')
        ext = []
        ctx.route('**/*', lambda r, ext=ext: serve(r, ext))
        for name in PAGES:
            pg = ctx.new_page(); errs = []
            pg.on('console', lambda m, errs=errs: errs.append(m.text) if m.type == 'error' else None)
            pg.goto(f'{ORIGIN}/no-such-page' if name == '404.html' else f'{ORIGIN}/{name}'); pg.wait_for_load_state('load')
            pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
            pg.wait_for_function("[...document.images].every(i => i.complete)", timeout=15000)
            pg.evaluate("Promise.all([...document.images].map(i => i.decode().catch(() => null)))")
            pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(250)
            base = name[:-5]
            for kind, full in (('top', False), ('full', True)):
                f = f'{SHOTS}/{base}-{mode}-{kind}.png'; pg.screenshot(path=f, full_page=full); shots.append(f)
            sw = pg.evaluate('document.documentElement.scrollWidth')
            if sw > vp['width']: problems.append(f'{name} {mode}: page wider than the screen ({sw}px)')
            errs = [e for e in errs if not (name == '404.html' and '404' in e)]   # the 404 status itself
            if errs: problems.append(f'{name} {mode}: console errors {errs}')
            fonts = pg.evaluate("[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.style)")
            if mode == 'desktop': notes.append(f'{name}: fonts loaded {sorted(set(fonts))}')
            broken = pg.evaluate("[...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)")
            if broken: problems.append(f'{name} {mode}: images failed to load {broken}')
            for c in pg.evaluate(CONTRAST_JS): problems.append(f'{name} {mode}: low contrast {c}')
            if mode == 'desktop':
                pg.keyboard.press('Tab')
                first = pg.evaluate("document.activeElement.className + '|' + document.activeElement.textContent")
                if not first.startswith('skip'): problems.append(f'{name}: first Tab stop is not the skip link ({first})')
                n = pg.evaluate("document.querySelectorAll('a[href]:not([tabindex=\\'-1\\']),button:not([hidden]),input,select,textarea,[tabindex]:not([tabindex=\\'-1\\'])').length")
                for _ in range(n - 1):
                    pg.keyboard.press('Tab')
                    o = pg.evaluate("(() => { const e = document.activeElement; const s = getComputedStyle(e); return [e.tagName, e.textContent.trim().slice(0,30), s.outlineStyle, s.outlineWidth] })()")
                    if o[2] == 'none' or o[3] == '0px': problems.append(f'{name}: no visible focus outline on {o[0]} "{o[1]}"')
            pg.close()
        if ext: problems.append(f'{mode}: external requests on page load {sorted(set(ext))}')
        ctx.close()
    b.close()

print(f'Pages: {", ".join(PAGES)}')
print(f'Placeholders still to fill (unique, all pages): {len(unique_ph)}')
for x in unique_ph: print('   [ ]', x)
for n in notes: print('  note:', n)
print('Screenshots:', SHOTS, f'({len(shots)} files)')
print('PROBLEMS:' if problems else 'All checks passed.')
for x in problems: print(' -', x)
sys.exit(1 if problems else 0)
