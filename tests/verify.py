from __future__ import annotations

import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

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


def inspect_tree(pdf_path: Path, expected_roles: Counter[str], expected_frame_children: list[str]) -> None:
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
        raise AssertionError(f"{pdf_path.name}: roles {roles} != {expected_roles}")
    if len(mcrs) != len(set(mcrs)):
        raise AssertionError(f"{pdf_path.name}: duplicate page/MCID references")

    frame = object_value(children(document)[0])
    frame_roles = [str(object_value(kid).get("/S")) for kid in children(frame) if isinstance(object_value(kid), dict) and "/S" in object_value(kid)]
    if frame_roles != expected_frame_children:
        raise AssertionError(f"{pdf_path.name}: frame children {frame_roles} != {expected_frame_children}")


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


def main() -> None:
    build = Path(sys.argv[1]).resolve()
    expected_basic = Counter({"/Document": 1, "/frame": 1, "/frametitle": 1, "/P": 1})
    inspect_tree(build / "frame-paragraph-tagged.pdf", expected_basic, ["/frametitle", "/P"])
    inspect_tree(build / "package-only.pdf", expected_basic, ["/frametitle", "/P"])

    expected_unsupported = Counter({"/Document": 1, "/frame": 1, "/frametitle": 1})
    inspect_tree(build / "unsupported-list-tagged.pdf", expected_unsupported, ["/frametitle"])

    compare_pixels(
        build / "frame-paragraph-baseline.pdf",
        build / "frame-paragraph-tagged.pdf",
        build,
    )
    compare_pixels(
        build / "unsupported-list-baseline.pdf",
        build / "unsupported-list-tagged.pdf",
        build,
    )
    print("PASS: structure assertions and 300-DPI pixel regressions")


if __name__ == "__main__":
    main()

