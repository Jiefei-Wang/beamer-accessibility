# beamer-accessibility

Experimental low-level accessibility support for Beamer that preserves Beamer's visual implementation and ordinary frame syntax.

The current release automatically creates semantic structures for rendered frames, frame titles, and ordinary paragraphs. Unsupported constructs continue to compile and render normally but do not receive package-generated semantic tags. Lists are deliberately unsupported in v0.3.

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
Test paragraph.
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
```

The title is placed before body paragraphs in semantic order even though Beamer constructs its title box after processing the frame body.

## Unsupported constructs

In v0.3, `itemize`, `enumerate`, and `description` use their normal Beamer layout and receive no automatic package tags. Blocks, tables, columns, math, figures, graphics, notes, overlays, and other Beamer features have not yet been claimed as semantically supported.

This project does not yet claim PDF/UA conformance.

## Testing

From PowerShell:

```powershell
./tests/run-tests.ps1
```

The test suite compiles isolated tagged and untagged fixtures with pdfLaTeX, checks the structure tree with `pypdf`, and compares Poppler renderings at 300 DPI with Pillow. Tagged output must be pixel-identical to its PDF-management-only baseline.

## Installation

For the current MiKTeX user:

```powershell
./scripts/install-miktex.ps1
```

The script installs the `.sty` and `.cls` files in the user MiKTeX tree and refreshes the filename database.

## License

LaTeX Project Public License 1.3c or later.

