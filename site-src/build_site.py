# Builds Ryan O'Grady's portfolio into ../site/ from content.py (all copy) and img-src/ (image sources).
# Run from anywhere:   .venv/bin/python build_site.py            build, and warn loudly about unfilled placeholders
#                      .venv/bin/python build_site.py --release  refuse to build while any placeholder remains
# Output is plain static HTML/CSS with no JavaScript and no external requests: fonts are self-hosted.
# Deploy (later, not yet): upload the whole ../site/ folder to Netlify (publish directory = site root, no build command).
import hashlib, html, os, re, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C
import essays
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
    return ''.join(f'<p{c}>{keep_together(smart(p.strip()))}</p>' for p in re.split(r'\n\s*\n', x.strip()) if p.strip())

def keep_together(t):
    """Terms that should never break at their hyphen in justified text."""
    return t.replace('COVID-19', '<span class="nowrap">COVID-19</span>')

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
    label = w.get('pdf_label', 'Download PDF' if w.get('read') else 'Read the full essay')
    note = pages.lstrip(', ') if 'PDF' in label else f'PDF{pages}'   # avoid "Download PDF (PDF, 5 pages)"
    return (f'<p class="actions"><a class="btn" href="files/{pub}">{smart(label)} '
            f'<span class="btn-note">({note})</span></a></p>')

def card_href(w):
    """Where the card's title and picture lead: the reading page, else the first internal link, else the PDF."""
    if w.get('read'): return w['read']['page']
    for _, href, external in w.get('links', []):
        if not external: return href
    if w.get('pdf'): return f'files/{w["pdf"][1]}'
    return None

def read_and_pdf(w):
    """Card buttons: a reading page (if any) as the main action, the PDF beside it."""
    if not w.get('read'):
        return pdf_button(w)
    pdf = pdf_button(w)
    pdf_link = re.search(r'<a class="btn".*?</a>', pdf, flags=re.S).group(0).replace('Download PDF', 'PDF', 1) if pdf else ''
    return (f'<p class="actions"><a class="btn solid" href="{w["read"]["page"]}">Read the essay '
            f'<span class="arr" aria-hidden="true">&rarr;</span></a>{pdf_link}</p>')

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
:root{--on-accent:#fff;--topic:#38342e;--bar:#f6f3ee;--dot:#d9d2c5;--head-bg:rgba(250,248,244,.88);color-scheme:light;--ink:#1c1b19;--muted:#57524a;--bg:#faf8f4;--paper:#fff;--line:#e3ddd2;--soft:#f2eee6;
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
main .descriptor p,main p.topic,main p.lede,main p.kicker,main p.unit,main p.org,main p.actions,main p.crumb,main p.big,main p.name,main p.email-row{text-align:left;-webkit-hyphens:manual;hyphens:manual}
.wrap{max-width:var(--wrap);margin:0 auto;padding:0 var(--pad)}
.skip{position:absolute;left:12px;top:-60px;background:var(--ink);color:var(--bg);padding:10px 16px;border-radius:4px;z-index:10;text-decoration:none}
.skip:focus{top:12px;color:var(--bg)}
.kicker{font-family:var(--sans);font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 14px}
.num{color:var(--accent);font-variant-numeric:tabular-nums;margin-right:.6em}

/* header */
.site-head{position:sticky;top:0;z-index:20;border-bottom:1px solid var(--line);background:var(--head-bg);-webkit-backdrop-filter:saturate(1.4) blur(10px);backdrop-filter:saturate(1.4) blur(10px);transition:box-shadow .2s ease}
.site-head.scrolled{box-shadow:0 10px 24px -18px rgba(0,0,0,.45)}
.progress{position:absolute;left:0;right:0;bottom:-1px;height:2px;background:var(--accent);transform-origin:0 50%;transform:scaleX(var(--p,0))}
.head-tools{display:flex;align-items:center;gap:18px;flex-wrap:wrap}
.theme-toggle{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:50%;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer;padding:0}
.theme-toggle:hover{border-color:var(--ink)}
.theme-toggle svg{width:18px;height:18px}
.theme-toggle .moon,[data-theme-now=dark] .theme-toggle .sun{display:none}
[data-theme-now=dark] .theme-toggle .moon{display:block}
.nav a.is-current{border-bottom-color:var(--accent);color:var(--accent)}
.copy{margin-left:12px;font:600 13px/1 var(--sans);letter-spacing:.06em;text-transform:uppercase;color:var(--muted);background:none;border:1px solid var(--line);border-radius:999px;padding:7px 12px;cursor:pointer;vertical-align:middle}
.copy:hover{color:var(--ink);border-color:var(--ink)}
.email-line{display:flex;align-items:center;flex-wrap:wrap;gap:6px 0}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.colophon{font-size:14px;color:var(--muted);max-width:60ch;margin:0 0 12px}
html{scroll-padding-top:96px}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}body{transition:background-color .25s ease,color .25s ease}}
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
.hero h1{font-size:clamp(54px,9vw,120px);line-height:1.02;letter-spacing:-.025em;font-weight:380;margin:0 0 28px}
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
.exploring{margin-top:40px;padding-top:22px;border-top:1px solid var(--line);display:grid;grid-template-columns:15rem minmax(0,1fr);gap:6px 24px;align-items:baseline}
.exploring .kicker{margin:0}
.exploring+.exploring{margin-top:18px}
.points{margin:0;padding-left:1.1em}.points li{margin:0 0 6px}
.card .actions{margin-top:18px;display:flex;flex-wrap:wrap;gap:10px}
.card-link{color:inherit;text-decoration:none;background-image:linear-gradient(currentColor,currentColor);background-size:0 1px;background-repeat:no-repeat;background-position:0 100%;transition:background-size .25s ease}
.card-link:hover{color:inherit;background-size:100% 1px}
.card .thumb a{display:block;height:100%}
.card .thumb img{transition:transform .35s ease}
.card .thumb a:hover img{transform:scale(1.025)}
@media (prefers-reduced-motion:reduce){.card-link,.card .thumb img{transition:none}}
.standfirst{font-family:var(--serif);font-style:italic;font-size:clamp(20px,2vw,24px);line-height:1.45;color:var(--topic);margin:0 0 18px;max-width:40rem;text-align:left!important}
.essay-nav{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:44rem;margin:56px 0 24px;padding-top:24px;border-top:1px solid var(--line)}
.essay-nav a{display:block;text-decoration:none;color:var(--ink);padding:14px 16px;border:1px solid var(--line);border-radius:6px}
.essay-nav a:hover{border-color:var(--ink)}
.essay-nav .dir{display:block;font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.essay-nav .t{font-family:var(--serif);font-size:19px;line-height:1.3}
.essay-nav .next{text-align:right;grid-column:2}
@media (max-width:600px){.essay-nav{grid-template-columns:1fr}.essay-nav .next{grid-column:1}}
.updated{font-size:14px;color:var(--muted)}
.essay-head{max-width:46rem}
.essay-head .unit{margin-bottom:10px}
.page-hero.essay-head h1{font-size:clamp(36px,5vw,60px);line-height:1.08;letter-spacing:-.02em;margin:0 0 18px}
.essay-meta{font-size:15px;color:var(--muted);margin:0 0 18px;text-align:left!important}
.essay-body{max-width:44rem;font-family:var(--serif);font-size:20px;line-height:1.7;padding:clamp(8px,2vw,24px) 0 0;border-top:1px solid var(--line)}
.essay-body p{margin:0 0 1.05em}
.essay-body h2{font-size:clamp(24px,2.4vw,30px);line-height:1.25;margin:1.6em 0 .6em}
.essay-body .refs-h{font-family:var(--sans);font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-top:2.6em}
.refs{list-style:none;margin:0;padding:0;font-family:var(--sans);font-size:15px;line-height:1.55}
.refs li{padding-left:2em;text-indent:-2em;margin:0 0 .75em;overflow-wrap:anywhere}
@media (max-width:600px){.essay-body{font-size:18px}}
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
.frame .bar{height:26px;display:flex;align-items:center;gap:6px;padding:0 12px;border-bottom:1px solid var(--line);background:var(--bar)}
.frame .bar i{width:9px;height:9px;border-radius:50%;background:var(--dot);display:block}
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
.btn:hover{background:var(--ink);color:var(--bg)}
.btn.solid{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.btn.solid:hover{background:var(--accent-ink);border-color:var(--accent-ink);color:var(--on-accent)}
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
.topic{font-family:var(--serif);font-style:italic;font-size:19px;line-height:1.45;color:var(--topic);margin:0 0 16px}
.tags{list-style:none;margin:0 0 18px;padding:0;display:flex;flex-wrap:wrap;gap:6px}
.tags li{font-size:13.5px;line-height:1;padding:7px 11px;border:1px solid var(--line);border-radius:999px;background:var(--paper);color:var(--muted)}
.slides{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.slides figure{margin:0}
.slides figure:first-child{grid-column:1/-1}
.slides img{border:1px solid var(--line);border-radius:6px}

/* skills */
.skills{background:var(--tint);border-top:0}
.skills h2{margin-bottom:clamp(28px,4vw,48px)}
.skills-body{display:grid;grid-template-columns:minmax(0,8fr) minmax(0,4fr);gap:clamp(28px,5vw,72px);align-items:start;
 border-top:1px solid var(--accent);padding-top:clamp(24px,3vw,36px)}
.skills .audit{font-size:20px;line-height:1.65;max-width:62ch}
.skills .audit .ph{font-size:17px;padding:20px 22px;max-width:none}
.skill-groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:clamp(28px,4vw,48px);margin-bottom:clamp(48px,6vw,80px)}
.skill-group{border-top:1px solid var(--ink);padding-top:18px}
.skill-group h3{font-size:clamp(23px,2vw,27px);margin:0 0 12px}
.skill-text p:last-child{margin-bottom:0}
.skill-group .tags{margin:20px 0 0;align-content:start}
@media (min-width:701px){
 .skill-groups{grid-auto-rows:auto}
 .skill-group{display:grid;grid-row:span 3;grid-template-rows:subgrid;row-gap:0}
}
.skill-group p{font-size:17px;line-height:1.6}
.reflect-h{font-size:clamp(26px,2.6vw,34px);margin:0 0 18px}
.skills .audit p:first-child{font-family:var(--serif);font-size:clamp(23px,2.3vw,28px);line-height:1.4}
.skill-list{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px}
.skill-list li{background:var(--paper);border:1px solid #cbd6e4;border-radius:999px;padding:8px 14px;font-size:15px}

/* experience */
.xp{list-style:none;margin:0;padding:0}
.xp li{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);grid-template-areas:'dates text' 'role text';grid-template-rows:auto 1fr;align-items:start;gap:6px 40px;padding:24px 0;border-top:1px solid var(--line)}
.xp li>.dates{grid-area:dates}.xp li>div:nth-child(2){grid-area:role}.xp li>.text{grid-area:text}
.xp li:last-child{border-bottom:1px solid var(--line)}
.xp .dates{font-size:15px;color:var(--muted);font-variant-numeric:tabular-nums}
.xp h3{font-size:24px;margin:0 0 4px}
.xp .org{margin:0;color:var(--muted)}
.xp .text p:last-child{margin:0}
.xp .text p{font-size:17px;line-height:1.6}
.nowrap{white-space:nowrap}
.xp-sub{font-size:15px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:48px 0 12px;font-family:var(--sans);font-weight:600}

/* contact */
.contact .big{font-family:var(--serif);font-size:clamp(28px,4vw,48px);letter-spacing:-.02em;line-height:1.2;word-break:break-word}
.contact .lede+.emails{margin-top:20px}
.contact .email-row{margin:0 0 18px;display:flex;flex-direction:column;gap:2px}
.contact .email-row .big{font-size:clamp(22px,3vw,36px)}
.email-label{font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}

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
 .xp li{grid-template-columns:1fr;grid-template-areas:'dates' 'role' 'text';grid-template-rows:none}
 .xp li>.text:not(:empty){margin-top:10px}
 .site-foot .wrap{grid-template-columns:1fr}
 .exploring{grid-template-columns:1fr}
 .gallery{grid-template-columns:repeat(2,minmax(0,1fr))}
}
html[data-theme=dark]{--ink:#ebe7e0;--muted:#b4aca0;--bg:#141619;--paper:#1d2024;--line:#363a41;--soft:#1b1e22;--accent:#8db4e8;--accent-ink:#b8d1f2;--tint:#18202b;--on-accent:#0f141a;--topic:#d8d2c8;--bar:#23272c;--dot:#4a4f57;--head-bg:rgba(20,22,25,.86);color-scheme:dark}
@media (prefers-color-scheme:dark){html:not([data-theme=light]){--ink:#ebe7e0;--muted:#b4aca0;--bg:#141619;--paper:#1d2024;--line:#363a41;--soft:#1b1e22;--accent:#8db4e8;--accent-ink:#b8d1f2;--tint:#18202b;--on-accent:#0f141a;--topic:#d8d2c8;--bar:#23272c;--dot:#4a4f57;--head-bg:rgba(20,22,25,.86);color-scheme:dark}}
html[data-theme-now=dark] .card .thumb,html[data-theme-now=dark] .frame{border-color:#2b2f35}
@media print{.site-head,.skip,.actions,.copy,.theme-toggle,.progress{display:none!important}html,body{background:#fff!important;color:#000!important}body{font-size:11pt}.sec{padding:14pt 0;border-top:1px solid #ccc}.skills{background:none!important}.hero,.card,.skill-group,.xp li,.exploring{break-inside:avoid}.thumb,.portrait{display:none}main a[href^=http]::after,main a[href$='.pdf']::after{content:' (' attr(href) ')';font-size:9pt;color:#444;word-break:break-all}}
.work-head{display:flex;align-items:end;justify-content:space-between;gap:16px 32px;flex-wrap:wrap}
.rail{display:grid;grid-auto-flow:column;grid-auto-columns:calc((100% - 2 * clamp(20px,2.4vw,32px)) / 3);gap:clamp(20px,2.4vw,32px);
 overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;padding:4px 2px 18px;margin:0 -2px;scrollbar-width:thin;scrollbar-color:var(--line) transparent}
.rail:focus-visible{outline:3px solid var(--accent);outline-offset:6px}
.rail>.card{scroll-snap-align:start;border:1px solid var(--line);border-radius:8px;background:var(--paper);overflow:hidden;display:flex;flex-direction:column;padding:0}
.card .media{height:168px;border-bottom:1px solid var(--line);overflow:hidden;background:var(--tint)}
.card .media img{display:block;width:100%;height:100%;object-fit:cover;object-position:center;transition:transform .35s ease}
.card .media.fit img{object-fit:cover}
.page-preview{height:100%;padding:20px 20px 0;position:relative;
 background:var(--tint)}
.page-preview p{margin:0;font-family:var(--serif);font-size:15.5px;line-height:26px;color:var(--topic);text-align:left!important;hyphens:manual}
.page-preview::after{content:"";position:absolute;inset:auto 0 0 0;height:70%;background:linear-gradient(transparent,var(--tint))}
.card-body{display:flex;flex-direction:column;flex:1;padding:18px 20px 20px}
.card-body .unit{margin:0 0 12px}
.card-body h3{font-size:clamp(21px,1.7vw,24px);margin:0 0 10px}
.card-q{margin:0 0 16px}
.card-body .topic{font-size:16.5px;margin:0}
.card-summary{margin:0 0 18px}
.card-summary p{font-size:15.5px;line-height:1.6;margin:0 0 .7em;text-align:left!important;hyphens:manual}
.card-summary p:last-child{margin-bottom:0}
.card-body .tags{margin:0 0 20px;align-content:start}
.card-actions .actions{margin:0}
[hidden]{display:none!important}
/* the title link stretches over the whole card; buttons and the Summary toggle sit above it */
.rail>.card{position:relative}
.rail>.card .card-link::after{content:"";position:absolute;inset:0;z-index:1}
.card-actions .actions{position:relative;z-index:2}
.rail>.card:hover .card-link{background-size:100% 1px}
.rail>.card:hover .media img{transform:scale(1.03)}
.card-actions .actions{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px}
.card-actions .btn{padding:10px 16px;font-size:15px}
.card-actions .btn:first-child{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.card-actions .btn:first-child:hover{background:var(--accent-ink);border-color:var(--accent-ink);color:var(--on-accent)}
.card-actions .btn:not(:first-child){border-color:transparent;background:none;color:var(--accent);padding-left:2px;padding-right:2px}
.card-actions .btn:not(:first-child):hover{background:none;color:var(--accent-ink);text-decoration:underline;text-underline-offset:3px}
.more summary{cursor:pointer;font-size:14px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);list-style:none;display:inline-flex;align-items:center;gap:6px;padding:4px 0}
.more summary::-webkit-details-marker{display:none}
.more summary::after{content:"+";font-size:17px;line-height:1;font-weight:400}
.more[open] summary::after{content:"\2212"}
.more[open] summary{margin-bottom:8px}
.more p{font-size:16px}
.rail-wrap{position:relative}
.rail-btn{width:46px;height:46px;border-radius:50%;border:1px solid var(--ink);background:transparent;color:var(--ink);cursor:pointer;font-size:18px;display:grid;place-items:center}
.rail-btn:hover:not(:disabled){background:var(--ink);color:var(--bg)}
.rail-btn:disabled{opacity:.3;cursor:default}
.rail-count{font-size:14px;color:var(--muted);font-variant-numeric:tabular-nums;text-align:center;margin:14px 0 0}
.rail-btn{position:absolute;top:50%;transform:translateY(-50%);z-index:3;background:var(--bg);box-shadow:0 6px 18px -8px rgba(0,0,0,.35)}
.rail-btn.prev{left:-6px}.rail-btn.next{right:-6px}
/* centred mode (set by the script on wide screens): one card in focus, neighbours faded */
.rail.cover{grid-auto-columns:min(460px,64vw);padding-inline:calc(50% - min(460px,64vw) / 2);scroll-padding-inline:0;gap:28px}
.rail.cover>.card{scroll-snap-align:center;transition:opacity .35s ease,transform .35s ease,box-shadow .35s ease;opacity:.42;transform:scale(.93)}
.rail.cover>.card.is-active{opacity:1;transform:none;box-shadow:0 18px 40px -24px rgba(0,0,0,.45)}
.rail.cover{padding-block:8px 40px}.rail.cover~.rail-count,.rail-wrap~.rail-count{margin-top:0}
.rail.cover>.card:not(.is-active){cursor:pointer}
.rail.cover::-webkit-scrollbar{display:none}.rail.cover{scrollbar-width:none}
@media (prefers-reduced-motion:reduce){.rail.cover>.card{transition:none}}
.xp .more summary{font-size:13px}
/* wide screens: every card shares the rail's seven row tracks (subgrid), so rows line up across cards */
@media (min-width:701px){
 .rail{grid-template-rows:repeat(7,auto)}
 .rail,.rail.cover{row-gap:0}
 .rail>.card{display:grid;grid-row:span 7;grid-template-rows:subgrid;row-gap:0}
 .rail>.card>.card-body{display:grid;grid-row:span 6;grid-template-rows:subgrid;row-gap:0}
 .rail>.card>.card-body>*{min-width:0}
}
@media (max-width:1100px){.rail{grid-auto-columns:calc((100% - clamp(20px,2.4vw,32px)) / 2)}}
@media (max-width:700px){
 .rail{grid-auto-flow:row;grid-auto-columns:auto;overflow:visible;scroll-snap-type:none;padding:0;margin:0}
 .rail-btn,.rail-count{display:none!important}
}
@media (prefers-reduced-motion:reduce){.rail{scroll-behavior:auto}.card .media img{transition:none}}
@media (max-width:900px){.site-head{transition:transform .25s ease,box-shadow .2s ease}.site-head.head-hidden{transform:translateY(-100%)}}
@media (max-width:900px) and (prefers-reduced-motion:reduce){.site-head{transition:none}}
@media (max-width:600px){
 body{font-size:17px}
 .site-head .wrap{padding-top:14px;padding-bottom:14px}
 .nav ul{gap:2px 18px}
 .nav a{font-size:15.5px}
 .head-tools{display:contents}
 .theme-toggle{order:1;margin-left:auto;width:34px;height:34px}
 .nav{order:2;width:100%}
 html{scroll-padding-top:110px}
 .stage{padding-right:56px;padding-top:64px}
 .portrait{max-width:280px}
 .phone{width:34%;border-width:4px;border-radius:18px;bottom:-20px}
 .phone img{border-radius:14px}
 .gallery,.tiles{grid-template-columns:1fr}
 .gallery figure:first-child{grid-column:auto}.gallery .phone-shot{grid-row:auto}
 .frame .bar{height:18px}.frame .bar i{width:7px;height:7px}
}
""".replace('ACCENT', ACCENT)

SITE_JS = '(() => {\n  const d = document, root = d.documentElement;\n  const head = d.querySelector(\'.site-head\'), bar = d.querySelector(\'.progress\');\n  // Header shadow and reading progress\n  const onScroll = () => {\n    const max = root.scrollHeight - innerHeight;\n    if (head) head.classList.toggle(\'scrolled\', scrollY > 4);\n    if (bar) bar.style.setProperty(\'--p\', max > 0 ? Math.min(1, scrollY / max).toFixed(4) : 0);\n  };\n  addEventListener(\'scroll\', onScroll, { passive: true }); addEventListener(\'resize\', onScroll); onScroll();\n  // On small screens, tuck the header away while scrolling down and bring it back on the way up\n  let lastY = scrollY;\n  const small = matchMedia(\'(max-width: 900px)\');\n  addEventListener(\'scroll\', () => {\n    const y = scrollY;\n    if (head && small.matches) {\n      if (y > lastY + 6 && y > 140 && !head.contains(d.activeElement)) head.classList.add(\'head-hidden\');\n      else if (y < lastY - 6 || y <= 140) head.classList.remove(\'head-hidden\');\n    } else if (head) head.classList.remove(\'head-hidden\');\n    lastY = y;\n  }, { passive: true });\n  if (head) head.addEventListener(\'focusin\', () => head.classList.remove(\'head-hidden\'));\n  // Highlight the section currently in view: the last section whose top has passed 40% of the screen\n  const pairs = [...d.querySelectorAll(\'.nav a[href*="#"]\')]\n    .map(a => [d.getElementById(a.hash.slice(1)), a]).filter(([sec]) => sec);\n  const spy = () => {\n    if (!pairs.length) return;\n    let hit = null;\n    for (const p of pairs) if (p[0].getBoundingClientRect().top <= innerHeight * 0.4) hit = p;\n    if (innerHeight + scrollY >= root.scrollHeight - 2) hit = pairs[pairs.length - 1];\n    pairs.forEach(([, a]) => {\n      const on = hit && a === hit[1];\n      a.classList.toggle(\'is-current\', on);\n      if (on) a.setAttribute(\'aria-current\', \'location\'); else a.removeAttribute(\'aria-current\');\n    });\n  };\n  addEventListener(\'scroll\', spy, { passive: true }); spy();\n  // Selected work: on wide screens, a centred carousel with the active card in focus\n  const rail = d.querySelector(\'.rail\');\n  if (rail) {\n    const cards = [...rail.children];\n    const prev = d.querySelector(\'.rail-btn.prev\'), next = d.querySelector(\'.rail-btn.next\'), count = d.querySelector(\'.rail-count\');\n    const wide = matchMedia(\'(min-width: 701px)\');\n    let active = 0;\n    const centreOf = el => el.offsetLeft + el.offsetWidth / 2;\n    const goTo = (i, smooth = true) => {\n      i = Math.max(0, Math.min(cards.length - 1, i));\n      rail.scrollTo({ left: centreOf(cards[i]) - rail.clientWidth / 2, behavior: smooth ? \'smooth\' : \'auto\' });\n    };\n    const update = () => {\n      if (!rail.classList.contains(\'cover\')) return;\n      const mid = rail.scrollLeft + rail.clientWidth / 2;\n      let best = 0, dist = Infinity;\n      cards.forEach((c, i) => { const dd = Math.abs(centreOf(c) - mid); if (dd < dist) { dist = dd; best = i; } });\n      active = best;\n      cards.forEach((c, i) => c.classList.toggle(\'is-active\', i === active));\n      count.textContent = `${active + 1} of ${cards.length}`;\n      prev.disabled = active === 0;\n      next.disabled = active === cards.length - 1;\n    };\n    const mode = () => {\n      const on = wide.matches;\n      rail.classList.toggle(\'cover\', on);\n      [prev, next, count].forEach(el => { if (el) el.hidden = !on; });\n      if (!on) cards.forEach(c => c.classList.remove(\'is-active\'));\n      else { goTo(active, false); update(); }\n    };\n    prev.addEventListener(\'click\', () => goTo(active - 1));\n    next.addEventListener(\'click\', () => goTo(active + 1));\n    // a faded card comes to the centre when clicked (links inside it still work once it is active)\n    cards.forEach((c, i) => c.addEventListener(\'click\', e => {\n      if (rail.classList.contains(\'cover\') && i !== active) { e.preventDefault(); goTo(i); }\n    }));\n    // keyboard focus moving into a faded card brings it to the centre\n    cards.forEach((c, i) => c.addEventListener(\'focusin\', () => { if (rail.classList.contains(\'cover\') && i !== active) goTo(i); }));\n    rail.addEventListener(\'scroll\', () => requestAnimationFrame(update), { passive: true });\n    rail.addEventListener(\'keydown\', e => {\n      if (e.target !== rail) return;\n      if (e.key === \'ArrowRight\') { e.preventDefault(); goTo(active + 1); }\n      if (e.key === \'ArrowLeft\') { e.preventDefault(); goTo(active - 1); }\n    });\n    if (wide.addEventListener) wide.addEventListener(\'change\', mode);\n    addEventListener(\'resize\', () => { if (rail.classList.contains(\'cover\')) goTo(active, false); });\n    mode();\n  }\n  // Light and dark themes: follow the system unless the visitor has chosen\n  const mq = matchMedia(\'(prefers-color-scheme: dark)\');\n  const now = () => root.dataset.theme || (mq.matches ? \'dark\' : \'light\');\n  const toggle = d.querySelector(\'.theme-toggle\');\n  const sync = () => {\n    root.dataset.themeNow = now();\n    if (toggle) toggle.setAttribute(\'aria-label\', now() === \'dark\' ? \'Switch to light theme\' : \'Switch to dark theme\');\n  };\n  if (toggle) {\n    toggle.hidden = false;\n    toggle.addEventListener(\'click\', () => {\n      root.dataset.theme = now() === \'dark\' ? \'light\' : \'dark\';\n      try { localStorage.setItem(\'theme\', root.dataset.theme); } catch (e) {}\n      sync();\n    });\n  }\n  if (mq.addEventListener) mq.addEventListener(\'change\', sync);\n  sync();\n  // Copy email addresses\n  const live = d.getElementById(\'live\');\n  if (navigator.clipboard) d.querySelectorAll(\'.copy\').forEach(b => {\n    b.hidden = false;\n    b.addEventListener(\'click\', async () => {\n      try {\n        await navigator.clipboard.writeText(b.dataset.copy);\n        b.textContent = \'Copied\'; if (live) live.textContent = \'Email address copied\';\n        setTimeout(() => { b.textContent = \'Copy\'; }, 1800);\n      } catch (e) {}\n    });\n  });\n})();\n'

def build_og_image():
    """1200x630 link-preview card: name, degree line, descriptor and photo."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    W, H, pad = 1200, 630, 72
    im = Image.new('RGB', (W, H), '#faf8f4'); d = ImageDraw.Draw(im)
    serif = os.path.join(HERE, 'fonts-src', 'newsreader-Newsreader[opsz,wght].ttf')
    sans = os.path.join(HERE, 'fonts-src', 'sourcesans3-SourceSans3[wght].ttf')
    d.rectangle([0, 0, W, 10], fill=ACCENT)
    kicker = ImageFont.truetype(sans, 22)
    try: kicker.set_variation_by_axes([600])
    except Exception: pass
    k1, k2 = (C.HERO_KICKER.upper().split(' \u00b7 ') + [''])[:2]   # degree on one line, university on the next
    d.text((pad, 104), k1, font=kicker, fill='#57524a')
    if k2: d.text((pad, 134), k2, font=kicker, fill='#57524a')
    name = ImageFont.truetype(serif, 104)
    d.text((pad, 178), C.NAME.replace("'", '\u2019'), font=name, fill='#1c1b19')
    desc = ImageFont.truetype(serif, 34)
    words, lines, cur = str(C.DESCRIPTOR).split(), [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if d.textlength(t, font=desc) > 640: lines.append(cur); cur = wd
        else: cur = t
    lines.append(cur)
    for i, ln in enumerate(lines): d.text((pad, 330 + i * 46), ln, font=desc, fill='#38342e')
    if isinstance(C.PHOTO, tuple):
        ph = Image.open(os.path.join(HERE, 'img-src', C.PHOTO[0])).convert('RGB')
        ph = ImageOps.fit(ph, (360, 450))
        im.paste(ph, (W - pad - 360, (H - 450) // 2))
    im.save(os.path.join(OUT, 'og.jpg'), quality=88)

# ------------------------------------------------------------------ page parts
def head(title, desc, prefix='', page=''):
    og = ''
    if C.SITE_URL:
        og = (f'<meta property="og:type" content="website"><meta property="og:title" content="{attr(title)}">'
              f'<meta property="og:description" content="{attr(desc)}"><meta property="og:url" content="{C.SITE_URL}/{page}">'
              f'<meta property="og:image" content="{C.SITE_URL}/og.jpg"><meta property="og:image:width" content="1200">'
              f'<meta property="og:image:height" content="630"><meta property="og:image:alt" content="{attr(C.NAME)}: {attr(C.HERO_KICKER)}">'
              f'<meta name="twitter:card" content="summary_large_image">')
    return ('<!doctype html><html lang="en-AU"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{smart(title)}</title><meta name="description" content="{attr(desc)}">{NOINDEX}'
            f'<meta name="theme-color" content="#faf8f4">{og}'
            f'<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">'
            f'<link rel="preload" href="{prefix}fonts/newsreader.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="preload" href="{prefix}fonts/source-sans-3.woff2" as="font" type="font/woff2" crossorigin>'
            f'<link rel="stylesheet" href="{prefix}style.css?v={asset_version()}">'
            '<script>try{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}catch(e){}</script>'
            f'<script src="{prefix}site.js?v={asset_version()}" defer></script></head><body>'
            '<a class="skip" href="#main">Skip to content</a>')

def asset_version():
    return hashlib.sha1((CSS + SITE_JS).encode()).hexdigest()[:10]

def header(home=True):
    base = '' if home else 'index.html'
    items = ''.join(f'<li><a href="{base}#{a}">{smart(t)}</a></li>' for t, a in C.NAV)
    brand_href = '#top' if home else 'index.html'
    return (f'<header class="site-head" id="top"><div class="wrap"><a class="brand" href="{brand_href}">{smart(C.NAME)}</a>'
            f'<div class="head-tools"><nav class="nav" aria-label="Main"><ul>{items}</ul></nav>'
            f'<button class="theme-toggle" type="button" aria-label="Switch to dark theme" hidden><svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg><svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M20 14.6A8.5 8.5 0 0 1 9.4 4a8.5 8.5 0 1 0 10.6 10.6z"/></svg></button></div>'
            '</div><div class="progress" aria-hidden="true"></div></header>')

def footer():
    credits = ''
    for c in C.CREDITS:
        t = smart(c)
        for k, url in C.CREDIT_LINKS.items():
            t = t.replace(smart(k), f'<a href="{url}">{smart(k)}</a>', 1)
        credits += f'<li>{t}</li>'
    return (f'<footer class="site-foot"><div class="wrap"><div><p class="name">{smart(C.NAME)}</p><p>&copy; {C.YEAR}</p>'
            + (f'<p class="updated">Last updated {smart(C.LAST_UPDATED)}</p>' if getattr(C, 'LAST_UPDATED', None) else '') + '</div>'
            f'<div>{prose(C.AI_NOTE, "Footer: AI note") if C.AI_NOTE else ""}'
            + (f'<p class="colophon">{smart(C.COLOPHON)}</p>' if getattr(C, 'COLOPHON', None) else '')
            + f'<ul class="credits">{credits}</ul></div></div></footer></body></html>')

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
    # work: compact cards in a carousel; every card has the same media strip
    cards = ''
    for i, w in enumerate(C.WORK):
        where = f'Work card {i + 1} ({w["unit_code"]}): blurb'
        tags = ''.join(f'<li>{smart(t)}</li>' for t in w.get('tags', []))
        href = card_href(w)
        title_html = f'<a class="card-link" href="{href}">{smart(w["title"])}</a>' if href else smart(w["title"])
        if w.get('read'):   # essays: a ruled "page" carrying the essay's own opening line
            first = next(t for k, t in essay_blocks(w) if k == 'p')
            opening = ' '.join(re.sub(r'<[^>]+>', '', first).split()[:40])
            media = f'<div class="page-preview"><p>{opening}</p></div>'
        elif w.get('thumb'):
            media = img(w["thumb"][0], w["thumb"][1], [480, 960], "(max-width:700px) 92vw, 400px")
        else:
            media = ''
        media = f'<div class="media{" fit" if w.get("thumb_fit") == "contain" else ""}">{media}</div>'
        summary = f'<div class="card-summary">{prose(w.get("blurb"), where)}</div>'
        cards += (f'<article class="card" aria-roledescription="slide" aria-label="{i + 1} of {len(C.WORK)}">{media}<div class="card-body">'
                  f'{unit_line(w)}<h3><span class="type">{smart(w["type"])}</span>{title_html}</h3>'
                  f'<div class="card-q">{prose(w["topic"], where.replace("blurb", "topic line"), "topic")}</div>'
                  f'{summary}<ul class="tags" aria-label="Topics">{tags}</ul>'
                  f'<div class="card-actions">{read_and_pdf(w)}{link_buttons(w)}</div></div></article>')
    prev_btn = '<button class="rail-btn prev" type="button" aria-label="Previous piece of work" hidden><span aria-hidden="true">&larr;</span></button>'
    next_btn = '<button class="rail-btn next" type="button" aria-label="Next piece of work" hidden><span aria-hidden="true">&rarr;</span></button>'
    count = f'<p class="rail-count" aria-live="polite" hidden>1 of {len(C.WORK)}</p>'
    work = (f'<section class="sec" id="work" aria-labelledby="work-h"><div class="wrap">'
            f'<div class="work-head"><div><p class="kicker"><span class="num">02</span>Essays, presentations and campaigns</p><h2 id="work-h">{smart(C.WORK_HEAD)}</h2></div></div>'
            f'<div class="rail-wrap">{prev_btn}<div class="rail" role="region" aria-roledescription="carousel" aria-label="Selected work" tabindex="0">{cards}</div>{next_btn}</div>'
            f'{count}</div></section>')
    # skills
    if C.SKILLS_LIST is None: skl = ''
    elif isinstance(C.SKILLS_LIST, RyanWrites): skl = f'<p class="kicker">{smart(C.SKILLS_LIST_LABEL)}</p>' + ph(C.SKILLS_LIST, 'Skills: list')
    else: skl = f'<p class="kicker">{smart(C.SKILLS_LIST_LABEL)}</p><ul class="skill-list">' + ''.join(f'<li>{smart(s)}</li>' for s in C.SKILLS_LIST) + '</ul>'
    def skill_group(g):
        tags = ''.join(f'<li>{smart(t)}</li>' for t in g.get('tags') or [])
        return (f'<article class="skill-group"><h3>{smart(g["title"])}</h3><div class="skill-text">{prose(g["text"], "Skills: " + g["title"])}</div>'
                + (f'<ul class="tags" aria-label="Skills">{tags}</ul>' if tags else '') + '</article>')
    groups = ''.join(skill_group(g) for g in getattr(C, 'SKILL_GROUPS', []))
    skills = (f'<section class="sec skills" id="skills" aria-labelledby="skills-h"><div class="wrap">'
              f'<p class="kicker"><span class="num">03</span>{smart(C.SKILLS_KICKER)}</p><h2 id="skills-h">{smart(C.SKILLS_HEAD)}</h2>'
              + (f'<div class="skill-groups">{groups}</div>' if groups else '')
              + f'<div class="skills-body"><div class="audit"><h3 class="reflect-h">{smart(C.REFLECTION_HEAD)}</h3>{prose(C.SKILLS_AUDIT, "Skills: audit and reflection")}</div><div>{skl}</div></div></div></section>')
    # experience
    def xp_rows(items, label):
        return ''.join(f'<li><div class="dates">{inline(e["dates"], f"{label} {i + 1}: dates")}</div>'
                       f'<div><h3>{inline(e["role"], f"{label} {i + 1}: role")}</h3><p class="org">{smart(e["org"])}</p></div>'
                       + (f'<div class="text">{prose(e["text"], f"{label} {i + 1}: description")}</div></li>' if e.get("text") else '<div class="text"></div></li>')
                       for i, e in enumerate(items))
    rows = xp_rows([e for e in C.EXPERIENCE if not e.get('earlier')], 'Experience')
    earlier = [e for e in C.EXPERIENCE if e.get('earlier')]
    if earlier:
        rows += f'</ul><h3 class="xp-sub">{smart(C.EARLIER_HEAD)}</h3><ul class="xp">' + xp_rows(earlier, 'Earlier')
    edu = (f'<h3 class="xp-sub">{smart(C.EDUCATION_HEAD)}</h3><ul class="xp">{xp_rows(C.EDUCATION, "Education")}</ul>'
           if getattr(C, 'EDUCATION', None) else '')
    xp = (f'<section class="sec" id="experience" aria-labelledby="xp-h"><div class="wrap sec-grid">'
          f'<div class="sec-label"><p class="kicker"><span class="num">04</span>Employment, involvement and education</p><h2 id="xp-h">{smart(C.EXPERIENCE_HEAD)}</h2></div>'
          f'<div><ul class="xp">{rows}</ul>{edu}</div></div></section>')
    # contact
    if isinstance(C.EMAIL, RyanWrites): email = ph(C.EMAIL, 'Contact: email')
    elif isinstance(C.EMAIL, str): email = f'<p class="big"><a href="mailto:{html.escape(C.EMAIL)}">{html.escape(C.EMAIL)}</a></p>'
    else:  # list of (label, address)
        email = ''.join(f'<p class="email-row"><span class="email-label">{smart(label)}</span><span class="email-line">'
                        f'<a class="big" href="mailto:{html.escape(addr)}">{html.escape(addr)}</a>'
                        f'<button class="copy" type="button" data-copy="{html.escape(addr)}" aria-label="Copy {html.escape(label.lower())} email address" hidden>Copy</button></span></p>'
                        for label, addr in C.EMAIL) + '<span class="sr-only" aria-live="polite" id="live"></span>'
    contact = (f'<section class="sec contact" id="contact" aria-labelledby="contact-h"><div class="wrap sec-grid">'
               f'<div class="sec-label"><p class="kicker"><span class="num">05</span>Correspondence</p><h2 id="contact-h">{smart(C.CONTACT_HEAD)}</h2></div>'
               f'<div>{prose(C.CONTACT_LINE, "Contact: invitation line", "lede")}<div class="emails">{email}</div></div></div></section>')
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
            f'<p class="crumb"><a href="index.html#work"><span aria-hidden="true">&larr;</span> Selected work</a></p>'
            f'<p class="kicker">{smart(F["kicker"])}</p><h1 id="title">{smart(F["title"])}</h1>'
            f'<div class="feature-body"><div>{prose(P["overview"], "Project page: overview", "lede")}'
            f'<div class="actions"><a class="btn solid" href="{F["live_url"]}">{smart(F["live_label"])} <span class="arr" aria-hidden="true">&#8599;</span></a></div></div>'
            f'{meta_list(F)}</div></section>'
            f'<section aria-label="Screenshots of the campaign website" style="padding:clamp(24px,4vw,48px) 0 clamp(48px,6vw,80px)"><div class="gallery">{gal}</div></section>'
            + sec(P['website_head'], prose(P['website'], 'Project page: the website'), 'web-h')
            + sec(P['messaging_head'], prose(P['messaging'], 'Project page: messaging chapter'), 'msg-h')
            + (sec(P['tiles_head'], tiles, 'tiles-h') if tiles else '')
            + f'<p style="padding:24px 0 72px"><a class="btn" href="index.html#work">See all work <span class="arr" aria-hidden="true">&rarr;</span></a></p>'
            '</div></main>')
    return head(f'{F["title"]} | {C.NAME}', f'{F["title"]}: {F["type"]}, {F["unit_code"]} {F["unit_name"]}, {F["year"]}.', page='not-our-game.html') + header(home=False) + body + footer()

ESSAY_CHECKS = []   # (page, differences) from essays.verify, reported by the build

_ESSAY_CACHE = {}

def essay_blocks(w):
    r = w['read']
    if r['page'] in _ESSAY_CACHE: return _ESSAY_CACHE[r['page']]
    src = os.path.join(ESSAYS, r['src'])
    blocks = essays.from_docx(src) if src.endswith('.docx') else essays.from_pdf(src)
    for old, new in r.get('fixes', []):
        hits = [i for i, (_, t) in enumerate(blocks) if old in t]
        if len(hits) != 1: sys.exit(f'BUILD STOPPED: fix not found exactly once in {r["src"]}: {old!r}')
        k, t = blocks[hits[0]]; blocks[hits[0]] = (k, t.replace(old, new))
    pdf = os.path.join(ESSAYS, w['pdf'][0])
    ESSAY_CHECKS.append((r['page'], essays.verify(blocks, pdf, w['title'])))
    _ESSAY_CACHE[r['page']] = blocks
    return blocks

def essay_nav(w):
    """Previous and next reading pages, in the order the cards appear."""
    order = [x for x in C.WORK if x.get('read')]
    i = order.index(w)
    out = ''
    if i > 0:
        p = order[i - 1]
        out += f'<a class="prev" href="{p["read"]["page"]}"><span class="dir">&larr; Previous</span><span class="t">{smart(p["title"])}</span></a>'
    if i < len(order) - 1:
        n = order[i + 1]
        out += f'<a class="next" href="{n["read"]["page"]}"><span class="dir">Next &rarr;</span><span class="t">{smart(n["title"])}</span></a>'
    return f'<nav class="essay-nav" aria-label="More essays">{out}</nav>' if out else ''

def page_essay(w):
    blocks = essay_blocks(w)
    body_words = sum(len(re.sub(r'<[^>]+>', ' ', t).split()) for k, t in blocks if k in ('p', 'h'))
    minutes = max(1, round(body_words / 230))
    parts, refs = [], []
    for k, t in blocks:
        if k == 'h': parts.append(f'<h2>{t}</h2>')
        elif k == 'p': parts.append(f'<p>{t}</p>')
        elif k == 'refs': parts.append(f'<h2 class="refs-h">{t}</h2>')
        elif k == 'ref': refs.append(f'<li>{t}</li>')
    if refs:
        i = next(n for n, x in enumerate(parts) if x.startswith('<h2 class="refs-h"'))
        parts.insert(i + 1, '<ul class="refs">' + ''.join(refs) + '</ul>')
    pdf = f'files/{w["pdf"][1]}'
    head_html = (f'<section class="page-hero essay-head" aria-labelledby="title">'
                 f'<p class="crumb"><a href="index.html#work"><span aria-hidden="true">&larr;</span> Selected work</a></p>'
                 f'{unit_line(w)}<p class="kicker">{smart(w["type"])}</p><h1 id="title">{smart(w["title"])}</h1>'
                 f'<p class="standfirst">{smart(w["topic"])}</p>'
                 f'<p class="essay-meta">About {round(body_words, -2):,} words &middot; {minutes}-minute read &middot; '
                 f'Submitted for {smart(w["unit_code"])} {smart(w["unit_name"])}, Swinburne University of Technology, {smart(w["year"])}</p>'
                 f'<p class="actions"><a class="btn" href="{pdf}">Download PDF <span class="arr" aria-hidden="true">&darr;</span></a></p></section>')
    body = (f'<main id="main"><div class="wrap">{head_html}'
            f'<article class="essay-body" aria-labelledby="title">{"".join(parts)}</article>{essay_nav(w)}'
            f'<p style="padding:24px 0 72px"><a class="btn" href="index.html#work">See all work <span class="arr" aria-hidden="true">&rarr;</span></a></p>'
            '</div></main>')
    desc = f'{w["title"]}: {w["type"].lower()} by {C.NAME} for {w["unit_code"]} {w["unit_name"]}, Swinburne University of Technology, {w["year"]}.'
    return head(f'{w["title"]} | {C.NAME}', desc, page=w['read']['page']) + header(home=False) + body + footer()

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
    for w in C.WORK:
        if w.get('read'): pages[w['read']['page']] = (lambda w=w: page_essay(w))
    for f, fn in pages.items():
        html_out = fn()
        # essays are Ryan's submitted text, reproduced exactly; the em-dash rule applies to site copy only
        if '\u2014' in html_out and not f.startswith('essay-'): sys.exit(f'BUILD STOPPED: em dash in built {f}')
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write(html_out)
    os.makedirs(os.path.join(OUT, 'files'), exist_ok=True)
    for f in os.listdir(os.path.join(OUT, 'files')): os.remove(os.path.join(OUT, 'files', f))
    for src, pub in PDFS: shutil.copyfile(os.path.join(ESSAYS, src), os.path.join(OUT, 'files', pub))
    open(os.path.join(OUT, 'style.css'), 'w').write(CSS)
    build_og_image()
    open(os.path.join(OUT, 'site.js'), 'w').write(SITE_JS)
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
    for page, diffs in ESSAY_CHECKS:
        print(f'{page}: matches the submitted PDF word for word' if not diffs else f'{page}: {len(diffs)} difference(s) from the PDF')
        for d in diffs[:20]: print('   ', d)
    if RELEASE and any(d for _, d in ESSAY_CHECKS): sys.exit('RELEASE BUILD REFUSED: an essay page differs from its PDF')
    if drafts: print(f'{len(drafts)} assistant draft(s) still marked Draft(...): ' + ', '.join(drafts))
    if found: banner(found)
    else: print('No placeholders remain.')
