%% Thin convenience wrapper. Upstream Beamer remains the visual engine.
\NeedsTeXFormat{LaTeX2e}[2025-06-01]
\ProvidesClass{beamer-accessibility}[2026/09/01 v0.9 Low-level tagged Beamer wrapper]
\RequirePackage{pdfmanagement}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{beamer}\PassOptionsToPackage{\CurrentOption}{beamer-accessibility}}
\ProcessOptions\relax
\LoadClass{beamer}
\RequirePackage{beamer-accessibility}


