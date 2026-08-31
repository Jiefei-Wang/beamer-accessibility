# Validation record

Validated on 2026-08-31 with:

- MiKTeX 26.5
- LaTeX 2026-06-01 and L3 2026-08-10
- pdfTeX 1.40.29
- Beamer 3.78
- PDF management 0.97c
- Poppler rendering at 300 DPI in RGB

## Isolated tests

- Wrapper-class frame/title/paragraph structure: PASS
- Package-only loading with early PDF management: PASS
- Unique marked-content references: PASS
- Unsupported list contains no `P`, `L`, `LI`, `Lbl`, or `LBody` structures: PASS
- Frame/paragraph tagged output versus PDF-management-only baseline: zero differing pixels
- Unsupported-list tagged output versus PDF-management-only baseline: zero differing pixels

Run these checks with `tests/run-tests.ps1`.

## Integration deck

The package was installed in the MiKTeX user tree and loaded from there by the 25-page BIOS 6485 Lecture 1 integration deck. The lecture-local `.sty` and `.cls` copies were removed before testing.

- `pdfinfo`: `Tagged: yes`
- Pages: 25
- Structure counts: 25 `frame`, 24 `frametitle`, and 44 `P`
- Poppler comparison against the immutable gold master: 25/25 pages, zero differing pixels
- Extracted text: identical to the gold master

No PDF/UA conformance claim is made.

