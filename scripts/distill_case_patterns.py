#!/usr/bin/env python3
"""Distill reusable patterns from ingested case folders."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CASE_LIBRARY = ROOT / "case_library"


def load_analysis(case_dir: Path) -> dict[str, Any]:
    return json.loads((case_dir / "analysis.json").read_text(encoding="utf-8"))


def distill(case_dirs: list[Path]) -> str:
    slide_titles = []
    shape_counter: Counter[str] = Counter()
    density = []
    for case_dir in case_dirs:
        analysis = load_analysis(case_dir)
        for slide in analysis["slides"]:
            slide_titles.append(slide["title_guess"])
            density.append((slide["shape_count"], slide["text_boxes"], slide["title_guess"]))
        shape_counter.update(analysis["shape_distribution"])

    density.sort(reverse=True)
    lines = [
        "# 案例模式蒸馏结果",
        "",
        "## 一、输入案例",
        *[f"- {case_dir.name}" for case_dir in case_dirs],
        "",
        "## 二、常见标题线索",
        *[f"- {title}" for title, _ in Counter(slide_titles).most_common(12)],
        "",
        "## 三、常见形状类型",
        *[f"- 形状类型 {shape}: {count}" for shape, count in shape_counter.most_common(12)],
        "",
        "## 四、高密度页面候选",
        *[f"- 《{title}》：形状 {shape_count}，文本框 {text_boxes}" for shape_count, text_boxes, title in density[:10]],
        "",
        "## 五、建议下一步",
        "- 把稳定重复出现的表达升级为行业规则",
        "- 把固定品牌骨架升级为模板规则",
        "- 把单案例技巧保留在案例库，不直接写死进模板",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Distill reusable patterns from case_library.")
    parser.add_argument("cases", nargs="+", help="Case directories or case names under case_library")
    parser.add_argument("-o", "--output", help="Output markdown path")
    args = parser.parse_args()

    case_dirs: list[Path] = []
    for value in args.cases:
        path = Path(value)
        if not path.is_absolute():
            path = CASE_LIBRARY / value
        path = path.resolve()
        if not path.exists():
            raise SystemExit(f"Case directory not found: {value}")
        case_dirs.append(path)

    content = distill(case_dirs)
    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content + "\n", encoding="utf-8")
        print(f"Wrote: {out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
