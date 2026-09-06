# University accessibility audit

Reviewed 2026-09-06. UTMB is the working institutional context, inferred from
the UTMB colors in the course. Published [UTMB standards](https://www.utmb.edu/accessibility/guidelines/utmb)
identify WCAG 2.1 AA. Its [presentation guidance](https://www.utmb.edu/brand/usage-guidelines/presentations)
also addresses readability, contrast, descriptions, and reading order.

This is an engineering audit of PDF semantics, not institutional certification.
PowerPoint template and brand requirements are not automatically met by Beamer.

| Requirement | Package contribution | Author/manual work |
| --- | --- | --- |
| Non-text alternatives | Image/TikZ descriptions and composite figures | Accurate descriptions and data equivalents. |
| Reading order/headings | Frame/title-page headings, columns, blocks, lists | Check every page and complex layout. |
| Tables | Explicit cells, header scope, title and summary | Declare actual headers; simplify complex tables. |
| Navigation | Language, title display, bookmarks, structured links | Meaningful titles, keyboard access, and link purpose. |
| Math/code | Spoken Formula alternatives; code rendering | Describe formulas and test with assistive technology. |
| Contrast/legibility | Limited optional contrast preset | Actual colors, fonts, clipping, and chart labels/patterns. |

## Course findings

Original course files were read but not changed. Four copied decks compiled to
114 pages: 23, 30, 31, and 30 for Lectures 1 through 4. The latest full-deck
structural audit found missing figure alternatives: 2 in Lecture 1, 0 in
Lecture 2, 7 in Lecture 3, and 4 in Lecture 4. A structural pass alone does not
establish accessibility: tables, math, contrast, size, and reading quality still
require review.

The shared histogram already supplies a meaningful native TikZ description;
the package now transfers it to a Figure tag. Other informative graphics need
authored descriptions. Plain tables need explicit header and cell markup.
Do not invent descriptions or mark informative content decorative to pass checks.

Generate exact source locations without editing slides:

```powershell
python scripts/audit_source.py "../biostat slides"
```

The scanner is heuristic, not a TeX parser. Macro definitions, enclosing figure
descriptions, and layout-only tables require judgment. Use institutional tools
and a screen reader, and inspect every page before distribution.

The [source reminders](course-source-reminders.md) record the exact locations from this audit.
