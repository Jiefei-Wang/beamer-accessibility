# Architecture and maintenance boundaries

The wrapper selects PDF management before Beamer. Low-level tagpdf structures
and Beamer hooks preserve the upstream presentation engine. pdfLaTeX is the
validated engine; LaTeX-lab replacements are outside this implementation.

Each rendered frame maps to Sect. Frame and title-page titles map to H1; block
titles map to H2. Beamer builds titles after processing body content, so heading
structures are inserted first. Bookmarks use meaningful titles once per logical
frame. Title token lists must not be fully expanded before hyperref sanitization.

Paragraphs have explicit begin/end state. Lists track three nesting depths and
separate labels from bodies. Columns and blocks enclose their content. Repeated
template furniture is artifact content.

A pause closes paragraph structure and marked content before reopening according
to covering depth. Merely reopening an MCID in the old paragraph exposes future
text. Images and TikZ also check covering depth. Behavioral tests check actual
page-specific text and figure ownership.

Graphicx keys are parsed before selecting Figure or artifact. Retain the actual
opened state separately because graphicx reparses options. An accessibleFigure
owns enclosed image content. Clear options between images. Decorative content
suspends paragraph marked content and restores it afterward.

Native TikZ uses environment ownership and picture callbacks. PGFPlots creates
internal pictures: nested callbacks must not create duplicate Figure structures.
Suppress paragraph creation while assembling a described graphic.

Explicit table rows/cells avoid replacing TeX alignment parsing. Counters select
TH scope from declared header rows and first-column settings. Reset options per
table. Titles use /T, not replacement /Alt. Summaries use the Table /Summary
attribute. Header scopes use /Row or /Column. Complex spans are outside scope.

AccessibleMath suspends surrounding marked content and supplies an authored
Formula alternative. Ordinary mathematics is not translated automatically.

verify.py checks hierarchies, text identity, and paired 300-DPI rasters.
verify_at.py is a structural validator, not assistive technology: it checks PDF
Boolean values, alternatives, list/table grammar, marked-content balance, parent
pointers, ParentTree ownership, and annotation OBJR associations. Forms inherit
enclosing marked content and use their own resources. Empty content segments
are warnings: TeX box assembly and pauses can create them without losing text.

The deliberately missing-alt fixture must produce an error; the validator
function itself has no filename exemption. Negative controls test invalid PDFs.
Link boundaries can change font kerning and inferred extraction whitespace before
punctuation. Link tests require every nonspace character and correct annotation
structure; visual inspection checks rendering. Universal pixel identity is not
claimed.

Compiled fixtures and rasters go to adjacent out directories. Render caches use
complete PDF byte hashes. Only generated page PNGs are replaced; caller-supplied
directories are not recursively deleted. CI and PowerShell share the Python
runner. Tests do not install the package into the user's TeX tree.
