# Architecture Specification: eamer-accessibility (v1.0)

This document details the internal architecture, lifecycle hooks, state machines, and PDF stream invariants of eamer-accessibility.

---

## 1. Core Architecture Decision

eamer-accessibility decouples PDF management activation from LaTeX-lab's experimental document metadata framework:

`	ext
\RequirePackage{pdfmanagement}
  -> \documentclass{beamer}
  -> \RequirePackage{tagpdf}
  -> PDF Catalog Metadata Injection (/Lang, /ViewerPreferences)
  -> RoleMap Configuration (frame -> Sect, frametitle -> H1, block -> Div, blocktitle -> H2, column -> Div, Table -> Table, TR -> TR, TH -> TH, TD -> TD)
  -> Scoped Lifecycle Hooks (Frame, Title, Paragraph, List, Block, Column, Table, Graphic, Footnote, Bookmark)
`

### Rationale
In LaTeX 2025/2026, \DocumentMetadata forces loading of complete LaTeX-lab modules, whose kernel footnote and list modifications conflict with Beamer's box-based slide assembly engine. Loading pdfmanagement early and 	agpdf low-level allows precise, surgical tagging without interfering with Beamer internals.

---

## 2. Structural Hierarchy & Role Mapping

All custom presentation elements are registered in the PDF /RoleMap to standard PDF/UA structure types:

| Custom Tag | Standard PDF Role | Purpose |
| :--- | :--- | :--- |
| /Document | Document | Root structure container |
| /frame | Sect | Slide section container |
| /frametitle | H1 | Primary slide heading |
| /block | Div | Semantic block / card container |
| /blocktitle | H2 | Secondary block heading |
| /column | Div | Column container in multi-column layouts |
| /P | P | Prose paragraph |
| /L | L | Ordered or unordered list |
| /LI | LI | List item |
| /Lbl | Lbl | List item bullet or number label |
| /LBody | LBody | List item body |
| /Figure | Figure | Graphic element with /Alt attribute |
| /Table | Table | Tabular data container |
| /TR | TR | Table row container |
| /TH | TH | Table header cell |
| /TD | TD | Table data cell |

---

## 3. Incremental State Machine & Overlay Policies

Beamer creates overlays by executing the slide body multiple times with differing values of internal overlay counters.

### 3.1 Overlay Policy Engine
- **overlay-policy=pages (Default)**:
  Every rendered page receives a fresh /frame structure element. Tagging is dynamically gated against \beamer@coveringdepth:
  - When \beamer@coveringdepth = 0, content is visible and is tagged with proper semantic structure elements and marked content records.
  - When \beamer@coveringdepth > 0, content is covered (invisible or dimmed) and marked content is either suppressed or tagged as a non-structural artifact (/Artifact).
  - Content visible across multiple consecutive pages is intentionally re-tagged on each physical page, ensuring screen-reader users navigating sequentially encounter the full context of that slide.
- **overlay-policy=handout**:
  Executes Beamer's internal handout mode (\beamer@handoutmode). All overlay specifications and pauses are collapsed so that each frame produces a single final page.
- **overlay-policy=strict**:
  Hooks \item overlay detection and \pause to raise an immediate \PackageError, stopping compilation to enforce non-incremental slides.

### 3.2 The \pause State Machine
\pause can occur in vertical mode (between blocks or paragraphs) or in horizontal mode (mid-paragraph):
- When \g__ba_para_open_bool is true (horizontal mode), \ba@pause safely ends the active marked content chunk (\tag_mc_end:), executes Beamer's internal pause mechanism, and opens a new marked content chunk (\tag_mc_begin:n {}) for subsequent text in that paragraph once resumed.
- This maintains 100% text classification and zero empty paragraphs, preserving pixel-exact visual rendering at 300 DPI.

---

## 4. Tables and Cell Tagging Architecture

eamer-accessibility provides structured table tagging via ccessibleTable and ccessibletabular:
- **ccessibleTable**: Sets table-level metadata (	itle and summary) and initializes \g__ba_in_table_bool to prevent spurious paragraph tagging during table cell construction.
- **ccessibletabular**: Manages the /Table structure. Prevents recursive /Table nesting when nested within ccessibleTable.
- **\tablehead and \tablecell**:
  - \tablehead opens a /TR row and tags each cell as a header cell (/TH).
  - \tablecell opens a /TR row and tags each cell as a data cell (/TD).
- **Unannotated Table Detection**:
  Hooks env/tabular/before to inspect \g__ba_in_table_bool. If a plain 	abular is detected without accessibility markup, issues a compiler warning (or error in 	able-policy=strict).

---

## 5. Figures and Graphics Architecture

- **ccessibleFigure**: Encloses figures, TikZ pictures, and PGFPlots diagrams.
  - Sets \g__ba_in_figure_bool to true, which inhibits LaTeX para/begin hooks from opening premature /P elements inside TikZ graphics.
  - Maps decorative graphics to /Artifact marked content when decorative=true.
  - Attaches alternative text via /Alt on the /Figure structure element.
- **Standard \includegraphics**:
  - Automatically extracts lt or lttext keys.
  - Verifies presence of non-empty alternative text in strict figure modes (igure-policy=strict).

---

## 6. PDF Bookmarks & Navigation Architecture

- **Outline Deduplication**:
  Beamer's \beamer@writebookmarks is hooked using a subframe guard boolean \g__ba_frame_first_subframe_bool.
  - On the first physical page of a logical frame, \beamer@writebookmarks emits the outline entry to the PDF catalog.
  - On subsequent overlay pages of the same frame, \beamer@writebookmarks is suppressed.
  - This ensures exactly one outline entry per slide in PDF viewer sidebars.
- **Navigation Symbols**:
  - Suppressed by default (
avigation-symbols=hidden) by emitting \setbeamertemplate{navigation symbols}{} before the document begins, eliminating untagged navigation button artifacts.

---

## 7. Contrast & Color Compliance

- **ccessible-colors=wong**:
  Defines an accessible 8-color palette based on Bang Wong's Nature Methods (2011) colorblind-safe design.
  - All text-background combinations guarantee a contrast ratio >= 4.5:1 (WCAG 2.1 AA) and >= 6.5:1 for key theme elements.
  - Default visual appearance remains 100% standard Beamer unless explicitly requested via ccessible-colors.

---

## 8. Multi-Column Layout Architecture

- \beamer@columncom and \beamer@columnenv:
  - Wrap columns in /column (Div) elements.
  - Preserve standard Beamer's \leavevmode\raggedright\beamer@colheadskip baseline positioning for bit-exact 300-DPI visual rendering.
  - When [T] alignment is used, vertical glue adjustment executes cleanly in vertical mode to prevent empty paragraph records.
