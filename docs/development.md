# Development status

## Current milestone

Version 0.9 provides automatic low-level tagging for rendered frames, frame titles, ordinary paragraphs, single-level and nested `itemize` lists (up to 3 levels), `enumerate` lists (up to 3 levels), mixed `itemize`/`enumerate` nesting, Beamer block environments (`block`, `alertblock`, `exampleblock`, and untitled blocks), multi-column slide layouts (`columns`, `column` environments, and `\column` command), graphics with author-provided alternative text (`\includegraphics[alt={...}]{...}` and `figure` environments), inline/display math formulas, fragile code listings (`listings`), and reference footnotes. It also injects essential PDF document catalog metadata (`/Lang` and `/ViewerPreferences` with `/DisplayDocTitle true`) with configurable document language. It has been validated across 10 diverse presentation themes, verified via the automated AT Accessibility Validator, and retains upstream Beamer as the visual engine using pdfLaTeX.

Unsupported constructs (such as item overlay specifications and description lists) are safely detected and fall back cleanly to untagged Beamer output without corrupting the structure tree.

## Architecture decision

The package uses early `pdfmanagement` without `\DocumentMetadata`:

```text
pdfmanagement
  -> upstream Beamer
  -> low-level tagpdf
  -> Document Catalog /Lang & /ViewerPreferences injection
  -> narrowly scoped Beamer, graphicx, footnote, and paragraph hooks
```

This separation is necessary in the validated LaTeX 2026 environment. `\DocumentMetadata` loads the complete LaTeX-lab module collection, whose footnote and list replacements conflict with Beamer 3.78. The project does not snapshot or restore kernel list and footnote implementations.

## Validated structure

```text
Catalog (/Lang "en-US", /ViewerPreferences << /DisplayDocTitle true >>)
StructTreeRoot
  Document
    frame -> Sect
      frametitle -> H1
        MCR
      P
        MCR
      column -> Div
        block -> Div
          blocktitle -> H2
            MCR
          P
            MCR
          L
            LI
              Lbl
                MCR
              LBody
                P
                  MCR
                L (nested sublist)
                  LI
                    Lbl
                      MCR
                    LBody
                      P
                        MCR
      column -> Div
        block -> Div
          blocktitle -> H2
            MCR
          P
            MCR
            Figure
              /Alt (Alternative text description)
              MCR
            MCR
      P
        MCR
```

- **Document Catalog Metadata:** Injects `/Lang` attribute (configurable via `lang` class/package option, defaulting to `en-US`) and `/ViewerPreferences` with `/DisplayDocTitle true` directly into the PDF Catalog via `\pdfmanagement_add:nnn`.
- **Frame Titles:** Beamer processes the frame body before constructing the title box. The title template uses `firstkid=true` so the frame title precedes body paragraphs semantically without changing the visual box order.
- **Multi-column slide layouts:** Intercepts both `beamer@columnenv` and `\beamer@columncom` with `\renewenvironment<>` and `\renewcommand<>`, preserving overlay options `<#3>` and optional alignment/mode `[#1]` while placing `\ba_column_begin:` and `\ba_column_end:` inside the `minipage` lifecycle.
- **List tagging:** Intercepts Beamer's `itemize` and `enumerate` environment lifecycles and templates (`itemize item/subitem/subsubitem`, `enumerate item/subitem/subsubitem`), emitting compliant `L -> LI -> Lbl + LBody -> (P, L ...)` hierarchies across nesting levels 1, 2, and 3.
- **Block tagging:** Wraps `block begin` / `block end`, `block alerted begin` / `block alerted end`, and `block example begin` / `block example end`. A title-phase state machine ensures block titles are tagged as `blocktitle` (`H2`) while body prose and lists are tagged within `block` (`Div`) without unwanted `<P>` nesting in both standard and rounded (`beamerboxesrounded`) themes.
- **Graphics tagging:** Intercepts `\Gin@ii` from `graphicx`, accepting `alt` and `alttext` keys and emitting `/Figure` structure elements containing leaf MCR and `/Alt` attribute strings.
- **Math, Verbatim & Footnotes:** Tagging chains paragraph closures cleanly on paragraph starts and container boundaries, avoiding spurious vertical whatsits around display math `\[ ... \]`, code listings, and footnote boxes.
- **AT Validator:** `tests/verify_at.py` inspects PDF trees to verify PDF/UA semantic structure rules, RoleMap completeness, Figure Alt coverage, list grammar, and leaf MCR uniqueness.

## Next milestone (v1.0)

1. Comprehensive documentation, API reference, and user guide.
2. Cross-platform CI automation script and verification pipeline.
3. Stable release packaging and v1.0 readiness review.



