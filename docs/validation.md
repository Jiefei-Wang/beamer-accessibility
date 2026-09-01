# Validation record

Validated on 2026-08-31 with:

- MiKTeX 26.5
- LaTeX 2026-06-01 and L3 2026-08-10
- pdfTeX 1.40.29
- Beamer 3.78
- PDF management 0.97c
- Poppler rendering at 300 DPI in RGB

## Isolated tests (19 Fixture Suites)

- `frame-paragraph`: Frame, title, and body paragraph tagging: PASS (0 differing pixels)
- `package-only`: Standalone package loading after `\documentclass{beamer}`: PASS (0 differing pixels)
- `basic-list`: Standard 2-item itemize `L -> LI -> (Lbl, LBody -> P)`: PASS (0 differing pixels)
- `para-before-list`: Prose preceding itemize list: PASS (0 differing pixels)
- `para-after-list`: Prose following itemize list: PASS (0 differing pixels)
- `para-before-after-list`: Prose before and after itemize list: PASS (0 differing pixels)
- `list-first-content`: List as the first content in frame without title: PASS (0 differing pixels)
- `single-item-list`: Single-item itemize list: PASS (0 differing pixels)
- `multi-para-item`: Multiple paragraphs within a single list item: PASS (0 differing pixels)
- `inline-formatting`: Item text with `\textbf`, `\alert`, math, and formatting: PASS (0 differing pixels)
- `nested-itemize`: 2-level nested itemize: PASS (0 differing pixels)
- `nested-itemize-3level`: 3-level nested itemize (`itemize item` -> `subitem` -> `subsubitem`): PASS (0 differing pixels)
- `basic-enumerate`: Standard 3-item numbered enumerate list: PASS (0 differing pixels)
- `nested-enumerate`: 2-level nested enumerate (`1.` -> `1.1`): PASS (0 differing pixels)
- `mixed-itemize-enumerate`: Enumerate inside itemize & itemize inside enumerate: PASS (0 differing pixels)
- `enumerate-inline-formatting`: Enumerate items with `\textbf`, `\alert`, math: PASS (0 differing pixels)
- `enumerate-multi-para`: Multi-paragraph enumerate items: PASS (0 differing pixels)
- `unsupported-list`: Unsupported description fallback: PASS (0 differing pixels)
- `unsupported-overlay-list`: Multi-slide overlay list fallback: PASS (0 differing pixels)

Run these checks with `tests/run-tests.ps1` or `python tests/verify.py build/tests`.

## Integration deck

The package was installed in the MiKTeX user tree and loaded from there by the 23-page BIOS 6485 Lecture 1 integration deck.

- `pdfinfo`: `Tagged: yes`
- Pages: 23
- Structure counts: 23 `frame`, 22 `frametitle`, 20 `L`, 76 `LI`, 76 `Lbl`, 76 `LBody`, and 148 `P`
- Marked Content References: 246 total, 246 unique (0 duplicate MCIDs)
- Text match: 100% exact text match
- Visual comparison: 0 differing pixels on 22/23 pages; slide 20 line wrap difference due to authored content overflowing text width by 1.64pt.

No PDF/UA conformance claim is made.



