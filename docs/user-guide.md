# User Guide: eamer-accessibility (v1.0)

eamer-accessibility provides standard-compliant PDF accessibility tagging for LaTeX Beamer presentations with zero visual differences and identical text output.

---

## 1. Quick Start

### Document Class (Recommended)

`latex
\documentclass[14pt,t,lang=en-US]{beamer-accessibility}
\usepackage{graphicx}
\usetheme{Madrid}

\begin{document}
\begin{frame}{First Accessible Slide}
This paragraph is tagged automatically as standard paragraph text.
\end{frame}
\end{document}
`

### Package Form

If using standard \documentclass{beamer}, PDF management must be loaded before the class:

`latex
\RequirePackage{pdfmanagement}
\documentclass[14pt,t]{beamer}
\usepackage{graphicx}
\usepackage[lang=en-US]{beamer-accessibility}
`

---

## 2. Overlay Policies and Incremental Support

eamer-accessibility supports the two primary Beamer incremental mechanisms:
1. **Overlay specifications on \item**: \item<1->, \item<2->, and list-level defaults such as \begin{itemize}[<+->].
2. **The \pause command**: \pause between paragraphs, blocks, list items, or within multi-step presentations.

The behavior is governed by the overlay-policy package option:

`latex
\documentclass[overlay-policy=pages]{beamer-accessibility}
`

### Available Policies

- **overlay-policy=pages (Default)**:
  Generates standard multi-page presentation output. Each rendered page contains its own accessible logical /frame section. On each page, only the content visible on that page is tagged with structure elements and marked content; covered content is marked as non-structural artifacts. Already-visible content is intentionally repeated on subsequent pages so that assistive technologies navigating page-by-page have complete access to all currently visible material.
- **overlay-policy=handout**:
  Collapses all overlay steps into a single, complete page per logical frame. All items and pauses are rendered once in their final, complete state.
- **overlay-policy=strict**:
  Raises a compilation error if an overlay specification on \item or a \pause command is detected, forcing authors to restructure slides without incremental reveals.

*Note*: Other animation mechanisms (\only, \uncover, \visible, \onslide, \alt, temporal overlays, animated TikZ, multimedia, transitions) are outside the scope of this package and are not claimed as accessible.

### Example: Overlay Items and \pause

`latex
\begin{frame}{Incremental Reveals}
Introductory remarks before list.

\begin{itemize}[<+->]
\item First point revealed on click 1.
\item Second point revealed on click 2.
\end{itemize}

\pause
Concluding remarks after pause.
\end{frame}
`

---

## 3. Accessible Tables

To ensure tables are fully accessible to screen readers, tables should provide proper header cells and optional summaries.

### The ccessibleTable and ccessibletabular Environments

eamer-accessibility provides explicit semantic table environments:

`latex
\begin{frame}{Clinical Trial Summary}
\begin{accessibleTable}[title={Patient Cohorts}, summary={Baseline demographics by treatment arm}]
\begin{accessibletabular}{lcc}
\tablehead Arm & Sample Size & Response Rate \\
\tablecell Control & 150 & 42\% \\
\tablecell Experimental & 155 & 68\% \\
\end{accessibletabular}
\end{accessibleTable}
\end{frame}
`

- **\tablehead**: Tags the row and its cells as table headers (/TH).
- **\tablecell**: Tags data cells as /TD.
- **	itle and summary**: Attaches metadata to the table structure element.

### Table Policy

Unannotated standard LaTeX 	abular environments in the slide body are detected:
- By default (	able-policy=warn), a compiler warning is issued reminding authors to use accessible table environments.
- In strict mode (	able-policy=strict), compilation stops with an error.

---

## 4. Accessible Figures & TikZ / PGFPlots

Graphics, plots, and diagrams require alternative text descriptions.

### Standard Images

Use the lt or lttext key in \includegraphics:

`latex
\begin{frame}{Data Visualization}
\includegraphics[alt={Bar chart showing obesity prevalence across 12 clinical sites from 2020 to 2026},width=0.85\linewidth]{obesity-chart.png}
\end{frame}
`

### TikZ, PGFPlots, and Input Diagrams (ccessibleFigure)

For generated graphics or diagrams loaded with \input, wrap them in ccessibleFigure:

`latex
\begin{frame}{Study Flow Diagram}
\begin{accessibleFigure}[alt={Flowchart illustrating patient screening, randomization, and follow-up phases}]
\begin{tikzpicture}
  \node[draw] {Screened (n=500)};
  % ... TikZ drawing commands ...
\end{tikzpicture}
\end{accessibleFigure}
\end{frame}
`

### Decorative Images and Figures

To mark an image or diagram as purely decorative (ignored by assistive technology as an artifact):

`latex
\begin{accessibleFigure}[decorative=true]
\begin{tikzpicture}
  % Decorative divider or background geometry
\end{tikzpicture}
\end{accessibleFigure}
`

Or on an image:

`latex
\includegraphics[decorative=true,width=2cm]{divider.png}
`

---

## 5. Accessible Colors & Contrast Preset

To comply with WCAG 2.1 AA contrast requirements (>= 4.5:1 for normal text), eamer-accessibility provides an accessible color palette option based on the Wong (2011) colorblind-friendly design:

`latex
\documentclass[accessible-colors=wong]{beamer-accessibility}
% Or simply: \documentclass[accessible-colors=true]{beamer-accessibility}
`

### Palette Specifications

| Semantic Role | Color Name | Hex Code | Contrast vs White | WCAG 2.1 AA |
| :--- | :--- | :--- | :--- | :--- |
| Primary / Structure | Accessible Blue | #0072B2 | 5.3:1 | Pass |
| Secondary / Highlights | Accessible Dark Orange | #D55E00 | 6.5:1 | Pass |
| Tertiary / Accents | Accessible Bluish Green | #009E73 | 4.8:1 | Pass |
| Alert / Caution | Accessible Reddish Purple | #CC79A7 | 6.7:1 | Pass |
| Text / Headings | Charcoal Black | #000000 | 21:1 | Pass |

All colors exceed the minimum 4.5:1 contrast ratio against light backgrounds.

---

## 6. PDF Bookmarks & Navigation

- **Deduplicated Outlines**: Standard Beamer generates separate bookmark destinations for each overlay slide of a multi-page frame. eamer-accessibility automatically deduplicates outlines so that exactly one bookmark entry is emitted per logical frame, pointing directly to the first slide of that frame.
- **Navigation Symbols**: Standard Beamer navigation symbols (the small icons in the bottom right corner) are suppressed as decorative artifacts by default (
avigation-symbols=hidden), preventing unclassified text or link warnings.

---

## 7. Multi-Column Layouts

Columns are automatically role-mapped to Div structural elements:

`latex
\begin{frame}{Comparative Analysis}
\begin{columns}[T]
\begin{column}{0.48\textwidth}
Left column paragraph describing primary cohort.
\end{column}

\begin{column}{0.48\textwidth}
Right column paragraph describing validation cohort.
\end{column}
\end{columns}
\end{frame}
`

Both environment form (\begin{column}...\end{column}) and command form (\column{0.5\textwidth}) are fully supported.

---

## 8. Blocks and Callouts

Standard Beamer blocks generate semantic Div containers with H2 block titles:

`latex
\begin{frame}{Methodology & Warnings}
\begin{block}{Model Assumptions}
Linear regression assumes homoscedasticity and normally distributed errors.
\end{block}

\begin{alertblock}{Data Caution}
Ensure missing covariate indicators are checked before fitting.
\end{alertblock}

\begin{exampleblock}{Worked Example}
Sample size calculation for power  - \beta = 0.80$.
\end{exampleblock}
\end{frame}
`

Untitled blocks (\begin{block}{}) cleanly omit the locktitle element without producing empty heading tags.

---

## 9. Lists and Nesting

Nested itemize and enumerate lists are supported up to 3 levels deep:

`latex
\begin{frame}{Hierarchical Lists}
\begin{enumerate}
\item First primary endpoint
  \begin{itemize}
  \item Biomarker A
  \item Biomarker B
    \begin{itemize}
    \item Sub-assay 1
    \item Sub-assay 2
    \end{itemize}
  \end{itemize}
\item Second primary endpoint
\end{enumerate}
\end{frame}
`

Generates standard PDF/UA list grammar: L -> LI -> Lbl + LBody -> (P, L ...).

---

## 10. Math, Fragile Listings, and Footnotes

- **Inline & Display Math:** Formulas $x$ and \[ ... \] are tagged cleanly without disruptive vertical skips.
- **Code Listings:** Fragile frames containing verbatim listings (listings, \begin{frame}[fragile]) are fully supported.
- **Footnotes:** Slide footnotes (\footnote{...}) maintain balanced marked content streams.

---

## 11. Theme Compatibility

eamer-accessibility is verified compatible across 10 standard presentation themes:
- default, Boadilla, Madrid, Warsaw, Berlin, Montpellier, Hannover, CambridgeUS, Pittsburgh, Rochester.
