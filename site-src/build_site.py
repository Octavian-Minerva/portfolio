# Builds Ryan O'Grady's portfolio into ../site/ from content.py (all copy) and img-src/ (image sources).
# Run from anywhere:   .venv/bin/python build_site.py            build, and warn loudly about unfilled placeholders
#                      .venv/bin/python build_site.py --release  refuse to build while any placeholder remains
# Output is plain static HTML/CSS with no JavaScript and no external requests: fonts are self-hosted.
# Deploy (later, not yet): upload the whole ../site/ folder to Netlify (publish directory = site root, no build command).
import html, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C
from content import RyanWrites

OUT = os.path.abspath(os.path.join(HERE, '..', 'site'))
IMG_SRC = os.path.join(HERE, 'img-src')
FONT_SRC = os.path.join(HERE, 'fonts-src')
RELEASE = '--release' in sys.argv
PREVIEW = '--preview' in sys.argv   # feedback preview: adds noindex so search engines skip it
NOINDEX = '<meta name="robots" content="noindex">' if PREVIEW else ''
PDFS = []           # (source in ESSAYS, public name) collected while rendering
ESSAYS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'essays-src')
PLACEHOLDERS = []   # (where, RyanWrites) collected while rendering

# ------------------------------------------------------------------ text helpers
def smart(s):
    """Escape for HTML and make quotes typographic. Refuses em dashes."""
    if '\u2014' in s:
        sys.exit(f'BUILD STOPPED: em dash in content: {s[:80]!r}')
    s = re.sub(r"(\w)'(\w)", '\\1\u2019\\2', s)             # apostrophes: O'Grady, don't
    s = re.sub(r"(^|[\s(\[])'", '\\1\u2018', s)              # opening single quote
    s = s.replace("'", '\u2019')
    s = re.sub(r'(^|[\s(\[])"', '\\1\u201c', s)              # opening double quote
    s = s.replace('"', '\u201d')
    return html.escape(s, quote=False)

def attr(s):
    """Text for an attribute (alt, title, content): smart quotes, then escape double quotes."""
    return smart(s).replace('"', '&quot;')

def ph(x, where, inline=False):
    PLACEHOLDERS.append((where, x))
    tag = 'span' if inline else 'div'
    length = f' <span class="ph-len">({html.escape(x.length)})</span>' if x.length else ''
    return (f'<{tag} class="ph{" ph-i" if inline else ""}" data-placeholder="{html.escape(where)}">'
            f'<b class="ph-who">[{html.escape(x.who)}]</b> <span class="ph-what">{smart(x.what)}</span>{length}</{tag}>')

def prose(x, where, cls=''):
    """Paragraph text: a RyanWrites placeholder, None (omit), or a string (blank line = new paragraph)."""
    if x is None: return ''
    if isinstance(x, RyanWrites): return ph(x, where)
    c = f' class="{cls}"' if cls else ''
    return ''.join(f'<p{c}>{smart(p.strip())}</p>' for p in re.split(r'\n\s*\n', x.strip()) if p.strip())

def listing(x, where):
    """A list of short items: placeholder, None (omit), a list of strings, or a plain string."""
    if x is None: return ''
    if isinstance(x, RyanWrites): return ph(x, where)
    if isinstance(x, str): return prose(x, where)
    return '<ul class="points">' + ''.join(f'<li>{smart(i)}</li>' for i in x) + '</ul>'

def pdf_button(w):
    if not w.get('pdf'): return ''
    src, pub = w['pdf']
    PDFS.append((src, pub))
    pages = ''
    try:
        out = subprocess.run(['pdfinfo', os.path.join(ESSAYS, src)], capture_output=True, text=True).stdout
        n = re.search(r'Pages:\s+(\d+)', out); pages = f', {n.group(1)} pages' if n else ''
    except FileNotFoundError: pass
    return (f'<p class="actions"><a class="btn" href="files/{pub}">Read the full essay '
            f'<span class="btn-note">(PDF{pages})</span></a></p>')

def link_buttons(w):
    out = ''
    for label, href, external in w.get('links', []):
        arrow = '&#8599;' if external else '&rarr;'
        out += f'<a class="btn" href="{href}">{smart(label)} <span class="arr" aria-hidden="true">{arrow}</span></a>'
    return f'<p class="actions">{out}</p>' if out else ''

def inline(x, where):
    if x is None: return ''
    if isinstance(x, RyanWrites): return ph(x, where, inline=True)
    return smart(x)

# ------------------------------------------------------------------ assets
IMAGES = {}  # source file -> (rel path of largest, width, height, srcset)

def build_image(src, widths):
    """Resize an img-src file to progressive JPEGs at the given widths. Returns (src, w, h, srcset)."""
    from PIL import Image
    if src in IMAGES: return IMAGES[src]
    path = os.path.join(IMG_SRC, src)
    if not os.path.exists(path): sys.exit(f'BUILD STOPPED: image missing: img-src/{src}')
    im = Image.open(path).convert('RGB')
    base = os.path.splitext(src)[0]
    out = []
    for w in widths:
        w = min(w, im.width)
        h = round(im.height * w / im.width)
        rel = f'images/{base}-{w}.jpg'
        dst = os.path.join(OUT, rel)
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(path):
            im.resize((w, h), Image.LANCZOS).save(dst, 'JPEG', quality=82, optimize=True, progressive=True)
        out.append((rel, w, h))
    rel, w, h = out[-1]
    IMAGES[src] = (rel, w, h, ', '.join(f'{r} {ww}w' for r, ww, _ in out))
    return IMAGES[src]

def img(src, alt, widths, sizes, cls='', eager=False, prefix=''):
    rel, w, h, srcset = build_image(src, widths)
    srcset = ', '.join(prefix + s for s in srcset.split(', '))
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ''
    return (f'<img{c} src="{prefix}{rel}" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" '
            f'alt="{attr(alt)}" {load} decoding="async">')

FONTS = [('newsreader-Newsreader[opsz,wght].ttf', 'newsreader.woff2'),
         ('newsreader-Newsreader-Italic[opsz,wght].ttf', 'newsreader-italic.woff2'),
         ('sourcesans3-SourceSans3[wght].ttf', 'source-sans-3.woff2')]
UNICODES = 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2013-2014,U+2018-201E,U+2022,U+2026,U+2032-2033,U+20AC,U+2122,U+2190-2193,U+2212'

def build_fonts():
    os.makedirs(os.path.join(OUT, 'fonts'), exist_ok=True)
    for src, dst in FONTS:
        d = os.path.join(OUT, 'fonts', dst)
        if os.path.exists(d): continue
        from fontTools import subset
        subset.main([os.path.join(FONT_SRC, src), f'--unicodes={UNICODES}', '--flavor=woff2',
                     '--layout-features=kern,liga,calt,onum,lnum,pnum,tnum,smcp,c2sc,case', f'--output-file={d}'])
    for lic in ('newsreader-OFL.txt', 'sourcesans3-OFL.txt'):
        shutil.copy(os.path.join(FONT_SRC, lic), os.path.join(OUT, 'fonts', 'OFL-' + lic.split('-')[0] + '.txt'))

# ------------------------------------------------------------------ design
ACCENT = '#1d4e89'
FAVICON = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="{ACCENT}"/>'
           '<text x="32" y="45" text-anchor="middle" font-family="Georgia,\'Times New Roman\',serif" font-size="38" fill="#fff">R</text></svg>')

CSS = r"""
@font-face{font-family:Newsreader;src:url(fonts/newsreader.woff2) format('woff2');font-weight:200 800;font-style:normal;font-display:swap}
@font-face{font-family:Newsreader;src:url(fonts/newsreader-italic.woff2) format('woff2');font-weight:200 800;font-style:italic;font-display:swap}
@font-face{font-family:'Source Sans 3';src:url(fonts/source-sans-3.woff2) format('woff2');font-weight:200 900;font-style:normal;font-display:swap}
:root{--ink:#1c1b19;--muted:#57524a;--bg:#faf8f4;--paper:#fff;--line:#e3ddd2;--soft:#f2eee6;
 --accent:ACCENT;--accent-ink:#163d6c;--tint:#ebf0f6;--serif:Newsreader,Georgia,'Times New Roman',serif;
 --sans:'Source Sans 3',system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;--wrap:1160px;--pad:clamp(20px,4vw,40px)}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:24px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:18px;line-height:1.6;
 font-feature-settings:'kern','liga';text-rendering:optimizeLegibility;-webkit-font-smoothing:antialiased}
img{max-width:100%;height:auto;display:block}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:3px}
a:hover{color:var(--accent-ink);text-decoration-thickness:2px}
:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:2px}
h1,h2,h3{font-family:var(--serif);font-weight:400;line-height:1.1;margin:0;letter-spacing:-.01em;font-optical-sizing:auto}
p{margin:0 0 1em}
/* Ryan's preference: justified body text, with hyphenation (lang="en-AU") to keep word gaps even in narrow columns */
main p{text-align:justify;-webkit-hyphens:auto;hyphens:auto;hyphenate-limit-chars:8 4 3}
main p.lede,main p.kicker,main p.unit,main p.org,main p.actions,main p.crumb,main p.big,main p.name{text-align:left;-webkit-hyphens:manual;hyphens:manual}
.wrap{max-width:var(--wrap);margin:0 auto;padding:0 var(--pad)}
.skip{position:absolute;left:12px;top:-60px;background:var(--ink);color:#fff;padding:10px 16px;border-radius:4px;z-index:10;text-decoration:none}
.skip:focus{top:12px;color:#fff}
.kicker{font-family:var(--sans);font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 14px}
.num{color:var(--accent);font-variant-numeric:tabular-nums;margin-right:.6em}

/* header */
.site-head{border-bottom:1px solid var(--line)}
.site-head .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px 28px;flex-wrap:wrap;padding-top:18px;padding-bottom:18px}
.brand{font-family:var(--serif);font-size:22px;color:var(--ink);text-decoration:none;letter-spacing:-.005em}
.brand:hover{color:var(--ink)}
.nav ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:4px 26px}
.nav a{color:var(--ink);text-decoration:none;font-size:16px;padding:6px 0;border-bottom:1px solid transparent}
.nav a:hover{border-bottom-color:var(--ink)}
.nav a[aria-current]{border-bottom-color:var(--accent);color:var(--accent)}

/* hero */
.hero{padding:clamp(56px,9vw,120px) 0 clamp(56px,8vw,104px)}
.hero .wrap{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(0,1fr);gap:clamp(32px,6vw,88px);align-items:end}
.hero h1{font-size:clamp(54px,9vw,120px);line-height:.94;letter-spacing:-.025em;font-weight:380;margin:0 0 28px}
.hero .descriptor{font-family:var(--serif);font-size:clamp(22px,2.4vw,28px);line-height:1.35;max-width:30ch}
.portrait{margin:0;position:relative}
.portrait img{border-radius:4px;aspect-ratio:4/5;object-fit:cover;width:100%}
.monogram{aspect-ratio:4/5;border-radius:4px;background:
 repeating-linear-gradient(0deg,transparent 0 23px,rgba(29,78,137,.08) 23px 24px),var(--tint);
 display:grid;place-items:center;font-family:var(--serif);font-size:clamp(64px,9vw,120px);color:rgba(29,78,137,.35);letter-spacing:-.03em}
.portrait .ph{position:absolute;left:12px;right:12px;bottom:12px}

/* sections */
.sec{padding:clamp(64px,9vw,120px) 0;border-top:1px solid var(--line)}
.sec-grid{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,9fr);gap:clamp(24px,4vw,56px)}
.sec h2{font-size:clamp(34px,4.4vw,52px);letter-spacing:-.02em}
.sec-label h2{font-size:clamp(28px,3vw,36px)}
.lede{font-family:var(--serif);font-size:clamp(24px,2.6vw,32px);line-height:1.32;letter-spacing:-.005em;max-width:34ch}
.measure{max-width:64ch}
.exploring{margin-top:40px;padding-top:22px;border-top:1px solid var(--line);display:grid;grid-template-columns:auto 1fr;gap:6px 24px;align-items:baseline}
.exploring .kicker{margin:0}
.exploring+.exploring{margin-top:18px}
.points{margin:0;padding-left:1.1em}.points li{margin:0 0 6px}
.card .actions{margin-top:18px;display:flex;flex-wrap:wrap;gap:10px}
.card .thumb{margin:0 0 22px;aspect-ratio:4/3;overflow:hidden;border:1px solid var(--line);background:#fff}
.card .thumb img{display:block;width:100%;height:100%;object-fit:cover;object-position:top center}
.card .thumb.fit img{object-fit:contain;object-position:center}
.btn-note{font-weight:400;opacity:.8}

/* featured */
.feature-head{display:flex;justify-content:space-between;align-items:end;gap:24px;flex-wrap:wrap;margin-bottom:clamp(28px,4vw,48px)}
.feature-head h2{font-size:clamp(44px,6.5vw,84px);letter-spacing:-.03em}
.stage{position:relative;padding-right:clamp(40px,10vw,150px);margin-bottom:clamp(40px,5vw,64px)}
.frame{background:var(--paper);border:1px solid var(--line);border-radius:10px;overflow:hidden;
 box-shadow:0 1px 2px rgba(28,27,25,.05),0 24px 48px -24px rgba(28,27,25,.28)}
.frame .bar{height:26px;display:flex;align-items:center;gap:6px;padding:0 12px;border-bottom:1px solid var(--line);background:#f6f3ee}
.frame .bar i{width:9px;height:9px;border-radius:50%;background:#d9d2c5;display:block}
.phone{position:absolute;right:0;bottom:-28px;width:clamp(120px,22%,240px);border:6px solid #1c1b19;border-radius:26px;overflow:hidden;
 background:#1c1b19;box-shadow:0 24px 48px -16px rgba(28,27,25,.45)}
.phone img{border-radius:20px}
.feature-body{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:clamp(28px,5vw,72px);align-items:start}
.meta{margin:0;display:grid;grid-template-columns:auto 1fr;gap:10px 20px;font-size:16px;border-top:1px solid var(--ink);padding-top:16px}
.meta dt{font-weight:600;color:var(--muted);font-size:13px;letter-spacing:.1em;text-transform:uppercase;padding-top:3px}
.meta dd{margin:0}
.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 20px;border-radius:999px;font-weight:600;font-size:16px;text-decoration:none;
 border:1.5px solid var(--ink);color:var(--ink);background:transparent}
.btn:hover{background:var(--ink);color:#fff}
.btn.solid{background:var(--accent);border-color:var(--accent);color:#fff}
.btn.solid:hover{background:var(--accent-ink);border-color:var(--accent-ink);color:#fff}
.btn .arr{font-family:var(--sans)}

/* work cards */
.work-head{margin-bottom:clamp(28px,4vw,48px)}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:clamp(40px,5vw,64px) clamp(28px,4vw,56px)}
.card{border-top:1px solid var(--ink);padding-top:20px;display:flex;flex-direction:column}
.card.wide{grid-column:1/-1;display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:clamp(24px,4vw,56px);align-items:start}
.card .unit{font-size:14px;color:var(--muted);margin:0 0 12px;letter-spacing:.01em}
.card .unit b{color:var(--ink);font-weight:600;letter-spacing:.04em}
.card h3{font-size:clamp(25px,2.3vw,29px);line-height:1.15;margin:0 0 16px;letter-spacing:-.012em}
.card .type{font-family:var(--sans);display:block;font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-bottom:10px}
.topic{font-family:var(--serif);font-style:italic;font-size:19px;line-height:1.45;color:#38342e;margin:0 0 16px}
.tags{list-style:none;margin:0 0 18px;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.tags li{font-size:13.5px;line-height:1;padding:7px 11px;border:1px solid var(--line);border-radius:999px;background:var(--paper);color:var(--muted)}
.slides{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.slides figure{margin:0}
.slides figure:first-child{grid-column:1/-1}
.slides img{border:1px solid var(--line);border-radius:6px}

/* skills */
.skills{background:var(--tint);border-top:0}
.skills h2{font-size:clamp(44px,6.5vw,84px);letter-spacing:-.03em;margin-bottom:clamp(28px,4vw,48px)}
.skills-body{display:grid;grid-template-columns:minmax(0,8fr) minmax(0,4fr);gap:clamp(28px,5vw,72px);align-items:start;
 border-top:1px solid var(--accent);padding-top:clamp(24px,3vw,36px)}
.skills .audit{font-size:20px;line-height:1.65;max-width:62ch}
.skills .audit .ph{font-size:17px;padding:20px 22px;max-width:none}
.skills .audit p:first-child{font-family:var(--serif);font-size:clamp(23px,2.3vw,28px);line-height:1.4}
.skill-list{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px}
.skill-list li{background:var(--paper);border:1px solid #cbd6e4;border-radius:999px;padding:8px 14px;font-size:15px}

/* experience */
.xp{list-style:none;margin:0;padding:0}
.xp li{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,4fr) minmax(0,5fr);gap:12px 32px;padding:24px 0;border-top:1px solid var(--line)}
.xp li:last-child{border-bottom:1px solid var(--line)}
.xp .dates{font-size:15px;color:var(--muted);font-variant-numeric:tabular-nums}
.xp h3{font-size:24px;margin:0 0 4px}
.xp .org{margin:0;color:var(--muted)}
.xp .text p:last-child{margin:0}
.xp-sub{font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:48px 0 0;font-family:var(--sans);font-weight:600}

/* contact */
.contact .big{font-family:var(--serif);font-size:clamp(28px,4vw,48px);letter-spacing:-.02em;line-height:1.2;word-break:break-word}

/* footer */
.site-foot{border-top:1px solid var(--line);padding:40px 0 56px;font-size:15px;color:var(--muted)}
.site-foot .wrap{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr);gap:20px 48px}
.site-foot .name{font-family:var(--serif);font-size:22px;color:var(--ink);margin:0 0 6px}
.credits{list-style:none;margin:16px 0 0;padding:0;font-size:13.5px;line-height:1.5}
.credits li{margin-bottom:4px}
.site-foot a{color:var(--muted)}

/* detail page */
.crumb{font-size:15px;margin:0 0 28px}
.crumb a{text-decoration:none}
.page-hero{padding:clamp(48px,7vw,96px) 0 clamp(36px,5vw,56px)}
.page-hero h1{font-size:clamp(52px,8vw,108px);letter-spacing:-.03em;line-height:.95;margin:0 0 32px}
.page-hero .feature-body{align-items:end}
.gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(24px,3vw,40px);align-items:start}
.gallery figure:first-child{grid-column:span 2}
.gallery .phone-shot{grid-row:span 2;align-self:stretch}
.gallery figure{margin:0}
.gallery figcaption,.slides figcaption,.tiles figcaption{font-size:14px;color:var(--muted);margin-top:10px}
.gallery .phone-shot{display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--soft);border-radius:10px;padding:28px}
.gallery .phone-shot .phone{position:static;width:min(240px,62%)}
.gallery .phone-shot figcaption{align-self:flex-start}
.prose-sec{display:grid;grid-template-columns:minmax(0,3fr) minmax(0,9fr);gap:clamp(20px,4vw,56px);padding:clamp(40px,5vw,64px) 0;border-top:1px solid var(--line)}
.prose-sec h2{font-size:clamp(26px,2.8vw,34px)}
.tiles{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.tiles figure{margin:0}
.tiles img{border-radius:6px;border:1px solid var(--line)}

/* placeholders: deliberately loud, temporary */
.ph{border:2px dashed #b45309;background:#fff6e5;color:#5b3608;border-radius:6px;padding:14px 16px;font-family:var(--sans);
 font-size:15.5px;line-height:1.45;font-style:normal;letter-spacing:0;text-transform:none;font-weight:400;max-width:62ch}
.ph-who{color:#8a3c04;font-weight:700;margin-right:2px}
.ph-len{white-space:nowrap}
.ph-i{display:inline;padding:2px 8px;border-width:1.5px;font-size:14px;line-height:1.9;box-decoration-break:clone;-webkit-box-decoration-break:clone}

/* responsive */
@media (max-width:900px){
 .hero .wrap{grid-template-columns:1fr}
 .portrait{max-width:340px}
 .sec-grid,.prose-sec,.feature-body,.card.wide,.skills-body{grid-template-columns:1fr}
 .cards{grid-template-columns:1fr}
 .xp li{grid-template-columns:1fr}
 .site-foot .wrap{grid-template-columns:1fr}
 .exploring{grid-template-columns:1fr}
 .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media (max-width:600px){
 body{font-size:17px}
 .site-head .wrap{padding-top:14px;padding-bottom:14px}
 .nav ul{gap:2px 18px}
 .nav a{font-size:15.5px}
 .stage{padding-right:56px;padding-top:64px}
 .portrait{max-width:280px}
 .phone{width:34%;border-width:4px;border-radius:18px;bottom:-20px}
 .phone img{border-radius:14px}
 .gallery,.tiles{grid-template-columns:1fr}
 .gallery figure:first-child{grid-column:auto}.gallery .phone-shot{grid-row:auto}
 .frame .bar{height:18px}.frame .bar i{width:7px;height:7px}
}
""".replace('ACCENT', ACCENT)

# ------------------------------------------------------------------ page parts
def head(title, desc, prefix=''):
    og = ''
    if C.SITE_URL:
        og = (f'<meta property="og:type" content="website"><meta property="og:title" content="{attr(title)}">'
              f'<meta property="og:description" content="{attr(desc)}"><meta property="og:url" content="{C.SITE_URL}">')
    return ('<!doctype html><html lang="en-AU"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{smart(title)}</title><meta name="description" content="{attr(desc)}">{NOINDEX}'
            f'<meta name="theme-color" content="#faf8f4">{og}'
            f'<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">'
            f'<link rel="preload" href="{prefix}fonts/newsreader.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="preload" href="{prefix}fonts/source-sans-3.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="stylesheet" href="{prefix}style.css"></head><body>'
            '<a class="skip" href="#main">Skip to content</a>')

def header(home=True):
    base = '' if home else 'index.html'
    items = ''.join(f'<li><a href="{base}#{a}">{smart(t)}</a></li>' for t, a in C.NAV)
    brand_href = '#top' if home else 'index.html'
    return (f'<header class="site-head" id="top"><div class="wrap"><a class="brand" href="{brand_href}">{smart(C.NAME)}</a>'
            f'<nav class="nav" aria-label="Main"><ul>{items}</ul></nav></div></header>')

def footer():
    credits = ''
    for c in C.CREDITS:
        t = smart(c)
        for k, url in C.CREDIT_LINKS.items():
            t = t.replace(smart(k), f'<a href="{url}">{smart(k)}</a>', 1)
        credits += f'<li>{t}</li>'
    return (f'<footer class="site-foot"><div class="wrap"><div><p class="name">{smart(C.NAME)}</p><p>&copy; {C.YEAR}</p></div>'
            f'<div>{prose(C.AI_NOTE, "Footer: AI note") if C.AI_NOTE else ""}<ul class="credits">{credits}</ul></div></div></footer></body></html>')

def unit_line(d):
    return f'<p class="unit"><b>{smart(d["unit_code"])}</b> {smart(d["unit_name"])} <span aria-hidden="true">&middot;</span> {smart(d["year"])}</p>'

def meta_list(F):
    live = F['live_url']
    return ('<dl class="meta">'
            f'<dt>Unit</dt><dd>{smart(F["unit_code"])} {smart(F["unit_name"])}</dd>'
            f'<dt>Year</dt><dd>{smart(F["year"])}</dd>'
            f'<dt>Type</dt><dd>{smart(F["type"])}</dd>'
            f'<dt>Role</dt><dd>{smart(F["role"])}</dd>'
            f'<dt>Live</dt><dd><a href="{live}">{html.escape(live.split("//")[1])}</a></dd></dl>')

DESKTOP_W, PHONE_W = [900, 1600, 2400], [300, 600]

def frame(src, alt, sizes, eager=False):
    return f'<div class="frame"><div class="bar" aria-hidden="true"><i></i><i></i><i></i></div>{img(src, alt, DESKTOP_W, sizes, eager=eager)}</div>'

# ------------------------------------------------------------------ pages
def page_home():
    F = C.FEATURED
    # hero
    if C.PHOTO is None:
        photo = '<figure class="portrait"><div class="monogram" aria-hidden="true">RO</div></figure>'
    elif isinstance(C.PHOTO, RyanWrites):
        photo = f'<figure class="portrait"><div class="monogram" aria-hidden="true">RO</div>{ph(C.PHOTO, "Hero: photo")}</figure>'
    else:
        photo = f'<figure class="portrait">{img(C.PHOTO[0], C.PHOTO[1], [450, 900], "(max-width:900px) 340px, 33vw", eager=True)}</figure>'
    hero = (f'<section class="hero" aria-labelledby="name"><div class="wrap"><div><p class="kicker">{smart(C.HERO_KICKER)}</p>'
            f'<h1 id="name">{smart(C.NAME)}</h1><div class="descriptor">{prose(C.DESCRIPTOR, "Hero: descriptor")}</div></div>{photo}</div></section>')
    # about
    about = (f'<section class="sec" id="about" aria-labelledby="about-h"><div class="wrap sec-grid">'
             f'<div class="sec-label"><p class="kicker"><span class="num">01</span>Purpose</p><h2 id="about-h">{smart(C.ABOUT_HEAD)}</h2></div>'
             f'<div>{prose(C.PURPOSE, "About: purpose statement", "lede")}'
             + (f'<div class="measure" style="margin-top:28px">{prose(C.ABOUT_BIO, "About: short bio")}</div>' if C.ABOUT_BIO is not None else '')
             + (f'<div class="exploring"><p class="kicker">{smart(C.INTERESTS_LABEL)}</p><div>{listing(C.INTERESTS, "About: interests")}</div></div>' if C.INTERESTS is not None else '')
             + (f'<div class="exploring"><p class="kicker">{smart(C.EXPLORING_LABEL)}</p><div>{listing(C.EXPLORING, "About: now")}</div></div>' if C.EXPLORING is not None else '')
             + '</div></div></section>')
    # work
    cards = ''
    for i, w in enumerate(C.WORK):
        where = f'Work card {i + 1} ({w["unit_code"]}): blurb'
        tags = ''.join(f'<li>{smart(t)}</li>' for t in w.get('tags', []))
        text = (f'<div>{unit_line(w)}<h3><span class="type">{smart(w["type"])}</span>{smart(w["title"])}</h3>'
                f'{prose(w["topic"], where.replace("blurb", "topic line"), "topic")}<ul class="tags" aria-label="Topics">{tags}</ul>{prose(w["blurb"], where)}{pdf_button(w)}{link_buttons(w)}</div>')
        if w.get('slides'):
            figs = ''.join(f'<figure>{img(s, a, [700, 1400], "(max-width:900px) 92vw, 640px" if j == 0 else "(max-width:900px) 45vw, 320px")}</figure>'
                           for j, (s, a) in enumerate(w['slides']))
            cards += f'<article class="card wide"><div class="slides">{figs}</div>{text}</article>'
        else:
            thumb = (f'<figure class="thumb{" fit" if w.get("thumb_fit") == "contain" else ""}">{img(w["thumb"][0], w["thumb"][1], [480, 960], "(max-width:700px) 92vw, 400px")}</figure>'
                     if w.get('thumb') else '')
            cards += f'<article class="card">{thumb}{text}</article>'
    work = (f'<section class="sec" id="work" aria-labelledby="work-h"><div class="wrap">'
            f'<div class="work-head"><p class="kicker"><span class="num">02</span>Essays, presentations and campaigns</p><h2 id="work-h">{smart(C.WORK_HEAD)}</h2></div>'
            f'<div class="cards">{cards}</div></div></section>')
    # skills
    if C.SKILLS_LIST is None: skl = ''
    elif isinstance(C.SKILLS_LIST, RyanWrites): skl = f'<p class="kicker">{smart(C.SKILLS_LIST_LABEL)}</p>' + ph(C.SKILLS_LIST, 'Skills: list')
    else: skl = f'<p class="kicker">{smart(C.SKILLS_LIST_LABEL)}</p><ul class="skill-list">' + ''.join(f'<li>{smart(s)}</li>' for s in C.SKILLS_LIST) + '</ul>'
    skills = (f'<section class="sec skills" id="skills" aria-labelledby="skills-h"><div class="wrap">'
              f'<p class="kicker"><span class="num">03</span>{smart(C.SKILLS_KICKER)}</p><h2 id="skills-h">{smart(C.SKILLS_HEAD)}</h2>'
              f'<div class="skills-body"><div class="audit">{prose(C.SKILLS_AUDIT, "Skills: audit and reflection")}</div><div>{skl}</div></div></div></section>')
    # experience
    def xp_rows(items, label):
        return ''.join(f'<li><div class="dates">{inline(e["dates"], f"{label} {i + 1}: dates")}</div>'
                       f'<div><h3>{inline(e["role"], f"{label} {i + 1}: role")}</h3><p class="org">{smart(e["org"])}</p></div>'
                       f'<div class="text">{prose(e["text"], f"{label} {i + 1}: description")}</div></li>'
                       for i, e in enumerate(items))
    rows = xp_rows(C.EXPERIENCE, 'Experience')
    edu = (f'<h3 class="xp-sub">{smart(C.EDUCATION_HEAD)}</h3><ul class="xp">{xp_rows(C.EDUCATION, "Education")}</ul>'
           if getattr(C, 'EDUCATION', None) else '')
    xp = (f'<section class="sec" id="experience" aria-labelledby="xp-h"><div class="wrap sec-grid">'
          f'<div class="sec-label"><p class="kicker"><span class="num">04</span>Work, clubs and study</p><h2 id="xp-h">{smart(C.EXPERIENCE_HEAD)}</h2></div>'
          f'<div><ul class="xp">{rows}</ul>{edu}</div></div></section>')
    # contact
    if isinstance(C.EMAIL, RyanWrites): email = ph(C.EMAIL, 'Contact: email')
    else: email = f'<p class="big"><a href="mailto:{html.escape(C.EMAIL)}">{html.escape(C.EMAIL)}</a></p>'
    contact = (f'<section class="sec contact" id="contact" aria-labelledby="contact-h"><div class="wrap sec-grid">'
               f'<div class="sec-label"><p class="kicker"><span class="num">05</span>Get in touch</p><h2 id="contact-h">{smart(C.CONTACT_HEAD)}</h2></div>'
               f'<div>{prose(C.CONTACT_LINE, "Contact: invitation line", "lede")}<div style="margin-top:20px">{email}</div></div></div></section>')
    body = f'<main id="main">{hero}{about}{work}{skills}{xp}{contact}</main>'
    return head(C.PAGE_TITLE, C.META_DESCRIPTION) + header() + body + footer()

def page_featured():
    F, P = C.FEATURED, C.FEATURED_PAGE
    shots = F['shots']
    gal = ''
    for src, kind, cap, alt in shots:
        if kind == 'phone':
            gal += (f'<figure class="phone-shot"><div class="phone">{img(src, alt, PHONE_W, "240px")}</div>'
                    f'<figcaption>{smart(cap)}</figcaption></figure>')
        else:
            gal += f'<figure>{frame(src, alt, "(max-width:600px) 92vw, (max-width:1200px) 60vw, 720px")}<figcaption>{smart(cap)}</figcaption></figure>'
    if C.SOCIAL_TILES:
        tiles = '<div class="tiles">' + ''.join(f'<figure>{img(s, a, [500, 1000], "(max-width:600px) 92vw, 360px")}<figcaption>{smart(c)}</figcaption></figure>'
                                                for s, a, c in C.SOCIAL_TILES) + '</div>'
    elif C.SOCIAL_TILES_TODO is not None:
        tiles = ph(C.SOCIAL_TILES_TODO, 'Project page: social tiles')
    else:
        tiles = None
    def sec(h, inner, sid):
        return f'<section class="prose-sec" aria-labelledby="{sid}"><h2 id="{sid}">{smart(h)}</h2><div class="measure">{inner}</div></section>'
    body = (f'<main id="main"><div class="wrap"><section class="page-hero" aria-labelledby="title">'
            f'<p class="crumb"><a href="index.html#work"><span aria-hidden="true">&larr;</span> {smart(C.NAME)}</a></p>'
            f'<p class="kicker">{smart(F["kicker"])}</p><h1 id="title">{smart(F["title"])}</h1>'
            f'<div class="feature-body"><div>{prose(P["overview"], "Project page: overview", "lede")}'
            f'<div class="actions"><a class="btn solid" href="{F["live_url"]}">{smart(F["live_label"])} <span class="arr" aria-hidden="true">&#8599;</span></a></div></div>'
            f'{meta_list(F)}</div></section>'
            f'<section aria-label="Screenshots of the campaign website" style="padding:clamp(24px,4vw,48px) 0 clamp(48px,6vw,80px)"><div class="gallery">{gal}</div></section>'
            + sec(P['website_head'], prose(P['website'], 'Project page: the website'), 'web-h')
            + sec(P['messaging_head'], prose(P['messaging'], 'Project page: messaging chapter'), 'msg-h')
            + (sec(P['tiles_head'], tiles, 'tiles-h') if tiles else '')
            + f'<p style="padding:24px 0 72px"><a class="btn" href="index.html#work">See more work <span class="arr" aria-hidden="true">&rarr;</span></a></p>'
            '</div></main>')
    return head(f'{F["title"]} | {C.NAME}', f'{F["title"]}: {F["type"]}, {F["unit_code"]} {F["unit_name"]}, {F["year"]}.') + header(home=False) + body + footer()

def page_404():
    t, s = C.NOT_FOUND
    body = (f'<main id="main"><div class="wrap"><section class="page-hero"><p class="kicker">404</p><h1>{smart(t)}</h1>'
            f'<p class="lede">{smart(s)}</p><p><a class="btn solid" href="/">Home</a></p></section></div></main>')
    PL = list(PLACEHOLDERS)
    out = head(f'{t} | {C.NAME}', s, prefix='/') + header(home=False).replace('href="index.html', 'href="/index.html') + body + footer()
    PLACEHOLDERS[:] = PL  # footer placeholder already counted on other pages
    return out.replace('src="images/', 'src="/images/')

# ------------------------------------------------------------------ build
def scan_content_for_dashes():
    def walk(x, path):
        if isinstance(x, str):
            if '\u2014' in x: sys.exit(f'BUILD STOPPED: em dash in content.py ({path}): {x[:80]!r}')
        elif isinstance(x, RyanWrites): walk(x.what, path)
        elif isinstance(x, dict): [walk(v, f'{path}.{k}') for k, v in x.items()]
        elif isinstance(x, (list, tuple)): [walk(v, f'{path}[{i}]') for i, v in enumerate(x)]
    for k, v in vars(C).items():
        if k.isupper(): walk(v, k)

def count_placeholders():
    found = []
    def walk(x, path):
        if isinstance(x, RyanWrites): found.append((path, x))
        elif isinstance(x, dict): [walk(v, f'{path}.{k}') for k, v in x.items()]
        elif isinstance(x, (list, tuple)): [walk(v, f'{path}[{i}]') for i, v in enumerate(x)]
    for k, v in vars(C).items():
        if k.isupper(): walk(v, k)
    return found

def count_drafts():
    found = []
    def walk(x, path):
        if isinstance(x, (C.DraftStr, C.DraftList)): found.append(path)
        elif isinstance(x, dict): [walk(v, f'{path}.{k}') for k, v in x.items()]
        elif isinstance(x, (list, tuple)): [walk(v, f'{path}[{i}]') for i, v in enumerate(x)]
    for k, v in vars(C).items():
        if k.isupper() and k != 'DRAFTS': walk(v, k)
    return found

def banner(found):
    bar = '!' * 78
    print(f'\n{bar}\n!!  {len(found)} PLACEHOLDER(S) STILL UNFILLED. DO NOT SUBMIT OR DEPLOY THIS BUILD.\n{bar}', file=sys.stderr)
    for path, x in found:
        print(f'  - {path:<34} [{x.who}] {x.what[:70]}{"..." if len(x.what) > 70 else ""} ({x.length})', file=sys.stderr)
    print(f'{bar}\n  Fill them in site-src/content.py. "--release" refuses to build until none remain.\n{bar}\n', file=sys.stderr)

if __name__ == '__main__':
    scan_content_for_dashes()
    found = count_placeholders()
    drafts = count_drafts()
    if RELEASE and found:
        banner(found); sys.exit('RELEASE BUILD REFUSED: placeholders remain (listed above).')
    if RELEASE and drafts:
        sys.exit('RELEASE BUILD REFUSED: assistant drafts remain (Draft(...) in content.py):\n  ' + '\n  '.join(drafts))
    os.makedirs(os.path.join(OUT, 'images'), exist_ok=True)
    build_fonts()
    pages = {'index.html': page_home, 'not-our-game.html': page_featured, '404.html': page_404}
    for f, fn in pages.items():
        html_out = fn()
        if '\u2014' in html_out: sys.exit(f'BUILD STOPPED: em dash in built {f}')
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write(html_out)
    os.makedirs(os.path.join(OUT, 'files'), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, 'files')): os.remove(os.path.join(OUT, 'files', f))
    for src, pub in PDFS: shutil.copyfile(os.path.join(ESSAYS, src), os.path.join(OUT, 'files', pub))
    open(os.path.join(OUT, 'style.css'), 'w').write(CSS)
    open(os.path.join(OUT, 'favicon.svg'), 'w').write(FAVICON)
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')   # GitHub Pages: publish files untouched, no Jekyll
    open(os.path.join(OUT, '_headers'), 'w').write(
        "/*\n  Referrer-Policy: strict-origin-when-cross-origin\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n"
        "/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n/images/*\n  Cache-Control: public, max-age=604800\n")
    # remove resized images no longer referenced
    used = {os.path.basename(p) for v in IMAGES.values() for p in [s.split(' ')[0] for s in v[3].split(', ')]}
    for f in os.listdir(os.path.join(OUT, 'images')):
        if f not in used: os.remove(os.path.join(OUT, 'images', f))
    print('built', OUT, sorted(os.listdir(OUT)))
    if drafts: print(f'{len(drafts)} assistant draft(s) still marked Draft(...): ' + ', '.join(drafts))
    if found: banner(found)
    else: print('No placeholders remain.')
