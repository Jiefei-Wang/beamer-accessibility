# beamer-accessibility

Experimental low-level accessibility support for Beamer that preserves Beamer's visual implementation and ordinary frame syntax.

The current release automatically creates semantic structures for rendered frames, frame titles, ordinary paragraphs, single-level and nested `itemize` lists (up to 3 levels), `enumerate` lists (up to 3 levels), mixed `itemize`/`enumerate` nesting, and Beamer block environments (`block`, `alertblock`, `exampleblock`, and untitled blocks). Unsupported constructs (such as item overlay specifications and description lists) continue to compile and render normally but fall back gracefully without emitting broken or partial tags.

## Requirements

- LaTeX 2025-06-01 or later
- Beamer 3.78 or a compatible release
- `pdfmanagement` and `tagpdf`
- pdfLaTeX is the currently validated engine

The package intentionally does not use `\DocumentMetadata`, because the LaTeX 2026 document-metadata path loads LaTeX-lab replacements that conflict with Beamer's list and footnote machinery.

## Usage

The wrapper class initializes PDF management early and then loads upstream Beamer:

```latex
\documentclass[14pt,t]{beamer-accessibility}
\usetheme{Boadilla}

\begin{document}
\begin{frame}{Block and List Overview}
Introductory paragraph before the block.

\begin{block}{Important Milestone}
Paragraph inside the block.

\begin{enumerate}
\item First numbered milestone with \textbf{bold} text.
  \begin{itemize}
  \item Nested bullet subitem.
  \end{itemize}
\item Second numbered milestone.
\end{enumerate}
\end{block}

\begin{alertblock}{Warning}
Alert block text.
\end{alertblock}

Summary paragraph after blocks.
\end{frame}
\end{document}
```

Package-only use is also supported when PDF management is selected before Beamer:

```latex
\RequirePackage{pdfmanagement}
\documentclass[14pt,t]{beamer}
\usepackage{beamer-accessibility}
```

No commands are required in frame bodies.

## Supported semantic structures

```text
Document
  frame (role-mapped to Sect)
    frametitle (role-mapped to H1)
    P
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
    P
```

- **Frame Titles:** The title is placed before body paragraphs in semantic order (`firstkid=true`) even though Beamer constructs its title box after processing the frame body.
- **Blocks (`block`, `alertblock`, `exampleblock`):** Emits compliant `block -> (blocktitle, P ..., L ...)` structure mapped to `Div` and `H2`. Untitled blocks omit `blocktitle` cleanly.
- **Lists (`itemize` & `enumerate`):** Emits compliant `L -> LI -> (Lbl, LBody -> (P, L ...))` hierarchies for single-level and nested lists up to 3 levels deep (`itemize item/subitem/subsubitem`, `enumerate item/subitem/subsubitem`, and arbitrary mixed nestings).
- **Transitions:** Seamless paragraph open/close boundaries before, after, and within blocks and list items.
- **Visual & Text Identity:** Tagged output is guaranteed to have **0 differing pixels at 300 DPI** against untagged baseline and identical extracted text.

## Unsupported constructs & graceful fallback

In v0.6:
- Items with explicit overlay specifications (`\item<1->`, `\item<2->`) fall back cleanly to untagged presentation.
- `description` environments fall back cleanly to untagged presentation.
- Tables, columns, math, figures, graphics, and notes are scheduled for subsequent milestones.

This project does not yet claim PDF/UA conformance.

## Testing

From PowerShell:

```powershell
./tests/run-tests.ps1
```

The test suite compiles isolated tagged and untagged fixtures with pdfLaTeX, checks the structure tree with `pypdf`, validates unique `(MCID, Pg)` tuples, and compares Poppler renderings at 300 DPI with Pillow. Tagged output must be pixel-identical (0 differing pixels) to its baseline.

## Installation

For the current MiKTeX user:

```powershell
./scripts/install-miktex.ps1
```

The script installs the `.sty` and `.cls` files in the user MiKTeX tree and refreshes the filename database.

## License

LaTeX Project Public License 1.3c or later.

