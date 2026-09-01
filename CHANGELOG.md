# Changelog

## 0.5 — 2026-08-31

- Add automatic semantic tagging for nested `itemize` lists up to 3 levels (`itemize item`, `itemize subitem`, `itemize subsubitem`).
- Add automatic semantic tagging for `enumerate` lists up to 3 levels (`enumerate item`, `enumerate subitem`, `enumerate subsubitem`).
- Support arbitrary mixed nesting hierarchies (`enumerate` inside `itemize`, `itemize` inside `enumerate`, 3-level mixed lists).
- Implement depth-indexed list lifecycle (`\g__ba_list_depth_int`, `\g__ba_list_pending_i/ii/iii_bool`, `\g__ba_list_open_i/ii/iii_bool`, `\g__ba_li_open_i/ii/iii_bool`, `\g__ba_lbody_open_i/ii/iii_bool`) ensuring strict `L -> LI -> Lbl + LBody -> (P, L ...)` containment.
- Support multi-paragraph items, inline formatting, math formulas, and clean paragraph transitions across all list levels.
- Maintain safe fallback suppression for list depths > 3, item overlays (`\item<1->`), and `description` environments.
- Expand test harness to 19 isolated fixture suites verifying structure tree hierarchy, unique `(MCID, Pg)` tuples, exact text extraction, and 300-DPI zero-pixel visual regressions.
- Validate on full 23-page real lecture integration deck (`lecture 1.pdf`) tagging 20 lists and 76 items with 246 unique MCIDs.

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


