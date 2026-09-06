"""Behavioral regressions that tag counts alone cannot establish."""
from pathlib import Path
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, DecodedStreamObject, DictionaryObject
from verify_at import (children, object_value, validate_content_stream_coverage,
                       validate_pdf_accessibility, validate_link_annotations)
from verify import compare_pixels, compare_text


def nodes(reader, role):
    found = []
    def walk(node):
        node = object_value(node)
        if isinstance(node, dict):
            if node.get('/S') == role:
                found.append(node)
            for child in children(node):
                walk(child)
    walk(reader.trailer['/Root']['/StructTreeRoot'])
    return found


def checked(path):
    content = {}
    streams = validate_content_stream_coverage(path, content)
    structure = validate_pdf_accessibility(path, content)
    links = validate_link_annotations(path)
    assert not streams['errors'] + structure['errors'] + links['errors'], (path, streams, structure, links)
    return PdfReader(path), content


def main():
    out = Path(sys.argv[1]).resolve()
    r, content = checked(out/'decorative-table-tagged.pdf')
    assert not nodes(r, '/Table') and not nodes(r, '/TH') and not nodes(r, '/TD')
    assert any('Meaningfulparagraph' in ''.join(v) for v in content.values())
    r, content = checked(out/'center-in-list-tagged.pdf')
    spoken = ''.join(''.join(v) for v in content.values())
    assert '/home/u12345678/ta01-03.xlsx' in spoken and 'C:/BIOS6485/ta01-03.xlsx' in spoken
    r, text = checked(out/'pause-paragraphs-tagged.pdf')
    assert not any('Secondsection' in ''.join(v) for (page, _), v in text.items() if page == 0)
    assert any('Secondsection' in ''.join(v) for (page, _), v in text.items() if page == 1)
    r, _ = checked(out/'figure-reveal-tagged.pdf')
    figures = nodes(r, '/Figure')
    assert len(figures) == 1 and figures[0]['/Alt'] == 'Revealed image'
    assert object_value(children(figures[0])[0])['/Pg'].indirect_reference == r.pages[1].indirect_reference
    r, _ = checked(out/'native-tikz-tagged.pdf')
    assert [f['/Alt'] for f in nodes(r, '/Figure')] == ['Bar heights are two and three.']
    r, _ = checked(out/'figure-options-tagged.pdf')
    assert [f['/Alt'] for f in nodes(r, '/Figure')] == ['Meaningful image', 'A composite figure with one image']
    r, _ = checked(out/'semantic-features-tagged.pdf')
    first, second = nodes(r, '/Table')
    assert first['/T'] == 'Measurements' and '/Alt' not in first
    assert object_value(first['/A'])['/Summary'] == 'Groups and sample sizes'
    assert not second.get('/T') and '/A' not in second
    assert [object_value(n['/A'])['/Scope'] for n in nodes(r, '/TH')] == ['/Column','/Column','/Row','/Column','/Column']
    assert nodes(r, '/Formula')[0]['/Alt'] == 'the sum of x sub i divided by n'
    r, _ = checked(out/'titlepage-tagged.pdf')
    assert len(nodes(r, '/frametitle')) == 2
    assert r.outline[0]['/Title'] == 'Statistical distributions'
    assert r.get_destination_page_number(r.outline[0]) == 0
    r, _ = checked(out/'bookmarks-check-tagged.pdf')
    assert [r.get_destination_page_number(n) for n in r.outline] == [0, 1, 2]
    r, _ = checked(out/'links-tagged.pdf')
    assert validate_link_annotations(out/'links-tagged.pdf')['structured_links'] == 2
    # Marked-content boundaries can prevent cross-boundary font kerning; pypdf
    # may infer an extra space before punctuation. Require every nonspace character.
    baseline_text = ''.join(page.extract_text() or '' for page in PdfReader(out/'links-baseline.pdf').pages)
    tagged_text = ''.join(page.extract_text() or '' for page in r.pages)
    assert ''.join(baseline_text.split()) == ''.join(tagged_text.split())

    # Renaming an invalid PDF must not hide its missing alternative text.
    writer = PdfWriter(clone_from=out/'image-without-alt-tagged.pdf')
    mutated = out/'validator-mutation.pdf'
    writer.write(mutated)
    report = validate_pdf_accessibility(mutated,{})
    assert any('missing required non-empty /Alt' in e for e in report['errors'])
    assert any("no meaningful PDF title" in e for e in validate_pdf_accessibility(mutated, {}, require_title=True)["errors"])
    # pypdf BooleanObject(False) is truthy in Python; validate its actual value.
    writer = PdfWriter(clone_from=out/'titlepage-tagged.pdf')
    writer.root_object['/MarkInfo'][NameObject('/Marked')] = BooleanObject(False)
    writer.root_object['/ViewerPreferences'][NameObject('/DisplayDocTitle')] = BooleanObject(False)
    writer.write(mutated)
    report = validate_pdf_accessibility(mutated,{})
    assert any('/Marked true' in e for e in report['errors'])
    assert any('/DisplayDocTitle true' in e for e in report['errors'])

    # Text inside an untagged Form inherits the enclosing Figure marked content.
    writer = PdfWriter()
    page = writer.add_blank_page(width=100,height=100)
    form = DecodedStreamObject()
    form.set_data(b'BT (inside form) Tj ET')
    form[NameObject('/Subtype')] = NameObject('/Form')
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/XObject'): DictionaryObject({NameObject('/Fm'):writer._add_object(form)})})
    stream = DecodedStreamObject(); stream.set_data(b'/Figure <</MCID 0>> BDC /Fm Do EMC')
    page[NameObject('/Contents')] = writer._add_object(stream)
    writer.write(mutated)
    content = {}; report = validate_content_stream_coverage(mutated,content)
    assert not report['errors'] and 'inside form' in ''.join(content[(0,0)])
    mutated.unlink()
    print('Behavioral regressions passed: reveals, figures, tables, math, titles, links, and validator negative controls.')

if __name__ == '__main__':
    main()
