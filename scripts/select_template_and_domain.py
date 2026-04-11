#!/usr/bin/env python3
"""Recommend template and domain pack from project brief."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYOUT_INDEX = ROOT / "templates" / "layouts" / "layouts_index.json"


def pick_domain(text: str) -> str:
    explicit = extract_field(text, "推荐行业包") or extract_field(text, "识别领域")
    if explicit:
        explicit_lower = explicit.lower()
        if "security_service" in explicit_lower or "安服" in explicit:
            return "security_service"
        if "finance_solution" in explicit_lower or "金融" in explicit or "银行" in explicit:
            return "finance_solution"
        if "government_report" in explicit_lower or "政务" in explicit or "政府" in explicit:
            return "government_report"
        if "general" in explicit_lower:
            return "general"
    lower = text.lower()
    if any(keyword in lower for keyword in ["安服", "hw", "攻防", "security", "安全运营"]):
        return "security_service"
    if any(keyword in lower for keyword in ["finance", "金融", "银行"]):
        return "finance_solution"
    if any(keyword in lower for keyword in ["government", "政务", "政府"]):
        return "government_report"
    return "general"


def pick_templates(index: dict, text: str) -> list[str]:
    explicit = extract_field(text, "推荐模板") or extract_field(text, "模板倾向建议")
    if explicit and explicit not in {"待确认", "待用户确认 / 系统后续推荐"}:
        normalized: list[str] = []
        mapping = {
            "长亭安服": "security_service",
            "security_service": "security_service",
            "长亭通用墨绿色": "chaitin",
            "chaitin": "chaitin",
        }
        for part in re.split(r"[，,、/\s]+", explicit):
            key = part.strip().strip("`")
            if not key:
                continue
            normalized_key = mapping.get(key, key)
            if normalized_key in index.get("layouts", {}) and normalized_key not in normalized:
                normalized.append(normalized_key)
        if normalized:
            return normalized[:3]

    candidates: list[str] = []
    for key, values in index.get("quickLookup", {}).items():
        if key.lower() in text.lower() or key in text:
            candidates.extend(values)
    if not candidates:
        candidates = ["exhibit", "mckinsey"]
    seen: list[str] = []
    for item in candidates:
        if item not in seen:
            seen.append(item)
    return seen[:3]


def extract_field(text: str, label: str) -> str:
    match = re.search(rf"(?m)^- {re.escape(label)}：(.+)$", text)
    return match.group(1).strip() if match else ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Recommend template and domain pack from project brief.")
    parser.add_argument("brief", help="Path to project_brief.md")
    parser.add_argument("-o", "--output", help="Optional output markdown path")
    args = parser.parse_args()

    brief_path = Path(args.brief).expanduser().resolve()
    text = brief_path.read_text(encoding="utf-8")
    index = json.loads(LAYOUT_INDEX.read_text(encoding="utf-8"))
    domain = pick_domain(text)
    templates = pick_templates(index, text)

    content = "\n".join(
        [
            "# 模板与行业建议",
            "",
            f"- 推荐行业包：`{domain}`",
            f"- 推荐模板：{', '.join(f'`{item}`' for item in templates)}",
            "- 建议先确认模板后，再进入故事线规划与页型选择",
            "",
        ]
    )

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"Wrote: {out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
