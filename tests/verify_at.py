from __future__ import annotations

import sys
import argparse
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


def number_tree(node):
    """Resolve a PDF number tree, including trees split into /Kids."""
    node = object_value(node)
    if not isinstance(node, dict):
        return {}
    values = list(node.get("/Nums", []))
    result = {int(values[i]): values[i + 1] for i in range(0, len(values) - 1, 2)}
    for kid in node.get("/Kids", []):
        result.update(number_tree(kid))
    return result


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
    resources=None,
    inherited_stack=None,
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
    mc_stack: list[dict] = list(inherited_stack or [])
    initial_depth = len(mc_stack)
    resources = object_value(resources or {})

    for operands, op in cs.operations:
        if op == b"BMC":
            tag = str(operands[0]) if operands else "Unknown"
            is_art = "Artifact" in tag
            mc_stack.append({"tag": tag, "mcid": None, "is_artifact": is_art})

        elif op == b"BDC":
            tag = str(operands[0]) if operands else "Unknown"
            props = object_value(operands[1]) if len(operands) > 1 else {}
            if isinstance(props, str):
                props = object_value(object_value(resources.get("/Properties", {})).get(props, {}))
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
                res = resources
                xobjs = object_value(res.get("/XObject", {})) if isinstance(res, dict) else {}
                if isinstance(xobjs, dict) and xobj_name in xobjs:
                    xobj = object_value(xobjs[xobj_name])
                    if isinstance(xobj, dict) and xobj.get("/Subtype") == "/Form":
                        obj_id = id(xobj)
                        if obj_id not in visited_forms:
                            visited_forms.add(obj_id)
                            parse_stream_operations(xobj, reader, page_idx, mcid_text_map, report, visited_forms,
                                                    xobj.get("/Resources", resources), mc_stack)
                            visited_forms.remove(obj_id)

    if len(mc_stack) != initial_depth:
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
        parse_stream_operations(contents, reader, page_idx, mcid_text_map, report, resources=page.get("/Resources", {}))

    return report


def validate_pdf_accessibility(pdf_path: Path, mcid_text_map: dict[tuple[int, int], list[str]], *, require_title: bool = False) -> dict:
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
        "warnings": [],
        "errors": [],
    }

    marked = object_value(root.get("/MarkInfo", {}))
    if marked.get("/Marked") != True:
        report["errors"].append("Catalog does not declare tagged content (/Marked true)")
    for index, page in enumerate(reader.pages):
        if page.get("/Tabs") != "/S":
            report["errors"].append(f"Page {index + 1}: tab order must follow structure (/Tabs /S)")
    if not str((reader.metadata or {}).get("/Title", "")).strip():
        report["errors" if require_title else "warnings"].append("Document has no meaningful PDF title; set \\title{...} or pdftitle")

    # 1. Catalog /Lang
    lang = root.get("/Lang")
    report["catalog_lang"] = str(lang) if lang else None
    if not lang:
        report["errors"].append("Catalog missing /Lang attribute")

    # 2. ViewerPreferences /DisplayDocTitle
    viewer_prefs = object_value(root.get("/ViewerPreferences"))
    if viewer_prefs and viewer_prefs.get("/DisplayDocTitle") == True:
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

    parent_tree = number_tree(struct_root.get("/ParentTree"))

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
            if parent_node is not None and object_value(node.get("/P")) is not parent_node:
                report["errors"].append(f"Structure at {path} has incorrect parent pointer")

            if tag == "/Figure":
                alt = node.get("/Alt")
                alt_str = str(alt).strip() if alt else None
                report["figures"].append({"path": path, "alt": alt_str})
                if not alt_str:
                    report["errors"].append(f"Figure at {path} missing required non-empty /Alt attribute")

            elif tag == "/Formula":
                if not str(node.get("/Alt", "")).strip():
                    report["errors"].append(f"Formula at {path} missing spoken alternative text")

            elif tag == "/TH":
                attrs = object_value(node.get("/A", []))
                attrs = attrs if isinstance(attrs, list) else [attrs]
                scopes = [object_value(a).get("/Scope") for a in attrs if isinstance(object_value(a), dict)]
                if not any(scope in ("/Row", "/Column", "/Both") for scope in scopes):
                    report["errors"].append(f"Table header at {path} lacks row/column scope")

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
                pg_idx = page_ref_to_idx.get(str(node.get("/Pg")))
            if pg_idx is None:
                report["errors"].append(f"MCR at {path} references an unknown page")
                return
            mcrs.append((mcid, pg_idx, path))
            key_number = reader.pages[pg_idx].get("/StructParents")
            owners = object_value(parent_tree.get(key_number, []))
            if not isinstance(owners, list) or mcid >= len(owners) or mcid < 0:
                report["errors"].append(f"ParentTree has no entry for page {pg_idx + 1}, MCID {mcid}")
            elif object_value(owners[mcid]) is not parent_node:
                report["errors"].append(f"ParentTree owner mismatch at page {pg_idx + 1}, MCID {mcid}")

            # Verify that this MCID actually has content in the stream if it's a paragraph or list body
            key = (pg_idx, mcid)
            if key not in mcid_text_map:
                has_child_struct = False
                if parent_node is not None:
                    has_child_struct = any(get_struct_tag(k) in ("/Figure", "/Table", "/L", "/block") for k in children(parent_node))
                if not has_child_struct:
                    if tag in ("/P", "/LBody") or (tag is None and ("/LBody" in path or "/P" in path)):
                        report["warnings"].append(
                            f"Empty marked-content record: {path} references (page {pg_idx + 1}, MCID {mcid}) but stream has 0 text operations"
                        )

        for idx, kid in enumerate(children(node)):
            kid_tag = get_struct_tag(kid) or f"kid[{idx}]"
            walk(kid, f"{path}/{kid_tag}", node)

    walk(document, "/Document", struct_root)

    report["mcid_count"] = len(mcrs)
    unique_mcrs = {(m[0], m[1]) for m in mcrs}
    report["unique_mcid_count"] = len(unique_mcrs)
    if len(mcrs) != len(unique_mcrs):
        report["errors"].append(f"Duplicate (MCID, Page) pairs: {len(mcrs)} total vs {len(unique_mcrs)} unique")

    referenced = {(page, mcid) for mcid, page, _ in mcrs}
    for key in mcid_text_map:
        if key not in referenced:
            report["errors"].append(f"Content at page {key[0] + 1}, MCID {key[1]} has no structure-tree owner")
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

    parent_tree = number_tree(reader.trailer["/Root"].get("/StructTreeRoot", {}).get("/ParentTree"))
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
                    owner = object_value(parent_tree.get(struct_parent))
                    if not isinstance(owner, dict) or owner.get("/S") != "/Link":
                        report["errors"].append(f"Page {page_num + 1}: Link ParentTree entry is missing or not a Link")
                    elif not any(object_value(k).get("/Type") == "/OBJR" and object_value(object_value(k).get("/Obj")) is annot
                                 for k in children(owner) if isinstance(object_value(k), dict)):
                        report["errors"].append(f"Page {page_num + 1}: Link structure lacks matching annotation OBJR")
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
    parser = argparse.ArgumentParser(description="Partial PDF structural checks, not accessibility certification")
    parser.add_argument("directory", nargs="?", type=Path, default=Path(__file__).parent/"fixtures"/"out")
    parser.add_argument("--require-title", action="store_true", help="Treat missing document titles as errors for deliverable PDFs")
    args = parser.parse_args()
    test_dir = args.directory.resolve()
    tagged_files = sorted(test_dir.glob("*-tagged.pdf"))
    if not tagged_files:
        tagged_files = sorted(test_dir.glob("*.pdf"))
    if not tagged_files:
        raise SystemExit("No PDFs found: refusing to report an empty validation run as success")

    print(f"Validating PDF structure, content stream coverage, and link annotations for {len(tagged_files)} PDFs in {test_dir.name}...")
    failures = 0
    for pdf_file in tagged_files:
        mcid_text_map: dict[tuple[int, int], list[str]] = {}
        cs_report = validate_content_stream_coverage(pdf_file, mcid_text_map)
        struct_report = validate_pdf_accessibility(pdf_file, mcid_text_map, require_title=args.require_title)
        link_report = validate_link_annotations(pdf_file)

        all_errors = struct_report["errors"] + cs_report["errors"] + link_report["errors"]
        # This fixture deliberately omits alt text: assert detection rather than exempting the PDF.
        if pdf_file.name == "image-without-alt-tagged.pdf":
            expected = [e for e in all_errors if "missing required non-empty /Alt" in e]
            if len(expected) != 1:
                all_errors.append("Expected exactly one missing-alt diagnostic")
            else:
                all_errors.remove(expected[0])
        for warning in struct_report["warnings"]:
            print(f"  [WARN] {pdf_file.name}: {warning}")
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
        print(f"\nSUCCESS: All {len(tagged_files)} files passed structural, content-stream coverage, and link checks (not accessibility certification).")


if __name__ == "__main__":
    main()
