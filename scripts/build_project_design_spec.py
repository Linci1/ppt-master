#!/usr/bin/env python3
"""Build a project-root design_spec.md starter from Agent planning outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from template_semantics import FIXED_TEMPLATES as SEMANTIC_FIXED_TEMPLATES
    from template_semantics import fixed_template_matches_entry
except ImportError:
    TOOLS_DIR = Path(__file__).resolve().parent
    import sys

    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from template_semantics import FIXED_TEMPLATES as SEMANTIC_FIXED_TEMPLATES  # type: ignore
    from template_semantics import fixed_template_matches_entry  # type: ignore

try:
    from build_production_packet import (
        CANVAS_SPECS,
        analyze_project,
        infer_complex_mode,
        infer_advanced_pattern,
        infer_layout_mode,
        normalize_template_id,
        infer_preferred_template,
        parse_brief_value,
    )
except ImportError:
    TOOLS_DIR = Path(__file__).resolve().parent
    import sys

    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from build_production_packet import (  # type: ignore
        CANVAS_SPECS,
        analyze_project,
        infer_complex_mode,
        infer_advanced_pattern,
        infer_layout_mode,
        normalize_template_id,
        infer_preferred_template,
        parse_brief_value,
    )


GENERATED_HEADER = [
    "> 该文件由 `ppt_agent.py execute` 生成，作为项目级 `design_spec.md` 首稿。",
    "> 若后续 Strategist 已人工完善本文件，默认不应被自动覆盖；如需刷新，请显式使用 `--force`。",
]
LAYOUT_INDEX_PATH = Path(__file__).resolve().parent.parent / "templates" / "layouts" / "layouts_index.json"
FIXED_TEMPLATES = set(SEMANTIC_FIXED_TEMPLATES)
TEMPLATE_DECK_SOFT_CAP = 2
TEMPLATE_PAGE_GROUP_SOFT_CAP = 1
TEMPLATE_ROLE_PATTERN_SOFT_CAP = 1
TEMPLATE_REBALANCE_TOLERANCE = 6
TEMPLATE_CROSS_TIER_TOLERANCE = 4
TEMPLATE_SEMANTIC_DRIFT_TOLERANCE = 1
SECURITY_SERVICE_TITLE_PATTERN_RULES = (
    (("关键证据总览", "证据证明"), "evidence_wall"),
    (("攻击结果归因", "结果导向案例", "典型案例摘要"), "evidence_attached_case_chain"),
    (("项目范围", "整体回顾"), "swimlane_collaboration"),
    (("社工钓鱼路径", "钓鱼路径"), "swimlane_collaboration"),
    (("内网侧攻击路径",), "attack_case_chain"),
    (("互联网侧攻击路径",), "multi_lane_execution_chain"),
    (("风险结构总览", "根因拆解"), "attack_tree_architecture"),
    (("审计问题", "异常登陆", "高危端口", "限源"), "governance_control_matrix"),
    (("通用口令", "通用密码", "凭证"), "attack_tree_architecture"),
    (("安全意识", "识别与响应", "员工"), "operation_loop"),
    (("整改复测机制", "整改闭环", "治理闭环"), "operation_loop"),
    (("长亭安服价值", "能力总览", "服务价值"), "layered_system_map"),
)
SECURITY_SERVICE_TEMPLATE_HINTS = {
    "evidence_wall": {
        "12_grid.svg": ("关键证据总览", "证据证明", "截图", "日志", "留痕", "原始证据"),
        "16_table.svg": ("分组证据", "证据列表", "证据归并"),
        "07_data.svg": ("指标", "数量", "汇总"),
    },
    "evidence_attached_case_chain": {
        "19_result_leading_case.svg": ("攻击结果归因", "结果导向案例", "典型案例摘要", "突破路径", "结果证明"),
        "05_case.svg": ("案例链", "社工", "钓鱼", "旁证"),
        "07_data.svg": ("结果总览", "影响结果"),
    },
    "swimlane_collaboration": {
        "05_case.svg": ("项目范围", "整体回顾", "范围", "时间", "对象", "社工钓鱼路径", "客户侧", "长亭侧", "协同", "多角色"),
        "10_timeline.svg": ("阶段推进", "联动"),
        "06_tactics.svg": ("战前", "战中", "战后"),
    },
    "attack_case_chain": {
        "19_result_leading_case.svg": ("内网侧攻击路径", "横向移动", "后台接管", "权限复用"),
        "05_case.svg": ("案例链", "路径拆解"),
        "09_comparison.svg": ("多链路", "双链"),
    },
    "multi_lane_execution_chain": {
        "09_comparison.svg": ("互联网侧攻击路径", "攻击链展开", "双链", "执行链"),
        "10_timeline.svg": ("阶段推进", "路径推进"),
        "05_case.svg": ("协同路径",),
    },
    "attack_tree_architecture": {
        "08_product.svg": ("风险结构总览", "根因", "分层结构", "互联网侧系统", "防护待加强"),
        "17_service_overview.svg": ("通用口令", "通用密码", "凭证", "账号", "密码"),
        "18_domain_capability_map.svg": ("风险结构", "问题拆解", "内网", "域"),
    },
    "governance_control_matrix": {
        "16_table.svg": ("审计问题", "异常登陆", "控制矩阵", "治理优先级", "控制点", "限源"),
        "12_grid.svg": ("治理看板", "风险域", "动作域"),
        "07_data.svg": ("指标", "审计留痕"),
    },
    "operation_loop": {
        "18_domain_capability_map.svg": ("安全意识", "整改复测机制", "闭环", "识别与响应", "持续优化"),
        "17_service_overview.svg": ("机制", "运营"),
        "06_tactics.svg": ("动作", "策略"),
    },
    "layered_system_map": {
        "18_domain_capability_map.svg": ("长亭安服价值", "能力价值", "结果价值"),
        "17_service_overview.svg": ("能力总览", "服务体系", "平台", "能力域"),
        "08_product.svg": ("能力结构", "支撑关系"),
    },
}
SECURITY_SERVICE_STANDARD_TEMPLATE_HINTS = {
    "07_data.svg": (
        "关键结果",
        "重要成果",
        "结果",
        "成果",
        "证明",
        "证据",
        "命中",
        "获取",
        "高价值",
        "结果结论",
    ),
    "12_grid.svg": (
        "整体回顾",
        "项目范围",
        "范围",
        "总览",
        "概览",
        "背景",
        "对象",
        "维度",
        "分组",
    ),
    "16_table.svg": (
        "清理",
        "收尾",
        "检查",
        "要求",
        "台账",
        "账号",
        "文件",
        "遗留",
        "项",
    ),
    "03_content.svg": (
        "说明",
        "概述",
        "回顾",
        "总结",
        "原则",
        "背景",
        "整体",
    ),
}


def estimate_body_font_size(analysis: dict[str, Any]) -> str:
    page_count = int(analysis.get("page_count", 0) or 0)
    complex_count = len(analysis.get("complex_pages", []))
    if complex_count >= 4 or page_count >= 20:
        return "16px"
    if complex_count >= 2 or page_count >= 14:
        return "17px"
    return "18px"


def estimate_style_objective(style: str, template_name: str, domain_name: str) -> str:
    parts = []
    if style and style != "待确认":
        parts.append(style)
    if template_name:
        parts.append(f"对齐 `{template_name}` 模板骨架")
    if domain_name and domain_name != "未提取到":
        parts.append(f"吸收 `{domain_name}` 行业表达")
    parts.append("先稳住品牌与逻辑，再在正文区保持灵活")
    return "；".join(parts)


def infer_page_role(entry: dict[str, str], page_num: int, total_pages: int, advanced_pattern: str) -> str:
    if advanced_pattern in {"无", "none"}:
        return ""

    text = " ".join(
        [
            entry.get("页面类型", ""),
            entry.get("页面意图", ""),
            entry.get("证明目标", ""),
            entry.get("推荐页型", ""),
            entry.get("核心判断", ""),
        ]
    )
    if any(keyword in text for keyword in ("总览", "概览", "地图", "体系", "框架")) or page_num <= 5:
        return "概览页"
    if any(keyword in text for keyword in ("案例", "证据", "数据", "结果", "证明", "客户", "资质", "赛事")):
        return "证明页"
    if any(keyword in text for keyword in ("建议", "收束", "总结", "落地", "路径")) or page_num >= max(total_pages - 2, 1):
        return "收束页"
    return "推进页"


def build_relation_text(
    prev_title: str | None,
    current_title: str,
    next_title: str | None,
    page_role: str,
) -> tuple[str, str]:
    if prev_title:
        previous_relation = f"承接上一页《{prev_title}》的结论，把信息继续推进到《{current_title}》所需的结构表达。"
    elif page_role == "概览页":
        previous_relation = "作为正文起点页，先把后续章节所需的框架、范围与判断基线建立起来。"
    else:
        previous_relation = "作为当前段落的起始页，先明确本页的判断对象、范围与证明方式。"

    if next_title:
        next_relation = f"本页结论将继续传递到下一页《{next_title}》，为后续案例、证据或动作展开做铺垫。"
    elif page_role == "收束页":
        next_relation = "本页承担当前段落收束任务，后续页面应直接承接其结论进入总结或结束。"
    else:
        next_relation = "本页输出当前判断后，后续页面应围绕其结果继续展开证据、落地或总结。"

    return previous_relation, next_relation


def infer_fallback_reason(entry: dict[str, str]) -> str:
    text = " ".join(
        [
            entry.get("页面意图", ""),
            entry.get("证明目标", ""),
            entry.get("核心判断", ""),
            entry.get("推荐页型", ""),
        ]
    )
    if any(keyword in text for keyword in ("说明", "原则", "概述", "摘要", "结论")):
        return "当前页核心是单一判断或轻量说明，尚不足以支撑重型结构表达。"
    return "当前页暂未形成可稳定复用的复杂关系，先使用基础页型承载，避免为了复杂而复杂。"


def normalize_inline_text(value: str) -> str:
    cleaned = re.sub(r"[`*]", "", value or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "待补齐"


def clean_optional_text(value: str) -> str:
    cleaned = re.sub(r"[`*]", "", value or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_signal_text(*parts: str) -> str:
    cleaned = []
    for part in parts:
        text = clean_optional_text(part)
        if text:
            cleaned.append(text)
    return " ".join(cleaned)


def page_group_key(entry: dict[str, str]) -> str:
    raw = clean_optional_text(entry.get("页面类型", "") or entry.get("推荐页型", ""))
    if "/" in raw:
        return clean_optional_text(raw.split("/", 1)[0])
    return raw


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def template_tier_rank(tier: str) -> int:
    order = {
        "primary": 0,
        "default": 0,
        "secondary": 1,
        "fallback": 2,
    }
    return order.get(clean_optional_text(tier), 3)


def build_ranked_candidate(
    template_name: str,
    score: int,
    *,
    tier: str = "default",
    semantic_score: int = 0,
) -> dict[str, Any]:
    return {
        "template_name": template_name,
        "score": score,
        "tier": tier,
        "semantic_score": semantic_score,
    }


def usage_count(
    planned_pages: list[dict[str, Any]] | None,
    *,
    template_name: str,
    page_group: str = "",
    page_role: str = "",
    advanced_pattern: str = "",
) -> dict[str, int]:
    if not planned_pages or not template_name or template_name in FIXED_TEMPLATES:
        return {
            "deck": 0,
            "page_group": 0,
            "role_pattern": 0,
            "pattern": 0,
        }

    deck = 0
    page_group_hits = 0
    role_pattern_hits = 0
    pattern_hits = 0
    normalized_pattern = clean_optional_text(advanced_pattern)
    normalized_group = clean_optional_text(page_group)
    normalized_role = clean_optional_text(page_role)

    for item in planned_pages:
        existing_template = clean_optional_text(str(item.get("preferred_template", "")))
        if existing_template != template_name or existing_template in FIXED_TEMPLATES:
            continue
        deck += 1
        if normalized_group and clean_optional_text(str(item.get("page_group", ""))) == normalized_group:
            page_group_hits += 1
        existing_pattern = clean_optional_text(str(item.get("advanced_pattern", "")))
        if normalized_pattern and existing_pattern == normalized_pattern:
            pattern_hits += 1
            if normalized_role and clean_optional_text(str(item.get("page_role", ""))) == normalized_role:
                role_pattern_hits += 1

    return {
        "deck": deck,
        "page_group": page_group_hits,
        "role_pattern": role_pattern_hits,
        "pattern": pattern_hits,
    }


def diversity_adjustment(
    planned_pages: list[dict[str, Any]] | None,
    *,
    template_name: str,
    page_group: str = "",
    page_role: str = "",
    advanced_pattern: str = "",
) -> int:
    stats = usage_count(
        planned_pages,
        template_name=template_name,
        page_group=page_group,
        page_role=page_role,
        advanced_pattern=advanced_pattern,
    )
    if template_name in FIXED_TEMPLATES:
        return 0

    score = 0
    if stats["deck"] == 0:
        score += 4
    elif stats["deck"] == 1:
        score += 1

    score -= stats["deck"] * 3
    score -= stats["page_group"] * 7
    score -= stats["pattern"] * 2
    score -= stats["role_pattern"] * 8

    if stats["deck"] >= TEMPLATE_DECK_SOFT_CAP:
        score -= 10 + (stats["deck"] - TEMPLATE_DECK_SOFT_CAP) * 6
    if stats["page_group"] >= TEMPLATE_PAGE_GROUP_SOFT_CAP:
        score -= 12 + (stats["page_group"] - TEMPLATE_PAGE_GROUP_SOFT_CAP) * 6
    if stats["role_pattern"] >= TEMPLATE_ROLE_PATTERN_SOFT_CAP:
        score -= 12 + (stats["role_pattern"] - TEMPLATE_ROLE_PATTERN_SOFT_CAP) * 6
    return score


def exceeds_diversity_soft_cap(
    planned_pages: list[dict[str, Any]] | None,
    *,
    template_name: str,
    page_group: str = "",
    page_role: str = "",
    advanced_pattern: str = "",
) -> bool:
    stats = usage_count(
        planned_pages,
        template_name=template_name,
        page_group=page_group,
        page_role=page_role,
        advanced_pattern=advanced_pattern,
    )
    return bool(
        stats["deck"] >= TEMPLATE_DECK_SOFT_CAP
        or stats["page_group"] >= TEMPLATE_PAGE_GROUP_SOFT_CAP
        or stats["role_pattern"] >= TEMPLATE_ROLE_PATTERN_SOFT_CAP
    )


def choose_ranked_template(
    ranked: list[dict[str, Any]],
    planned_pages: list[dict[str, Any]] | None,
    *,
    page_group: str = "",
    page_role: str = "",
    advanced_pattern: str = "",
) -> str:
    if not ranked:
        return ""

    best = ranked[0]
    best_score = int(best.get("score", 0))
    best_template = str(best.get("template_name", ""))
    best_tier = str(best.get("tier", "default"))
    best_semantic = int(best.get("semantic_score", 0))
    if not exceeds_diversity_soft_cap(
        planned_pages,
        template_name=best_template,
        page_group=page_group,
        page_role=page_role,
        advanced_pattern=advanced_pattern,
    ):
        return best_template

    same_tier_candidates = [
        candidate
        for candidate in ranked[1:]
        if template_tier_rank(str(candidate.get("tier", "default"))) == template_tier_rank(best_tier)
    ]
    for candidate in same_tier_candidates:
        score = int(candidate.get("score", 0))
        template_name = str(candidate.get("template_name", ""))
        if best_score - score > TEMPLATE_REBALANCE_TOLERANCE:
            break
        if not exceeds_diversity_soft_cap(
            planned_pages,
            template_name=template_name,
            page_group=page_group,
            page_role=page_role,
            advanced_pattern=advanced_pattern,
        ):
            return template_name

    for candidate in ranked[1:]:
        score = int(candidate.get("score", 0))
        template_name = str(candidate.get("template_name", ""))
        candidate_tier = str(candidate.get("tier", "default"))
        candidate_semantic = int(candidate.get("semantic_score", 0))
        if template_tier_rank(candidate_tier) <= template_tier_rank(best_tier):
            continue
        if best_score - score > TEMPLATE_REBALANCE_TOLERANCE:
            break
        if best_score - score > TEMPLATE_CROSS_TIER_TOLERANCE:
            continue
        if best_semantic - candidate_semantic > TEMPLATE_SEMANTIC_DRIFT_TOLERANCE:
            continue
        if candidate_semantic <= 0 and best_semantic > 0:
            continue
        if not exceeds_diversity_soft_cap(
            planned_pages,
            template_name=template_name,
            page_group=page_group,
            page_role=page_role,
            advanced_pattern=advanced_pattern,
        ):
            return template_name
    return best_template


def keyword_score(text: str, keywords: list[str] | tuple[str, ...], *, weight: int = 1) -> int:
    score = 0
    for keyword in keywords:
        if keyword and keyword in text:
            score += weight
    return score


def load_advanced_page_strategy(template_name: str) -> dict[str, Any]:
    template_id = normalize_template_id(template_name)
    if not template_id:
        return {}
    try:
        content = json.loads(LAYOUT_INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return content.get("layouts", {}).get(template_id, {}).get("advancedPageStrategy", {})


def choose_advanced_pattern_from_signals(entry: dict[str, str], strategy: dict[str, Any]) -> str:
    patterns = strategy.get("patterns", {})
    if not patterns:
        return "无"

    weighted_fields = [
        (normalize_signal_text(entry.get("页面类型", ""), entry.get("推荐页型", "")), 4),
        (normalize_signal_text(entry.get("页面意图", ""), entry.get("证明目标", "")), 3),
        (normalize_signal_text(entry.get("核心判断", "")), 3),
        (normalize_signal_text(entry.get("支撑证据", ""), entry.get("备注", "")), 2),
    ]
    best_pattern = "无"
    best_score = 0
    for pattern_name, meta in patterns.items():
        signals = ordered_unique(
            list(meta.get("triggerSignals", []) or [])
            + list(meta.get("fitFor", []) or [])
            + list(meta.get("structureSignals", []) or [])
        )
        score = 0
        for field_text, weight in weighted_fields:
            if not field_text:
                continue
            score += keyword_score(field_text, signals, weight=weight)
        label = clean_optional_text(meta.get("label", ""))
        if label:
            label_keywords = [part.strip() for part in re.split(r"[ /／]", label) if part.strip()]
            score += keyword_score(normalize_signal_text(*(field for field, _ in weighted_fields)), label_keywords, weight=1)
        if score > best_score:
            best_pattern = pattern_name
            best_score = score
    return best_pattern if best_score >= 3 else "无"


def choose_security_service_pattern(entry: dict[str, str], current_pattern: str) -> str:
    title_text = normalize_signal_text(entry.get("页面类型", ""), entry.get("推荐页型", ""))
    full_text = normalize_signal_text(
        entry.get("页面类型", ""),
        entry.get("推荐页型", ""),
        entry.get("页面意图", ""),
        entry.get("证明目标", ""),
        entry.get("核心判断", ""),
    )
    scores: dict[str, int] = {}
    if current_pattern not in {"", "无", "none"}:
        scores[current_pattern] = scores.get(current_pattern, 0) + 4

    for keywords, pattern_name in SECURITY_SERVICE_TITLE_PATTERN_RULES:
        score = keyword_score(title_text, keywords, weight=4) + keyword_score(full_text, keywords, weight=2)
        if score:
            scores[pattern_name] = scores.get(pattern_name, 0) + score

    if not scores:
        return current_pattern
    best_pattern, best_score = max(scores.items(), key=lambda item: (item[1], item[0]))
    return best_pattern if best_score >= 4 else current_pattern


def choose_standard_security_service_template(
    entry: dict[str, str],
    current_template: str,
    *,
    explicit_current: bool = False,
    planned_pages: list[dict[str, Any]] | None = None,
    page_role: str = "",
) -> str:
    candidates = ordered_unique(
        [
            current_template,
            "03_content.svg",
            "12_grid.svg",
            "07_data.svg",
            "16_table.svg",
        ]
    )
    signal_text = normalize_signal_text(
        entry.get("页面类型", ""),
        entry.get("推荐页型", ""),
        entry.get("页面意图", ""),
        entry.get("证明目标", ""),
        entry.get("核心判断", ""),
        entry.get("支撑证据", ""),
        entry.get("备注", ""),
    )
    page_group = page_group_key(entry)
    recommended_type = clean_optional_text(entry.get("推荐页型", ""))
    previous = planned_pages[-1] if planned_pages else None

    if explicit_current and current_template and current_template in candidates:
        return current_template

    def rank_candidate(template_name: str) -> dict[str, Any]:
        score = 0
        semantic_score = 0
        if template_name == current_template:
            score += 5
        semantic_score += keyword_score(signal_text, SECURITY_SERVICE_STANDARD_TEMPLATE_HINTS.get(template_name, ()), weight=2)

        if recommended_type:
            if recommended_type in {"概览页", "总览页"}:
                if template_name == "12_grid.svg":
                    semantic_score += 6
                if template_name == "03_content.svg":
                    semantic_score += 3
            if recommended_type in {"证据页", "结果页", "数据页"} and template_name == "07_data.svg":
                semantic_score += 8
            if recommended_type in {"问题拆解页", "清单页"} and template_name == "16_table.svg":
                semantic_score += 6

        if "关键结果" in signal_text or "重要成果" in signal_text:
            if template_name == "07_data.svg":
                semantic_score += 8
            if template_name == "12_grid.svg":
                semantic_score += 2
        if "整体回顾" in signal_text or "项目范围" in signal_text:
            if template_name == "12_grid.svg":
                semantic_score += 7
            if template_name == "03_content.svg":
                semantic_score += 3
        if any(token in signal_text for token in ("清理", "收尾", "账号", "遗留文件", "检查项")):
            if template_name == "16_table.svg":
                semantic_score += 9
            if template_name == "03_content.svg":
                semantic_score -= 2

        score += semantic_score

        if planned_pages:
            recent_same_template = sum(
                1
                for item in planned_pages[-3:]
                if clean_optional_text(item.get("preferred_template", "")) == template_name
            )
            same_group_run = sum(
                1
                for item in planned_pages[-3:]
                if clean_optional_text(item.get("preferred_template", "")) == template_name
                and clean_optional_text(item.get("page_group", "")) == page_group
            )
            score -= recent_same_template * 3
            score -= same_group_run * 4
            if previous and clean_optional_text(previous.get("preferred_template", "")) == template_name:
                score -= 5

        if template_name == "03_content.svg":
            score -= 4
        return build_ranked_candidate(template_name, score, semantic_score=semantic_score)

    ranked = sorted(
        (rank_candidate(template_name) for template_name in candidates),
        key=lambda item: (int(item["score"]), str(item["template_name"])),
        reverse=True,
    )
    return choose_ranked_template(
        ranked,
        planned_pages,
        page_group=page_group,
        page_role=page_role,
    )


def infer_advanced_pattern_from_entry(entry: dict[str, str]) -> str:
    inferred_mode = infer_complex_mode(entry)
    pattern = infer_advanced_pattern(inferred_mode)
    return pattern if pattern not in {"无", "none"} else "无"


def choose_template_for_pattern(
    current_template: str,
    advanced_pattern: str,
    strategy: dict[str, Any],
    *,
    explicit_current: bool = False,
    entry: dict[str, str] | None = None,
    planned_pages: list[dict[str, Any]] | None = None,
    primary_template: str = "",
    page_role: str = "",
) -> str:
    if advanced_pattern in {"无", "none"}:
        return current_template
    meta = strategy.get("patterns", {}).get(advanced_pattern, {})
    disallowed = set(meta.get("mustNotFallbackTo", []) or [])
    disallowed.update(strategy.get("fallbackGuard", {}).get("disallowedAsDefault", []) or [])
    primary_templates = meta.get("primaryTemplates", []) or []
    secondary_templates = meta.get("secondaryTemplates", []) or []
    fallback_templates = meta.get("fallbackTemplates", []) or []
    allowed_templates = set(primary_templates + secondary_templates + fallback_templates)

    if (
        explicit_current
        and current_template
        and current_template not in disallowed
        and (not allowed_templates or current_template in allowed_templates)
    ):
        return current_template
    if advanced_pattern == "attack_tree_architecture" and entry:
        issue_text = " ".join(
            [
                entry.get("页面类型", ""),
                entry.get("页面意图", ""),
                entry.get("核心判断", ""),
            ]
        )
        if "风险结构总览" in issue_text and "08_product.svg" in primary_templates:
            return "08_product.svg"
        if any(keyword in issue_text for keyword in ("安全意识", "员工", "人员", "钓鱼", "培训")):
            if "18_domain_capability_map.svg" in secondary_templates:
                return "18_domain_capability_map.svg"
        if any(keyword in issue_text for keyword in ("口令", "密码", "凭证", "账号")):
            if "17_service_overview.svg" in secondary_templates:
                return "17_service_overview.svg"
        if any(keyword in issue_text for keyword in ("审计", "端口", "驻留", "内网")):
            if "18_domain_capability_map.svg" in secondary_templates:
                return "18_domain_capability_map.svg"
    candidates = ordered_unique(
        primary_templates
        + secondary_templates
        + ([current_template] if current_template else [])
        + fallback_templates
    )
    if not candidates:
        if current_template and current_template not in disallowed:
            return current_template
        return secondary_templates[0] if secondary_templates else current_template

    signal_text = normalize_signal_text(
        entry.get("页面类型", "") if entry else "",
        entry.get("推荐页型", "") if entry else "",
        entry.get("页面意图", "") if entry else "",
        entry.get("证明目标", "") if entry else "",
        entry.get("核心判断", "") if entry else "",
        entry.get("支撑证据", "") if entry else "",
    )
    page_group = page_group_key(entry or {})
    previous = planned_pages[-1] if planned_pages else None

    def candidate_tier(template_name: str) -> str:
        if template_name in primary_templates:
            return "primary"
        if template_name in secondary_templates:
            return "secondary"
        if template_name in fallback_templates:
            return "fallback"
        return "default"

    def rank_candidate(template_name: str) -> dict[str, Any]:
        tier = candidate_tier(template_name)
        if template_name in disallowed:
            return build_ranked_candidate(template_name, -10_000, tier=tier, semantic_score=-10_000)
        score = 0
        semantic_score = 0
        if template_name in primary_templates:
            score += 18 - primary_templates.index(template_name) * 2
        elif template_name in secondary_templates:
            score += 12 - secondary_templates.index(template_name) * 2
        elif template_name in fallback_templates:
            score += 4 - fallback_templates.index(template_name)

        if template_name == current_template:
            score += 8 if explicit_current else 3

        template_hints = SECURITY_SERVICE_TEMPLATE_HINTS.get(advanced_pattern, {})
        for hinted_template, keywords in template_hints.items():
            if hinted_template != template_name:
                continue
            semantic_score += keyword_score(signal_text, keywords, weight=2)

        if planned_pages:
            recent_same_template = sum(
                1
                for item in planned_pages[-3:]
                if clean_optional_text(item.get("preferred_template", "")) == template_name
            )
            same_group_run = sum(
                1
                for item in planned_pages[-3:]
                if clean_optional_text(item.get("preferred_template", "")) == template_name
                and clean_optional_text(item.get("page_group", "")) == page_group
            )
            score -= recent_same_template * 3
            score -= same_group_run * 4
            if previous and clean_optional_text(previous.get("preferred_template", "")) == template_name:
                score -= 6
            if previous and clean_optional_text(previous.get("advanced_pattern", "")) == advanced_pattern and clean_optional_text(previous.get("preferred_template", "")) == template_name:
                score -= 4

        if primary_template == "security_service":
            if template_name in {"03_content.svg", "11_list.svg"}:
                score -= 20
            if advanced_pattern == "evidence_wall" and template_name == "12_grid.svg":
                semantic_score += 6
            if advanced_pattern == "governance_control_matrix" and template_name == "16_table.svg":
                semantic_score += 6
            if advanced_pattern == "swimlane_collaboration" and template_name == "05_case.svg":
                semantic_score += 6
            if advanced_pattern == "multi_lane_execution_chain" and template_name == "09_comparison.svg":
                semantic_score += 5

        score += semantic_score
        return build_ranked_candidate(template_name, score, tier=tier, semantic_score=semantic_score)

    ranked = sorted(
        (rank_candidate(template_name) for template_name in candidates),
        key=lambda item: (int(item["score"]), str(item["template_name"])),
        reverse=True,
    )
    best_score = int(ranked[0]["score"])
    best_template = str(ranked[0]["template_name"])
    if best_score <= -10_000:
        if primary_templates:
            return primary_templates[0]
        if current_template and current_template not in disallowed:
            return current_template
        return secondary_templates[0] if secondary_templates else current_template
    return choose_ranked_template(
        ranked,
        planned_pages,
        page_group=page_group,
        page_role=page_role,
        advanced_pattern=advanced_pattern,
    )


def resolve_page_plan(
    analysis: dict[str, Any],
    entry: dict[str, str],
    *,
    planned_pages: list[dict[str, Any]] | None = None,
) -> tuple[str, str, dict[str, str] | None]:
    page_num = entry.get("page_num", "")
    page_num_int = int(page_num) if str(page_num).isdigit() else None
    total_pages = len(analysis.get("outline_entries", []) or [])
    matched_complex = next((item for item in analysis["complex_pages"] if item["page_num"] == page_num), None)
    explicit_template = clean_optional_text(entry.get("优先页型", "") or entry.get("当前优先页型", ""))
    if explicit_template in FIXED_TEMPLATES and not fixed_template_matches_entry(
        explicit_template,
        entry,
        page_num=page_num_int,
        total_pages=total_pages,
    ):
        explicit_template = ""
    current_template = explicit_template or infer_preferred_template(
        entry,
        analysis["primary_template"],
        matched_complex,
        page_num=page_num_int,
        total_pages=total_pages,
    )
    if current_template in FIXED_TEMPLATES and fixed_template_matches_entry(
        current_template,
        entry,
        page_num=page_num_int,
        total_pages=total_pages,
    ):
        return "无", current_template, matched_complex
    if current_template in FIXED_TEMPLATES:
        current_template = ""
    explicit_pattern = clean_optional_text(entry.get("高级正文模式", "") or entry.get("当前高级正文模式", ""))
    if explicit_pattern and explicit_pattern not in {"待补齐", ""}:
        advanced_pattern = explicit_pattern
    else:
        advanced_pattern = infer_advanced_pattern(matched_complex) if matched_complex else "无"
    normalized_primary_template = normalize_template_id(str(analysis["primary_template"] or ""))
    strategy = load_advanced_page_strategy(str(analysis["primary_template"] or ""))

    if advanced_pattern in {"无", "none"}:
        advanced_pattern = infer_advanced_pattern_from_entry(entry)
    if advanced_pattern in {"无", "none"} and strategy:
        advanced_pattern = choose_advanced_pattern_from_signals(entry, strategy)
    if normalized_primary_template == "security_service":
        advanced_pattern = choose_security_service_pattern(entry, advanced_pattern)
    page_role = infer_page_role(entry, page_num_int or 0, total_pages, advanced_pattern)

    if advanced_pattern in {"无", "none"} and normalized_primary_template == "security_service":
        preferred_template = choose_standard_security_service_template(
            entry,
            current_template,
            explicit_current=bool(explicit_template),
            planned_pages=planned_pages,
            page_role=page_role,
        )
    else:
        preferred_template = choose_template_for_pattern(
            current_template,
            advanced_pattern,
            strategy,
            explicit_current=bool(explicit_template),
            entry=entry,
            planned_pages=planned_pages,
            primary_template=normalized_primary_template,
            page_role=page_role,
        )
    return advanced_pattern, preferred_template, matched_complex


def plan_outline_pages(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    planned_pages: list[dict[str, Any]] = []
    total_pages = len(analysis["outline_entries"])
    for index, entry in enumerate(analysis["outline_entries"]):
        advanced_pattern, preferred_template, matched_complex = resolve_page_plan(
            analysis,
            entry,
            planned_pages=planned_pages,
        )
        page_num = entry.get("page_num", str(index + 1))
        page_num_int = int(page_num) if str(page_num).isdigit() else index + 1
        page_role = infer_page_role(entry, page_num_int, total_pages, advanced_pattern)
        planned_pages.append(
            {
                "page_num": page_num,
                "title": entry.get("页面类型") or entry.get("推荐页型") or f"第 {page_num} 页",
                "advanced_pattern": advanced_pattern,
                "preferred_template": preferred_template,
                "matched_complex": matched_complex,
                "page_group": page_group_key(entry),
                "page_role": page_role,
            }
        )
    return planned_pages


def build_page_block(
    analysis: dict[str, Any],
    entry: dict[str, str],
    index: int,
    priorities: list[str],
    *,
    resolved_plan: dict[str, Any] | None = None,
) -> list[str]:
    page_num = entry.get("page_num", str(index + 1))
    page_title = entry.get("页面类型") or entry.get("推荐页型") or f"第 {page_num} 页"
    if resolved_plan:
        advanced_pattern = str(resolved_plan["advanced_pattern"])
        preferred_template = str(resolved_plan["preferred_template"])
        matched_complex = resolved_plan.get("matched_complex")
    else:
        advanced_pattern, preferred_template, matched_complex = resolve_page_plan(analysis, entry)
    layout_mode = infer_layout_mode(entry, preferred_template)
    total_pages = len(analysis["outline_entries"])
    page_num_int = int(page_num) if str(page_num).isdigit() else index + 1
    page_role = infer_page_role(entry, page_num_int, total_pages, advanced_pattern)

    previous_title = None
    next_title = None
    if index > 0:
        prev = analysis["outline_entries"][index - 1]
        previous_title = prev.get("页面类型") or prev.get("推荐页型") or f"第 {index} 页"
    if index + 1 < total_pages:
        nxt = analysis["outline_entries"][index + 1]
        next_title = nxt.get("页面类型") or nxt.get("推荐页型") or f"第 {index + 2} 页"

    previous_relation, next_relation = build_relation_text(previous_title, page_title, next_title, page_role)

    lines = [
        f"#### 第 {page_num} 页 {page_title}",
        f"- **布局**: {layout_mode}",
        f"- **页面意图**: {normalize_inline_text(entry.get('页面意图', '待补齐'))}",
        f"- **证明目标**: {normalize_inline_text(entry.get('证明目标', '待补齐'))}",
        f"- **高级正文模式**: {advanced_pattern}",
        f"- **优先页型**: `{preferred_template}`",
    ]
    if preferred_template in {"03_content.svg", "11_list.svg"}:
        lines.append(f"- **回退原因**: {infer_fallback_reason(entry)}")
    if advanced_pattern not in {"无", "none"}:
        lines.extend(
            [
                f"- **页面角色**: {page_role}",
                f"- **与上一页关系**: {previous_relation}",
                f"- **与下一页关系**: {next_relation}",
            ]
        )
    lines.extend(
        [
            f"- **标题**: {page_title}",
            f"- **Core Judgment**: {normalize_inline_text(entry.get('核心判断', '待补齐'))}",
            f"- **Supporting Evidence**: {normalize_inline_text(entry.get('支撑证据', '待补齐'))}",
            f"- **Recommended Page Type**: {normalize_inline_text(entry.get('推荐页型', '待补齐'))}",
            "- **Content Points**:",
            f"  - Audience Focus Alignment: {normalize_inline_text(str(analysis['answers'].get('audience', '') or '待补齐'))}",
            f"  - Goal Alignment: {normalize_inline_text(str(analysis['answers'].get('goal', '') or '待补齐'))}",
        ]
    )
    if matched_complex:
        lines.extend(
            [
                f"  - Complex Mode: {matched_complex['mode']}",
                f"  - Blueprint Suggestion: `{matched_complex['blueprint']}`",
            ]
        )
    lines.append("")
    return lines


def render_design_spec_text(analysis: dict[str, Any]) -> str:
    answers = analysis["answers"]
    brief_text = analysis["brief_text"]
    project_name = str(
        answers.get("project_name")
        or parse_brief_value(brief_text, "项目名称")
        or Path(analysis["project_dir"]).name
    )
    audience = str(answers.get("audience") or parse_brief_value(brief_text, "主要受众") or "待确认")
    scenario = str(answers.get("scenario") or parse_brief_value(brief_text, "场景") or "待确认")
    goal = str(answers.get("goal") or parse_brief_value(brief_text, "核心目标") or "待确认")
    style = str(answers.get("style") or parse_brief_value(brief_text, "风格偏好") or "待确认")
    language = str(answers.get("language") or parse_brief_value(brief_text, "语言") or "中文")
    format_key = str(answers.get("format") or parse_brief_value(brief_text, "输出格式") or "ppt169")
    priorities = list(answers.get("priorities") or [])
    canvas = CANVAS_SPECS.get(format_key, CANVAS_SPECS["ppt169"])
    primary_template = analysis["primary_template"] or "待确认"
    domain_name = str(analysis["recommended_domain"] or "待确认").strip("`")
    body_font_size = estimate_body_font_size(analysis)
    style_objective = estimate_style_objective(style, primary_template, domain_name)
    color_scheme = f"{primary_template or 'project'}_starter"

    lines = [
        f"# {project_name} - Design Specification",
        "",
        *GENERATED_HEADER,
        "",
        "## 0. Machine Readiness",
        f"canvas: {format_key}",
        f"body_font_size: {body_font_size}",
        f"color_scheme: {color_scheme}",
        f"font_plan: template_aligned_starter",
        f"page_count: {analysis['page_count']}",
        f"target_audience: {audience}",
        f"style_objective: {style_objective}",
        "",
        "## I. Project Information",
        f"- Project Name: {project_name}",
        f"- Canvas Format: {format_key} ({canvas['name']})",
        f"- Target Audience: {audience}",
        f"- Scenario: {scenario}",
        f"- Core Goal: {goal}",
        f"- Preferred Template: {primary_template}",
        f"- Domain Pack: {domain_name}",
        f"- Language: {language}",
        f"- Priority Messages: {', '.join(priorities) if priorities else '待补齐'}",
        "",
        "## II. Canvas Specification",
        f"- ViewBox: `{canvas['viewbox']}`",
        f"- Dimensions: {canvas['dimensions']}",
        "- Safe Area: 待结合模板固定骨架与品牌保护区进一步细化",
        "- Content Area: 默认位于标题区与页脚保护区之间，不得侵入 Logo 与底部装饰条",
        "",
        "## III. Visual Theme",
        f"- Theme Direction: 以 `{primary_template}` 模板骨架为基础，保持品牌元素固定，正文内容按 `{domain_name}` 叙事规则展开。",
        f"- Tone: {style}",
        "- Color Strategy: 以模板现有主色、强调色、安全区规则为准，避免在执行期自行换色。",
        "- Background Strategy: 固定页优先沿用模板背景；正文页在保护区内灵活排布信息层级。",
        "",
        "## IV. Typography System",
        "- Font Plan: 优先继承模板 design_spec 的字体组合，不在项目内临时混用多套字体。",
        f"- Body Font Size: {body_font_size}",
        "- Dense Page Override: 高信息密度页优先通过结构增密和拆页解决，不通过极端缩字号解决。",
        "",
        "## V. Layout Principles",
        "- Fixed Skeleton: Logo、页脚、装饰条、标题引导条、安全区必须固定保留。",
        "- Flexible Body: 正文区可根据页面意图命中不同页型与复杂结构，但不得侵入品牌保护区。",
        "- Soft QA First: 逐页检查中文断句、留白、拥挤感、卡片溢出、图文打架，而不是只在导出后补救。",
        "- Complexity Rule: 只有当文档天然存在链路、分层、矩阵、闭环或协同时，才启用高级正文模式。",
        "",
        "## VI. Input Assets",
    ]
    if analysis["sources"]:
        lines.extend(f"- Existing Source: {name}" for name in analysis["sources"])
    else:
        lines.append("- Existing Source: 当前未检测到归档源文件，执行前需确认是否仍需导入或补图")
    lines.extend(
        [
            f"- Template Docs: {', '.join(analysis['template_docs']) if analysis['template_docs'] else '待执行时人工补读'}",
            f"- Domain Docs: {', '.join(analysis['domain_docs']) if analysis['domain_docs'] else '待执行时人工补读'}",
            "- Image Policy: 优先使用原文档已有图片、原始截图和历史素材；只有原材料不足时才考虑 AI 补图。",
            "",
            "## VII. Execution Guardrails",
            "- 生成前先确认 design_spec、复杂页建模、模板骨架三者一致。",
            "- 复杂页先建模再绘制；普通页先检查信息密度再选布局。",
            "- 每页生成后立即做文本与版式 QA，不等待整套 PPT 导出后统一返工。",
            "",
            "## VIII. Content Outline",
            "",
        ]
    )

    planned_pages = plan_outline_pages(analysis)
    for index, (entry, resolved_plan) in enumerate(zip(analysis["outline_entries"], planned_pages)):
        lines.extend(build_page_block(analysis, entry, index, priorities, resolved_plan=resolved_plan))

    lines.extend(
        [
            "## IX. Speaker Notes Requirements",
            "- 每页备注至少写明：承接关系、核心讲法、时间提示。",
            "- 对复杂页，备注中需明确先看哪里、再如何展开节点与证据。",
            "",
            "## X. Next Actions",
            "- 若本文件为自动首稿，请优先补齐模板细节、行业规则和复杂页文字质量。",
            "- 复杂页标题若调整，需同步更新 `notes/complex_page_models.md` 对应标题。",
            "- 正式进入 Executor 前，必须完成 `design_spec_validator.py` 与复杂页建模检查。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_project_design_spec(
    project_path: str | Path,
    *,
    force: bool = False,
) -> tuple[Path, bool, str]:
    project_dir = Path(project_path).expanduser().resolve()
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    design_spec_path = project_dir / "design_spec.md"
    if design_spec_path.exists() and not force:
        return design_spec_path, False, "已存在 design_spec.md，默认保留现有文件。"

    analysis = analyze_project(project_dir)
    content = render_design_spec_text(analysis)
    design_spec_path.write_text(content, encoding="utf-8")
    return design_spec_path, True, "已生成项目级 design_spec.md 首稿。"


def main() -> None:
    parser = argparse.ArgumentParser(description="基于 Agent 规划结果生成项目根目录 design_spec.md 首稿。")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--force", action="store_true", help="已存在 design_spec.md 时强制覆盖")
    args = parser.parse_args()

    path, written, message = build_project_design_spec(args.project_path, force=args.force)
    print(message)
    print(f"design_spec: {path}")
    if not written:
        print("如需刷新，请重新执行并加上 `--force`。")


if __name__ == "__main__":
    main()
