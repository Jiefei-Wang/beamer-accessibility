from __future__ import annotations

import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image
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


def collect(node, roles: Counter[str], mcrs: list[tuple[int, str]]) -> None:
    node = object_value(node)
    if not isinstance(node, dict):
        return
    if "/S" in node:
        roles[str(node["/S"])] += 1
    if "/MCID" in node:
        mcrs.append((int(node["/MCID"]), str(node.get("/Pg"))))
    for kid in children(node):
        collect(kid, roles, mcrs)


def inspect_tree(
    pdf_path: Path,
    expected_roles: Counter[str],
    expected_frame_children: list[str] | None = None,
    tree_checker: Callable[[dict], None] | None = None,
) -> None:
    reader = PdfReader(pdf_path)
    root = object_value(reader.trailer["/Root"])
    if "/StructTreeRoot" not in root:
        raise AssertionError(f"{pdf_path.name}: missing StructTreeRoot")
    structure_root = object_value(root["/StructTreeRoot"])
    document = object_value(structure_root["/K"])
    if str(document.get("/S")) != "/Document":
        raise AssertionError(f"{pdf_path.name}: root child is not Document")

    roles: Counter[str] = Counter()
    mcrs: list[tuple[int, str]] = []
    collect(document, roles, mcrs)
    if roles != expected_roles:
        raise AssertionError(f"{pdf_path.name}: roles {dict(roles)} != {dict(expected_roles)}")
    if len(mcrs) != len(set(mcrs)):
        raise AssertionError(f"{pdf_path.name}: duplicate page/MCID references ({len(mcrs)} total, {len(set(mcrs))} unique)")

    frame = object_value(children(document)[0])
    if expected_frame_children is not None:
        frame_roles = [
            get_struct_tag(kid)
            for kid in children(frame)
            if get_struct_tag(kid) is not None
        ]
        if frame_roles != expected_frame_children:
            raise AssertionError(
                f"{pdf_path.name}: frame children {frame_roles} != {expected_frame_children}"
            )

    if tree_checker is not None:
        tree_checker(frame)


def check_list_structure(frame_node: dict, expected_item_count: int, expected_body_p_counts: list[int] | None = None) -> None:
    """Verifies that L -> LI -> (Lbl, LBody -> P) is correctly structured."""
    frame_kids = [k for k in children(frame_node) if get_struct_tag(k) is not None]
    lists = [k for k in frame_kids if get_struct_tag(k) == "/L"]
    if not lists:
        raise AssertionError("No /L structure found in frame")
    list_node = object_value(lists[0])
    items = [k for k in children(list_node) if get_struct_tag(k) == "/LI"]
    if len(items) != expected_item_count:
        raise AssertionError(f"Expected {expected_item_count} items in list, got {len(items)}")

    if expected_body_p_counts is None:
        expected_body_p_counts = [1] * expected_item_count

    for i, (item, expected_p_count) in enumerate(zip(items, expected_body_p_counts)):
        item_kids = [k for k in children(item) if get_struct_tag(k) is not None]
        item_tags = [get_struct_tag(k) for k in item_kids]
        if item_tags != ["/Lbl", "/LBody"]:
            raise AssertionError(f"Item {i} children {item_tags} != ['/Lbl', '/LBody']")
        lbl_node = item_kids[0]
        lbody_node = item_kids[1]
        body_p_nodes = [k for k in children(lbody_node) if get_struct_tag(k) == "/P"]
        if len(body_p_nodes) != expected_p_count:
            raise AssertionError(f"Item {i} LBody expected {expected_p_count} /P, got {len(body_p_nodes)}")


def render(pdf_path: Path, destination: Path) -> list[Path]:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    subprocess.run(
        ["pdftoppm", "-r", "300", "-png", str(pdf_path), str(destination / "page")],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return sorted(destination.glob("page-*.png"))


def compare_pixels(baseline: Path, tagged: Path, work: Path) -> None:
    baseline_pages = render(baseline, work / f"{baseline.stem}-png")
    tagged_pages = render(tagged, work / f"{tagged.stem}-png")
    if len(baseline_pages) != len(tagged_pages):
        raise AssertionError(f"page-count mismatch: {baseline.name} vs {tagged.name}")
    for page, (baseline_png, tagged_png) in enumerate(zip(baseline_pages, tagged_pages), 1):
        baseline_pixels = np.array(Image.open(baseline_png).convert("RGB"))
        tagged_pixels = np.array(Image.open(tagged_png).convert("RGB"))
        differing = np.any(baseline_pixels != tagged_pixels, axis=2)
        if differing.any():
            raise AssertionError(
                f"{tagged.name} page {page}: {int(differing.sum())} differing pixels"
            )


def compare_text(baseline: Path, tagged: Path) -> None:
    base_reader = PdfReader(baseline)
    tag_reader = PdfReader(tagged)
    base_text = "".join(p.extract_text() for p in base_reader.pages).strip()
    tag_text = "".join(p.extract_text() for p in tag_reader.pages).strip()
    if base_text != tag_text:
        raise AssertionError(
            f"{tagged.name} text mismatch:\nBASELINE:\n{base_text}\nTAGGED:\n{tag_text}"
        )


@dataclass
class FixtureSpec:
    name: str
    roles: Counter[str]
    frame_children: list[str] | None = None
    baseline: str | None = None
    tree_checker: Callable[[dict], None] | None = None
    check_pixels: bool = True
    check_text: bool = True


def main() -> None:
    build = Path(sys.argv[1]).resolve()

    fixtures: list[FixtureSpec] = [
        # Basic frame and paragraph fixtures
        FixtureSpec(
            name="frame-paragraph-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 1}),
            frame_children=["/frametitle", "/P"],
            baseline="frame-paragraph-baseline",
        ),
        FixtureSpec(
            name="package-only",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 1}),
            frame_children=["/frametitle", "/P"],
            baseline="package-only-baseline",
        ),
        # Single-level plain itemize fixtures
        FixtureSpec(
            name="basic-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 2}),
            frame_children=["/frametitle", "/L"],
            baseline="basic-list-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        FixtureSpec(
            name="para-before-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 3, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2}),
            frame_children=["/frametitle", "/P", "/L"],
            baseline="para-before-list-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        FixtureSpec(
            name="para-after-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 3, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2}),
            frame_children=["/frametitle", "/L", "/P"],
            baseline="para-after-list-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        FixtureSpec(
            name="para-before-after-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 4, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2}),
            frame_children=["/frametitle", "/P", "/L", "/P"],
            baseline="para-before-after-list-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        FixtureSpec(
            name="list-first-content-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 2}),
            frame_children=["/L"],
            baseline="list-first-content-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        FixtureSpec(
            name="single-item-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 1, "/Lbl": 1, "/LBody": 1, "/P": 1}),
            frame_children=["/frametitle", "/L"],
            baseline="single-item-list-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=1),
        ),
        FixtureSpec(
            name="multi-para-item-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 3}),
            frame_children=["/frametitle", "/L"],
            baseline="multi-para-item-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2, expected_body_p_counts=[2, 1]),
        ),
        FixtureSpec(
            name="inline-formatting-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 2}),
            frame_children=["/frametitle", "/L"],
            baseline="inline-formatting-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        # Nested itemize fixtures (v0.5)
        FixtureSpec(
            name="nested-itemize-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 2, "/LI": 4, "/Lbl": 4, "/LBody": 4, "/P": 4}),
            frame_children=["/frametitle", "/L"],
            baseline="nested-itemize-baseline",
        ),
        FixtureSpec(
            name="nested-itemize-3level-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 3, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            frame_children=["/frametitle", "/L"],
            baseline="nested-itemize-3level-baseline",
        ),
        # Enumerate and mixed nesting fixtures (v0.5)
        FixtureSpec(
            name="basic-enumerate-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            frame_children=["/frametitle", "/L"],
            baseline="basic-enumerate-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=3),
        ),
        FixtureSpec(
            name="nested-enumerate-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 2, "/LI": 4, "/Lbl": 4, "/LBody": 4, "/P": 4}),
            frame_children=["/frametitle", "/L"],
            baseline="nested-enumerate-baseline",
        ),
        FixtureSpec(
            name="mixed-itemize-enumerate-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 4, "/LI": 7, "/Lbl": 7, "/LBody": 7, "/P": 7}),
            frame_children=["/frametitle", "/L", "/L"],
            baseline="mixed-itemize-enumerate-baseline",
        ),
        FixtureSpec(
            name="enumerate-inline-formatting-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 2}),
            frame_children=["/frametitle", "/L"],
            baseline="enumerate-inline-formatting-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        FixtureSpec(
            name="enumerate-multi-para-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 3}),
            frame_children=["/frametitle", "/L"],
            baseline="enumerate-multi-para-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2, expected_body_p_counts=[2, 1]),
        ),
        # Unsupported fallback fixtures
        FixtureSpec(
            name="unsupported-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1}),
            frame_children=["/frametitle"],
            baseline="unsupported-list-baseline",
        ),
        FixtureSpec(
            name="unsupported-overlay-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2}),
            baseline="unsupported-overlay-list-baseline",
        ),
    ]

    print(f"Running verification on {len(fixtures)} fixtures...")
    for spec in fixtures:
        tagged_pdf = build / f"{spec.name}.pdf"
        if not tagged_pdf.exists():
            raise FileNotFoundError(f"Missing PDF: {tagged_pdf}")

        inspect_tree(tagged_pdf, spec.roles, spec.frame_children, spec.tree_checker)

        if spec.baseline:
            baseline_pdf = build / f"{spec.baseline}.pdf"
            if not baseline_pdf.exists():
                raise FileNotFoundError(f"Missing baseline PDF: {baseline_pdf}")

            if spec.check_text:
                compare_text(baseline_pdf, tagged_pdf)

            if spec.check_pixels:
                compare_pixels(baseline_pdf, tagged_pdf, build)

        print(f"  [OK] {spec.name}")

    print("ALL TESTS PASSED: structure assertions, text identity, and 300-DPI pixel regressions.")


if __name__ == "__main__":
    main()


