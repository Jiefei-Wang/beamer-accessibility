%% Thin convenience wrapper. Upstream Beamer remains the visual engine.
\NeedsTeXFormat{LaTeX2e}[2025-06-01]
\ProvidesClass{beamer-accessibility}[2026/09/01 v1.0 Accessible Beamer wrapper with early PDF management]
\RequirePackage{iftex}
\ifxetex
  \ClassError{beamer-accessibility}
    {XeLaTeX is not supported for tagged PDF presentations}
    {beamer-accessibility relies on direct PDF management and tagpdf structures that^^J%
     are not supported by the XeTeX/xdvipdfmx backend.^^J%
     Please compile using pdflatex (recommended) or lualatex.}
\fi
\RequirePackage{pdfmanagement}
\newif\ifba@handout
\ba@handoutfalse
\DeclareOption{overlay-policy=handout}{\ba@handouttrue\PassOptionsToClass{handout}{beamer}\PassOptionsToPackage{overlay-policy=handout}{beamer-accessibility}}
\DeclareOption{overlay-policy=pages}{\PassOptionsToPackage{overlay-policy=pages}{beamer-accessibility}}
\DeclareOption{overlay-policy=strict}{\PassOptionsToPackage{overlay-policy=strict}{beamer-accessibility}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{beamer}\PassOptionsToPackage{\CurrentOption}{beamer-accessibility}}
\ProcessOptions\relax
\LoadClass{beamer}
\RequirePackage{beamer-accessibility}
