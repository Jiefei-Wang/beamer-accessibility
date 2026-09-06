# Validation record: 2026-09-06

This record supersedes older claims of universal pixel identity or automatic
standards compliance. Tests inspect selected PDF properties; they do not run a
screen reader, certify PDF/UA, or certify WCAG compliance.

## Results

- 148 TeX fixtures in the final suite, including five intentional compilation failures.
- 68 explicit structure/text regression specifications passed.
- 63 paired fixtures require zero differing pixels at 300 DPI.
- 72 tagged PDFs passed content-stream, structure, metadata-flag, ParentTree,
  header-scope, and annotation checks. The deliberate missing-alt fixture must
  produce its expected error; its name is not exempted inside the validator.
- Behavioral checks passed for hidden prose and figures, native PGFPlots alt text,
  composite/decorative images, table scopes and option resets, spoken formulas,
  title-page headings, bookmark destinations, centered text in list items,
  decorative tables, and link annotation ownership.
- Validator negative controls passed for missing alt text after renaming a PDF,
  required document titles, false PDF Boolean flags, and inherited Form content.
- Strict/warning policies and the actual applied contrast-preset colors passed.

Compilation and checks were iterated as defects were fixed. The final verification
commands are:

```powershell
python tests/run_tests.py
```

Individual verification commands (run after compilation) are:

```powershell
python tests/verify.py tests/fixtures/out
python tests/verify_at.py tests/fixtures/out
python tests/verify_regressions.py tests/fixtures/out
```

For deliverable PDFs, use the additional title requirement:

```powershell
python tests/verify_at.py path/to/pdf-directory --require-title
```

All LaTeX outputs and rendered test pages are in tests/fixtures/out. The Python
runner is shared by PowerShell and CI. Expected-error checks match the intended
diagnostic, including TeX line wrapping. Renders are cached only for byte-identical
PDFs. Missing PDFs and empty validation directories cannot pass silently.

## Visual scope and exceptions

Representative renders were inspected for title pages, native PGFPlots, composite
images, annotated tables/formulas, links, and empty/centered layout cases. The
explicit figure wrappers now match their baseline pixels after a trailing-space
fix, enabling checks previously disabled in the suite. The contrast preset is
compared against a baseline with the intended palette applied.

Five structure/text fixtures retain explicit pixel-check exclusions: ordinary
inline/display mathematics, description lists, row-and-column-header tables,
empty-layout cases, and the new combined formula/table case. These do not have
a universal zero-pixel guarantee. The reviewed row-header table differed by 315
pixels and the combined formula case by 35 pixels; the latter is punctuation
kerning at a tagging boundary. Link boundaries also change cross-boundary kerning
and can cause pypdf to infer whitespace before punctuation; link checks preserve
every nonspace character and validate annotation structure. These exceptions are
visible in verify.py and verify_regressions.py, not presented as pixel-identical.

Some synthetic fixtures deliberately have no document title; they generate
warnings unless --require-title is selected. Empty marked-content segments are
also warnings: box assembly and pauses can create them without losing content.
No guarantee is made about arbitrary styles, contrast combinations, or font sizes.

## Real course coverage

The course sources changed during this review. The retained regression snapshot
contains four copied decks totaling 114 pages (23, 30, 31, 30). Earlier snapshots
also exposed bugs now retained as focused fixtures, including centered pathname
examples inside list items. Original course files were not edited by this work.

All four retained copies compiled. The structural audit reported only missing
figure alternatives: 2, 0, 7, and 4 respectively. Plain-table warnings and manual
math/visual checks remain outside those structural pass counts. See the
[university audit](university-accessibility.md) and
[source reminders](course-source-reminders.md) for author responsibilities.

Scratch copies, PDFs, logs, hashes, and machine-readable reports are retained
under build/course and build. Each copied TeX source has its own adjacent out
folder. These generated artifacts are excluded from version control.

No package installation, publishing, original-slide revision, or independent
screen-reader/PDF-UA certification was performed.
