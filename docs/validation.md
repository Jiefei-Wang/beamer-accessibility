# Validation record

Validated on 2026-09-01 with:

- MiKTeX 26.5
- LaTeX 2026-06-01 and L3 2026-08-10
- pdfTeX 1.40.29
- Beamer 3.78
- PDF management 0.97c
- Poppler rendering at 300 DPI in RGB

## Isolated tests (30 Fixture Suites)

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
- `basic-block`: Standard `block` with `blocktitle` and body prose: PASS (0 differing pixels)
- `alert-and-example-block`: `alertblock` and `exampleblock` tagging: PASS (0 differing pixels)
- `multi-para-block`: Multi-paragraph block body tagging: PASS (0 differing pixels)
- `block-with-list`: Block containing nested `enumerate` and `itemize`: PASS (0 differing pixels)
- `untitled-block`: Untitled block (`\begin{block}{}`) omitting `blocktitle` cleanly: PASS (0 differing pixels)
- `mixed-blocks-prose`: Prose before, between, and after multiple blocks: PASS (0 differing pixels)
- `basic-image`: Standalone `\includegraphics[alt={...}]{...}` with `/Figure` and `/Alt`: PASS (0 differing pixels)
- `image-without-alt`: Standalone `\includegraphics` without `alt` attribute: PASS (0 differing pixels)
- `inline-image`: Inline graphic inside paragraph text: PASS (0 differing pixels)
- `block-with-image`: Graphic with alternative text inside a Beamer `block`: PASS (0 differing pixels)
- `figure-environment`: `\begin{figure}` with `\caption`: PASS (0 differing pixels)
- `unsupported-list`: Unsupported description fallback: PASS (0 differing pixels)
- `unsupported-overlay-list`: Multi-slide overlay list fallback: PASS (0 differing pixels)

Run these checks with `tests/run-tests.ps1` or `python tests/verify.py build/tests`.

## Integration deck

The package was installed in the MiKTeX user tree and loaded from there by the 23-page BIOS 6485 Lecture 1 integration deck.

- `pdfinfo`: `Tagged: yes`
- Pages: 23
- Structure counts: 23 `frame`, 22 `frametitle`, 2 `Figure`, 12 `block`, 12 `blocktitle`, 20 `L`, 76 `LI`, 76 `Lbl`, 76 `LBody`, and 136 `P` (457 total structure objects)
- Text match: 100% exact text match across all 23 pages
- Visual comparison: **0 differing pixels across all 23 pages at 300 DPI (23/23 exact match)**

No PDF/UA conformance claim is made.



