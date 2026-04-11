#!/usr/bin/env python3
from __future__ import annotations

"""Render SVG pages to PNG previews for visual QA.

Usage:
    python3 scripts/render_svg_pages.py <project_path>
    python3 scripts/render_svg_pages.py <project_path> -s final
    python3 scripts/render_svg_pages.py <project_path>/svg_final --pages 02_目录.svg 05_风险分布与关键成果.svg
"""

import argparse
import sys
from pathlib import Path

import fitz


def resolve_svg_dir(target: Path, source: str) -> Path:
    if target.is_dir() and any(target.glob("*.svg")):
        return target
    if not target.is_dir():
        raise FileNotFoundError(f"Path not found: {target}")

    if source == "auto":
        if (target / "svg_final").is_dir():
            return target / "svg_final"
        if (target / "svg_output").is_dir():
            return target / "svg_output"
        raise FileNotFoundError(f"No svg_final/ or svg_output/ found under: {target}")

    svg_dir = target / f"svg_{source}"
    if not svg_dir.is_dir():
        raise FileNotFoundError(f"SVG directory not found: {svg_dir}")
    return svg_dir


def resolve_output_dir(target: Path, svg_dir: Path, output: str | None) -> Path:
    if output:
        return Path(output)
    if target.is_dir() and not any(target.glob("*.svg")):
        return target / "visual_qc" / svg_dir.name
    return svg_dir.parent / "visual_qc"


def select_svg_files(svg_dir: Path, pages: list[str]) -> list[Path]:
    svg_files = sorted(svg_dir.glob("*.svg"))
    if not pages:
        return svg_files

    wanted = set()
    for page in pages:
        candidate = page if page.endswith(".svg") else f"{page}.svg"
        wanted.add(candidate)

    selected = [path for path in svg_files if path.name in wanted]
    missing = sorted(wanted - {path.name for path in selected})
    if missing:
        raise FileNotFoundError(f"Requested SVG page(s) not found in {svg_dir}: {', '.join(missing)}")
    return selected


def render_svg(svg_path: Path, output_path: Path, scale: float) -> None:
    document = fitz.open(stream=svg_path.read_bytes(), filetype="svg")
    try:
        pixmap = document[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        pixmap.save(str(output_path))
    finally:
        document.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Render SVG pages to PNG previews for visual QA.")
    parser.add_argument("target", help="Project path or SVG directory")
    parser.add_argument(
        "-s",
        "--source",
        choices=["auto", "output", "final"],
        default="auto",
        help="Use svg_output/ or svg_final/ when a project path is provided (default: auto, prefers final).",
    )
    parser.add_argument("-o", "--output", help="Output directory for rendered PNG previews")
    parser.add_argument(
        "--scale",
        type=float,
        default=2.0,
        help="Render scale multiplier passed to PyMuPDF (default: 2.0)",
    )
    parser.add_argument(
        "--pages",
        nargs="*",
        default=[],
        help="Optional exact SVG filenames (with or without .svg) to render",
    )
    args = parser.parse_args()

    try:
        target = Path(args.target)
        svg_dir = resolve_svg_dir(target, args.source)
        output_dir = resolve_output_dir(target, svg_dir, args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        svg_files = select_svg_files(svg_dir, args.pages)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if not svg_files:
        print(f"No SVG files found in {svg_dir}", file=sys.stderr)
        return 2

    print("PPT Master - SVG Visual QA Renderer")
    print("=" * 50)
    print(f"  SVG directory: {svg_dir}")
    print(f"  Output directory: {output_dir}")
    print(f"  Render scale: {args.scale}")
    print(f"  File count: {len(svg_files)}")

    rendered = 0
    for svg_file in svg_files:
        output_file = output_dir / f"{svg_file.stem}.png"
        render_svg(svg_file, output_file, args.scale)
        print(f"  [OK] {svg_file.name} -> {output_file.name}")
        rendered += 1

    print(f"\n[Done] Rendered {rendered}/{len(svg_files)} SVG page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
