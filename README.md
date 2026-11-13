# Ryan O'Grady: portfolio

Static personal portfolio. `site/` is the built site (plain HTML and CSS; nothing to build to serve it). `site-src/` holds the generator.

- All copy lives in `site-src/content.py`.
- `site-src/build_site.py` builds the site. Flags: one for a noindex draft copy, and `--release` for the final build, which refuses to run while placeholders or drafts remain.
- `site-src/check_site.py` checks links, alt text, contrast and keyboard focus, and takes screenshots. It needs Pillow, fontTools and Playwright.
