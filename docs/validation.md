# Validation record

Validated on 2026-08-31 with:

- MiKTeX 26.5
- LaTeX 2026-06-01 and L3 2026-08-10
- pdfTeX 1.40.29
- Beamer 3.78
- PDF management 0.97c
- Poppler rendering at 300 DPI in RGB

## Isolated tests (13 Fixture Suites)

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
- `unsupported-list`: Unsupported enumerate fallback: PASS (0 differing pixels)
- `unsupported-overlay-list`: Multi-slide overlay itemize fallback: PASS (0 differing pixels)
- `unsupported-nested-list`: Nested itemize fallback: PASS (0 differing pixels)

Run these checks with `tests/run-tests.ps1`.

## Integration deck

The package was installed in the MiKTeX user tree and loaded from there by the 23-page BIOS 6485 Lecture 1 integration deck.

- `pdfinfo`: `Tagged: yes`
- Pages: 23
- Structure counts: 23 `frame`, 22 `frametitle`, 14 `L`, 46 `LI`, 46 `Lbl`, 46 `LBody`, and 114 `P`
- Marked Content References: 182 total, 182 unique (0 duplicate MCIDs)
- Poppler comparison against baseline: 23/23 pages, zero differing pixels (0 pixel diff across entire deck)
- Extracted text: 100% identical to the baseline

No PDF/UA conformance claim is made.


