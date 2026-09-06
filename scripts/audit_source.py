"""Read-only source reminders for the supported course syntax; not a TeX parser."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path


def strip_comments(source):
    return re.sub(r'(?<!\\)%[^\n]*', lambda m: ' ' * len(m[0]), source)


def audit(path):
    source = strip_comments(path.read_text(encoding='utf-8-sig'))
    findings = []
    def add(match, kind, detail):
        findings.append({'file': str(path), 'line': source.count('\n', 0, match.start()) + 1,
                         'kind': kind, 'detail': detail})
    # Literal source checks; macro-generated content still requires PDF inspection.
    for match in re.finditer(r'\\includegraphics\*?\s*(\[[\s\S]*?\])?\s*\{([^{}]+)\}', source):
        options = match[1] or ''
        if not re.search(r'(?:alt|alttext)\s*=\s*\{\s*\S', options) and not re.search(r'(?:decorative|artifact)\s*=\s*true', options):
            add(match, 'image-description', f'Provide meaningful alt text for {match[2]}.')
    for match in re.finditer(r'\\begin\{tabular\*?\}', source):
        add(match, 'table-semantics', 'Review headers and migrate data cells to accessible table markup; mark layout-only material appropriately.')
    for match in re.finditer(r'\\begin\{tikzpicture\}\s*(\[[\s\S]*?\])?', source):
        options = match[1] or ''
        if not re.search(r'(?:alt|alttext)\s*=', options) and not re.search(r'decorative\s*=\s*true', options):
            add(match, 'diagram-description', 'Provide a native TikZ alt option or an enclosing accessibleFigure description.')
    for match in re.finditer(r'\\(?:tiny|scriptsize)\b', source):
        add(match, 'manual-legibility', 'Inspect the rendered text size and contrast at normal viewing distance.')
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    files = sorted(args.source.rglob('*.tex')) if args.source.is_dir() else [args.source]
    if not files:
        parser.error('No TeX sources found')
    findings = [item for path in files for item in audit(path)]
    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        print('Source reminders (heuristic; inspect compiled PDF and macro definitions):')
        for item in findings:
            print(f"{item['file']}:{item['line']}: [{item['kind']}] {item['detail']}")
        print(f'{len(findings)} reminders across {len(files)} source files.')

if __name__ == '__main__':
    main()
