#!/usr/bin/env python3
"""Build SVG execution orchestration assets from project design_spec.md."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from check_complex_page_model import extract_model_blocks, parse_model_block
except ImportError:
    import sys

    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from check_complex_page_model import extract_model_blocks, parse_model_block  # type: ignore


FIXED_TEMPLATES = {"01_cover.svg", "02_toc.svg", "02_chapter.svg", "04_ending.svg"}
EXECUTION_CONTRACTS_FILENAME = "page_execution_contracts.json"
PAGE_CONTEXT_DIRNAME = "page_context_min"
QUEUE_MACHINE_FILENAME = "svg_execution_queue.machine.json"
REPEAT_WARNING_WINDOW = 4
TEMPLATE_DECK_WARNING_CAP = 2
TEMPLATE_STABILITY_HINTS = {
    "05_case.svg": "stable",
    "07_data.svg": "stable",
    "08_product.svg": "heavy",
    "09_comparison.svg": "balanced",
    "10_timeline.svg": "stable",
    "11_list.svg": "stable",
    "12_grid.svg": "stable",
    "13_highlight.svg": "stable",
    "16_table.svg": "stable",
    "17_service_overview.svg": "heavy",
    "18_domain_capability_map.svg": "heavy",
    "19_result_leading_case.svg": "stable",
}
STABLE_COMPLEX_TEMPLATES = {
    "05_case.svg",
    "07_data.svg",
    "12_grid.svg",
    "16_table.svg",
    "19_result_leading_case.svg",
}
BOUNDED_COMPLEX_TEMPLATES = {"09_comparison.svg", "10_timeline.svg"}
HEAVY_COMPLEX_TEMPLATES = {
    "08_product.svg",
    "17_service_overview.svg",
    "18_domain_capability_map.svg",
}
GENERIC_EVIDENCE_VALUES = {"关键证据", "证据", "风险", "结果", "判断", "支撑证据"}
EVIDENCE_SIGNAL_MARKERS = (
    "rce",
    "webshell",
    "内存马",
    "漏洞",
    "权限",
    "凭证",
    "后台",
    "数据库",
    "服务器",
    "日志",
    "敏感",
    "ip",
    "弱口令",
    "横向",
    "域控",
    "命令执行",
    "落点",
    "钓鱼",
    "外联",
)
PLANNING_TONE_MARKERS = (
    "建议",
    "规划",
    "后续",
    "推进",
    "需要",
    "可从",
    "应当",
    "拟",
    "计划",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str, *, overwrite: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return
    path.write_text(content, encoding="utf-8")


def clean_text(value: str) -> str:
    cleaned = re.sub(r"[`*]", "", value or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_semantic_text(value: str) -> str:
    return re.sub(r"[\s，,；;。:：、\-_/()（）]", "", clean_text(value)).lower()


def split_brief_points(value: str, *, limit: int = 8) -> list[str]:
    cleaned = clean_text(value)
    if not cleaned:
        return []
    parts = re.split(r"(?:\s*[①②③④⑤⑥⑦⑧⑨⑩]\s*|\n+|[；;。])", cleaned)
    results: list[str] = []
    for part in parts:
        text = clean_text(re.sub(r"^[\-\d\.、]+\s*", "", part))
        if not text:
            continue
        results.append(text)
        if len(results) >= limit:
            return results
    if len(results) <= 1 and ("，" in cleaned or "," in cleaned):
        comma_parts = re.split(r"[，,]", cleaned)
        for part in comma_parts:
            text = clean_text(re.sub(r"^[\-\d\.、]+\s*", "", part))
            if not text:
                continue
            results.append(text)
            if len(results) >= limit:
                break
    return results[:limit]


def compact_highlight(value: str, *, limit: int = 22) -> str:
    text = clean_text(re.sub(r"^[^：:]{1,16}[：:]\s*", "", value))
    text = re.sub(r"[。；;]+$", "", text)
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def looks_like_high_value_evidence(value: str) -> bool:
    text = compact_highlight(value)
    if not text or text in GENERIC_EVIDENCE_VALUES or len(text) <= 4:
        return False
    if text.lower().endswith(".svg") or re.fullmatch(r"\d{2}[a-z_]+\.svg", text.lower()):
        return False
    lowered = text.lower()
    if any(marker in text for marker in PLANNING_TONE_MARKERS):
        return False
    if any(marker in lowered for marker in EVIDENCE_SIGNAL_MARKERS):
        return True
    if re.search(r"\d", text):
        return True
    if any(token in text for token in ("总览", "概览", "概述", "路径分析", "布局", "页面", "页型")):
        return False
    return len(normalize_semantic_text(text)) >= 8


def evidence_score(value: str) -> tuple[int, int]:
    text = compact_highlight(value)
    lowered = text.lower()
    score = sum(2 for marker in EVIDENCE_SIGNAL_MARKERS if marker in lowered)
    if re.search(r"\d", text):
        score += 1
    if len(text) >= 8:
        score += 1
    return score, -len(text)


def extract_first_value(block: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        pattern = rf"(?im)^\s*-\s*\*\*{re.escape(label)}\*\*\s*[:：]\s*(.+)$"
        match = re.search(pattern, block)
        if match:
            return clean_text(match.group(1))
    return ""


def split_page_blocks(content: str) -> list[tuple[str, str]]:
    match = re.search(r"(?ms)^## VIII\. Content Outline\s*$\n(.*?)(?=^## IX\.)", content)
    if not match:
        return []
    outline_body = match.group(1)
    heading_re = re.compile(r"(?im)^####\s+(.+)$")
    matches = list(heading_re.finditer(outline_body))
    blocks: list[tuple[str, str]] = []
    for idx, item in enumerate(matches):
        start = item.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(outline_body)
        blocks.append((item.group(1).strip(), outline_body[start:end]))
    return blocks


def parse_design_spec_pages(design_spec_path: Path) -> list[dict[str, str]]:
    content = read_text(design_spec_path)
    pages: list[dict[str, str]] = []
    for idx, (heading, block) in enumerate(split_page_blocks(content), start=1):
        title_match = re.match(r"第\s*(\d+)\s*页\s*(.+)", heading)
        page_num = title_match.group(1) if title_match else str(idx)
        title = title_match.group(2).strip() if title_match else heading
        pages.append(
            {
                "page_num": page_num,
                "title": title,
                "layout": extract_first_value(block, ("布局", "Layout")),
                "page_intent": extract_first_value(block, ("页面意图", "Page Intent")),
                "proof_goal": extract_first_value(block, ("证明目标", "Proof Goal")),
                "advanced_pattern": extract_first_value(block, ("高级正文模式", "Advanced Pattern")) or "无",
                "preferred_template": extract_first_value(block, ("优先页型", "Preferred Template")),
                "fallback_reason": extract_first_value(block, ("回退原因", "Fallback Reason")),
                "page_role": extract_first_value(block, ("页面角色", "Page Role")),
                "prev_relation": extract_first_value(block, ("与上一页关系", "Relation To Previous Page")),
                "next_relation": extract_first_value(block, ("与下一页关系", "Relation To Next Page")),
                "core_judgment": extract_first_value(block, ("Core Judgment", "核心判断")),
                "supporting_evidence": extract_first_value(block, ("Supporting Evidence", "支撑证据")),
                "recommended_page_type": extract_first_value(block, ("Recommended Page Type", "推荐页型")),
            }
        )
    return pages


def page_family(page: dict[str, str]) -> str:
    template_name = page.get("preferred_template", "")
    pattern = page.get("advanced_pattern", "")
    if template_name in FIXED_TEMPLATES:
        return "fixed"
    if pattern and pattern not in {"无", "none"}:
        return "complex"
    return "standard"


def normalize_pattern_token(value: str) -> str:
    token = clean_text(value or "").lower()
    return "none" if token in {"", "无", "none"} else token


def resolve_template_stability(page: dict[str, Any]) -> str:
    family = page_family(page)
    template_name = clean_text(str(page.get("preferred_template", "")))
    if family == "fixed":
        return "fixed"
    if template_name in TEMPLATE_STABILITY_HINTS:
        return TEMPLATE_STABILITY_HINTS[template_name]
    if family == "complex":
        return "balanced" if template_name else "heavy"
    return "stable" if template_name else "balanced"


def resolve_complex_class(page: dict[str, Any]) -> str:
    if page_family(page) != "complex":
        return "not_complex"
    template_name = clean_text(str(page.get("preferred_template", "")))
    if template_name in STABLE_COMPLEX_TEMPLATES:
        return "stable_complex"
    if template_name in BOUNDED_COMPLEX_TEMPLATES:
        return "bounded_complex"
    if template_name in HEAVY_COMPLEX_TEMPLATES:
        return "heavy_complex"
    stability = str(page.get("template_stability") or resolve_template_stability(page))
    if stability == "heavy":
        return "heavy_complex"
    if stability == "balanced":
        return "bounded_complex"
    return "stable_complex"


def build_layout_signature(page: dict[str, Any]) -> str:
    return (
        f"{page_family(page)}:"
        f"{clean_text(str(page.get('preferred_template', ''))) or 'auto'}:"
        f"{normalize_pattern_token(str(page.get('advanced_pattern', '无')))}"
    )


def repeat_block_reason(prev_page: dict[str, Any] | None, page: dict[str, Any]) -> str:
    if not prev_page:
        return ""
    current_family = page_family(page)
    prev_family = page_family(prev_page)
    if "fixed" in {current_family, prev_family}:
        return ""
    current_template = clean_text(str(page.get("preferred_template", "")))
    prev_template = clean_text(str(prev_page.get("preferred_template", "")))
    if not current_template or current_template != prev_template:
        return ""

    current_pattern = normalize_pattern_token(str(page.get("advanced_pattern", "无")))
    prev_pattern = normalize_pattern_token(str(prev_page.get("advanced_pattern", "无")))
    if current_family == prev_family == "standard":
        return (
            f"与上一页第 {prev_page.get('page_num')} 页连续复用同一正文骨架 "
            f"`{current_template}`，已触发前置重复布局阻断。"
        )
    if current_pattern == prev_pattern and current_pattern != "none":
        return (
            f"与上一页第 {prev_page.get('page_num')} 页连续复用同一复杂骨架 "
            f"`{current_template}` / 模式 `{page.get('advanced_pattern') or '无'}`，"
            "已触发前置重复布局阻断。"
        )
    return (
        f"与上一页第 {prev_page.get('page_num')} 页连续复用同一布局骨架 "
        f"`{current_template}`，即使主题不同也容易形成视觉重复，已触发前置重复布局阻断。"
    )


def repeat_window_warning(recent_pages: list[dict[str, Any]], page: dict[str, Any]) -> list[str]:
    current_template = clean_text(str(page.get("preferred_template", "")))
    if not current_template:
        return []
    warnings: list[str] = []
    for prev_page in recent_pages[-REPEAT_WARNING_WINDOW:]:
        if clean_text(str(prev_page.get("preferred_template", ""))) != current_template:
            continue
        warnings.append(
            f"最近 {REPEAT_WARNING_WINDOW + 1} 个正文页窗口内再次命中 `{current_template}`，"
            f"请确认第 {page.get('page_num')} 页不会与第 {prev_page.get('page_num')} 页产生视觉复用。"
        )
        break
    return warnings


def deck_repeat_warning(content_pages: list[dict[str, Any]], page: dict[str, Any]) -> list[str]:
    current_template = clean_text(str(page.get("preferred_template", "")))
    if not current_template or current_template in FIXED_TEMPLATES:
        return []

    current_pattern = normalize_pattern_token(str(page.get("advanced_pattern", "无")))
    same_template_pages = [
        prev_page
        for prev_page in content_pages
        if clean_text(str(prev_page.get("preferred_template", ""))) == current_template
    ]
    if len(same_template_pages) < TEMPLATE_DECK_WARNING_CAP:
        return []

    latest_page = same_template_pages[-1]
    warnings = [
        f"`{current_template}` 在正文中已累计出现 {len(same_template_pages) + 1} 次，"
        f"第 {page.get('page_num')} 页请确认是否仍必须沿用该骨架；最近一次出现在第 {latest_page.get('page_num')} 页。"
    ]
    if current_pattern != "none":
        same_pattern_pages = [
            prev_page
            for prev_page in same_template_pages
            if normalize_pattern_token(str(prev_page.get("advanced_pattern", "无"))) == current_pattern
        ]
        if same_pattern_pages:
            warnings.append(
                f"当前页模式 `{page.get('advanced_pattern') or '无'}` 与既有同模板页存在叠加，"
                "请优先检查是否还有同语义但不同骨架的候选模板。"
            )
    return warnings


def semantic_overlap_warning(recent_pages: list[dict[str, Any]], page: dict[str, Any]) -> list[str]:
    current_template = clean_text(str(page.get("preferred_template", "")))
    current_pattern = normalize_pattern_token(str(page.get("advanced_pattern", "无")))
    current_core = normalize_semantic_text(str(page.get("core_judgment", "")))
    current_goal = normalize_semantic_text(str(page.get("proof_goal", "")))
    if not (current_core or current_goal):
        return []

    warnings: list[str] = []
    for prev_page in recent_pages[-REPEAT_WARNING_WINDOW:]:
        prev_template = clean_text(str(prev_page.get("preferred_template", "")))
        prev_pattern = normalize_pattern_token(str(prev_page.get("advanced_pattern", "无")))
        prev_core = normalize_semantic_text(str(prev_page.get("core_judgment", "")))
        prev_goal = normalize_semantic_text(str(prev_page.get("proof_goal", "")))
        if not (prev_core or prev_goal):
            continue
        same_template_or_pattern = bool(
            current_template
            and prev_template
            and current_template == prev_template
        ) or (current_pattern != "none" and current_pattern == prev_pattern)
        if not same_template_or_pattern:
            continue
        if current_core and prev_core and (current_core == prev_core or current_core in prev_core or prev_core in current_core):
            warnings.append(
                f"第 {page.get('page_num')} 页与第 {prev_page.get('page_num')} 页的核心判断高度相近，"
                "请确认相邻页不是在重复表达同一结论。"
            )
            break
        if current_goal and prev_goal and (current_goal == prev_goal or current_goal in prev_goal or prev_goal in current_goal):
            warnings.append(
                f"第 {page.get('page_num')} 页与第 {prev_page.get('page_num')} 页的证明目标高度相近，"
                "请确认相邻页不是在重复推进同一证明。"
            )
            break
    return warnings


def prepare_execution_pages(pages: list[dict[str, str]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    recent_content_pages: list[dict[str, Any]] = []
    content_pages: list[dict[str, Any]] = []
    for raw_page in pages:
        page: dict[str, Any] = dict(raw_page)
        family = page_family(page)
        blockers: list[str] = []
        warnings: list[str] = []
        page["template_stability"] = resolve_template_stability(page)
        page["complex_class"] = resolve_complex_class(page)
        if family == "fixed":
            recent_content_pages = []
        else:
            blockers_reason = repeat_block_reason(recent_content_pages[-1] if recent_content_pages else None, page)
            if blockers_reason:
                blockers.append(blockers_reason)
            else:
                warnings.extend(repeat_window_warning(recent_content_pages, page))
                warnings.extend(semantic_overlap_warning(recent_content_pages, page))
                warnings.extend(deck_repeat_warning(content_pages, page))
            recent_content_pages.append(page)
            recent_content_pages = recent_content_pages[-(REPEAT_WARNING_WINDOW + 1) :]
            content_pages.append(page)

        page["layout_signature"] = build_layout_signature(page)
        page["preflight_blockers"] = blockers
        page["preflight_warnings"] = warnings
        page["repeat_risk"] = "hard_block" if blockers else ("warning" if warnings else "none")
        prepared.append(page)
    return prepared


def filename_slug(title: str) -> str:
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", title.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "page"


def expected_svg_name(page: dict[str, str]) -> str:
    return f"{int(page['page_num']):02d}_{filename_slug(page['title'])}.svg"


def qa_focus(page: dict[str, str]) -> str:
    family = page_family(page)
    if family == "fixed":
        return "品牌骨架、Logo、安全区、页码与固定装饰条不允许被正文侵入。"
    if family == "complex":
        return "重点检查结构是否清晰、模块是否重叠、证据挂载是否抢焦点、阅读顺序是否成立。"
    return "重点检查文本断句、卡片贴边、拥挤感、内容密度和与品牌区的冲突。"


def execution_policy(page: dict[str, str]) -> dict[str, Any]:
    family = page_family(page)
    preferred_template = clean_text(page.get("preferred_template", ""))
    layout_locked = bool(preferred_template) or family == "fixed"
    template_stability = str(page.get("template_stability") or resolve_template_stability(page))
    complex_class = str(page.get("complex_class") or resolve_complex_class(page))
    preflight_blockers = list(page.get("preflight_blockers") or [])
    preflight_warnings = list(page.get("preflight_warnings") or [])

    if family == "fixed":
        policy = {
            "page_family": family,
            "render_lane": "fixed_fast_lane",
            "qa_tier": "brand_skeleton",
            "preview_strategy": "on_error",
            "layout_locked": True,
            "default_auto_repair_rounds": 0,
            "soft_qa_mode": "never",
            "allow_preflight_progression_reframe": False,
            "allow_runtime_progression_reframe": False,
        }
        policy["template_stability"] = template_stability
        policy["complex_class"] = complex_class
        policy["stable_skeleton_hit"] = True
        policy["preflight_blockers"] = preflight_blockers
        policy["preflight_warnings"] = preflight_warnings
        return policy

    if family == "complex":
        stable_complex_hit = layout_locked and complex_class == "stable_complex"
        bounded_complex_hit = layout_locked and complex_class == "bounded_complex"
        policy = {
            "page_family": family,
            "render_lane": (
                "complex_fast_lane"
                if stable_complex_hit
                else ("complex_bounded_lane" if bounded_complex_hit else "complex_heavy_lane")
            ),
            "qa_tier": "complex_full",
            # Preview rendering is the dominant cost in full runs. Even heavy pages should
            # render previews only when the current round already shows errors or blockers.
            "preview_strategy": "on_error",
            "layout_locked": layout_locked,
            "default_auto_repair_rounds": 0 if stable_complex_hit else 1,
            # Keep heavy pages on semantic QA, but trigger it by signal instead of forcing
            # the most expensive path on every clean first-round render.
            "soft_qa_mode": "on_signal",
            "allow_preflight_progression_reframe": True,
            "allow_runtime_progression_reframe": False,
        }
        policy["template_stability"] = template_stability
        policy["complex_class"] = complex_class
        policy["stable_skeleton_hit"] = stable_complex_hit or bounded_complex_hit
        policy["preflight_blockers"] = preflight_blockers
        policy["preflight_warnings"] = preflight_warnings
        return policy

    stable_standard_hit = layout_locked and template_stability == "stable"
    policy = {
        "page_family": family,
        "render_lane": "standard_fast_lane" if stable_standard_hit else "standard_balanced_lane",
        "qa_tier": "layout_and_density",
        "preview_strategy": "on_error",
        "layout_locked": layout_locked,
        "default_auto_repair_rounds": 0 if stable_standard_hit else 1,
        "soft_qa_mode": "never",
        "allow_preflight_progression_reframe": False,
        "allow_runtime_progression_reframe": False,
    }
    policy["template_stability"] = template_stability
    policy["complex_class"] = complex_class
    policy["stable_skeleton_hit"] = stable_standard_hit
    policy["preflight_blockers"] = preflight_blockers
    policy["preflight_warnings"] = preflight_warnings
    return policy


def page_context_path(briefs_dir: Path, expected_svg: str) -> Path:
    return briefs_dir / f"{expected_svg.replace('.svg', '')}.json"


def page_summary(page: dict[str, Any]) -> str:
    return clean_text(
        str(page.get("core_judgment") or page.get("proof_goal") or page.get("page_intent") or page.get("title") or "")
    )


def prune_complex_model(model: dict[str, Any]) -> dict[str, Any]:
    if not model:
        return {}
    keep_keys = [
        "heading",
        "page_role",
        "page_intent",
        "proof_goal",
        "main_judgment",
        "sub_judgment_items",
        "argument_spine_items",
        "key_nodes_items",
        "key_relations_items",
        "evidence_plan_items",
        "visual_focus_items",
        "closure_items",
    ]
    pruned: dict[str, Any] = {}
    for key in keep_keys:
        value = model.get(key)
        if value in ("", [], None):
            continue
        pruned[key] = value
    return pruned


def collect_evidence_highlights(
    page: dict[str, Any],
    complex_model: dict[str, Any],
    *,
    limit: int = 4,
) -> list[str]:
    candidates: list[str] = []
    candidates.extend(split_brief_points(str(page.get("supporting_evidence") or ""), limit=8))
    candidates.extend(split_brief_points(str(page.get("core_judgment") or ""), limit=4))
    for key in ("evidence_plan_items", "key_nodes_items", "key_relations_items", "closure_items"):
        value = complex_model.get(key)
        if isinstance(value, list):
            candidates.extend(clean_text(str(item)) for item in value if clean_text(str(item)))
        elif isinstance(value, str):
            candidates.extend(split_brief_points(value, limit=6))

    ranked: list[tuple[tuple[int, int], str, str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        highlight = compact_highlight(candidate)
        normalized = normalize_semantic_text(highlight)
        if not normalized or normalized in seen or not looks_like_high_value_evidence(highlight):
            continue
        seen.add(normalized)
        ranked.append((evidence_score(highlight), normalized, highlight))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [item[2] for item in ranked[:limit]]


def load_complex_model_map(project_dir: Path) -> dict[str, dict[str, Any]]:
    model_path = project_dir / "notes" / "complex_page_models.md"
    if not model_path.exists():
        return {}
    content = read_text(model_path)
    if not content.strip():
        return {}
    model_map: dict[str, dict[str, Any]] = {}
    for title, block in extract_model_blocks(content).items():
        parsed = parse_model_block(title, block)
        page_num_match = re.match(r"^第\s*(\d+)\s*页\s*(.+)$", title)
        if page_num_match:
            model_map[page_num_match.group(1)] = parsed
    return model_map


def build_page_context_payload(
    page: dict[str, Any],
    *,
    policy: dict[str, Any],
    prev_page: dict[str, Any] | None,
    next_page: dict[str, Any] | None,
    complex_model: dict[str, Any],
) -> dict[str, Any]:
    evidence_highlights = collect_evidence_highlights(page, complex_model, limit=4)
    return {
        "page_num": str(page.get("page_num") or ""),
        "expected_svg": expected_svg_name(page),
        "page_title": str(page.get("title") or ""),
        "page_role": str(page.get("page_role") or ""),
        "page_intent": str(page.get("page_intent") or ""),
        "proof_goal": str(page.get("proof_goal") or ""),
        "core_judgment": str(page.get("core_judgment") or ""),
        "supporting_evidence": str(page.get("supporting_evidence") or ""),
        "semantic_points": [
            item
            for item in [
                clean_text(str(page.get("core_judgment") or "")),
                clean_text(str(page.get("proof_goal") or "")),
                clean_text(str(page.get("supporting_evidence") or "")),
            ]
            if item
        ],
        "evidence_highlights": evidence_highlights,
        "preferred_template": str(page.get("preferred_template") or ""),
        "advanced_pattern": str(page.get("advanced_pattern") or "无"),
        "relations": {
            "prev_relation": str(page.get("prev_relation") or ""),
            "next_relation": str(page.get("next_relation") or ""),
        },
        "neighbors": {
            "previous": {
                "page_num": str(prev_page.get("page_num") or ""),
                "title": str(prev_page.get("title") or ""),
                "summary": page_summary(prev_page),
            }
            if prev_page
            else {},
            "next": {
                "page_num": str(next_page.get("page_num") or ""),
                "title": str(next_page.get("title") or ""),
                "summary": page_summary(next_page),
            }
            if next_page
            else {},
        },
        "template_rules": {
            "page_family": str(policy.get("page_family") or ""),
            "preferred_template": str(page.get("preferred_template") or ""),
            "template_stability": str(policy.get("template_stability") or ""),
            "complex_class": str(policy.get("complex_class") or ""),
            "layout_locked": bool(policy.get("layout_locked", False)),
            "render_lane": str(policy.get("render_lane") or ""),
            "qa_tier": str(policy.get("qa_tier") or ""),
            "soft_qa_mode": str(policy.get("soft_qa_mode") or ""),
            "preview_strategy": str(policy.get("preview_strategy") or ""),
            "preflight_warnings": list(policy.get("preflight_warnings") or []),
        },
        "complex_model": prune_complex_model(complex_model),
    }


def write_page_context_files(project_dir: Path, pages: list[dict[str, Any]], notes_dir: Path) -> Path:
    context_dir = notes_dir / PAGE_CONTEXT_DIRNAME
    context_dir.mkdir(parents=True, exist_ok=True)
    model_map = load_complex_model_map(project_dir)
    for index, page in enumerate(pages):
        prev_page = pages[index - 1] if index > 0 else None
        next_page = pages[index + 1] if index + 1 < len(pages) else None
        policy = execution_policy(page)
        payload = build_page_context_payload(
            page,
            policy=policy,
            prev_page=prev_page,
            next_page=next_page,
            complex_model=model_map.get(str(page.get("page_num") or ""), {}),
        )
        write_text(
            page_context_path(context_dir, expected_svg_name(page)),
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        )
    return context_dir


def build_queue_text(project_path: Path, pages: list[dict[str, str]]) -> str:
    lines = [
        "# SVG 执行队列",
        "",
        f"- Project: `{project_path}`",
        f"- Total Pages: {len(pages)}",
        f"- Fixed Pages: {sum(1 for page in pages if page_family(page) == 'fixed')}",
        f"- Standard Pages: {sum(1 for page in pages if page_family(page) == 'standard')}",
        f"- Complex Pages: {sum(1 for page in pages if page_family(page) == 'complex')}",
        "",
        "## 执行顺序",
        "- 严格按页序生成，不跳页并行。",
        "- 每页生成完成后立即做当前页 QA，再进入下一页。",
        "- 命中复杂页时，先看复杂页建模，再开始画 SVG。",
        "",
    ]
    for page in pages:
        policy = execution_policy(page)
        summary = page_summary(page)
        lines.extend(
            [
                f"### 第 {page['page_num']} 页 - {page['title']}",
                f"- 执行摘要：`{expected_svg_name(page)}` / `{page_family(page)}` / lane=`{policy['render_lane']}` / class=`{policy['complex_class']}`",
                f"- 结构提醒：页型=`{page.get('preferred_template') or '待补齐'}` / 模式=`{page.get('advanced_pattern') or '无'}` / Soft QA=`{policy['soft_qa_mode']}`",
                f"- 页面摘要：{summary or '待补齐'}",
                f"- 事实入口：`notes/{PAGE_CONTEXT_DIRNAME}/{expected_svg_name(page).replace('.svg', '.json')}`",
                f"- 人工提醒：`notes/page_briefs/{expected_svg_name(page).replace('.svg', '.md')}`",
                (
                    f"- 前置阻断：{'；'.join(policy['preflight_blockers'])}"
                    if policy["preflight_blockers"]
                    else "- 前置阻断：无"
                ),
                (
                    f"- 预警：{'；'.join(policy['preflight_warnings'])}"
                    if policy["preflight_warnings"]
                    else "- 预警：无"
                ),
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def build_machine_queue_payload(project_path: Path, pages: list[dict[str, Any]], notes_dir: Path) -> dict[str, Any]:
    context_dir = notes_dir / PAGE_CONTEXT_DIRNAME
    page_briefs_dir = notes_dir / "page_briefs"
    page_items: list[dict[str, Any]] = []
    for page in pages:
        policy = execution_policy(page)
        expected_svg = expected_svg_name(page)
        page_items.append(
            {
                "page_num": str(page.get("page_num") or ""),
                "title": str(page.get("title") or ""),
                "expected_svg": expected_svg,
                "page_family": page_family(page),
                "summary": page_summary(page),
                "page_role": str(page.get("page_role") or ""),
                "page_intent": str(page.get("page_intent") or ""),
                "proof_goal": str(page.get("proof_goal") or ""),
                "core_judgment": str(page.get("core_judgment") or ""),
                "supporting_evidence": str(page.get("supporting_evidence") or ""),
                "preferred_template": str(page.get("preferred_template") or ""),
                "advanced_pattern": str(page.get("advanced_pattern") or "无"),
                "brief_path": str(page_briefs_dir / expected_svg.replace(".svg", ".md")),
                "context_min_path": str(page_context_path(context_dir, expected_svg)),
                "qa_focus": qa_focus(page),
                "preflight_blockers": list(policy.get("preflight_blockers") or []),
                "preflight_warnings": list(policy.get("preflight_warnings") or []),
                "execution_policy": policy,
            }
        )
    return {
        "project": str(project_path),
        "total_pages": len(page_items),
        "fixed_pages": sum(1 for page in pages if page_family(page) == "fixed"),
        "standard_pages": sum(1 for page in pages if page_family(page) == "standard"),
        "complex_pages": sum(1 for page in pages if page_family(page) == "complex"),
        "pages": page_items,
    }


def build_status_text(project_path: Path, pages: list[dict[str, str]]) -> str:
    lines = [
        "# SVG 执行状态",
        "",
        f"- Project: `{project_path}`",
        "- Status: ready_to_generate_svg",
        "",
        "## 阶段状态",
        "- design_spec: done",
        "- complex_page_models: done",
        "- page_briefs: done",
        "- svg_generation: pending",
        "- notes_generation: pending",
        "- postprocess: pending",
        "- export: pending",
        "",
        "## 页面进度",
    ]
    for page in pages:
        lines.append(f"- [ ] {expected_svg_name(page)}")
    return "\n".join(lines) + "\n"


def build_postprocess_text(project_path: Path) -> str:
    return "\n".join(
        [
            "# SVG 后处理与导出计划",
            "",
            f"- Project: `{project_path}`",
            "",
            "## 生成完全部 `svg_output/` 后执行",
            "```bash",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/check_svg_text_fit.py {project_path}/svg_output",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/finalize_svg.py {project_path}",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/check_svg_text_fit.py {project_path}/svg_final",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/render_svg_pages.py {project_path} -s final",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/write_qa_manifest.py {project_path} --format ppt169",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py status {project_path}",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/svg_to_pptx.py {project_path} -s final",
            "```",
            "",
            "## 门禁",
            "- `svg_output` 与 `svg_final` 的文本适配检查都必须通过。",
            "- `qa_manifest.json` 的关键质量项未通过时，不得交付。",
            "- `ppt_agent.py status` / `project_manager.py validate` 与 `svg_to_pptx.py` 现在共用同一套 export gate 状态；先看状态，再决定是否导出。",
            "- `svg_to_pptx.py` 现已内置导出前 QA 门禁；若存在阻断项，会自动刷新 `qa_manifest.json` 并拒绝导出最终 PPT。",
        ]
    ) + "\n"


def build_total_md_skeleton(pages: list[dict[str, str]]) -> str:
    sections: list[str] = []
    for page in pages:
        svg_name = expected_svg_name(page)
        sections.extend(
            [
                f"# {svg_name}",
                "",
                "[过渡] ",
                "",
                "要点：",
                "① ",
                "② ",
                "③ ",
                "",
                "时长：待补齐",
                "",
                "---",
                "",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"


def build_page_brief_text(page: dict[str, str]) -> str:
    policy = execution_policy(page)
    lines = [
        f"# 第 {page['page_num']} 页 - {page['title']}",
        "",
        f"- 预期 SVG：`{expected_svg_name(page)}`",
        f"- 页面家族：`{page_family(page)}`",
        f"- 执行通道：`{policy['render_lane']}`",
        f"- QA 层级：`{policy['qa_tier']}`",
        f"- 模板稳定度：`{policy['template_stability']}`",
        f"- 复杂页分级：`{policy['complex_class']}`",
        f"- 默认自动修复轮数：{policy['default_auto_repair_rounds']}",
        f"- Preview 策略：`{policy['preview_strategy']}`",
        f"- Soft QA：`{policy['soft_qa_mode']}`",
        f"- 布局：{page.get('layout') or '待补齐'}",
        f"- 优先页型：`{page.get('preferred_template') or '待补齐'}`",
        f"- 高级正文模式：{page.get('advanced_pattern') or '无'}",
        f"- 页面角色：{page.get('page_role') or '无'}",
        f"- 事实源：`notes/{PAGE_CONTEXT_DIRNAME}/{expected_svg_name(page).replace('.svg', '.json')}`",
        "",
        "## 执行提醒",
        "- 结构化事实以 `page_context_min` 为准，brief 只保留人工执行提醒，不再重复抄写主判断与证据原文。",
        f"- QA 重点：{qa_focus(page)}",
        f"- 与上一页关系：{page.get('prev_relation') or '无'}",
        f"- 与下一页关系：{page.get('next_relation') or '无'}",
    ]
    if policy["preflight_blockers"]:
        lines.append(f"- 前置阻断：{'；'.join(policy['preflight_blockers'])}")
    if policy["preflight_warnings"]:
        lines.append(f"- 预警：{'；'.join(policy['preflight_warnings'])}")
    if page.get("fallback_reason"):
        lines.append(f"- 回退原因：{page['fallback_reason']}")
    return "\n".join(lines) + "\n"


def build_execution_contracts(pages: list[dict[str, str]], notes_dir: Path) -> dict[str, Any]:
    contracts: list[dict[str, Any]] = []
    context_dir = notes_dir / PAGE_CONTEXT_DIRNAME
    for page in pages:
        contracts.append(
            {
                "page_num": page["page_num"],
                "title": page["title"],
                "expected_svg": expected_svg_name(page),
                "preferred_template": page.get("preferred_template", ""),
                "advanced_pattern": page.get("advanced_pattern", "无"),
                "page_role": page.get("page_role", ""),
                "page_intent": page.get("page_intent", ""),
                "proof_goal": page.get("proof_goal", ""),
                "core_judgment": page.get("core_judgment", ""),
                "template_stability": page.get("template_stability", ""),
                "complex_class": page.get("complex_class", ""),
                "layout_signature": page.get("layout_signature", ""),
                "repeat_risk": page.get("repeat_risk", "none"),
                "preflight_blockers": list(page.get("preflight_blockers") or []),
                "preflight_warnings": list(page.get("preflight_warnings") or []),
                "context_min_path": str(page_context_path(context_dir, expected_svg_name(page))),
                "execution_policy": execution_policy(page),
            }
        )
    return {
        "policy_version": 2,
        "freeze_rule": "render 阶段默认不再晚重构；相邻复杂页换骨架只允许在首轮渲染前预处理一次。",
        "contracts": contracts,
    }


def build_svg_execution_pack(project_path: str | Path) -> dict[str, str]:
    project_dir = Path(project_path).expanduser().resolve()
    design_spec_path = project_dir / "design_spec.md"
    if not design_spec_path.exists():
        raise FileNotFoundError(f"design_spec.md not found: {design_spec_path}")

    pages = prepare_execution_pages(parse_design_spec_pages(design_spec_path))
    if not pages:
        raise ValueError("design_spec.md 中未解析到内容页大纲")

    notes_dir = project_dir / "notes"
    briefs_dir = notes_dir / "page_briefs"
    queue_path = notes_dir / "svg_execution_queue.md"
    queue_machine_path = notes_dir / QUEUE_MACHINE_FILENAME
    status_path = notes_dir / "svg_generation_status.md"
    postprocess_path = notes_dir / "svg_postprocess_plan.md"
    contracts_path = notes_dir / EXECUTION_CONTRACTS_FILENAME
    total_md_path = notes_dir / "total.md"
    page_context_dir = write_page_context_files(project_dir, pages, notes_dir)

    write_text(queue_path, build_queue_text(project_dir, pages))
    write_text(queue_machine_path, json_dumps(build_machine_queue_payload(project_dir, pages, notes_dir)))
    write_text(status_path, build_status_text(project_dir, pages))
    write_text(postprocess_path, build_postprocess_text(project_dir))
    write_text(contracts_path, json_dumps(build_execution_contracts(pages, notes_dir)))
    write_text(total_md_path, build_total_md_skeleton(pages), overwrite=False)

    for page in pages:
        brief_path = briefs_dir / f"{expected_svg_name(page).replace('.svg', '.md')}"
        write_text(brief_path, build_page_brief_text(page))

    return {
        "queue": str(queue_path),
        "queue_machine": str(queue_machine_path),
        "status": str(status_path),
        "postprocess": str(postprocess_path),
        "contracts": str(contracts_path),
        "page_briefs": str(briefs_dir),
        "page_context_min": str(page_context_dir),
        "total_md": str(total_md_path),
    }


def json_dumps(data: dict[str, Any]) -> str:
    import json

    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="基于 design_spec 生成 SVG 执行编排包。")
    parser.add_argument("project_path", help="项目路径")
    args = parser.parse_args()

    outputs = build_svg_execution_pack(args.project_path)
    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
