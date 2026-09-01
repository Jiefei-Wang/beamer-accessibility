# Changelog

## 0.8 — 2026-09-01

- Add automatic semantic tagging for multi-column slide layouts (`columns`, `column` environments, and `\column` command).
- Tag columns with `role/new-tag = column/Div`.
- Wrap Beamer's `\beamer@columncom` and `beamer@columnenv` with `\renewenvironment<>` and `\renewcommand<>`, preserving overlay options `<#3>` and optional mode `[#1]` while placing `\ba_column_begin:` and `\ba_column_end:` inside the `minipage` lifecycle.
- Update `\endcolumn` to alias `\endbeamer@columnenv` for clean environment-form column termination.
- Validate compatibility across 10 diverse presentation themes (`Boadilla`, `Madrid`, `Warsaw`, `Berlin`, `Montpellier`, `Hannover`, `CambridgeUS`, `Pittsburgh`, `Rochester`, `default`), confirming 0 differing pixels and identical text extraction.
- Expand test harness to 36 isolated fixture suites verifying `/column` structure elements, mixed composition (columns + blocks + nested lists + figures with alt text), unique `(MCID, Pg)` tuples, exact text extraction, and 300-DPI zero-pixel visual regressions.
- Validate on full 23-page real lecture integration deck (`lecture 1.pdf`) tagging 12 columns, 2 figures, 12 blocks, 12 block titles, 20 lists, and 76 items across 485 structure objects with zero pixel differences.

## 0.7 — 2026-09-01

- Add automatic semantic tagging for graphics and figures (`\includegraphics`, `figure` environment).
- Support author-provided alternative text via `alt` and `alttext` keys on `\includegraphics[alt={...}, ...]{...}`, generating `/Figure` structure elements with standard PDF `/Alt` attributes.
- Wrap `\Gin@ii` from `graphicx` cleanly, preserving all standard graphics options (`width`, `height`, `scale`, `trim`, `clip`, `keepaspectratio`, etc.) with zero visual perturbation.
- Implement paragraph marked-content pausing and resuming around inline and standalone graphics, producing compliant structure nesting without splitting paragraph boxes.
- Support standalone graphics, inline graphics embedded inside prose, graphics inside Beamer `block` environments, and `figure` environments with `\caption`.
- Expand test harness to 30 isolated fixture suites verifying `/Figure` tags, `/Alt` attributes, unique `(MCID, Pg)` tuples, exact text extraction, and 300-DPI zero-pixel visual regressions.
- Validate on full 23-page real lecture integration deck (`lecture 1.pdf`) tagging 2 figures, 12 blocks, 12 block titles, 20 lists, and 76 items across 457 structure objects with zero pixel differences.

## 0.6 — 2026-09-01

- Add automatic semantic tagging for Beamer block environments (`block`, `alertblock`, `exampleblock`, and untitled blocks).
- Tag blocks with `role/new-tag = block/Div` and block titles with `role/new-tag = blocktitle/H2`.
- Wrap Beamer's `block begin` / `block end`, `block alerted begin` / `block alerted end`, and `block example begin` / `block example end` templates.
- Implement title-phase state machine distinguishing block title typesetting from block body paragraphs, supporting both standard and rounded (`beamerboxesrounded`) inner themes without unwanted `<P>` nesting.
- Support multi-paragraph blocks, nested lists (`itemize` and `enumerate`) inside blocks, and untitled blocks (`\begin{block}{}`) omitting `blocktitle` cleanly.
- Expand test harness to 25 isolated fixture suites verifying structure tree hierarchy, unique `(MCID, Pg)` tuples, exact text extraction, and 300-DPI zero-pixel visual regressions.
- Validate on full 23-page real lecture integration deck (`lecture 1.pdf`) tagging 12 blocks, 12 block titles, 20 lists, and 76 items across 455 structure objects with zero pixel differences.

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


