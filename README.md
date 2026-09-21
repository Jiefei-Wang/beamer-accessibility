# beamer-accessibility

Experimental semantic PDF tagging for Beamer, tested against the syntax in the
BIOS 6485 course slides. It keeps Beamer as the visual engine.

**Changing the class alone does not make a presentation accessible.** Authors
still supply meaningful figure descriptions, table headers, document/slide titles,
and readable content. Automated checks are not PDF/UA or WCAG certification.

## Quick start

```latex
\documentclass[14pt,t,lang=en-US]{beamer-accessibility}
\usetheme{Boadilla}
\title{Picturing distributions}
\author{Course instructor}
\begin{document}
\begin{frame}{Distribution of measurements}
\includegraphics[alt={Describe the relevant pattern and values},width=3cm]{chart}
\end{frame}
\end{document}
```

Use pdfLaTeX with LaTeX 2025-06-01 or later, `pdfmanagement`, `tagpdf`, and a
compatible Beamer (development tested with the installed MiKTeX toolchain).
The wrapper loads PDF management before Beamer. Do not add `\DocumentMetadata`
to this workflow; the LaTeX-lab replacements are not supported here.

Package-only use:

```latex
\RequirePackage{pdfmanagement}
\documentclass[14pt,t]{beamer}
\usepackage[lang=en-US]{beamer-accessibility}
```

## What is supported

- Frames and title-page titles as headings; meaningful slide bookmarks.
- Paragraphs, blocks, columns, and itemize/enumerate/description lists up to three levels.
- Item overlays and `\pause`, with only revealed content included in reading order.
- Images with `alt`/`alttext`, or `decorative=true`.
- Native `tikzpicture[alt={...}]` including the course's PGFPlots histogram.
- Explicit `accessibleFigure` wrappers for composite diagrams.
- Explicit table cells with row/column header scope and optional table summaries.
- `\AccessibleMath{spoken description}{$...$}` for inline formulas.
- Fragile `listings` content and footnote text; actual reading quality still needs review.

Plain `tabular` is detected, not automatically assigned meaningful headers.
Unannotated math renders normally but is not converted into spoken mathematics.
See the [user guide](docs/user-guide.md) for exact supported syntax and limits.

## University requirements

The course uses UTMB branding. The implementation audit uses UTMB's published
[accessibility standards](https://www.utmb.edu/accessibility/guidelines/utmb) and
[presentation guidance](https://www.utmb.edu/brand/usage-guidelines/presentations).
This package addresses PDF semantics. It does not replace institutional template,
font, visual design, or manual accessibility review requirements.

See the [requirements and course audit](docs/university-accessibility.md).

## Installation

```powershell
git clone https://github.com/Jiefei-Wang/beamer-accessibility.git
cd beamer-accessibility
# For MiKTeX:
.\scripts\install-miktex.ps1
# For TeX Live:
.\scripts\install-texlive.ps1
```

The installer updates the user MiKTeX or TeX Live tree. It is not needed to run tests from this
repository. Compile with outputs in an adjacent `out` directory, for example:

```powershell
New-Item -ItemType Directory -Force examples/out
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=examples/out examples/minimal.tex
```

## Tests

```powershell
python tests/run_tests.py
# Equivalent PowerShell entry point:
.\tests\run-tests.ps1
```

The runner compiles fixtures twice, asserts intentional failures, compares text
and 300-DPI pixels for paired regressions, and inspects PDF structure/content.
All LaTeX outputs and rendered test images go to `tests/fixtures/out`.
Run a focused compile with `--pattern 'figure-*.tex' --compile-only`.

These checks do not run a screen reader or certify PDF/UA compliance. The
[validation record](docs/validation.md) distinguishes tested behavior from
remaining author responsibilities. [Architecture](docs/architecture.md) explains
implementation boundaries.

## Release

`./scripts/build-release.ps1` builds the distribution archive.
License: LaTeX Project Public License 1.3c or later.
