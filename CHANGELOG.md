# Changelog

## 0.3 — 2026-08-31

- Initialize PDF management before upstream Beamer through a thin wrapper class.
- Load low-level `tagpdf` without `\DocumentMetadata` or LaTeX-lab document modules.
- Add automatic structures for frames, frame titles, and ordinary paragraphs.
- Preserve title-before-body semantic order with Beamer's existing title template.
- Leave unsupported list environments visually unchanged and untagged.
- Add isolated structure and pixel-regression tests.

