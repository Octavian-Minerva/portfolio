# Ryan O'Grady: portfolio

Personal portfolio of Ryan O'Grady, live at https://ryanoogrady.netlify.app (mirror: https://octavian-minerva.github.io/portfolio/).

`site/` is the built static site (plain HTML, CSS and a small script; Netlify serves it as-is). `site-src/` holds the Python generator: all copy is in `site-src/content.py`.

## Building

Requires Python 3.11, `pandoc` (for .docx essays) and poppler's `pdftohtml` and `pdftotext` (for PDF essays). The essay sources (`essays-src/`, alongside `site/`) are not in this repository, so the reading pages cannot be rebuilt from a fresh clone without them.

```
cd site-src
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python build_site.py --release   # build into ../site
.venv/bin/python check_site.py             # links, accessibility, contrast, screenshots
.venv/bin/python test_interactions.py      # interactive behaviour
```

The browser checks expect Chromium at `/opt/pw-browsers/`; elsewhere, run `.venv/bin/playwright install chromium` and change the `EXE` line in `check_site.py` and `test_interactions.py`.
