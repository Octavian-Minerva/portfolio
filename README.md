# Ryan O'Grady: portfolio

Personal portfolio of Ryan O'Grady, live at https://ryanoogrady.netlify.app (mirror: https://octavian-minerva.github.io/portfolio/).

`site/` is the built static site (plain HTML, CSS and a small script; Netlify serves it as-is). `site-src/` holds the Python generator: all copy is in `site-src/content.py`.

```
cd site-src
.venv/bin/python build_site.py --release   # build into ../site
.venv/bin/python check_site.py             # links, accessibility, contrast, screenshots
.venv/bin/python test_interactions.py      # interactive behaviour
```

**Before working on the site, read [AGENTS.md](AGENTS.md):** setup, publishing, the essay sources that live outside this repository, and the design and content decisions behind the site.
