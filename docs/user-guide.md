# User Guide: `beamer-accessibility` (v1.0)

`beamer-accessibility` provides standard-compliant PDF accessibility tagging for LaTeX Beamer presentations with zero visual differences and identical text output.

---

## Overlay policies

The `overlay-policy` option defaults to `pages`. Supported `\item` overlay specifications and `\pause` are tagged only when visible on each rendered page; already-visible content is intentionally repeated. Use `overlay-policy=handout` for a single complete accessible page per frame. Use `overlay-policy=strict` to stop on either supported incremental construct and revise the source. Other Beamer overlay mechanisms are outside this task and are not claimed as accessible support.

Inline TikZ/PGFPlots can be wrapped with `accessibleFigure[alt={...}]` (or `decorative=true`); the wrapper also supports material loaded with `\input`. Tables can use the existing explicit `accessibletabular` API, or its `accessibleTable` alias, together with `\tablehead` and `\tablecell`.


## 1. Quick Start

### Document Class (Recommended)

```latex
\documentclass[14pt,t,lang=en-US]{beamer-accessibility}
\usepackage{graphicx}
\usetheme{Madrid}

\begin{document}
\begin{frame}{First Accessible Slide}
This paragraph is tagged automatically as standard paragraph text.
\end{frame}
\end{document}
```

### Package Form

If using standard `\documentclass{beamer}`, PDF management must be loaded before the class:

```latex
\RequirePackage{pdfmanagement}
\documentclass[14pt,t]{beamer}
\usepackage{graphicx}
\usepackage[lang=en-US]{beamer-accessibility}
```

---

## 2. Document Language & Catalog Metadata

Set the natural language of the presentation using the `lang` option (defaults to `en-US`):

```latex
\documentclass[lang=en-GB]{beamer-accessibility}
```

This injects:
- `/Lang (en-GB)` into the PDF Document Catalog.
- `/ViewerPreferences << /DisplayDocTitle true >>` into the Catalog.

---

## 3. Graphics & Alternative Text

To provide accessible descriptions for images, use the `alt` or `alttext` key in `\includegraphics`:

```latex
\begin{frame}{Data Visualization}
\includegraphics[alt={Bar chart showing obesity prevalence across 12 clinical sites from 2020 to 2026},width=0.85\linewidth]{obesity-chart.png}
\end{frame}
```

Supported locations:
- Standalone graphics on frames
- Inline graphics within text paragraphs
- Graphics inside `block`, `alertblock`, and `exampleblock` environments
- Graphics inside `column` layouts and `figure` environments

---

## 4. Multi-Column Layouts

Columns are automatically role-mapped to `Div` structural elements:

```latex
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
```

Both environment form (`\begin{column}...\end{column}`) and command form (`\column{0.5\textwidth}`) are fully supported.

---

## 5. Blocks and Callouts

Standard Beamer blocks generate semantic `Div` containers with `H2` block titles:

```latex
\begin{frame}{Methodology & Warnings}
\begin{block}{Model Assumptions}
Linear regression assumes homoscedasticity and normally distributed errors.
\end{block}

\begin{alertblock}{Data Caution}
Ensure missing covariate indicators are checked before fitting.
\end{alertblock}

\begin{exampleblock}{Worked Example}
Sample size calculation for power $1 - \beta = 0.80$.
\end{exampleblock}
\end{frame}
```

Untitled blocks (`\begin{block}{}`) omit the `blocktitle` element cleanly without empty heading tags.

---

## 6. Lists and Nesting

Nested `itemize` and `enumerate` lists are supported up to 3 levels deep:

```latex
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
```

Generates standard PDF/UA list grammar: `L -> LI -> Lbl + LBody -> (P, L ...)`.

---

## 7. Math, Fragile Listings, and Footnotes

- **Inline & Display Math:** Formulas `$x$` and `\[ ... \]` are tagged cleanly without disruptive vertical skips.
- **Code Listings:** Fragile frames containing verbatim listings (`listings`, `\begin{frame}[fragile]`) are fully supported.
- **Footnotes:** Slide footnotes (`\footnote{...}`) maintain balanced marked content streams.

---

## 8. Theme Compatibility

`beamer-accessibility` is verified compatible across 10 standard presentation themes:
- `default`, `Boadilla`, `Madrid`, `Warsaw`, `Berlin`, `Montpellier`, `Hannover`, `CambridgeUS`, `Pittsburgh`, `Rochester`.
