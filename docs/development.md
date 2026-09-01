# Development status

## Current milestone

Version 0.7 provides automatic low-level tagging for rendered frames, frame titles, ordinary paragraphs, single-level and nested `itemize` lists (up to 3 levels), `enumerate` lists (up to 3 levels), mixed `itemize`/`enumerate` nesting, Beamer block environments (`block`, `alertblock`, `exampleblock`, and untitled blocks), and graphics with author-provided alternative text (`\includegraphics[alt={...}]{...}` and `figure` environments). It retains upstream Beamer as the visual implementation and uses pdfLaTeX.

Unsupported constructs (such as item overlay specifications and description lists) are safely detected and fall back cleanly to untagged Beamer output without corrupting the structure tree.

## Architecture decision

The package uses early `pdfmanagement` without `\DocumentMetadata`:

```text
pdfmanagement
  -> upstream Beamer
  -> low-level tagpdf
  -> narrowly scoped Beamer, graphicx, and paragraph hooks
```

This separation is necessary in the validated LaTeX 2026 environment. `\DocumentMetadata` loads the complete LaTeX-lab module collection, whose footnote and list replacements conflict with Beamer 3.78. The project does not snapshot or restore kernel list and footnote implementations.

## Validated structure

```text
StructTreeRoot
  Document
    frame -> Sect
      frametitle -> H1
        MCR
      P
        MCR
      block -> Div
        blocktitle -> H2
          MCR
        P
          MCR
          Figure
            /Alt (Alternative text description)
            MCR
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
      P
        MCR
```

- Beamer processes the frame body before constructing the title box. The title template uses `firstkid=true` so the frame title precedes body paragraphs semantically without changing the visual box order.
- List tagging intercepts Beamer's `itemize` and `enumerate` environment lifecycles and templates (`itemize item/subitem/subsubitem`, `enumerate item/subitem/subsubitem`), emitting compliant `L -> LI -> Lbl + LBody -> (P, L ...)` hierarchies across nesting levels 1, 2, and 3.
- Block tagging wraps `block begin` / `block end`, `block alerted begin` / `block alerted end`, and `block example begin` / `block example end`. A title-phase state machine ensures block titles are tagged as `blocktitle` (`H2`) while body prose and lists are tagged within `block` (`Div`) without unwanted `<P>` nesting in both standard and rounded (`beamerboxesrounded`) themes.
- Graphics tagging intercepts `\Gin@ii` from `graphicx`, accepting `alt` and `alttext` keys and emitting `/Figure` structure elements containing leaf MCR and `/Alt` attribute strings.
- Precise frame body boundary gating prevents stray paragraph tagging from presentation furniture (headline, footline, navigation symbols, and sidebars).

## Next milestone (v0.8)

1. Columns (`\begin{columns}\begin{column}{...}...\end{column}\end{columns}`) tagged as structured sub-regions or semantic parts.
2. Theme compatibility across major Beamer outer and inner themes (Berlin, Madrid, Warsaw, Metropolis, etc.).
3. Slide composition regression suite ensuring multi-column layouts, mixed media, and complex blocks maintain strict 0-pixel visual identity.



