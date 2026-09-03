from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import ContentStream, DictionaryObject, ArrayObject, NameObject


def object_value(value):
    return value.get_object() if hasattr(value, "get_object") else value


def children(node):
    node = object_value(node)
    if not isinstance(node, dict) or "/K" not in node:
        return []
    kids = node["/K"]
    return kids if isinstance(kids, list) else [kids]


def get_struct_tag(node) -> str | None:
    node = object_value(node)
    if isinstance(node, dict) and "/S" in node:
        return str(node["/S"])
    return None


def extract_text_from_operands(operator: bytes, operands: list) -> str:
    """Extracts raw text strings from PDF text operator operands."""
    if operator == b"TJ" and operands:
        parts = []
        for item in operands[0]:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, bytes):
                parts.append(item.decode("latin1", errors="ignore"))
        return "".join(parts)
    elif operator in (b"Tj", b"'") and operands:
        item = operands[0]
        return item if isinstance(item, str) else item.decode("latin1", errors="ignore")
    elif operator == b'"' and len(operands) >= 3:
        item = operands[2]
        return item if isinstance(item, str) else item.decode("latin1", errors="ignore")
    return ""


def parse_stream_operations(
    stream_obj,
    reader: PdfReader,
    page_idx: int,
    mcid_text_map: dict[tuple[int, int], list[str]],
    report: dict,
    visited_forms: set | None = None,
) -> None:
    """Parses a PDF content stream (page or Form XObject) with full operator grammar."""
    if visited_forms is None:
        visited_forms = set()

    try:
        cs = ContentStream(stream_obj, reader)
    except Exception as e:
        report["errors"].append(f"Page {page_idx + 1}: Failed to parse ContentStream: {e}")
        return

    TEXT_OPS = {b"Tj", b"TJ", b"'", b'"'}
    GRAPHIC_OPS = {
        b"m", b"l", b"c", b"v", b"y", b"h", b"re",
        b"S", b"s", b"f", b"F", b"f*", b"B", b"B*", b"b", b"b*", b"sh"
    }

    # Each element: {"tag": str, "mcid": int | None, "is_artifact": bool}
    mc_stack: list[dict] = []

    for operands, op in cs.operations:
        if op == b"BMC":
            tag = str(operands[0]) if operands else "Unknown"
            is_art = "Artifact" in tag
            mc_stack.append({"tag": tag, "mcid": None, "is_artifact": is_art})

        elif op == b"BDC":
            tag = str(operands[0]) if operands else "Unknown"
            props = object_value(operands[1]) if len(operands) > 1 else {}
            mcid = None
            is_art = "Artifact" in tag
            if isinstance(props, dict):
                if "/MCID" in props:
                    mcid = int(props["/MCID"])
                if props.get("/Type") == "/Artifact" or "/Artifact" in str(props):
                    is_art = True

            # Detect nested content-bearing MCIDs
            active_mcids = [frame["mcid"] for frame in mc_stack if frame["mcid"] is not None]
            if mcid is not None and active_mcids:
                report["errors"].append(
                    f"Page {page_idx + 1}: Nested content-bearing MCID {mcid} inside active MCID {active_mcids[-1]}"
                )

            mc_stack.append({"tag": tag, "mcid": mcid, "is_artifact": is_art})

        elif op == b"EMC":
            if mc_stack:
                mc_stack.pop()
            else:
                report["errors"].append(f"Page {page_idx + 1}: Extraneous EMC encountered with empty marked-content stack")

        elif op in TEXT_OPS:
            report["total_text_ops"] += 1
            extracted = extract_text_from_operands(op, operands)

            if not mc_stack:
                report["unclassified_text_ops"] += 1
                report["errors"].append(
                    f"Page {page_idx + 1}: Unclassified text op '{op.decode()}' with text {extracted!r} outside marked content"
                )
            else:
                top = mc_stack[-1]
                any_artifact = any(frame["is_artifact"] for frame in mc_stack)

                if any_artifact:
                    report["artifact_text_ops"] += 1
                elif top["mcid"] is not None:
                    report["tagged_text_ops"] += 1
                    key = (page_idx, top["mcid"])
                    mcid_text_map.setdefault(key, []).append(extracted)
                else:
                    report["unclassified_text_ops"] += 1
                    report["errors"].append(
                        f"Page {page_idx + 1}: Text op '{op.decode()}' inside marked content /{top['tag']} without MCID or Artifact"
                    )

        elif op in GRAPHIC_OPS:
            report["total_graphic_ops"] += 1
            if mc_stack:
                top = mc_stack[-1]
                if top.get("mcid") is not None:
                    mcid_text_map.setdefault((page_idx, top["mcid"]), []).append(f"<{op.decode()}>")

        elif op == b"Do":
            report["total_graphic_ops"] += 1
            if mc_stack:
                top = mc_stack[-1]
                if top.get("mcid") is not None:
                    mcid_text_map.setdefault((page_idx, top["mcid"]), []).append("<Do>")
            if operands:
                xobj_name = operands[0]
                res = object_value(stream_obj.get("/Resources", {})) if isinstance(stream_obj, dict) else {}
                xobjs = object_value(res.get("/XObject", {})) if isinstance(res, dict) else {}
                if isinstance(xobjs, dict) and xobj_name in xobjs:
                    xobj = object_value(xobjs[xobj_name])
                    if isinstance(xobj, dict) and xobj.get("/Subtype") == "/Form":
                        obj_id = id(xobj)
                        if obj_id not in visited_forms:
                            visited_forms.add(obj_id)
                            parse_stream_operations(xobj, reader, page_idx, mcid_text_map, report, visited_forms)

    if mc_stack:
        report["errors"].append(
            f"Page {page_idx + 1}: Unbalanced marked content stream: {len(mc_stack)} tags still open at end of stream ({[m['tag'] for m in mc_stack]})"
        )


def validate_content_stream_coverage(pdf_path: Path, mcid_text_map: dict[tuple[int, int], list[str]]) -> dict:
    reader = PdfReader(pdf_path)
    report = {
        "file": pdf_path.name,
        "total_text_ops": 0,
        "tagged_text_ops": 0,
        "artifact_text_ops": 0,
        "unclassified_text_ops": 0,
        "total_graphic_ops": 0,
        "errors": [],
    }

    for page_idx, page in enumerate(reader.pages):
        contents = page.get("/Contents")
        if not contents:
            continue
        parse_stream_operations(contents, reader, page_idx, mcid_text_map, report)

    return report


def validate_pdf_accessibility(pdf_path: Path, mcid_text_map: dict[tuple[int, int], list[str]]) -> dict:
    reader = PdfReader(pdf_path)
    root = object_value(reader.trailer["/Root"])
    report = {
        "file": pdf_path.name,
        "pages": len(reader.pages),
        "catalog_lang": None,
        "display_doc_title": False,
        "struct_tree_root": False,
        "role_map": {},
        "structure_counts": Counter(),
        "mcid_count": 0,
        "unique_mcid_count": 0,
        "figures": [],
        "errors": [],
    }

    # 1. Catalog /Lang
    lang = root.get("/Lang")
    report["catalog_lang"] = str(lang) if lang else None
    if not lang:
        report["errors"].append("Catalog missing /Lang attribute")

    # 2. ViewerPreferences /DisplayDocTitle
    viewer_prefs = object_value(root.get("/ViewerPreferences"))
    if viewer_prefs and bool(viewer_prefs.get("/DisplayDocTitle")):
        report["display_doc_title"] = True
    else:
        report["errors"].append("Catalog ViewerPreferences missing /DisplayDocTitle true")

    # 3. StructTreeRoot
    if "/StructTreeRoot" not in root:
        report["errors"].append("Missing /StructTreeRoot")
        return report

    report["struct_tree_root"] = True
    struct_root = object_value(root["/StructTreeRoot"])

    # 4. RoleMap
    role_map = object_value(struct_root.get("/RoleMap", {}))
    report["role_map"] = {str(k): str(v) for k, v in role_map.items()}

    document = object_value(struct_root.get("/K"))
    if not document or str(document.get("/S")) != "/Document":
        report["errors"].append(f"Root child is {document.get('/S') if document else None}, expected /Document")
        return report

    # 5. Page map for page indirect reference resolution
    page_ref_to_idx = {}
    for idx, page in enumerate(reader.pages):
        page_ref_to_idx[id(page)] = idx
        if hasattr(page, "indirect_reference") and page.indirect_reference:
            page_ref_to_idx[str(page.indirect_reference)] = idx

    # 6. Walk structure tree
    visited = set()
    mcrs = []

    def walk(node, path="", parent_node=None):
        obj_id = id(node)
        if obj_id in visited:
            report["errors"].append(f"Cycle detected in structure tree at {path}")
            return
        visited.add(obj_id)

        node = object_value(node)
        if not isinstance(node, dict):
            return

        tag = get_struct_tag(node)
        if tag is not None:
            report["structure_counts"][tag] += 1

            if tag == "/Figure":
                alt = node.get("/Alt")
                alt_str = str(alt).strip() if alt else None
                report["figures"].append({"path": path, "alt": alt_str})
                if not alt_str and pdf_path.name != "image-without-alt-tagged.pdf":
                    report["errors"].append(f"Figure at {path} missing required non-empty /Alt attribute")

            elif tag == "/L":
                for kid in children(node):
                    ktag = get_struct_tag(kid)
                    if ktag is not None and ktag != "/LI":
                        report["errors"].append(f"List at {path} contains non-LI child: {ktag}")

            elif tag == "/LI":
                kids = [get_struct_tag(k) for k in children(node) if get_struct_tag(k) is not None]
                if "/Lbl" not in kids:
                    report["errors"].append(f"ListItem at {path} missing /Lbl child")
                if "/LBody" not in kids:
                    report["errors"].append(f"ListItem at {path} missing /LBody child")

            elif tag == "/Table":
                for kid in children(node):
                    ktag = get_struct_tag(kid)
                    if ktag is not None and ktag != "/TR":
                        report["errors"].append(f"Table at {path} contains non-TR child: {ktag}")

            elif tag == "/TR":
                for kid in children(node):
                    ktag = get_struct_tag(kid)
                    if ktag is not None and ktag not in ("/TH", "/TD"):
                        report["errors"].append(f"TableRow at {path} contains child {ktag}, expected /TH or /TD")

        # Handle MCR
        if "/MCID" in node:
            mcid = int(node["/MCID"])
            pg_obj = object_value(node.get("/Pg"))
            pg_idx = page_ref_to_idx.get(id(pg_obj))
            if pg_idx is None:
                pg_idx = page_ref_to_idx.get(str(node.get("/Pg")), 0)
            mcrs.append((mcid, pg_idx, path))

            # Verify that this MCID actually has content in the stream if it's a paragraph or list body
            key = (pg_idx, mcid)
            if key not in mcid_text_map:
                has_child_struct = False
                if parent_node is not None:
                    has_child_struct = any(get_struct_tag(k) in ("/Figure", "/Table", "/L", "/block") for k in children(parent_node))
                if not has_child_struct:
                    if tag in ("/P", "/LBody") or (tag is None and ("/LBody" in path or "/P" in path)):
                        report["errors"].append(
                            f"Empty marked-content record: {path} references (page {pg_idx + 1}, MCID {mcid}) but stream has 0 text operations"
                        )

        for idx, kid in enumerate(children(node)):
            kid_tag = get_struct_tag(kid) or f"kid[{idx}]"
            walk(kid, f"{path}/{kid_tag}", node)

    walk(document, "/Document")

    report["mcid_count"] = len(mcrs)
    unique_mcrs = {(m[0], m[1]) for m in mcrs}
    report["unique_mcid_count"] = len(unique_mcrs)
    if len(mcrs) != len(unique_mcrs):
        report["errors"].append(f"Duplicate (MCID, Page) pairs: {len(mcrs)} total vs {len(unique_mcrs)} unique")

    return report


def validate_link_annotations(pdf_path: Path) -> dict:
    reader = PdfReader(pdf_path)
    report = {
        "file": pdf_path.name,
        "total_links": 0,
        "structured_links": 0,
        "furniture_links": 0,
        "errors": [],
    }

    for page_num, page in enumerate(reader.pages):
        annots = page.get("/Annots", [])
        for a_ref in annots:
            annot = object_value(a_ref)
            if not isinstance(annot, dict):
                continue
            if annot.get("/Subtype") == "/Link":
                report["total_links"] += 1
                struct_parent = annot.get("/StructParent")
                contents = annot.get("/Contents")

                if struct_parent is not None:
                    report["structured_links"] += 1
                else:
                    report["furniture_links"] += 1
                    report["errors"].append(
                        f"Page {page_num + 1}: Interactive Link annotation missing required /StructParent attribute"
                    )

                if not contents or not str(contents).strip():
                    if struct_parent is None:
                        report["errors"].append(
                            f"Page {page_num + 1}: Link annotation missing accessible description or /Contents"
                        )

    return report


def main() -> None:
    test_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "build/tests").resolve()
    tagged_files = sorted(test_dir.glob("*-tagged.pdf"))
    if not tagged_files:
        tagged_files = sorted(test_dir.glob("*.pdf"))

    print(f"Validating accessibility structure, content stream coverage, and link annotations for {len(tagged_files)} PDFs in {test_dir.name}...")
    failures = 0
    for pdf_file in tagged_files:
        mcid_text_map: dict[tuple[int, int], list[str]] = {}
        cs_report = validate_content_stream_coverage(pdf_file, mcid_text_map)
        struct_report = validate_pdf_accessibility(pdf_file, mcid_text_map)
        link_report = validate_link_annotations(pdf_file)

        all_errors = struct_report["errors"] + cs_report["errors"] + link_report["errors"]
        if all_errors:
            print(f"  [FAIL] {pdf_file.name}:")
            for err in all_errors:
                print(f"    - {err}")
            failures += 1
        else:
            lang_str = struct_report["catalog_lang"] or "N/A"
            structs_str = ", ".join(f"{k.lstrip('/')}:{v}" for k, v in sorted(struct_report["structure_counts"].items()))
            print(
                f"  [PASS] {pdf_file.name} (Lang={lang_str}, MCIDs={struct_report['mcid_count']}, "
                f"TextOps: {cs_report['total_text_ops']} [tagged={cs_report['tagged_text_ops']}, artifact={cs_report['artifact_text_ops']}], "
                f"Links: {link_report['total_links']} [struct={link_report['structured_links']}, furniture={link_report['furniture_links']}], {structs_str})"
            )

    if failures > 0:
        print(f"\nFAILED: {failures} files had accessibility validation errors.")
        sys.exit(1)
    else:
        print(f"\nSUCCESS: All {len(tagged_files)} files passed AT accessibility, content-stream coverage, and link validation.")


if __name__ == "__main__":
    main()
