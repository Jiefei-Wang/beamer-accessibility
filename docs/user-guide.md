# Authoring accessible Beamer PDFs

The wrapper adds semantic structure; the author supplies meaning. Use pdfLaTeX,
load the wrapper before other packages, and set `\title`, `\author`, and `lang`.
Use meaningful, preferably unique frame titles. Title-page titles and frame
titles are tagged as headings and used for bookmarks.

## Options

| Option | Behavior |
| --- | --- |
| `lang=en-US` | PDF document language; use the language actually spoken in the slides. |
| `strict` or `mode=strict` | Missing figure alternatives and plain tables stop compilation. |
| `compat` or `mode=compat` | Default: report those problems as warnings. |
| `table-policy=strict` | Stop on unannotated tables without enabling all strict checks. |
| `table-policy=warn` | Default table policy; `strict` still takes precedence. |
| `overlay-policy=pages` | Default: each overlay is a separately tagged page. |
| `overlay-policy=handout` | Wrapper selects Beamer handout mode. |
| `overlay-policy=strict` | Reject item overlay specifications and `\pause`. |
| `accessible-colors=true` | Apply the limited contrast preset described below. |
| `navigation-symbols=hidden` | Default: suppress Beamer navigation icons. |
| `navsymbols=true` | Show navigation icons; not an accessibility guarantee. |

For package-only handouts, also pass `handout` to the Beamer class.
Other overlay commands (`\only`, `\visible`, arbitrary `\onslide`, animated TikZ,
multimedia, and transitions) are outside the supported overlay contract.

## Figures

```latex
\includegraphics[alt={Describe the chart's relevant pattern and values},width=3cm]{chart}
\includegraphics[decorative=true,width=1cm]{ornament}
```

`alttext` aliases `alt`; `artifact` aliases `decorative`. `decorative=false`
requires a description. Whitespace-only descriptions are missing descriptions.
An informative chart must not be marked decorative merely to silence a warning.
Describe information that a reader cannot recover from surrounding prose.

Native TikZ/PGFPlots, including diagrams loaded with `\input`:

```latex
\begin{tikzpicture}[alt={Two bars have heights two and three}]
  \draw (0,0) rectangle (1,2);
  \draw (1,0) rectangle (2,3);
\end{tikzpicture}
```

For a composite graphic, use one description around all its parts:

```latex
\begin{accessibleFigure}[alt={Explain the whole diagram}]
  \includegraphics[width=3cm]{diagram}
\end{accessibleFigure}
```

The lowercase `accessiblefigure` is an alias with the same option syntax.
The wrapper suppresses nested graphic tags. Keep surrounding explanation and
captions outside the wrapper. A figure alternative describes the whole enclosed
content, so prose inside it is not independently navigable.

## Tables

The package does not infer headers from visual formatting or from the first row
of an arbitrary `tabular`. Use explicit accessible tables. Keep every complete
cell in braces and finish every row with `\tablerowend` before `\\`.

```latex
\begin{accessibleTable}[title={Enrollment},summary={Sample sizes by study arm},
                         header-rows=1,first-column-headers=true]
\begin{accessibletabular}{lr}
\tablecell{Arm} & \tablecell{Number} \tablerowend \\
\tablecell{Control} & \tablecell{150} \tablerowend \\
\tablecell{Treatment} & \tablecell{155} \tablerowend \\
\end{accessibletabular}
\end{accessibleTable}
```

`header-rows` defaults to 1. In those rows `\tablecell` creates column headers;
`first-column-headers=true` makes subsequent first-column cells row headers.
Otherwise cells are `TD`. Use `header-rows=0` when no complete header row exists.
`\tablehead[column]{...}` and `\tablehead[row]{...}` explicitly declare scope;
`\tablehead{...}` chooses column scope in header rows and row scope thereafter.
Options reset for each `accessibleTable`. Lowercase `accessibletable` is an alias.
`title` is a structure title, not replacement text for the table. `summary` is a
Table summary attribute. Neither is a visible caption.

Standard `booktabs` rules work between annotated rows. Merged cells, nested tables,
complex header associations, and longtable are not automatically handled. Split
complex tables into simple tables, or provide an accessible alternative. Do not
wrap a table in `accessibleTable` and leave its cells unannotated.

## Mathematics, code, and footnotes

```latex
The mean is \AccessibleMath{the sum of x sub i divided by n}
  {$\bar{x}=\frac{1}{n}\sum_i x_i$}.
```

`\AccessibleMath` accepts an inline math expression including its normal math
delimiters and supplies a Formula alternative. It does not derive speech from
TeX or provide MathML navigation. Ordinary `$...$` and display equations retain
normal rendering, but reliable spoken mathematics needs authored descriptions
or an accessible companion explanation. Do not claim automatic math accessibility.

Fragile `listings` frames preserve code text. Check punctuation, indentation,
and reading order using the PDF reader and screen reader used by students.
Footnote text remains tagged and punctuation after a footnote remains in the
reading structure. This does not supply a bidirectional note-reference navigation
system.

## Reading order

Body content follows source order: left column then right column, with frame
headings moved first in structure order. Blocks have level-two headings.
Lists have `L > LI > Lbl + LBody` structure; description lists are included.
Each overlay page repeats its currently visible content intentionally. Check that
its structure does not expose future reveals. Handouts are often easier to read.

## Contrast and layout

`accessible-colors=true` adjusts alerted text, alert-block text/background, and
Boadilla-style footer colors. It is not a Wong palette and does not inspect or
repair arbitrary theme, image, chart, syntax-highlighting, or author colors.
There is no `accessible-colors=wong` option. The preset's tested pairs exceed
4.5:1; assess all actual foreground/background combinations independently.
Color must not be the only cue. Check font size, clipping, labels, line breaks,
and projection readability. A tagged PDF can still be visually inaccessible.

## Before distribution

Review meaningful document/slide titles, all informative graphics, table header
associations, math alternatives, reading order, and links. Inspect every page at
normal viewing size. Use institutional checking tools and assistive technology;
a successful LaTeX run or this repository's tests is not certification.
