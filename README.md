# beamer-accessibility

Experimental low-level accessibility support for Beamer that preserves Beamer's visual implementation and ordinary frame syntax.

The current release automatically creates semantic structures for rendered frames, frame titles, ordinary paragraphs, single-level and nested `itemize` lists (up to 3 levels), `enumerate` lists (up to 3 levels), mixed `itemize`/`enumerate` nesting, Beamer block environments (`block`, `alertblock`, `exampleblock`, and untitled blocks), multi-column slide layouts (`columns`, `column` environments, and `\column` command), graphics with author-provided alternative text (`\includegraphics[alt={...}]{...}` and `figure` environments), inline/display math formulas, fragile code listings (`listings`), and reference footnotes. It also injects essential PDF document catalog metadata (`/Lang` and `/ViewerPreferences` with `/DisplayDocTitle true`) with configurable document language. It has been verified compatible with diverse standard Beamer themes (`Boadilla`, `Madrid`, `Warsaw`, `Berlin`, `Montpellier`, `Hannover`, `CambridgeUS`, `Pittsburgh`, `Rochester`). Unsupported constructs (such as item overlay specifications and description lists) continue to compile and render normally but fall back gracefully without emitting broken or partial tags.

## Requirements

- LaTeX 2025-06-01 or later
- Beamer 3.78 or a compatible release
- `pdfmanagement` and `tagpdf`
- pdfLaTeX is the currently validated engine

The package intentionally does not use `\DocumentMetadata`, because the LaTeX 2026 document-metadata path loads LaTeX-lab replacements that conflict with Beamer's list and footnote machinery.

## Usage

The wrapper class initializes PDF management early and then loads upstream Beamer:

```latex
\documentclass[14pt,t,lang=en-US]{beamer-accessibility}
\usepackage{graphicx}
\usetheme{Madrid}

\begin{document}
\begin{frame}{Multi-Column and Block Overview}
Introductory paragraph spanning the slide width with math $E = mc^2$.

\begin{columns}[T]
\begin{column}{0.48\textwidth}
\begin{block}{Methodology}
\begin{enumerate}
\item Data collection
  \begin{itemize}
  \item Survey cohort
  \item Registry cohort
  \end{itemize}
\item Model specification
\end{enumerate}
\end{block}
\end{column}

\begin{column}{0.48\textwidth}
\begin{alertblock}{Diagnostics}
\includegraphics[alt={Diagnostic plot of model residuals},width=\linewidth]{residual-plot.png}
\end{alertblock}
\end{column}
\end{columns}

Summary paragraph after columns.
\end{frame}
\end{document}
```

Package-only use is also supported when PDF management is selected before Beamer:

```latex
\RequirePackage{pdfmanagement}
\documentclass[14pt,t]{beamer}
\usepackage{graphicx}
\usepackage[lang=en-US]{beamer-accessibility}
```

No commands are required in frame bodies. Authors provide accessible descriptions directly in standard `\includegraphics` calls using the `alt` or `alttext` key:

```latex
\includegraphics[alt={Bar chart showing distribution of obesity rates by state},width=0.8\linewidth]{chart.png}
```

## Supported semantic structures

```text
Document (Catalog: /Lang "en-US", /ViewerPreferences << /DisplayDocTitle true >>)
  frame (role-mapped to Sect)
    frametitle (role-mapped to H1)
    P
    column (role-mapped to Div)
      block (role-mapped to Div)
        blocktitle (role-mapped to H2)
        P
        L
          LI
            Lbl
            LBody
              P
              L (nested sublist)
                LI
                  Lbl
                  LBody
                    P
    column (role-mapped to Div)
      block (role-mapped to Div)
        blocktitle (role-mapped to H2)
        P
          Figure [Alt: "Description of image"]
    P
```

- **Document Metadata & Language (`/Lang`, `/ViewerPreferences`):** Automatically injects the document language tag into the PDF Catalog (configurable via `lang` class/package option, e.g., `lang=en-GB`, defaulting to `en-US`) and enables `/DisplayDocTitle true` in `/ViewerPreferences`.
- **Frame Titles:** The title is placed before body paragraphs in semantic order (`firstkid=true`) even though Beamer constructs its title box after processing the frame body.
- **Columns & Multi-Column Layouts (`column`):** Intercepts both environment (`\begin{column}...\end{column}`) and command (`\column{...}`) invocations inside `columns` to emit semantic `/column` structure elements role-mapped to `Div`. Paragraphs, blocks, lists, and figures inside columns nest naturally in their respective column containers.
- **Graphics & Alternative Text (`Figure`):** Intercepts `\includegraphics` to emit `/Figure` structure elements containing leaf marked content and `/Alt` attributes when provided via `alt` or `alttext` keys. Supports standalone graphics, inline graphics in prose, and graphics inside `block`, `column`, and `figure` environments.
- **Blocks (`block`, `alertblock`, `exampleblock`):** Emits compliant `block -> (blocktitle, P ..., L ...)` structure mapped to `Div` and `H2`. Untitled blocks omit `blocktitle` cleanly.
- **Lists (`itemize` & `enumerate`):** Emits compliant `L -> LI -> (Lbl, LBody -> (P, L ...))` hierarchies for single-level and nested lists up to 3 levels deep (`itemize item/subitem/subsubitem`, `enumerate item/subitem/subsubitem`, and arbitrary mixed nestings).
- **Math, Listings & Footnotes:** Tagging seamlessly preserves inline math `$x$`, display math equations `\[ ... \]`, fragile verbatim code listings (`listings`), and reference footnotes without disruptive vertical whatsits or stream imbalance.
- **Theme Compatibility:** Validated across standard inner and outer presentation themes (`Boadilla`, `Madrid`, `Warsaw`, `Berlin`, `Montpellier`, `Hannover`, `CambridgeUS`, `Pittsburgh`, `Rochester`), ensuring slide furniture (navigation bars, head/footlines, sidebars) does not pollute semantic reading trees.
- **Transitions:** Seamless paragraph open/close boundaries before, after, and within columns, blocks, graphics, and list items.
- **Visual & Text Identity:** Tagged output is guaranteed to have **0 differing pixels at 300 DPI** against untagged baseline and identical extracted text.

## Unsupported constructs & graceful fallback

In v0.9:

- **List Overlays:** Item overlays (e.g. `\item<2->` or `\begin{itemize}[<+->]`) are automatically detected and fall back cleanly without emitting partial list tags for inactive frames.
- **Description lists:** `description` environments fall back cleanly.
- **Tables:** Native table (`\begin{tabular}`) tagging is scheduled for subsequent milestones.

## Testing & Validation

The test suite runs with:

```powershell
./tests/run-tests.ps1
```

This:
1. Compiles both baseline and tagged PDFs for 40 isolated fixtures (80 `.tex` files).
2. Verifies strict structure trees via `pypdf`.
3. Ensures extracted text matches character-for-character.
4. Asserts **0 differing pixels at 300 DPI** via `pdftoppm` rendering.
5. Runs the automated Assistive Technology validator (`tests/verify_at.py`) checking Catalog metadata, RoleMap mappings, `/Figure` `/Alt` attributes, PDF/UA list grammar, and leaf MCR uniqueness.

## Installation

For the current MiKTeX user:

```powershell
./scripts/install-miktex.ps1
```

The script installs the `.sty` and `.cls` files in the user MiKTeX tree and refreshes the filename database.

## License

LaTeX Project Public License 1.3c or later.

