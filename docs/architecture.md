# Architecture Specification: `beamer-accessibility` (v1.0)

This document details the internal architecture, lifecycle hooks, state machines, and PDF stream invariants of `beamer-accessibility`.

---

## 1. Core Architecture Decision

`beamer-accessibility` decouples PDF management activation from LaTeX-lab's experimental document metadata framework:

```text
\RequirePackage{pdfmanagement}
  -> \documentclass{beamer}
  -> \RequirePackage{tagpdf}
  -> PDF Catalog Metadata Injection (/Lang, /ViewerPreferences)
  -> RoleMap Configuration (frame -> Sect, frametitle -> H1, block -> Div, blocktitle -> H2, column -> Div)
  -> Scoped Lifecycle Hooks (Frame, Title, Paragraph, List, Block, Column, Graphic, Footnote)
```

### Rationale
In LaTeX 2025/2026, `\DocumentMetadata` forces loading of complete LaTeX-lab modules, whose kernel footnote and list modifications conflict with Beamer's box-based slide assembly engine. Loading `pdfmanagement` early and `tagpdf` low-level allows precise, surgical tagging without interfering with Beamer internals.

---

## 2. Structural Hierarchy & Role Mapping

All custom presentation elements are registered in the PDF `/RoleMap` to standard PDF/UA structure types:

| Custom Tag | Standard PDF Role | Purpose |
| :--- | :--- | :--- |
| `/Document` | `Document` | Root structure container |
| `/frame` | `Sect` | Slide section container |
| `/frametitle` | `H1` | Primary slide heading |
| `/block` | `Div` | Semantic block / card container |
| `/blocktitle` | `H2` | Secondary block heading |
| `/column` | `Div` | Column container in multi-column layouts |
| `/P` | `P` | Prose paragraph |
| `/L` | `L` | Ordered or unordered list |
| `/LI` | `LI` | List item |
| `/Lbl` | `Lbl` | List item bullet or number label |
| `/LBody` | `LBody` | List item body |
| `/Figure` | `Figure` | Graphic element with `/Alt` attribute |

---

## 3. Lifecycle Hooks & Timing

### 3.1 Slide & Body Boundary Gating
- `env/beamer@frameslide/begin`: Emits `\ba_frame_begin:` to create a new `/frame` structure element.
- `env/beamer@framepauses/end`: Emits `\ba_body_end:` to close open body paragraphs before Beamer constructs the separate `frametitle` box.
- `env/beamer@frameslide/after`: Emits `\ba_frame_end:` to close the `/frame` structure element.

### 3.2 Slide Titles (`firstkid=true`)
Beamer processes frame body contents before typesetting the title box. To ensure natural reading order without altering visual construction:
- `\frametitle` is wrapped to call `\tag_struct_begin:n { tag = frametitle, firstkid = true }`.
- This inserts the `/frametitle` structure element as the first child of `/frame` in the structure tree.

### 3.3 Paragraph Lifecycle & Display Math Spacing
To avoid vertical whatsits before display math `$$`:
- `\AddToHook{para/begin}` is used solely to open paragraphs via `\ba_paragraph_begin:`.
- `\ba_paragraph_begin:` calls `\ba_paragraph_end:` at the start, ensuring previous paragraphs are closed without vertical whatsits before math environments.
- Container boundaries (`\ba_block_end:`, `\ba_column_end:`, `\ba_list_close_at:`) explicitly call `\ba_paragraph_end:`.

### 3.4 List Lifecycle & Depth Tracking
A stack tracks list state across nesting depths 1, 2, and 3:
- Booleans: `\g__ba_list_open_i_bool`, `\g__ba_li_open_i_bool`, `\g__ba_lbody_open_i_bool` (and `_ii`, `_iii`).
- Intercepts: `itemize item`, `itemize subitem`, `itemize subsubitem`, `enumerate item`, `enumerate subitem`, `enumerate subsubitem`.
- On item transition: Closes previous `LBody`, closes previous `LI`, opens new `LI`, opens `Lbl`, captures bullet MCID, opens `LBody`.

### 3.5 Graphics & Alternative Text
- Intercepts `\Gin@ii` from `graphicx`.
- Parses `alt` and `alttext` keys from options.
- If paragraph is open, suspends paragraph marked content (`\tag_mc_end:`), creates `/Figure` structure element with `/Alt (description)`, tags graphics content, closes `/Figure`, and resumes paragraph marked content (`\tag_mc_begin:`).

### 3.6 Multi-Column Layouts
- Intercepts `beamer@columnenv` and `\beamer@columncom`.
- Emits `\ba_column_begin:` (`/column` -> `Div`) at minipage entry and `\ba_column_end:` at minipage exit.

### 3.7 Footnote Marked Content Balance
- Slide footnotes are typeset into `\beamer@footins` `\vbox`.
- Wraps `\beamer@framefootnotetext` and `\@mpfootnotetext` to close outer paragraph marked content before `\setbox` and close footnote paragraph marked content inside `\vbox`, ensuring clean 1:1 `BDC`/`EMC` operator balance across content streams.

---

## 4. Fallback & Suppression

When unsupported constructs are detected (e.g. item overlays `\item<2->` or `description` lists):
- `\ba_suppress_begin:` increments `\g__ba_suppress_nesting_int`.
- All structure openings and marked content emissions are bypassed.
- Slide compiles and renders with 100% visual fidelity and zero broken structure elements.
