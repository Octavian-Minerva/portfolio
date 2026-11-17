# Handover guide: Ryan O'Grady's portfolio

Read this before changing anything. It records what the site is, how it is built and published, and the decisions behind its content and design, so that any agent (or person) can pick the work up without the original conversation.

Last updated: 17 November 2026.

## 1. What this is

- A personal portfolio for Ryan O'Grady: politics student (Bachelor of Arts, Politics, Power and Technology, Swinburne University of Technology) who also works as an AI systems developer.
- **Live:** https://ryanoogrady.netlify.app (canonical address; this is the one Ryan shares).
- **Mirror:** https://octavian-minerva.github.io/portfolio/ (GitHub Pages copy of the same build; no Netlify badge).
- **Repository:** https://github.com/Octavian-Minerva/portfolio (public).
- **Origin:** built in November 2026 as Ryan's assessment for the Swinburne unit ART20003 Skills and Strategies for Social Change ("Portfolio submission, reflection and skill sets"), and submitted that month. The brief asked for a public, professional portfolio that would become a living document, so the site is meant to keep growing after the unit.
- **Persona:** intellectual interests rather than a job pitch. The narrative is power: who holds it, how it is reproduced, the organisation of work and the social consequences of automation. Ryan studies to learn, not for a particular employer, so the purpose statement names interests and does not declare a career.

## 2. Repository layout

```
site/            built static site, committed and served as-is (Netlify publishes this folder)
site-src/        the generator
  content.py     nearly all copy and data (section labels 01, 02, 04 and 05 and button text are in build_site.py)
  build_site.py  HTML templates, the CSS (one string), the JavaScript (SITE_JS string), image, font and essay pipelines
  essays.py      turns submitted essays into reading pages and checks them word for word
  check_site.py  static and browser checks plus screenshots
  test_interactions.py  browser tests of the interactive parts
  img-src/       image sources (resized into site/images/ at build time)
  fonts-src/     Newsreader and Source Sans 3 variable fonts (OFL), subset into site/fonts/
netlify.toml     tells Netlify to publish site/ with no build command
README.md, AGENTS.md, CLAUDE.md   orientation (CLAUDE.md just imports this file)
.gitignore       a whitelist: only the paths above are committed
```

**Not in the repository (local to Ryan's workspace only):**

- `essays-src/`: the submitted essays the reading pages are built from (`his10003.docx`, `soc20013.docx`, `his10006-final.docx`, `phi10009.pdf`, matching PDFs, and `soc20013-presentation.pdf`). **A fresh clone cannot rebuild the site without this folder.** The build will stop when it tries to read an essay. Ask Ryan for the files; the published PDFs in `site/files/` are copies of the PDF sources under public names. None of the sources contain his student number.
- `shots/`: screenshots written by the checker (regenerated each run).
- The assessment notes (brief, rubric, full session log, draft tracker) live in Ryan's university workspace, in the ART20003 assessment folder. They include private details that were deliberately kept off the site.

## 3. Toolchain

- Python 3.11 with a virtual environment at `site-src/.venv` (not committed). Packages: `playwright==1.64.1`, `pillow`, `fonttools`, `brotli`. Pin Playwright: 1.65 bundles a Node binary that needs the system library `libatomic.so.1`, and without it the checker and tests stop with "Connection closed while reading from the driver". 1.64.1 runs without it and works with the Chromium build at `/opt/pw-browsers/`.
- Playwright's Chromium for the checker and tests. **Both scripts look for the browser at `/opt/pw-browsers/chromium_headless_shell-*/...`** (the original environment). On another machine, run `playwright install chromium` and change the `EXE` line in `check_site.py` and `test_interactions.py`.
- System tools for essays: `pandoc` (tested with 2.17) for .docx sources, poppler's `pdftohtml` and `pdftotext` (tested with 22.12) for PDF sources.
- LibreOffice is only needed if you render .docx files to check them; the site does not use it.

## 4. Build, check, publish

Run from `site-src/`:

```
.venv/bin/python build_site.py --release             # the build to publish; refuses on any guard below
.venv/bin/python build_site.py --release --preview   # guarded review copy with noindex (--preview alone only warns)
.venv/bin/python check_site.py             # add --online to fetch external links
.venv/bin/python test_interactions.py
```

Guards:

- **Every build** stops on an em dash in `content.py` or in built site copy. Essay bodies are exempt from the build guard because they are reproduced exactly, but `check_site.py` flags em dashes on every page, so an essay containing one would fail the checker.
- **`--release`** also refuses while any `RyanWrites(...)` placeholder or `Draft(...)` marker remains in `content.py` (none remain; the mechanism is kept for future drafting rounds), or when an essay page's words differ from the submitted PDF. The essay comparison ignores punctuation, hyphens, quote style and italics. It runs after `site/` has been written, so **never commit after a refused build**.

`check_site.py` covers broken links and anchors, missing alt text or image dimensions, duplicate ids, one h1 per page, `lang="en-AU"`, no external requests, no console errors, no horizontal overflow, WCAG AA contrast in light, dark and phone modes, and that every Tab stop shows a focus outline. `test_interactions.py` covers the theme toggle, section highlight, copy buttons, print layout, the carousel (arrows, counter, centring, row alignment at 820, 1160 and 1440px, equal card heights, whole-card links), the phone header, essay navigation and phone stacking. Both must pass before publishing.

**Publishing:**

1. Commit `site/` and `site-src/` to `main` and push. Netlify deploys `main` automatically (publish directory `site`, set in `netlify.toml`).
2. Refresh the GitHub Pages mirror: `git branch -D gh-pages; git subtree split --prefix site -b gh-pages; git push -f origin gh-pages`. (`site/.nojekyll` stops GitHub running Jekyll.)
3. Confirm the change is live by fetching the changed page and looking for the new text. (The `style.css?v=` hash changes only when the CSS or JavaScript changes.)
4. Update `LAST_UPDATED` in `content.py` (shown in the footer) whenever content changes.

Commits so far use Ryan's identity: `git -c user.name="Ryan O'Grady" -c user.email="268145835+Octavian-Minerva@users.noreply.github.com" commit ...`.

**Netlify facts worth knowing:**

- Project name `ryanoogrady` on Ryan's free account. Visitor access protection was switched on when the project was created, which sends every visitor to a Netlify login page. It is now off; check it stays off.
- Netlify rewrites internal links to "pretty URLs" (`/essay-cold-war` rather than `essay-cold-war.html`), adds an HTML comment, and injects a "Powered by Netlify" badge. Netlify's documentation says Free projects can switch the badge off (Project configuration > General > Powered by Netlify badge), but in November 2026 Ryan's account asked him to upgrade first, so it was left on. If it matters later, try the setting again, upgrade, or move hosting (for example Cloudflare Pages); the GitHub Pages mirror has no badge.
- The build writes `site/_headers` (security headers; fonts cached for a year, images for a week). Edit it in `build_site.py`, not in `site/`. CSS and JS are cache-busted with a content hash (`?v=`), because a stale cached stylesheet once made new HTML render with old styling.

## 5. How the site is built (architecture)

- **No framework, no trackers, no third-party requests.** Plain HTML and CSS with one small script for progressive enhancement. Fonts are self-hosted and subset to a fixed Latin range (`UNICODES` in `build_site.py`). Existing `.woff2` files are not rebuilt, so delete `site/fonts/*.woff2` after changing that range.
- **Pages:** `index.html` (everything), `not-our-game.html` (the campaign), four `essay-*.html` reading pages, `404.html`. Files: `site/files/` (PDFs), `site/images/` (responsive JPEGs at several widths), `og.jpg` (link-preview image generated by the build), `favicon.svg`.
- **Home page sections:** hero (name, degree, descriptor, photo); 01 About (purpose, background, "Areas of interest", dated "At present" list); 02 Selected work (carousel); 03 Skills audit and reflection (three skill areas, then the reflection); 04 Experience and involvement (current roles, "Earlier work", "Education"); 05 Contact; footer (colophon, credits, last updated).
- **Content model:** `content.py` holds plain strings and lists. Blank lines inside a string make new paragraphs. Each `WORK` item can carry `read` (build a reading page from a file in `essays-src/`, with optional `fixes`), `pdf` (publish a PDF), `thumb` (image), `links` (extra buttons), `topic` (the question line), `tags` and `blurb` (the summary), plus `type`, `unit_code`, `unit_name`, `year`, `thumb_fit` and `pdf_label`. The comments above `WORK` cover the main keys but are partly out of date (`slides` is never rendered). Cards with `read` show the essay's opening lines and ignore `thumb`.
- **Essay pages:** .docx sources go through pandoc; the one PDF-only essay is rebuilt from poppler's line positions. `essays.verify` compares every page with the submitted PDF word for word. `fixes` exists for one case: the HIS10006 .docx predates a one-sentence edit Ryan made before submitting, so the fix makes the page match what he actually submitted.
- **Interface features (deliberate, to show development competence):** sticky header with a reading-progress line and current-section highlight; light and dark themes (follows the system, the toggle remembers the choice in `localStorage`); copy buttons on email addresses; a print stylesheet; a header that hides while scrolling down on screens up to 900px wide; skip link and visible focus states throughout.

## 6. Design decisions

- **Typography:** Newsreader (serif) for headings and lead text, Source Sans 3 for body text. Body text is **justified** with Australian English hyphenation, at Ryan's request. Deliberate exceptions stay left-aligned: large lead text, labels, the italic question line on each card, the essay preview strip and the essay standfirst. Card summaries are justified (Ryan noticed when they were not).
- **Selected work carousel:** on screens wider than 700px, one card sits in the centre at full strength and its neighbours are faded and slightly smaller; clicking a faded card brings it to the centre. Arrows sit at the left and right edges, with a counter ("2 of 6") below. Phones get a plain stacked list.
- **Every card row lines up.** Each card uses CSS subgrid across seven shared rows (media, unit line, title, question, summary, tags, buttons), so each element starts at the same height on all six cards. Ryan's rule: fixed elements are anchored to other fixed elements, never to variable text. **Consequence:** the longest summary sets the height of every card. Cards are 460px wide from about 720px up (`min(460px, 64vw)`); at that width keep each summary to about 60 words (seven lines). The tests check alignment and equal heights, not length, so an overlong summary makes every card taller without failing: check the line count in the screenshots.
- **The whole card is the link** (a stretched link on the title); buttons sit above it and keep their own targets. Summaries are shown in full, not behind a toggle. The essay cards show a strip with the essay's real opening lines; Footscray and Not Our Game show images.
- **The same alignment rule applies elsewhere:** the three skill areas share rows (so the tags line up), the About list labels sit in one fixed-width column, and in Experience the date is pinned to the role title rather than spread across the row.
- **Section labels:** 02 to 04 use a short "X, Y and Z" description (for example "03 Research, technology and communication"); 01 "Purpose" and 05 "Correspondence" are single words. Keep new labels consistent with one of the two.

## 7. Content decisions

**Selected work (order matters):**

1. Not Our Game (ART20003 group campaign strategy). It was first a large featured section, then reduced to an equal card because a featured section gave one piece too much weight, and finally moved to the first card so the assessed unit's work is prominent.
2. Deterring Arrival: Asylum Policy in Australia and the United States (SOC20013 major essay).
3. Insulating News from the Market and the State (HIS10006 major essay).
4. Migrant Settlement and Gentrification in Footscray (SOC20013 tutorial presentation, final submitted slides).
5. Technological Progress and Power (PHI10009 major essay). Moved back from first place; its summary was rewritten from the essay itself.
6. Three vantage points of the Cold War: Hobsbawm, Gaddis, and Jervis (HIS10003 term essay). The title keeps the submitted sentence case.

**Rules for showing work:**

- Essays are reproduced **exactly as submitted**. Never edit essay text (including its own quirks such as straight quotes). Cover pages with student numbers were removed from the PDFs, and PDF metadata was cleaned.
- Not Our Game was a group project. The site credits only Ryan's parts (the campaign website, and the report's messaging and artefact sections). The campaign's social media tiles were groupmates' work, so they are not shown. Group members are not named. Campaign screenshots include AI-generated images; the footer says so.
- Pieces left out on purpose: the Media Content Development unit's work and his earlier Adobe Portfolio site.

**About and Experience:**

- Employer names are deliberately omitted; roles are described generically (for example "Self-storage business, casual"). Keep it that way.
- A one-month street fundraising job is mentioned in About and in the "Working with people" skill area, but not listed in Experience.
- The developer role title "AI systems developer" was suggested in drafting and accepted by Ryan with the rest of the copy. Arx is a self-built study planner that led to his development work.
- Contact lists a personal address and the university address; a dedicated professional address would be an improvement (see section 9).
- Time-sensitive copy to refresh: the "At present (November 2026)" list, `LAST_UPDATED`, "Halfway through a Bachelor of Arts", "to present" dates and the year on cards.

**Skills audit and reflection:**

- The brief required a skills audit and reflection of about 150 words. The reflection ("Reflection: the Not Our Game campaign") is **149 words** and is the version Ryan chose over a later rewrite. Do not rewrite it without asking him.
- The three skill areas are research and argument, building systems with AI, and working with people, each with a short evidence paragraph and tags.

**Disclosure:** the site itself carries no statement about how its copy was produced; that was a deliberate choice. Any public statement of that kind is Ryan's decision, so ask him.

## 8. Working with Ryan

- **Who writes what:** copy is drafted only from what Ryan supplies (his answers, his work, his corrections), never from invention, and nothing goes live without his approval.
- **Process:** propose changes in chat, wait for his sign-off, then list every change made. Show screenshots for visual changes. Verify facts against his actual work before writing them.
- **Writing style:** Australian English. No em dashes (the build enforces this); en dashes only in number ranges. A measured, formal, academic register. He has rejected overstated or salesy words ("striking", "passionate", "unique") and repeated openers ("I argue" on several cards, "particularly" three times in a paragraph). Summaries lead with the claim and name concrete examples rather than abstractions.
- **Design taste:** consistency and alignment over decoration. He notices misaligned buttons, uneven rows, mixed text alignment and inconsistent labels. Check desktop (about 1160 and 1440px), tablet (about 760px) and phone (390px), in light and dark.

## 9. Known issues and ideas

- `essays-src/` is not in the repository (see section 2). Adding it would make the repo self-contained; the essay text is already public on the site, but it is Ryan's call because the repository is public.
- Netlify badge on the free plan (see section 4).
- The GitHub Pages mirror and the Netlify site serve identical pages with no `rel="canonical"` link. Search engines may index both. Adding a canonical tag pointing to `SITE_URL` would fix it.
- `content.py` still holds retired fields that are switched off (`SOCIAL_TILES`, `SOCIAL_TILES_TODO`, `SKILLS_LIST`, `SKILLS_LIST_LABEL`, `CONTACT_LINE`, `AI_NOTE`, and the unused `FEATURED_PAGE["tiles_head"]`; `FEATURED_PAGE` itself is live). They are harmless and documented in place.
- Ideas that fit the brief or that Ryan has raised: a custom domain; a dedicated professional contact email; a LinkedIn link once he has a profile; new essays and projects as he completes them.

## 10. Timeline

- 10 to 11 Nov 2026: brief analysed; custom static site chosen over Word/PDF or Adobe Portfolio for production values and a living public profile; skeleton generator built.
- 12 to 13 Nov: interests, work history and selection worked out through question rounds; copy written from Ryan's answers and tracked item by item until he accepted it; preview published on GitHub Pages; photo added; featured campaign section removed.
- 14 Nov: essays given on-site reading pages verified against the submitted PDFs; interface features added; carousel designed and refined; alignment and spacing pass; independent review; deployed to Netlify; submitted.
- 16 Nov: this handover written.
