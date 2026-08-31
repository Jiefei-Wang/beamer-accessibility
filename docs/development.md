# Development status

## Current milestone

Version 0.3 provides automatic low-level tagging for rendered frames, frame titles, and ordinary paragraphs. It retains upstream Beamer as the visual implementation and uses pdfLaTeX.

Unsupported list environments are detected and deliberately receive no partial package tagging. Once a list is encountered, paragraph tagging is suppressed for the remainder of that frame.

## Architecture decision

The package uses early `pdfmanagement` without `\DocumentMetadata`:

```text
pdfmanagement
  -> upstream Beamer
  -> low-level tagpdf
  -> narrowly scoped Beamer and paragraph hooks
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
```

Beamer processes the frame body before constructing the title box. The title template uses `firstkid=true` so the frame title precedes body paragraphs semantically without changing the visual box order.

## Next milestone

Add automatic tagging for a plain two-item Beamer `itemize` by wrapping Beamer's existing list lifecycle and label template:

```text
L
  LI
    Lbl
    LBody
```

The implementation must not parse or replace Beamer's overlay-aware list layout. Optional labels, overlays, and nesting must be tested separately; unsupported forms should fall back to untagged Beamer output.

Do not begin `enumerate`, `description`, blocks, tables, math, graphics, or PDF/UA metadata until the isolated `itemize` milestone passes structure and zero-pixel visual tests.

