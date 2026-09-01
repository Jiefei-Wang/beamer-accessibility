# beamer-accessibility

Experimental low-level accessibility support for Beamer that preserves Beamer's visual implementation and ordinary frame syntax.

The current release automatically creates semantic structures for rendered frames, frame titles, ordinary paragraphs, and single-level plain `itemize` lists. Unsupported constructs (such as nested lists, item overlay specifications, enumerate, and description) continue to compile and render normally but fall back gracefully without emitting broken or partial tags.

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
\begin{frame}{Test title}
Introductory paragraph before the list.

\begin{itemize}
\item First item with inline \textbf{bold} and \alert{alert}.
\item Second item with multiple paragraphs.

  Continuing paragraph inside the second item.
\end{itemize}

Summary paragraph after the list.
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
    L
      LI
        Lbl
        LBody
          P
```

- **Frame Titles:** The title is placed before body paragraphs in semantic order (`firstkid=true`) even though Beamer constructs its title box after processing the frame body.
- **Lists (`itemize`):** Emits compliant `L -> LI -> (Lbl, LBody -> P)` hierarchies.
- **Transitions:** Seamless paragraph open/close boundaries before, after, and within list items.
- **Visual & Text Identity:** Tagged output is guaranteed to have **0 differing pixels at 300 DPI** against untagged baseline and identical extracted text.

## Unsupported constructs & graceful fallback

In v0.4:
- Itemize items with explicit overlay specifications (`\item<1->`, `\item<2->`) fall back cleanly to untagged presentation.
- Nested itemize environments fall back cleanly to untagged presentation.
- `enumerate` and `description` environments fall back cleanly to untagged presentation.
- Blocks, tables, columns, math, figures, graphics, and notes are scheduled for subsequent milestones.

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

