# Changelog

## 0.4 — 2026-08-31

- Add automatic semantic tagging for single-level plain `itemize` lists (`L -> LI -> Lbl + LBody -> P`).
- Wrap Beamer's `itemize item` template at `begindocument/end` after all user themes are configured.
- Support pre-list, post-list, and multi-paragraph item transitions cleanly.
- Implement precise slide body boundary gating to eliminate unwanted paragraph tagging from presentation furniture and theme boxes.
- Add safe fallback suppression for unsupported constructs (nested lists, item overlays, enumerate, description).
- Expand test harness to 13 isolated fixture suites verifying structure tree hierarchy, unique `(MCID, Pg)` tuples, exact text extraction, and 300-DPI zero-pixel visual regressions.
- Validate full 23-page real lecture integration deck (`lecture 1.pdf`) with 0 pixel difference and identical text match.

## 0.3 — 2026-08-31

- Initialize PDF management before upstream Beamer through a thin wrapper class.
- Load low-level `tagpdf` without `\DocumentMetadata` or LaTeX-lab document modules.
- Add automatic structures for frames, frame titles, and ordinary paragraphs.
- Preserve title-before-body semantic order with Beamer's existing title template.
- Leave unsupported list environments visually unchanged and untagged.
- Add isolated structure and pixel-regression tests.


