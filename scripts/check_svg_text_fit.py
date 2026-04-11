#!/usr/bin/env python3
from __future__ import annotations

"""Check whether SVG text is likely to overflow or collide inside the layout.

Usage:
    python3 scripts/check_svg_text_fit.py <svg_file_or_directory>
    python3 scripts/check_svg_text_fit.py <project_path>/svg_output
    python3 scripts/check_svg_text_fit.py <project_path>/svg_final
"""

import re
import sys
from pathlib import Path
from typing import Iterable, Optional
from xml.etree import ElementTree as ET

try:
    from PIL import Image, ImageFont
except ImportError:
    Image = None  # type: ignore
    ImageFont = None  # type: ignore


FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
]


def parse_float(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else default


def resolve_font(size: float):
    if ImageFont is None:
        return None
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, max(1, int(round(size))))
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def measure_text_width(text: str, font_size: float) -> float:
    font = resolve_font(font_size)
    if font is None:
        return len(text) * font_size
    try:
        return float(font.getlength(text))
    except Exception:
        return len(text) * font_size


def rects_in_svg(root: ET.Element) -> list[tuple[float, float, float, float]]:
    rects: list[tuple[float, float, float, float]] = []
    for elem in root.iter():
        if elem.tag.split("}")[-1] != "rect":
            continue
        x = parse_float(elem.get("x"))
        y = parse_float(elem.get("y"))
        w = parse_float(elem.get("width"))
        h = parse_float(elem.get("height"))
        if w <= 0 or h <= 0:
            continue
        if w < 12 or h < 12:
            continue
        if w >= 1200 and h >= 700:
            continue
        rects.append((x, y, w, h))
    return rects


def text_lines(elem: ET.Element) -> Iterable[tuple[float, float, float, str, str]]:
    text_anchor = (elem.get("text-anchor") or "start").strip()
    font_size = parse_float(elem.get("font-size"), 16)
    tspans = [child for child in elem if child.tag.split("}")[-1] == "tspan"]

    if tspans:
        for tspan in tspans:
            line = "".join(tspan.itertext()).strip()
            if not line:
                continue
            yield (
                parse_float(tspan.get("x"), parse_float(elem.get("x"))),
                parse_float(tspan.get("y"), parse_float(elem.get("y"))),
                font_size,
                text_anchor,
                line,
            )
        return

    line = "".join(elem.itertext()).strip()
    if line:
        yield (
            parse_float(elem.get("x")),
            parse_float(elem.get("y")),
            font_size,
            text_anchor,
            line,
        )


def line_bbox(
    x: float,
    y: float,
    font_size: float,
    text_anchor: str,
    text: str,
) -> tuple[float, float, float, float]:
    width = measure_text_width(text, font_size)
    height = font_size * 1.2
    if text_anchor == "middle":
        left = x - width / 2
        right = x + width / 2
    elif text_anchor == "end":
        left = x - width
        right = x
    else:
        left = x
        right = x + width
    return (left, y - height, right, y)


def rect_bbox(rect: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    rx, ry, rw, rh = rect
    return (rx, ry, rx + rw, ry + rh)


def overlap_area(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> float:
    left = max(a[0], b[0])
    top = max(a[1], b[1])
    right = min(a[2], b[2])
    bottom = min(a[3], b[3])
    return max(0.0, right - left) * max(0.0, bottom - top)


def find_containing_rect(
    x: float,
    y: float,
    rects: Iterable[tuple[float, float, float, float]],
) -> Optional[tuple[float, float, float, float]]:
    containers = []
    for rect in rects:
        rx, ry, rw, rh = rect
        if rx - 1 <= x <= rx + rw + 1 and ry - 1 <= y <= ry + rh + 1:
            containers.append((rw * rh, rect))
    if not containers:
        return None
    return min(containers, key=lambda item: item[0])[1]


def find_best_rect_for_line(
    x: float,
    y: float,
    bbox: tuple[float, float, float, float],
    rects: Iterable[tuple[float, float, float, float]],
) -> Optional[tuple[float, float, float, float]]:
    overlaps = []
    for rect in rects:
        area = overlap_area(bbox, rect_bbox(rect))
        if area > 0:
            rx, ry, rw, rh = rect
            overlaps.append((rw * rh, -area, rect))
    if overlaps:
        return min(overlaps, key=lambda item: (item[0], item[1]))[2]

    return find_containing_rect(x, y, rects)


def width_budget(
    x: float,
    rect: tuple[float, float, float, float],
    text_anchor: str,
    pad: float = 16,
) -> float:
    rx, _, rw, _ = rect
    if text_anchor == "middle":
        return min(x - rx, rx + rw - x) * 2 - pad * 2
    if text_anchor == "end":
        return x - rx - pad
    return rx + rw - x - pad


def boxes_overlap(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    pad: float = 2.0,
) -> bool:
    left = max(a[0], b[0])
    top = max(a[1], b[1])
    right = min(a[2], b[2])
    bottom = min(a[3], b[3])
    return right - left > pad and bottom - top > pad


def should_ignore_line(line: str, font_size: float, text_anchor: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.isdigit() and len(stripped) <= 3 and font_size <= 20:
        return True
    # Centered numeric hero figures and chapter numerals are intentional visual anchors,
    # not body text that should be constrained by the nearest card width heuristic.
    if text_anchor == "middle" and stripped.isdigit() and len(stripped) <= 4:
        return True
    return False


def image_size(path: Path) -> Optional[tuple[int, int]]:
    if Image is None:
        return None
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def resolve_image_path(svg_path: Path, href: Optional[str]) -> Optional[Path]:
    if not href or href.startswith("data:") or "://" in href:
        return None
    return (svg_path.parent / href).resolve()


def check_svg(svg_path: Path) -> list[str]:
    root = ET.parse(svg_path).getroot()
    rects = rects_in_svg(root)
    issues: list[str] = []
    text_boxes: list[tuple[int, tuple[float, float, float, float], tuple[float, float, float, float], str]] = []

    for elem_index, elem in enumerate(root.iter()):
        if elem.tag.split("}")[-1] != "text":
            continue
        for x, y, font_size, text_anchor, line in text_lines(elem):
            if should_ignore_line(line, font_size, text_anchor):
                continue
            bbox = line_bbox(x, y, font_size, text_anchor, line)
            rect = find_best_rect_for_line(x, y, bbox, rects)
            if rect is None:
                continue
            rx, ry, rw, rh = rect
            budget = width_budget(x, rect, text_anchor)
            actual_width = measure_text_width(line, font_size)
            line_height = font_size * 1.2
            vertical_ok = (y <= ry + rh - 6) and (y - line_height >= ry - 6)
            text_boxes.append((elem_index, bbox, rect, line))

            if actual_width > budget or not vertical_ok:
                issues.append(
                    f"{svg_path.name}: '{line}' exceeds rect ({int(rx)},{int(ry)},{int(rw)},{int(rh)})"
                )

    for i in range(len(text_boxes)):
        elem_a, box_a, rect_a, line_a = text_boxes[i]
        for j in range(i + 1, len(text_boxes)):
            elem_b, box_b, rect_b, line_b = text_boxes[j]
            if elem_a == elem_b or rect_a != rect_b:
                continue
            if boxes_overlap(box_a, box_b):
                issues.append(
                    f"{svg_path.name}: text overlap inside rect ({int(rect_a[0])},{int(rect_a[1])},{int(rect_a[2])},{int(rect_a[3])}) -> '{line_a}' overlaps '{line_b}'"
                )

    for elem in root.iter():
        if elem.tag.split("}")[-1] != "image":
            continue
        href = elem.get("href") or elem.get("{http://www.w3.org/1999/xlink}href")
        image_path = resolve_image_path(svg_path, href)
        if image_path is None or not image_path.exists():
            continue
        box_w = parse_float(elem.get("width"))
        box_h = parse_float(elem.get("height"))
        if box_w * box_h < 80000:
            continue
        preserve = (elem.get("preserveAspectRatio") or "").lower()
        if "contain" not in preserve:
            continue
        size = image_size(image_path)
        if size is None or size[0] <= 0 or size[1] <= 0:
            continue
        image_ratio = size[0] / size[1]
        render_w = min(box_w, box_h * image_ratio)
        render_h = min(box_h, box_w / image_ratio)
        width_fill = render_w / box_w if box_w else 1.0
        height_fill = render_h / box_h if box_h else 1.0
        area_fill = width_fill * height_fill
        if area_fill < 0.45 or min(render_w, render_h) < 220:
            issues.append(
                f"{svg_path.name}: image '{Path(href).name}' is likely too small for its box ({int(box_w)}x{int(box_h)} -> rendered about {int(render_w)}x{int(render_h)})"
            )

    return issues


def collect_svg_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if (target / "svg_final").exists():
        return sorted((target / "svg_final").glob("*.svg"))
    if (target / "svg_output").exists():
        return sorted((target / "svg_output").glob("*.svg"))
    return sorted(target.glob("*.svg"))


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check_svg_text_fit.py <svg_file_or_directory>", file=sys.stderr)
        return 2

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Path not found: {target}", file=sys.stderr)
        return 2

    svg_files = collect_svg_files(target)
    if not svg_files:
        print(f"No SVG files found in {target}", file=sys.stderr)
        return 2

    issues: list[str] = []
    for svg_file in svg_files:
        issues.extend(check_svg(svg_file))

    if issues:
        for issue in issues:
            print(issue)
        return 1

    print(f"OK: checked {len(svg_files)} SVG files, no obvious text or image layout issues detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
