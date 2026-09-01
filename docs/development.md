# Development status

## Current milestone

Version 0.4 provides automatic low-level tagging for rendered frames, frame titles, ordinary paragraphs, and single-level plain `itemize` lists. It retains upstream Beamer as the visual implementation and uses pdfLaTeX.

Unsupported list constructs (such as nested lists, item overlay specifications, enumerate, and description) are safely detected and fall back cleanly to untagged Beamer output without corrupting the structure tree.

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
```

- Beamer processes the frame body before constructing the title box. The title template uses `firstkid=true` so the frame title precedes body paragraphs semantically without changing the visual box order.
- List tagging intercepts Beamer's `itemize` environment lifecycle and `itemize item` template, emitting standard `L -> LI -> Lbl + LBody -> P` hierarchies.
- Precise frame body boundary gating prevents stray paragraph tagging from presentation furniture (headline, footline, navigation symbols, and sidebars).

## Next milestone (v0.5)

Add support for nested `itemize` and `enumerate` lists:

```text
L
  LI
    Lbl
    LBody
      P
      L (nested list)
        LI
          Lbl
          LBody
            P
```

- Track list nesting depth and type (`itemize` vs `enumerate`).
- Map `enumerate` item labels (`\insertenumlabel`, `enumi`, `enumii`, etc.) cleanly to `Lbl`.
- Handle mixed nesting (e.g. `enumerate` inside `itemize` and vice versa).
- Maintain 0-pixel visual identity and strict structure validity.


