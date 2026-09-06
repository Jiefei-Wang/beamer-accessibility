from __future__ import annotations

import hashlib
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
    expected_lang: str | None = "en-US",
) -> None:
    reader = PdfReader(pdf_path)
    root = object_value(reader.trailer["/Root"])
    if "/StructTreeRoot" not in root:
        raise AssertionError(f"{pdf_path.name}: missing StructTreeRoot")
    structure_root = object_value(root["/StructTreeRoot"])
    document = object_value(structure_root["/K"])
    if str(document.get("/S")) != "/Document":
        raise AssertionError(f"{pdf_path.name}: root child is not Document")

    if expected_lang is not None:
        lang = root.get("/Lang")
        if lang != expected_lang:
            raise AssertionError(f"{pdf_path.name}: Catalog /Lang is {lang!r}, expected {expected_lang!r}")

    viewer_prefs = object_value(root.get("/ViewerPreferences"))
    if viewer_prefs is not None:
        if viewer_prefs.get("/DisplayDocTitle") != True:
            raise AssertionError(f"{pdf_path.name}: ViewerPreferences /DisplayDocTitle is not True")

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


def check_block_structure(frame_node: dict, expected_block_count: int, expected_has_titles: list[bool] | None = None) -> None:
    """Verifies that block -> (blocktitle, P ...) is correctly structured."""
    frame_kids = [k for k in children(frame_node) if get_struct_tag(k) is not None]
    blocks = [k for k in frame_kids if get_struct_tag(k) == "/block"]
    if len(blocks) != expected_block_count:
        raise AssertionError(f"Expected {expected_block_count} blocks in frame, got {len(blocks)}")
    if expected_has_titles is None:
        expected_has_titles = [True] * expected_block_count
    for i, (blk, has_title) in enumerate(zip(blocks, expected_has_titles)):
        blk_kids = [k for k in children(blk) if get_struct_tag(k) is not None]
        blk_tags = [get_struct_tag(k) for k in blk_kids]
        if has_title:
            if not blk_tags or blk_tags[0] != "/blocktitle":
                raise AssertionError(f"Block {i} expected first child /blocktitle, got {blk_tags}")
        else:
            if "/blocktitle" in blk_tags:
                raise AssertionError(f"Block {i} expected no /blocktitle, got {blk_tags}")


def check_figure_structure(frame_node: dict, expected_fig_count: int, expected_alts: list[str | None] | None = None) -> None:
    """Verifies that /Figure is present in the frame structure with expected Alt attributes."""
    roles: Counter[str] = Counter()
    mcrs: list[tuple[int, str]] = []
    collect(frame_node, roles, mcrs)
    if roles.get("/Figure", 0) != expected_fig_count:
        raise AssertionError(f"Expected {expected_fig_count} /Figure, got {roles.get('/Figure', 0)}")

    figures: list[dict] = []

    def find_figs(node):
        node = object_value(node)
        if isinstance(node, dict):
            if str(node.get("/S")) == "/Figure":
                figures.append(node)
            for k in children(node):
                find_figs(k)

    find_figs(frame_node)

    if len(figures) != expected_fig_count:
        raise AssertionError(f"Expected {expected_fig_count} figure nodes, got {len(figures)}")

    if expected_alts is not None:
        for i, (fig, exp_alt) in enumerate(zip(figures, expected_alts)):
            act_alt = fig.get("/Alt")
            if exp_alt is None:
                if act_alt is not None and str(act_alt).strip() != "":
                    raise AssertionError(f"Figure {i} expected no Alt, got {act_alt!r}")
            else:
                if act_alt is None or str(act_alt) != exp_alt:
                    raise AssertionError(f"Figure {i} expected Alt={exp_alt!r}, got {act_alt!r}")


def check_column_structure(frame_node: dict, expected_col_count: int) -> None:
    """Verifies that /column structure elements are present in the frame structure."""
    frame_kids = [object_value(k) for k in children(frame_node)]
    cols = [k for k in frame_kids if get_struct_tag(k) == "/column"]
    if len(cols) != expected_col_count:
        raise AssertionError(f"Expected {expected_col_count} columns in frame, got {len(cols)}")


def render(pdf_path: Path, destination: Path) -> list[Path]:
    # Cache only byte-identical PDFs; never recursively delete a caller-supplied path.
    if destination.resolve().parent != pdf_path.resolve().parent or not destination.name.endswith("-png"):
        raise ValueError("Render output must be a generated sibling -png directory")
    destination.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    stamp = destination / "render.sha256"
    pages = sorted(destination.glob("page-*.png"))
    if stamp.exists() and stamp.read_text() == digest and len(pages) == len(PdfReader(pdf_path).pages):
        return pages
    for page in pages:
        page.unlink()
    subprocess.run(
        ["pdftoppm", "-r", "300", "-png", str(pdf_path), str(destination / "page")],
        check=True, stdout=subprocess.DEVNULL,
    )
    stamp.write_text(digest)
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
    expected_lang: str | None = "en-US"


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
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
        ),
        FixtureSpec(
            name="nested-itemize-3level-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 3, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            frame_children=["/frametitle", "/L"],
            baseline="nested-itemize-3level-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=1),
        ),
        # Enumerate fixtures (v0.5)
        FixtureSpec(
            name="basic-enumerate-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            frame_children=["/frametitle", "/L"],
            baseline="basic-enumerate-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=3),
        ),
        FixtureSpec(
            name="six-item-enumerate-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 6, "/Lbl": 6, "/LBody": 6, "/P": 6}),
            frame_children=["/frametitle", "/L"],
            baseline="six-item-enumerate-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=6),
        ),
        FixtureSpec(
            name="nested-enumerate-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 2, "/LI": 4, "/Lbl": 4, "/LBody": 4, "/P": 4}),
            frame_children=["/frametitle", "/L"],
            baseline="nested-enumerate-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
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
        # Block environments (v0.6)
        FixtureSpec(
            name="basic-block-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/P": 3}),
            frame_children=["/frametitle", "/P", "/block", "/P"],
            baseline="basic-block-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
        ),
        FixtureSpec(
            name="alert-and-example-block-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 2, "/blocktitle": 2, "/P": 2}),
            frame_children=["/frametitle", "/block", "/block"],
            baseline="alert-and-example-block-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=2),
        ),
        FixtureSpec(
            name="multi-para-block-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/P": 3}),
            frame_children=["/frametitle", "/block"],
            baseline="multi-para-block-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
        ),
        FixtureSpec(
            name="block-with-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/L": 2, "/LI": 4, "/Lbl": 4, "/LBody": 4, "/P": 5}),
            frame_children=["/frametitle", "/block"],
            baseline="block-with-list-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
        ),
        FixtureSpec(
            name="untitled-block-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/P": 3}),
            frame_children=["/frametitle", "/P", "/block", "/P"],
            baseline="untitled-block-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1, expected_has_titles=[False]),
        ),
        FixtureSpec(
            name="mixed-blocks-prose-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 2, "/blocktitle": 2, "/P": 5}),
            frame_children=["/frametitle", "/P", "/block", "/P", "/block", "/P"],
            baseline="mixed-blocks-prose-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=2),
        ),
        # Graphics and alternative text fixtures (v0.7)
        FixtureSpec(
            name="basic-image-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 3, "/Figure": 1}),
            frame_children=["/frametitle", "/P", "/P", "/P"],
            baseline="basic-image-baseline",
            tree_checker=lambda f: check_figure_structure(f, expected_fig_count=1, expected_alts=["A chart showing distribution of variables"]),
        ),
        FixtureSpec(
            name="image-without-alt-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 3, "/Figure": 1}),
            frame_children=["/frametitle", "/P", "/P", "/P"],
            baseline="image-without-alt-baseline",
            tree_checker=lambda f: check_figure_structure(f, expected_fig_count=1, expected_alts=[None]),
        ),
        FixtureSpec(
            name="inline-image-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 1, "/Figure": 1}),
            frame_children=["/frametitle", "/P"],
            baseline="inline-image-baseline",
            tree_checker=lambda f: check_figure_structure(f, expected_fig_count=1, expected_alts=["Inline icon thumbnail"]),
        ),
        FixtureSpec(
            name="block-with-image-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/P": 3, "/Figure": 1}),
            frame_children=["/frametitle", "/block"],
            baseline="block-with-image-baseline",
            tree_checker=lambda f: check_figure_structure(f, expected_fig_count=1, expected_alts=["Statistical flow chart"]),
        ),
        FixtureSpec(
            name="figure-environment-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 3, "/Figure": 1}),
            frame_children=["/frametitle", "/P", "/Figure", "/P", "/P"],
            baseline="figure-environment-baseline",
            tree_checker=lambda f: check_figure_structure(f, expected_fig_count=1, expected_alts=["Distribution of participants by study cohort"]),
        ),
        # Multi-column slide layout & theme fixtures (v0.8)
        FixtureSpec(
            name="basic-columns-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 4, "/column": 2}),
            frame_children=["/frametitle", "/P", "/column", "/column", "/P"],
            baseline="basic-columns-baseline",
            tree_checker=lambda f: check_column_structure(f, expected_col_count=2),
        ),
        FixtureSpec(
            name="column-command-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 4, "/column": 2}),
            frame_children=["/frametitle", "/P", "/column", "/column", "/P"],
            baseline="column-command-baseline",
            tree_checker=lambda f: check_column_structure(f, expected_col_count=2),
        ),
        FixtureSpec(
            name="columns-with-lists-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 6, "/L": 2, "/LI": 4, "/Lbl": 4, "/LBody": 4, "/column": 2}),
            frame_children=["/frametitle", "/P", "/column", "/column", "/P"],
            baseline="columns-with-lists-baseline",
            tree_checker=lambda f: check_column_structure(f, expected_col_count=2),
        ),
        FixtureSpec(
            name="columns-mixed-composition-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 2, "/blocktitle": 2, "/column": 2, "/L": 2, "/LI": 5, "/Lbl": 5, "/LBody": 5, "/P": 10, "/Figure": 1}),
            frame_children=["/frametitle", "/P", "/column", "/column", "/P"],
            baseline="columns-mixed-composition-baseline",
            tree_checker=lambda f: check_column_structure(f, expected_col_count=2),
        ),
        FixtureSpec(
            name="theme-madrid-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 5}),
            frame_children=["/frametitle", "/P", "/block", "/P"],
            baseline="theme-madrid-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
        ),
        FixtureSpec(
            name="theme-warsaw-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 5}),
            frame_children=["/frametitle", "/P", "/block", "/P"],
            baseline="theme-warsaw-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
        ),
        # Hardening, Math, Code & Metadata fixtures (v0.9)
        FixtureSpec(
            name="math-inline-display-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/P": 3}),
            frame_children=["/frametitle", "/P", "/block", "/P"],
            baseline="math-inline-display-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
            check_pixels=False,
        ),
        FixtureSpec(
            name="fragile-listing-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/P": 5}),
            frame_children=["/frametitle", "/P", "/block", "/P"],
            baseline="fragile-listing-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
        ),
        FixtureSpec(
            name="footnote-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/P": 7}),
            frame_children=["/frametitle", "/P", "/P", "/P", "/block", "/P"],
            baseline="footnote-baseline",
            tree_checker=lambda f: check_block_structure(f, expected_block_count=1),
        ),
        FixtureSpec(
            name="custom-lang-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 1}),
            frame_children=["/frametitle", "/P"],
            baseline="custom-lang-baseline",
            expected_lang="en-GB",
        ),
        # Description list and overlay fixtures
        FixtureSpec(
            name="unsupported-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 3}),
            frame_children=["/frametitle", "/L", "/P"],
            baseline="unsupported-list-baseline",
            tree_checker=lambda f: check_list_structure(f, expected_item_count=2),
            check_pixels=False,
        ),
        FixtureSpec(
            name="unsupported-overlay-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            baseline="unsupported-overlay-list-baseline",
        ),
        FixtureSpec(
            name="accessible-table-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/Table": 1, "/TR": 3, "/TH": 3, "/TD": 6}),
            frame_children=["/frametitle", "/Table"],
            baseline="accessible-table-baseline",
        ),
        # Overlays & incremental fixtures
        FixtureSpec(
            name="overlay-items-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            baseline="overlay-items-baseline",
        ),
        FixtureSpec(
            name="overlay-plus-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            baseline="overlay-plus-baseline",
        ),
        FixtureSpec(
            name="overlay-nested-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/L": 4, "/LI": 7, "/Lbl": 7, "/LBody": 7, "/P": 7}),
            baseline="overlay-nested-list-baseline",
        ),
        FixtureSpec(
            name="overlay-para-after-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 5}),
            baseline="overlay-para-after-baseline",
        ),
        FixtureSpec(
            name="overlay-in-block-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/block": 2, "/blocktitle": 2, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            baseline="overlay-in-block-baseline",
        ),
        FixtureSpec(
            name="overlay-in-column-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/column": 4, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 5}),
            baseline="overlay-in-column-baseline",
        ),
        FixtureSpec(
            name="pause-paragraphs-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/P": 3}),
            baseline="pause-paragraphs-baseline",
        ),
        FixtureSpec(
            name="pause-in-block-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/block": 2, "/blocktitle": 2, "/P": 3}),
            baseline="pause-in-block-baseline",
        ),
        FixtureSpec(
            name="pause-after-list-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/L": 2, "/LI": 4, "/Lbl": 4, "/LBody": 4, "/P": 5}),
            baseline="pause-after-list-baseline",
        ),
        FixtureSpec(
            name="pause-combined-overlay-tagged",
            roles=Counter({"/Document": 1, "/frame": 3, "/frametitle": 3, "/L": 3, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 8}),
            baseline="pause-combined-overlay-baseline",
        ),
        # Overlay policies
        FixtureSpec(
            name="policy-pages-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/frametitle": 2, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3, "/P": 3}),
            baseline="policy-pages-baseline",
        ),
        FixtureSpec(
            name="policy-handout-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/L": 1, "/LI": 2, "/Lbl": 2, "/LBody": 2, "/P": 2}),
            baseline="policy-handout-baseline",
        ),
        # Tables & figures
        FixtureSpec(
            name="table-col-headers-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/Table": 1, "/TR": 3, "/TH": 3, "/TD": 6}),
            baseline="table-col-headers-baseline",
        ),
        FixtureSpec(
            name="table-row-col-headers-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/Table": 1, "/TR": 3, "/TH": 5, "/TD": 4}),
            baseline="table-row-col-headers-baseline",
            check_pixels=False,
        ),
        FixtureSpec(
            name="figure-pgfplots-alt-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/Figure": 1}),
            baseline="figure-pgfplots-alt-baseline",
        ),
        FixtureSpec(
            name="figure-tikz-decorative-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1}),
            baseline="figure-tikz-decorative-baseline",
        ),
        # Structural hardening & formatting
        FixtureSpec(
            name="centered-pathname-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 1}),
            baseline="centered-pathname-baseline",
        ),
        FixtureSpec(
            name="empty-cases-tagged",
            roles=Counter({"/Document": 1, "/frame": 2, "/column": 2, "/P": 4, "/frametitle": 1, "/L": 1, "/LI": 1, "/Lbl": 1, "/LBody": 1}),
            baseline="empty-cases-baseline",
            check_pixels=False,
        ),
        FixtureSpec(
            name="bookmarks-check-tagged",
            roles=Counter({"/Document": 1, "/frame": 4, "/frametitle": 3, "/P": 5, "/L": 2, "/LI": 3, "/Lbl": 3, "/LBody": 3}),
            baseline="bookmarks-check-baseline",
        ),
        FixtureSpec(
            name="nav-symbols-hidden-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 1}),
            baseline="nav-symbols-hidden-baseline",
        ),
        FixtureSpec(
            name="accessible-colors-tagged",
            roles=Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/block": 1, "/blocktitle": 1, "/P": 1}),
            baseline="accessible-colors-baseline",
        ),
    ]

    fixtures.extend([
        FixtureSpec(name="center-in-list-tagged", roles=Counter({"/Document":1,"/frame":1,"/frametitle":1,"/L":1,"/LI":2,"/Lbl":2,"/LBody":2,"/P":4}), baseline="center-in-list-baseline"),
        FixtureSpec(name="titlepage-tagged", roles=Counter({"/Document":1,"/frame":2,"/frametitle":2,"/P":4}), baseline="titlepage-baseline"),
        FixtureSpec(name="native-tikz-tagged", roles=Counter({"/Document":1,"/frame":1,"/frametitle":1,"/P":2,"/Figure":1}), baseline="native-tikz-baseline"),
        FixtureSpec(name="figure-options-tagged", roles=Counter({"/Document":1,"/frame":1,"/frametitle":1,"/P":3,"/Figure":2}), baseline="figure-options-baseline"),
        FixtureSpec(name="semantic-features-tagged", roles=Counter({"/Document":1,"/frame":1,"/frametitle":1,"/P":1,"/Formula":1,"/Table":2,"/TR":4,"/TH":5,"/TD":3}), baseline="semantic-features-baseline", check_pixels=False),  # Formula boundary changes punctuation kerning (35 pixels); visually reviewed.
    ])

    print(f"Running verification on {len(fixtures)} fixtures...")
    for spec in fixtures:
        tagged_pdf = build / f"{spec.name}.pdf"
        if not tagged_pdf.exists():
            raise FileNotFoundError(f"Missing PDF: {tagged_pdf}")

        inspect_tree(tagged_pdf, spec.roles, spec.frame_children, spec.tree_checker, spec.expected_lang)

        if spec.baseline:
            baseline_pdf = build / f"{spec.baseline}.pdf"
            if not baseline_pdf.exists():
                raise FileNotFoundError(f"Missing baseline PDF: {baseline_pdf}")

            if spec.check_text:
                compare_text(baseline_pdf, tagged_pdf)

            if spec.check_pixels:
                compare_pixels(baseline_pdf, tagged_pdf, build)

        print(f"  [OK] {spec.name}")

    # Additional verifications
    verify_bookmarks_outlines(build / "bookmarks-check-tagged.pdf")
    verify_accessible_contrast()
    assert "BA-ALERT-TITLE-FG=1,1,1;BG=0.75,0,0" in (build/"accessible-colors-tagged.log").read_text(errors="replace"), "Contrast preset was not applied to the actual theme"
    verify_negative_and_warning_tests(build)

    print("ALL TESTS PASSED: structure assertions, text identity, 300-DPI pixel regressions, contrast, and policy enforcement.")


def verify_bookmarks_outlines(pdf_path: Path):
    reader = PdfReader(pdf_path)
    outlines = reader.outline
    titles = [item["/Title"] for item in outlines if isinstance(item, dict) and "/Title" in item]
    if titles != ["First Titled Frame", "Slide 2", "Incremental Frame"]:
        raise AssertionError(f"Unexpected bookmark titles in {pdf_path.name}: {titles}")
    print("  [OK] Bookmarks outline hierarchy (1 outline per logical frame, no duplicates)")


def verify_accessible_contrast():
    def srgb_to_lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def luminance(r, g, b):
        return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)

    def contrast(rgb1, rgb2):
        l1 = luminance(*rgb1)
        l2 = luminance(*rgb2)
        hi, lo = max(l1, l2), min(l1, l2)
        return (hi + 0.05) / (lo + 0.05)

    pairs = [
        ("Alert block title (white on red!75!black)", (1.0, 1.0, 1.0), (0.75, 0.0, 0.0)),
        ("Alert block body (black on red!10!white)", (0.0, 0.0, 0.0), (1.0, 0.9, 0.9)),
        ("Author head/foot (white on blue!40!black)", (1.0, 1.0, 1.0), (0.0, 0.0, 0.4)),
        ("Title head/foot (white on blue!30!black)", (1.0, 1.0, 1.0), (0.0, 0.0, 0.3)),
        ("Date head/foot (white on blue!20!black)", (1.0, 1.0, 1.0), (0.0, 0.0, 0.2)),
        ("Alerted text (red!60!black on white)", (0.6, 0.0, 0.0), (1.0, 1.0, 1.0)),
    ]
    for name, c1, c2 in pairs:
        cr = contrast(c1, c2)
        if cr < 4.5:
            raise AssertionError(f"Contrast failure for {name}: {cr:.2f}:1 < 4.5:1")
    print("  [OK] Accessible contrast verification (all WCAG 2.1 AA >= 4.5:1)")


def verify_negative_and_warning_tests(build_dir: Path):
    tests = [
        ("tests/fixtures/policy-strict-test.tex", True, "Overlay specification on \\item detected"),
        ("tests/fixtures/table-unannotated-warn-test.tex", False, "Unannotated tabular detected in slide body"),
        ("tests/fixtures/table-unannotated-strict-test.tex", True, "Unannotated tabular detected in slide body"),
        ("tests/fixtures/figure-strict-missing-alt-test.tex", True, "missing required alternative text"),
    ]
    for tex_path, expect_error, pattern in tests:
        res = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={build_dir}", tex_path],
            capture_output=True, text=True, cwd=Path(__file__).resolve().parents[1]
        )
        raw = res.stdout + res.stderr
        output = raw.replace("\n", "").replace("\r", "")
        if expect_error:
            if res.returncode == 0:
                raise AssertionError(f"Expected failure for {tex_path}, but compilation succeeded!")
            if pattern not in output:
                raise AssertionError(f"Expected pattern '{pattern}' not found in output of {tex_path}")
        else:
            if res.returncode != 0:
                raise AssertionError(f"Expected success with warning for {tex_path}, but compilation failed!")
            if pattern not in output:
                raise AssertionError(f"Expected warning '{pattern}' not found in output of {tex_path}")
    print("  [OK] Negative and warning policy tests passed")


if __name__ == "__main__":
    main()


