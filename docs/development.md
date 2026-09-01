# Development status

## Current milestone

Version 0.5 provides automatic low-level tagging for rendered frames, frame titles, ordinary paragraphs, single-level and nested `itemize` lists (up to 3 levels), `enumerate` lists (up to 3 levels), and mixed `itemize`/`enumerate` nesting. It retains upstream Beamer as the visual implementation and uses pdfLaTeX.

Unsupported constructs (such as item overlay specifications and description lists) are safely detected and fall back cleanly to untagged Beamer output without corrupting the structure tree.

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
```

- Beamer processes the frame body before constructing the title box. The title template uses `firstkid=true` so the frame title precedes body paragraphs semantically without changing the visual box order.
- List tagging intercepts Beamer's `itemize` and `enumerate` environment lifecycles and templates (`itemize item/subitem/subsubitem`, `enumerate item/subitem/subsubitem`), emitting compliant `L -> LI -> Lbl + LBody -> (P, L ...)` hierarchies across nesting levels 1, 2, and 3.
- Precise frame body boundary gating prevents stray paragraph tagging from presentation furniture (headline, footline, navigation symbols, and sidebars).

## Next milestone (v0.6)

Add support for Beamer block environments (`block`, `alertblock`, `exampleblock`):

```text
frame -> Sect
  frametitle -> H1
  block -> Div
    blocktitle -> H2
      MCR
    P
      MCR
    L
      LI
        Lbl
        LBody
          P
```

- Tag block environments as `block/Div` containers.
- Tag block titles as `blocktitle/H2` headers.
- Tag block body contents (paragraphs, itemize, enumerate) within the block container.
- Handle blocks without titles, custom blocks, and nested blocks.
- Maintain 0-pixel visual identity and exact text match.



