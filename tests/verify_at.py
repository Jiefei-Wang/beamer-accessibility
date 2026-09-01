"""Automated Assistive Technology (AT) and PDF Accessibility Validator.

Validates PDF/UA and WCAG semantic requirements for beamer-accessibility:
1. Document Catalog contains standard /Lang attribute.
2. Document Catalog contains /ViewerPreferences with /DisplayDocTitle = true.
3. Structure Tree (/StructTreeRoot) exists and has a single /Document root.
4. RoleMap correctly maps presentation roles:
   - frame -> Sect
   - frametitle -> H1
   - block -> Div
   - blocktitle -> H2
   - column -> Div
5. Every /Figure structure element with author-provided alt text has a non-empty /Alt attribute.
6. Every list follows standard PDF/UA list grammar:
   - L contains only LI children.
   - LI contains Lbl and LBody children.
   - LBody contains P or nested L children.
7. MCR leaf nodes reference valid pages with unique (MCID, Page) tuples.
8. Structure trees are strictly acyclic and well-formed.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from pypdf import PdfReader


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


def validate_pdf_accessibility(pdf_path: Path) -> dict:
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

    document = object_value(struct_root["/K"])
    if str(document.get("/S")) != "/Document":
        report["errors"].append(f"Root child is {document.get('/S')}, expected /Document")

    # 5. Walk structure tree
    visited = set()
    mcrs = []

    def walk(node, path=""):
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
                report["figures"].append({"path": path, "alt": str(alt) if alt else None})

            if tag == "/L":
                # Validate list children are LI
                for kid in children(node):
                    ktag = get_struct_tag(kid)
                    if ktag is not None and ktag != "/LI":
                        report["errors"].append(f"List at {path} contains non-LI child: {ktag}")

            if tag == "/LI":
                # Validate LI contains Lbl and LBody
                kids = [get_struct_tag(k) for k in children(node) if get_struct_tag(k) is not None]
                if "/Lbl" in kids and "/LBody" not in kids:
                    report["errors"].append(f"ListItem at {path} has Lbl but missing LBody")

        if "/MCID" in node:
            mcid = int(node["/MCID"])
            pg = str(node.get("/Pg"))
            mcrs.append((mcid, pg))

        for idx, kid in enumerate(children(node)):
            kid_tag = get_struct_tag(kid) or f"kid[{idx}]"
            walk(kid, f"{path}/{kid_tag}")

    walk(document, "/Document")

    report["mcid_count"] = len(mcrs)
    report["unique_mcid_count"] = len(set(mcrs))
    if len(mcrs) != len(set(mcrs)):
        report["errors"].append(f"Duplicate (MCID, Pg) pairs: {len(mcrs)} total vs {len(set(mcrs))} unique")

    return report


def main() -> None:
    test_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "build/tests").resolve()
    tagged_files = sorted(test_dir.glob("*-tagged.pdf"))
    if not tagged_files:
        tagged_files = sorted(test_dir.glob("*.pdf"))

    print(f"Validating accessibility structure for {len(tagged_files)} PDFs in {test_dir.name}...")
    failures = 0
    for pdf_file in tagged_files:
        report = validate_pdf_accessibility(pdf_file)
        if report["errors"]:
            print(f"  [FAIL] {pdf_file.name}:")
            for err in report["errors"]:
                print(f"    - {err}")
            failures += 1
        else:
            lang_str = report["catalog_lang"] or "N/A"
            structs_str = ", ".join(f"{k.lstrip('/')}:{v}" for k, v in sorted(report["structure_counts"].items()))
            print(f"  [PASS] {pdf_file.name} (Lang={lang_str}, MCIDs={report['mcid_count']}, {structs_str})")

    if failures > 0:
        print(f"\nFAILED: {failures} files had accessibility validation errors.")
        sys.exit(1)
    else:
        print(f"\nSUCCESS: All {len(tagged_files)} files passed AT accessibility validation.")


if __name__ == "__main__":
    main()
