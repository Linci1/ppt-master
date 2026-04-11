#!/usr/bin/env python3
"""Build project brief markdown from structured /plan answers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


LIST_FIELDS = {
    "priorities",
    "must_keep",
    "reference_cases",
    "brand_mandatories",
    "source_docs",
    "source_ppts",
    "source_assets",
    "forbidden_terms",
    "forbidden_visuals",
    "planning_followups",
    "plan_risks",
}


def split_items(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = value.split(",")
    return [str(item).strip() for item in items if str(item).strip()]


def load_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))


def derive_from_plan_state(state: dict[str, Any]) -> dict[str, Any]:
    domain_context = state.get("domain_context") or {}
    next_questions = state.get("next_questions") or []
    optional_questions = state.get("suggested_optional_questions") or []
    blocking_items = state.get("blocking_items") or []
    optional_items = state.get("optional_items") or []

    followup_lines: list[str] = []
    for item in next_questions[:3]:
        question = str(item.get("question") or "").strip()
        if question:
            followup_lines.append(question)
    if not followup_lines:
        for item in optional_questions[:3]:
            question = str(item.get("question") or "").strip()
            if question:
                followup_lines.append(question)

    risk_lines: list[str] = []
    for item in blocking_items[:3]:
        reason = str(item.get("reason") or "").strip()
        label = str(item.get("label") or "").strip()
        if label and reason:
            risk_lines.append(f"{label}: {reason}")
    if not risk_lines:
        for item in optional_items[:3]:
            reason = str(item.get("reason") or "").strip()
            label = str(item.get("label") or "").strip()
            if label and reason:
                risk_lines.append(f"{label}: {reason}")

    return {
        "detected_domain": str(domain_context.get("domain_label") or ""),
        "domain_reason": str(domain_context.get("reason") or ""),
        "template_hint": str(domain_context.get("template_hint") or ""),
        "plan_stage": str(state.get("conversation_stage") or ""),
        "plan_round_objective": str(state.get("round_objective") or ""),
        "planning_followups": followup_lines,
        "plan_risks": risk_lines,
        "recommended_template": str(domain_context.get("template_hint") or ""),
        "recommended_domain_pack": str(domain_context.get("domain_id") or ""),
    }


def merge_data(args: argparse.Namespace, data: dict[str, Any], plan_state: dict[str, Any]) -> dict[str, Any]:
    derived = derive_from_plan_state(plan_state)
    merged: dict[str, Any] = {}
    for key in (
        "project_name",
        "industry",
        "scenario",
        "language",
        "format",
        "audience",
        "secondary_audience",
        "audience_focus",
        "goal",
        "desired_judgment",
        "desired_action",
        "priorities",
        "must_keep",
        "template",
        "reference_cases",
        "style",
        "complexity_preference",
        "brand_mandatories",
        "source_docs",
        "source_ppts",
        "source_assets",
        "allow_ai_images",
        "page_range",
        "time_limit",
        "reading_mode",
        "forbidden_terms",
        "forbidden_visuals",
        "detected_domain",
        "domain_reason",
        "template_hint",
        "plan_stage",
        "plan_round_objective",
        "planning_followups",
        "plan_risks",
        "recommended_template",
        "recommended_domain_pack",
        "recommended_storyline",
        "recommended_complex_pages",
        "current_risks",
    ):
        raw = data.get(key, derived.get(key, getattr(args, key, None)))
        merged[key] = split_items(raw) if key in LIST_FIELDS else (str(raw).strip() if raw is not None else "")

    if not merged["recommended_template"] and merged["template_hint"]:
        merged["recommended_template"] = merged["template_hint"]
    if not merged["recommended_domain_pack"] and merged["detected_domain"]:
        merged["recommended_domain_pack"] = merged["detected_domain"]
    if not merged["current_risks"] and merged["plan_risks"]:
        merged["current_risks"] = "；".join(merged["plan_risks"])

    return merged


def value_or_placeholder(value: str, placeholder: str = "待确认") -> str:
    return value or placeholder


def list_or_placeholder(items: list[str], placeholder: str = "待确认") -> list[str]:
    return items if items else [placeholder]


def render_list(title: str, items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build project_brief.md from structured /plan inputs.")
    parser.add_argument("-o", "--output", required=True, help="Output markdown path")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--industry", required=True)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--audience", required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--lang", dest="language", default="中文")
    parser.add_argument("--format", default="ppt169")
    parser.add_argument("--secondary-audience", default="")
    parser.add_argument("--audience-focus", default="")
    parser.add_argument("--desired-judgment", default="")
    parser.add_argument("--desired-action", default="")
    parser.add_argument("--priorities", default="")
    parser.add_argument("--must-keep", default="")
    parser.add_argument("--template", default="")
    parser.add_argument("--reference-cases", default="")
    parser.add_argument("--style", default="")
    parser.add_argument("--complexity-preference", default="")
    parser.add_argument("--brand-mandatories", default="")
    parser.add_argument("--source-docs", default="")
    parser.add_argument("--source-ppts", default="")
    parser.add_argument("--source-assets", default="")
    parser.add_argument("--allow-ai-images", default="")
    parser.add_argument("--page-range", default="")
    parser.add_argument("--time-limit", default="")
    parser.add_argument("--reading-mode", default="")
    parser.add_argument("--forbidden-terms", default="")
    parser.add_argument("--forbidden-visuals", default="")
    parser.add_argument("--recommended-template", default="")
    parser.add_argument("--recommended-domain-pack", default="")
    parser.add_argument("--recommended-storyline", default="")
    parser.add_argument("--recommended-complex-pages", default="")
    parser.add_argument("--current-risks", default="")
    parser.add_argument("--json", dest="json_path", help="Optional JSON answers file")
    parser.add_argument("--plan-state-json", dest="plan_state_json", help="Optional plan agent state JSON")
    args = parser.parse_args()

    data = load_json(args.json_path)
    plan_state = load_json(args.plan_state_json)
    merged = merge_data(args, data, plan_state)

    content = f"""# 项目简报

## 一、基础信息
- 项目名称：{value_or_placeholder(merged['project_name'])}
- 行业：{value_or_placeholder(merged['industry'])}
- 场景：{value_or_placeholder(merged['scenario'])}
- 语言：{value_or_placeholder(merged['language'], '中文')}
- 输出格式：{value_or_placeholder(merged['format'], 'ppt169')}

## 二、展示对象
- 主要受众：{value_or_placeholder(merged['audience'])}
- 次要受众：{value_or_placeholder(merged['secondary_audience'])}
- 受众更关心：{value_or_placeholder(merged['audience_focus'])}

## 三、本次目标
- 核心目标：{value_or_placeholder(merged['goal'])}
- 期待对方形成的判断：{value_or_placeholder(merged['desired_judgment'])}
- 期待对方采取的动作：{value_or_placeholder(merged['desired_action'])}

## 四、展示重点
{render_list('priorities', list_or_placeholder(merged['priorities']))}
- 必须保留的信息：{', '.join(list_or_placeholder(merged['must_keep']))}

## 五、品牌与模板要求
- 指定模板：{value_or_placeholder(merged['template'])}
- 历史案例参考：{', '.join(list_or_placeholder(merged['reference_cases']))}
- 风格偏好：{value_or_placeholder(merged['style'])}
- 复杂度偏好：{value_or_placeholder(merged['complexity_preference'])}
- 必须固定的品牌元素：{', '.join(list_or_placeholder(merged['brand_mandatories']))}

## 六、材料情况
- 源文档：{', '.join(list_or_placeholder(merged['source_docs']))}
- 历史 PPT：{', '.join(list_or_placeholder(merged['source_ppts']))}
- 图片 / 截图 / 图表：{', '.join(list_or_placeholder(merged['source_assets']))}
- 是否允许 AI 生图：{value_or_placeholder(merged['allow_ai_images'])}

## 七、交付约束
- 页数范围：{value_or_placeholder(merged['page_range'])}
- 时间限制：{value_or_placeholder(merged['time_limit'])}
- 可讲述 / 可阅读倾向：{value_or_placeholder(merged['reading_mode'])}
- 禁用表达：{', '.join(list_or_placeholder(merged['forbidden_terms']))}
- 禁用视觉形式：{', '.join(list_or_placeholder(merged['forbidden_visuals']))}

## 八、AI 初步判断
- 识别领域：{value_or_placeholder(merged['detected_domain'])}
- 识别依据：{value_or_placeholder(merged['domain_reason'])}
- 模板倾向建议：{value_or_placeholder(merged['template_hint'])}
- 当前 /plan 阶段：{value_or_placeholder(merged['plan_stage'])}
- 当前轮次目标：{value_or_placeholder(merged['plan_round_objective'])}
- 推荐模板：{value_or_placeholder(merged['recommended_template'])}
- 推荐行业包：{value_or_placeholder(merged['recommended_domain_pack'])}
- 推荐叙事结构：{value_or_placeholder(merged['recommended_storyline'])}
- 推荐复杂页位置：{value_or_placeholder(merged['recommended_complex_pages'])}
- 当前风险点：{value_or_placeholder(merged['current_risks'])}
- 建议补问：{', '.join(list_or_placeholder(merged['planning_followups']))}
"""

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content + "\n", encoding="utf-8")
    print(f"Wrote: {out}")


if __name__ == "__main__":
    main()
