"""Turn submitted essays into blocks for reading pages on the site.

Two sources:
  - .docx: converted with pandoc, which keeps italics and paragraphs exactly.
  - .pdf (when no .docx survives): read with poppler's pdftohtml -xml, which gives each line's
    position and italics; paragraphs are rebuilt from line spacing and line length, and reference
    entries from their hanging indent.

Each essay becomes a list of blocks: ('h', html) for headings, ('p', html) for body paragraphs,
('refs', html) for the reference-list heading and ('ref', html) for each entry. The essay's own
title (its first line) is dropped, because the page prints the title itself.

verify(blocks, pdf) compares the words on the page with the words in the published PDF and returns
any differences, so a conversion slip cannot reach the site unnoticed."""
import difflib, html, re, subprocess

REF_HEADINGS = {'references', 'reference list', 'bibliography', 'works cited'}


def _plain(fragment):
    return html.unescape(re.sub(r'<[^>]+>', '', fragment)).strip()


def _tidy(fragment):
    """Normalise inline markup to <em> only, collapse spaces."""
    f = re.sub(r'</?(?:strong|b|span)[^>]*>', '', fragment)
    f = re.sub(r'<(/?)i>', r'<\1em>', f)
    f = f.replace('&#160;', ' ').replace(' ', ' ')
    f = re.sub(r'\s+', ' ', f).strip()
    f = re.sub(r'</em>(\s*)<em>', r'\1', f)
    return f


def from_docx(path):
    out = subprocess.run(['pandoc', path, '-t', 'html', '--wrap=none'], capture_output=True, text=True, check=True).stdout
    paras = re.findall(r'<(p|h\d)[^>]*>(.*?)</\1>', out, flags=re.S)
    blocks, in_refs, first = [], False, True
    for tag, inner in paras:
        text = _plain(inner)
        if not text:
            continue
        if first:            # the essay's own title line
            first = False
            continue
        bold_only = re.fullmatch(r'\s*<strong>.*</strong>\s*', inner, flags=re.S) is not None or tag.startswith('h')
        if text.lower().rstrip(':') in REF_HEADINGS:
            in_refs = True
            blocks.append(('refs', html.escape(text)))
        elif in_refs:
            blocks.append(('ref', _tidy(inner)))
        elif bold_only and len(text) < 120:
            blocks.append(('h', html.escape(text)))
        else:
            blocks.append(('p', _tidy(inner)))
    return blocks


def from_pdf(path):
    xml = subprocess.run(['pdftohtml', '-xml', '-i', '-stdout', '-q', path], capture_output=True, text=True, check=True).stdout
    lines = []   # (page, top, left, right, html)
    for page_no, page in re.findall(r'<page number="(\d+)"(.*?)</page>', xml, flags=re.S):
        height = int(re.search(r'height="(\d+)"', xml.split(f'<page number="{page_no}"')[1]).group(1))
        rows = {}
        for top, left, width, inner in re.findall(r'<text top="(\d+)" left="(\d+)" width="(\d+)" height="\d+" font="\d+">(.*?)</text>', page, flags=re.S):
            top, left, width = int(top), int(left), int(width)
            if top > height * 0.9 or not _plain(inner):     # page numbers and blank runs
                continue
            rows.setdefault(top, []).append((left, width, inner))
        for top in sorted(rows):
            parts = sorted(rows[top])
            left = parts[0][0]
            right = max(l + w for l, w, _ in parts)
            lines.append((int(page_no), top, left, right, ' '.join(p[2] for p in parts)))
    body_left = min(l for _, _, l, _, _ in lines)
    full = max(r for *_, r, _ in lines)
    ref_at = next((i for i, ln in enumerate(lines) if _plain(ln[4]).lower().rstrip(':') in REF_HEADINGS), len(lines))

    def typical_gap(seq):
        gaps = sorted(b[1] - a[1] for a, b in zip(seq, seq[1:]) if a[0] == b[0] and b[1] > a[1])
        return gaps[len(gaps) // 2] if gaps else 30

    body_gap, ref_gap = typical_gap(lines[1:ref_at]), typical_gap(lines[ref_at + 1:])
    blocks, cur, in_refs, prev = [], [], False, None

    def flush(kind):
        nonlocal cur
        if cur:
            blocks.append((kind, _tidy(' '.join(cur))))
            cur = []

    for i, (page, top, left, right, inner) in enumerate(lines):
        if i == 0:                       # the essay's own title line
            prev = (page, top, left, right)
            continue
        if i == ref_at:
            flush('p')
            blocks.append(('refs', html.escape(_plain(inner))))
            in_refs, prev = True, None
            continue
        gap = ref_gap if in_refs else body_gap
        if prev is None:
            new = True
        elif prev[0] == page:
            new = top - prev[1] > gap * 1.25
        else:                            # page break: a short last line ends the paragraph
            new = prev[3] < full * 0.9
        if new:
            flush('ref' if in_refs else 'p')
        cur.append(inner)
        prev = (page, top, left, right)
    flush('ref' if in_refs else 'p')
    # rejoin words hyphenated across lines only where the PDF itself split them (rare in these files)
    return blocks


def words(text):
    text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
    text = text.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    text = re.sub(r'(\w)- (\w)', r'\1-\2', text)          # words split across PDF lines
    text = re.sub(r'[()"\[\]]', ' ', text)
    text = re.sub(r'(\S)/ (\S)', r'\1/\2', text).replace('-', '')   # compare without hyphens: PDFs drop them at line ends
    return [w.strip('.,;:?!') for w in text.split() if w.strip('.,;:?!')]


def verify(blocks, pdf, title):
    """Return a list of human-readable differences between the page text and the PDF text."""
    page_text = title + ' ' + ' '.join(b for _, b in blocks)
    pdf_text = subprocess.run(['pdftotext', pdf, '-'], capture_output=True, text=True).stdout
    pdf_lines = [l for l in pdf_text.splitlines() if not re.fullmatch(r'\s*\d{1,2}\s*', l)]   # page numbers
    a, b = words(page_text), words(' '.join(pdf_lines))
    diffs = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != 'equal':
            diffs.append(f'{op}: page "{" ".join(a[i1:i2])[:80]}" vs pdf "{" ".join(b[j1:j2])[:80]}"')
    return diffs
