#!/usr/bin/env python3
"""Deterministic current-page SVG executor for ppt-master.

This script is the first step toward making the SVG execution stage less
dependent on the main agent's live drafting. It renders the current page into
`svg_output/` from project planning artifacts plus template SVG placeholders.

Scope of this executor:
- Fixed skeleton pages: cover / toc / chapter / ending
- Generic content templates with `{{CONTENT_AREA}}`
- Several structured `security_service` templates via semantic placeholder fill

It does not replace final soft judgment or page polishing, but it can now
produce a starter SVG and run an immediate technical QA snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


def _missing_preview_renderer(exc: Exception):
    def _raiser(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError(
            "SVG preview renderer unavailable: "
            f"{type(exc).__name__}: {exc}. Install PyMuPDF / fitz to enable preview snapshots."
        )

    return _raiser


try:
    from build_svg_execution_pack import PAGE_CONTEXT_DIRNAME
    from build_svg_execution_pack import build_svg_execution_pack
    from build_svg_execution_pack import execution_policy as derive_execution_policy
    from check_complex_page_model import (
        extract_model_blocks,
        parse_model_block,
        validate_model_block,
    )
    from check_svg_text_fit import check_svg
    from svg_execution_runner import (
        append_log,
        detect_template_id,
        find_page,
        load_or_init_state,
        next_actionable_page,
        save_state_bundle,
        state_paths,
        sync_state_with_files,
    )
    from svg_quality_checker import SVGQualityChecker
except ImportError:
    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from build_svg_execution_pack import PAGE_CONTEXT_DIRNAME  # type: ignore
    from build_svg_execution_pack import build_svg_execution_pack  # type: ignore
    from build_svg_execution_pack import execution_policy as derive_execution_policy  # type: ignore
    from check_complex_page_model import (  # type: ignore
        extract_model_blocks,
        parse_model_block,
        validate_model_block,
    )
    from check_svg_text_fit import check_svg  # type: ignore
    from svg_execution_runner import (  # type: ignore
        append_log,
        detect_template_id,
        find_page,
        load_or_init_state,
        next_actionable_page,
        save_state_bundle,
        state_paths,
        sync_state_with_files,
    )
    from svg_quality_checker import SVGQualityChecker  # type: ignore

try:
    from render_svg_pages import render_svg as render_svg_preview
except Exception as exc:  # pragma: no cover - exercised via runtime env differences
    render_svg_preview = _missing_preview_renderer(exc)


ROOT = Path(__file__).resolve().parent.parent
RAW_PLACEHOLDERS = {"CONTENT_AREA", "PAGE_SUBTITLE"}
DEFAULT_DATE = datetime.now().strftime("%Y.%m.%d")
TIMING_SUMMARY_JSON = "svg_execution_timing_summary.json"
TIMING_SUMMARY_MD = "svg_execution_timing_summary.md"
SECURITY_LABEL_ALIASES = [
    ("核心业务资产", "核心资产"),
    ("核心资产稳定触达结果", "核心资产触达"),
    ("核心资产稳定触达", "核心资产触达"),
    ("横向移动扩散路径", "横向扩散"),
    ("横向移动", "横移"),
    ("低可见横移通道", "横移通道"),
    ("权限提升放大条件", "权限放大"),
    ("放大条件", "放大点"),
    ("入口证据链", "入口证据"),
    ("结果证据链", "结果证据"),
    ("复测闭环说明", "复测闭环"),
    ("跨域影响证明", "影响证明"),
    ("持续突破多层控制", "连续突破控制"),
]
SECURITY_LABEL_FILLERS = [
    "稳定",
    "持续",
    "完整",
    "关键",
    "过程",
    "路径",
    "说明",
    "结果",
]
SEMANTIC_KEYWORD_STOPWORDS = {
    "问题",
    "结果",
    "风险",
    "结构",
    "链路",
    "路径",
    "判断",
    "动作",
    "节点",
    "页面",
    "案例",
    "证明",
    "当前",
    "整体",
    "总体",
    "关键",
    "核心",
    "主要",
}
PLANNING_TONE_PATTERNS = [
    "把注意力",
    "让听众",
    "提醒听众",
    "承接上一页",
    "与上一页关系",
    "与下一页关系",
    "为后续",
    "做铺垫",
    "继续推进到",
    "这页给谁看",
]
JUDGMENT_MARKERS = (
    "已",
    "仍",
    "存在",
    "形成",
    "暴露",
    "导致",
    "带来",
    "需要",
    "应",
    "必须",
    "优先",
    "可",
    "无法",
    "缺失",
    "薄弱",
    "失守",
    "贯通",
    "触达",
    "失效",
)
GENERIC_JUDGMENT_PHRASES = {
    "风险总览",
    "攻击链总览",
    "关键结果",
    "整体回顾",
    "证据证明",
    "关键证据总览",
    "能力总览",
    "整改复测机制",
}
CLOSURE_ACTION_MARKERS = (
    "先",
    "再",
    "最后",
    "优先",
    "推进",
    "整改",
    "复测",
    "封堵",
    "切断",
    "收口",
    "验证",
    "压降",
    "补齐",
    "治理",
)
GENERIC_CLOSURE_PATTERNS = (
    "感谢聆听",
    "感谢观看",
    "欢迎沟通",
    "欢迎交流",
    "进一步沟通",
    "继续交流",
    "后续交流",
    "欢迎进一步",
)
SOFT_BLACKLIST_REWRITES = {
    "证据驾驶舱": "数据证明",
    "证据挂载": "证据证明",
    "挂载型案例页": "案例证明页",
    "高级洞察": "关键判断",
    "一体化协同提效": "协同推进",
    "能力沉淀闭环体系": "治理闭环",
    "安全水位拉齐": "控制能力补齐",
    "攻击赋能": "攻击利用",
    "关键证据证明": "关键结论摘要",
    "攻击链证据页": "典型链路拆解",
    "矩阵证据墙": "问题结构拆解",
    "协同案例链": "典型案例拆解",
    "结果证明总览": "关键结果摘要",
    "纵深突破证明页": "内网链路拆解",
    "证据链已闭合": "链路已完成验证",
}
SOFT_QA_CODES = {
    "adjacent_complex_progression",
    "security_service_pattern",
    "complex_page_headline",
    "complex_page_closure",
    "complex_page_argument_cohesion",
    "complex_page_structure",
    "complex_page_evidence",
}
SECTION_DESC_RULES = [
    (("整体回顾",), "先统一结果，再进入管理判断"),
    (("成果", "总结"), "汇总结果规模与风险判断"),
    (("攻击", "路径"), "从入口、放大到结果梳理主链"),
    (("问题", "整改"), "把问题结构收束到整改优先级"),
    (("问题", "分析"), "拆清根因，再明确治理动作"),
    (("社工",), "用案例说明人员入口如何转化"),
    (("漏洞",), "附录列示威胁与处置重点"),
    (("威胁", "清理"), "附录列示问题与清理闭环"),
    (("背景", "判断"), "项目背景与结果判断"),
    (("攻击", "证据"), "攻击链路与证据证明"),
    (("问题", "风险"), "问题机制与风险拆解"),
    (("整改", "闭环"), "整改优先级与闭环推进"),
    (("案例", "价值"), "关键案例与安服价值"),
]
PROGRESSION_PATTERN_ALTERNATIVES: dict[tuple[str, str], tuple[str, str, str]] = {
    ("governance_control_matrix", "16_table.svg"): (
        "matrix_defense_map",
        "12_grid.svg",
        "将连续治理矩阵页切换为问题结构拆解页，拉开相邻复杂页的表达差异",
    ),
    ("matrix_defense_map", "12_grid.svg"): (
        "governance_control_matrix",
        "16_table.svg",
        "将连续问题结构页切换为治理动作矩阵页，避免连续相同骨架重复",
    ),
    ("evidence_cockpit", "07_data.svg"): (
        "evidence_attached_case_chain",
        "19_result_leading_case.svg",
        "将连续摘要证明页切换为案例链路页，强化后一页的推进关系",
    ),
    ("evidence_cockpit", "05_case.svg"): (
        "evidence_cockpit",
        "07_data.svg",
        "社工案例页仍需要 KPI / 证据驾驶舱骨架，回切到数据驾驶舱页承接 evidence_cockpit 表达",
    ),
    ("evidence_attached_case_chain", "19_result_leading_case.svg"): (
        "evidence_cockpit",
        "07_data.svg",
        "将连续案例链页切换为摘要证明页，避免同类链路页连用",
    ),
    ("multi_lane_execution_chain", "09_comparison.svg"): (
        "evidence_attached_case_chain",
        "19_result_leading_case.svg",
        "将连续泳道链页切换为案例链页，减少相邻推进页同构",
    ),
}
PATTERN_STRUCTURE_TYPES = {
    "attack_case_chain": "链路",
    "evidence_attached_case_chain": "链路",
    "matrix_defense_map": "矩阵",
    "governance_control_matrix": "矩阵",
    "operation_loop": "闭环",
    "swimlane_collaboration": "泳道",
    "multi_lane_execution_chain": "泳道",
    "layered_system_map": "分层",
    "attack_tree_architecture": "分层",
    "maturity_model": "分层",
    "timeline_roadmap": "链路",
    "evidence_cockpit": "证据挂载",
    "evidence_wall": "证据挂载",
}


@dataclass
class PageContext:
    project_dir: Path
    page: dict[str, Any]
    template_id: str
    template_path: Path
    template_text: str
    project_name: str
    industry: str
    scenario: str
    audience: str
    goal: str
    desired_action: str
    section_name: str
    page_title: str
    page_role: str
    page_intent: str
    proof_goal: str
    core_judgment: str
    supporting_evidence: str
    evidence_highlights: list[str]
    complex_model: dict[str, Any]
    semantic_points: list[str]
    model_blockers: list[str]
    model_warnings: list[str]
    prev_relation: str
    next_relation: str
    storyline_sections: list[dict[str, str]]
    outline_entries: list[dict[str, str]]
    format_key: str
    report_date: str
    metadata_lock: dict[str, Any]
    template_asset_blockers: list[str]
    template_asset_warnings: list[str]
    execution_events: list[dict[str, Any]]


@dataclass
class RenderTuning:
    compact_cover: int = 0
    compact_toc: int = 0
    compact_standard: int = 0
    compact_matrix: int = 0
    compact_service_map: int = 0
    compact_attack_chain: int = 0
    compact_header_bundle: int = 0
    semantic_headline: int = 0
    semantic_closure: int = 0
    semantic_argument: int = 0
    progression_reframe: int = 0

    def signature(self) -> tuple[int, ...]:
        return (
            self.compact_cover,
            self.compact_toc,
            self.compact_standard,
            self.compact_matrix,
            self.compact_service_map,
            self.compact_attack_chain,
            self.compact_header_bundle,
            self.semantic_headline,
            self.semantic_closure,
            self.semantic_argument,
            self.progression_reframe,
        )


@dataclass(frozen=True)
class SlotBudgetRule:
    key: str
    max_chars: int
    max_lines: int = 1
    mode: str = "sentence"
    severity: str = "warning"


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def resolve_page_execution_policy(page: dict[str, Any]) -> dict[str, Any]:
    policy = derive_execution_policy(page)
    stored = page.get("execution_policy")
    if isinstance(stored, dict):
        merged = dict(policy)
        for key, value in stored.items():
            if key not in merged:
                merged[key] = value
                continue
            if isinstance(merged[key], bool):
                merged[key] = _coerce_bool(value)
            elif isinstance(merged[key], int):
                try:
                    merged[key] = int(value)
                except (TypeError, ValueError):
                    merged[key] = policy[key]
            else:
                merged[key] = value
        policy = merged
    page_family = str(page.get("page_family") or policy.get("page_family") or "").strip()
    complex_class = str(page.get("complex_class") or policy.get("complex_class") or "").strip()

    # Legacy execution_state records may still carry the older aggressive settings.
    # Normalize them here so reruns immediately benefit from the lighter strategy.
    if page_family == "fixed" and str(policy.get("preview_strategy") or "").strip() == "always":
        policy["preview_strategy"] = "on_error"
    if page_family == "complex" and complex_class == "heavy_complex":
        if str(policy.get("preview_strategy") or "").strip() == "always":
            policy["preview_strategy"] = "on_error"
        if str(policy.get("soft_qa_mode") or "").strip() == "always":
            policy["soft_qa_mode"] = "on_signal"
    page["execution_policy"] = policy
    return policy


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def elapsed_ms(start_time: float) -> int:
    return max(0, int(round((time.perf_counter() - start_time) * 1000)))


def format_duration_ms(value: Any) -> str:
    try:
        duration_ms = int(value or 0)
    except (TypeError, ValueError):
        duration_ms = 0
    return f"{duration_ms / 1000:.2f}s"


def _hash_path(path: Path, digest: "hashlib._Hash") -> None:
    resolved = path.expanduser().resolve()
    digest.update(resolved.as_posix().encode("utf-8"))
    if not resolved.exists():
        digest.update(b"MISSING")
        return
    if resolved.is_file():
        digest.update(b"FILE")
        digest.update(resolved.read_bytes())
        return
    digest.update(b"DIR")
    for child in sorted(resolved.rglob("*")):
        digest.update(str(child.relative_to(resolved)).encode("utf-8"))
        if child.is_file():
            digest.update(child.read_bytes())


def collect_page_input_paths(ctx: PageContext) -> list[Path]:
    tool_dir = Path(__file__).resolve().parent
    raw_paths: list[Path] = [
        ctx.project_dir / "project_brief.md",
        ctx.project_dir / "design_spec.md",
        ctx.project_dir / "notes" / "template_domain_recommendation.md",
        ctx.project_dir / "notes" / "storyline.md",
        ctx.project_dir / "notes" / "page_outline.md",
        ctx.project_dir / "notes" / "complex_page_models.md",
        ctx.template_path,
        Path(__file__).resolve(),
        tool_dir / "svg_quality_checker.py",
        tool_dir / "check_svg_text_fit.py",
        tool_dir / "render_svg_pages.py",
    ]
    for key in ("brief_path", "context_min_path"):
        raw_value = str(ctx.page.get(key) or "").strip()
        if raw_value:
            raw_paths.append(Path(raw_value))

    seen: set[str] = set()
    unique_paths: list[Path] = []
    for path in raw_paths:
        normalized = str(path.expanduser().resolve())
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(Path(normalized))
    return unique_paths


def build_page_input_fingerprint(
    ctx: PageContext,
    page_policy: dict[str, Any],
    *,
    auto_repair_enabled: bool,
    max_auto_repair_rounds: int,
) -> str:
    digest = hashlib.sha256()
    for path in collect_page_input_paths(ctx):
        _hash_path(path, digest)
    extra_values = [
        str(ctx.page.get("expected_svg") or ""),
        ctx.template_id,
        ctx.template_path.name,
        json.dumps(page_policy, ensure_ascii=False, sort_keys=True),
        f"auto_repair={bool(auto_repair_enabled)}",
        f"max_auto_repair_rounds={int(max_auto_repair_rounds)}",
    ]
    for value in extra_values:
        digest.update(value.encode("utf-8"))
    return digest.hexdigest()


def load_reusable_success_trace(
    trace_path: Path,
    output_path: Path,
    *,
    input_fingerprint: str,
) -> dict[str, Any] | None:
    if not trace_path.exists() or not output_path.exists():
        return None
    trace = read_json(trace_path)
    if not trace:
        return None
    if str(trace.get("input_fingerprint") or "") != input_fingerprint:
        return None
    final_status = str(trace.get("status") or "")
    if final_status not in {"generated", "completed"}:
        return None
    attempts = trace.get("attempts") or []
    if attempts:
        last_status = str((attempts[-1] or {}).get("status") or final_status)
        if last_status not in {"generated", "completed"}:
            return None
    return trace


def summarize_attempt_stage_totals(attempts: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "render_ms": 0,
        "write_svg_ms": 0,
        "text_fit_ms": 0,
        "quality_ms": 0,
        "preview_ms": 0,
        "evaluate_ms": 0,
        "repair_ms": 0,
        "total_ms": 0,
    }
    for attempt in attempts:
        timing = dict(attempt.get("timing") or {})
        for key in totals:
            totals[key] += int(timing.get(key, 0) or 0)
    return totals


def render_timing_summary_markdown(summary: dict[str, Any]) -> str:
    slow_pages = list(summary.get("slow_pages") or [])
    slow_stages = list(summary.get("slow_stages") or [])
    repeated_pages = list(summary.get("repeated_pages") or [])
    lines = [
        "# SVG 执行耗时汇总",
        "",
        f"- 页面总数：{summary.get('page_count', 0)}",
        f"- 有耗时记录页面：{summary.get('timed_page_count', 0)}",
        f"- 累计耗时：{format_duration_ms(summary.get('total_ms', 0))}",
        f"- 累计自动修复轮次：{summary.get('auto_repair_rounds_used', 0)}",
        f"- 多轮执行页面：{summary.get('repeated_page_count', 0)}",
        "",
        "## 最慢页面",
    ]
    if slow_pages:
        for item in slow_pages:
            lines.append(
                f"- 第 {item.get('page_num')} 页 `{item.get('page')}`：{format_duration_ms(item.get('total_ms', 0))}"
                f"（attempts={item.get('attempt_count', 0)}，quality={format_duration_ms(item.get('quality_ms', 0))}，"
                f"preview={format_duration_ms(item.get('preview_ms', 0))}，repair={format_duration_ms(item.get('repair_ms', 0))}）"
            )
    else:
        lines.append("- 暂无耗时数据。")
    lines.extend(["", "## 最重步骤"])
    if slow_stages:
        for item in slow_stages:
            lines.append(f"- `{item.get('stage')}`：{format_duration_ms(item.get('total_ms', 0))}")
    else:
        lines.append("- 暂无耗时数据。")
    lines.extend(["", "## 多轮执行页面"])
    if repeated_pages:
        for item in repeated_pages:
            lines.append(
                f"- 第 {item.get('page_num')} 页 `{item.get('page')}`：attempts={item.get('attempt_count', 0)}，"
                f"自动修复={item.get('auto_repair_rounds_used', 0)}，总耗时={format_duration_ms(item.get('total_ms', 0))}"
            )
    else:
        lines.append("- 暂无多轮执行页面。")
    return "\n".join(lines) + "\n"


def write_project_timing_summary(project_dir: Path) -> None:
    trace_dir = project_dir / "notes" / "page_execution"
    rows: list[dict[str, Any]] = []
    for trace_path in sorted(trace_dir.glob("*.json")):
        trace = read_json(trace_path)
        if not trace:
            continue
        timing = dict(trace.get("timing") or {})
        attempts = list(trace.get("attempts") or [])
        attempt_totals = summarize_attempt_stage_totals(attempts)
        page_num_raw = str(trace.get("page_num") or "0")
        try:
            page_num = int(page_num_raw)
        except ValueError:
            page_num = 0
        rows.append(
            {
                "page_num": page_num,
                "page": str(trace.get("page") or trace_path.stem),
                "status": str(trace.get("status") or ""),
                "attempt_count": int(trace.get("attempt_count", len(attempts)) or 0),
                "auto_repair_rounds_used": int(trace.get("auto_repair_rounds_used", 0) or 0),
                "total_ms": int(timing.get("total_ms", attempt_totals["total_ms"]) or 0),
                "render_ms": int(attempt_totals["render_ms"] or 0),
                "text_fit_ms": int(attempt_totals["text_fit_ms"] or 0),
                "quality_ms": int(attempt_totals["quality_ms"] or 0),
                "preview_ms": int(attempt_totals["preview_ms"] or 0),
                "repair_ms": int(attempt_totals["repair_ms"] or 0),
            }
        )

    stage_totals = {
        "render_ms": sum(item["render_ms"] for item in rows),
        "text_fit_ms": sum(item["text_fit_ms"] for item in rows),
        "quality_ms": sum(item["quality_ms"] for item in rows),
        "preview_ms": sum(item["preview_ms"] for item in rows),
        "repair_ms": sum(item["repair_ms"] for item in rows),
    }
    slow_stages = [
        {"stage": stage, "total_ms": total_ms}
        for stage, total_ms in sorted(stage_totals.items(), key=lambda item: item[1], reverse=True)
        if total_ms > 0
    ]
    slow_pages = sorted(rows, key=lambda item: item["total_ms"], reverse=True)[:10]
    repeated_pages = [item for item in rows if item["attempt_count"] > 1 or item["auto_repair_rounds_used"] > 0]
    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "page_count": len(rows),
        "timed_page_count": sum(1 for item in rows if item["total_ms"] > 0),
        "total_ms": sum(item["total_ms"] for item in rows),
        "auto_repair_rounds_used": sum(item["auto_repair_rounds_used"] for item in rows),
        "repeated_page_count": len(repeated_pages),
        "slow_pages": slow_pages,
        "slow_stages": slow_stages,
        "repeated_pages": repeated_pages[:10],
    }
    notes_dir = project_dir / "notes"
    write_text(notes_dir / TIMING_SUMMARY_JSON, json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    write_text(notes_dir / TIMING_SUMMARY_MD, render_timing_summary_markdown(summary))


def read_page_context_min(project_dir: Path, expected_svg: str) -> dict[str, Any]:
    context_path = project_dir / "notes" / PAGE_CONTEXT_DIRNAME / f"{expected_svg.replace('.svg', '')}.json"
    return read_json(context_path)


def normalize_text(value: str) -> str:
    text = re.sub(r"[`*_]+", "", value or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_cover_date(value: str) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    text = re.sub(r"[年月/\\-]", ".", text)
    text = text.replace("日", "")
    text = re.sub(r"\.+", ".", text).strip(".")
    match = re.fullmatch(r"(20\d{2})\.(\d{1,2})\.(\d{1,2})", text)
    if match:
        year, month, day = match.groups()
        return f"{year}.{int(month):02d}.{int(day):02d}"
    compact_match = re.fullmatch(r"(20\d{2})(\d{2})(\d{2})", re.sub(r"\D", "", text))
    if compact_match:
        year, month, day = compact_match.groups()
        return f"{year}.{month}.{day}"
    return text


def extract_local_asset_hrefs(svg_text: str) -> list[str]:
    refs: list[str] = []
    for href in re.findall(r'href="([^"]+)"', svg_text):
        if "{{" in href or href.startswith(("data:", "http://", "https://")):
            continue
        refs.append(href)
    return refs


def find_missing_asset_refs(svg_text: str, *, base_dir: Path) -> list[str]:
    missing: list[str] = []
    for href in extract_local_asset_hrefs(svg_text):
        asset_path = (base_dir / href).resolve()
        if asset_path.exists() and asset_path.is_file():
            continue
        missing.append(href)
    return missing


def append_execution_event(ctx: PageContext, event_type: str, **payload: Any) -> None:
    event = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    event.update(payload)
    ctx.execution_events.append(event)


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value or ""))


def looks_internal_project_token(value: str) -> bool:
    text = normalize_text(value)
    if not text or has_cjk(text):
        return False
    compact = re.sub(r"\s+", "", text)
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{8,}", compact))


def sanitize_source_title(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"[_-]?副本$", "", text)
    text = re.sub(r"[_-]?v\d+(?:\.\d+)*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[_-]?20\d{4,10}$", "", text)
    return text.strip(" _-")


def derive_display_project_name(project_dir: Path, fallback: str) -> str:
    if fallback and not looks_internal_project_token(fallback):
        return fallback

    source_dir = project_dir / "sources"
    if not source_dir.exists():
        return fallback

    preferred_files = sorted(source_dir.glob("*.docx")) + sorted(source_dir.glob("*.pdf")) + sorted(source_dir.glob("*.md"))
    for path in preferred_files:
        cleaned = sanitize_source_title(path.stem)
        if cleaned and has_cjk(cleaned):
            return cleaned

    for md_path in sorted(source_dir.glob("*.md")):
        lines = []
        for raw in md_path.read_text(encoding="utf-8").splitlines():
            stripped = normalize_text(raw)
            if not stripped or stripped.startswith("![") or stripped.startswith("|") or stripped.startswith("#"):
                continue
            if has_cjk(stripped) and len(stripped) <= 28:
                lines.append(stripped)
            if len(lines) >= 2:
                break
        if len(lines) >= 2:
            return sanitize_source_title(f"{lines[0]}{lines[1]}")
        if lines:
            return sanitize_source_title(lines[0])

    return fallback


def strip_display_prefix(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"^(章节页|目录页|封面页|结束页)\s*[/／]\s*", "", text)
    return text


def strip_storyline_range(value: str) -> str:
    text = normalize_text(value)
    text = re.sub(r"\s*[（(]第\s*\d+\s*[-–—]\s*\d+\s*页[）)]\s*$", "", text)
    text = re.sub(r"\s*[（(]第\s*\d+\s*页[）)]\s*$", "", text)
    return text


def extract_md_value(text: str, label: str) -> str:
    pattern = rf"(?m)^\s*-\s*{re.escape(label)}[:：]\s*(.+)$"
    match = re.search(pattern, text)
    return normalize_text(match.group(1)) if match else ""


def parse_storyline_sections(text: str) -> list[dict[str, str]]:
    matches = list(re.finditer(r"(?m)^###\s+章节\s+\d+\s*[：:]\s*(.+)$", text))
    sections: list[dict[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end]
        sections.append(
            {
                "title": strip_storyline_range(match.group(1)),
                "goal": extract_md_value(block, "章节目标"),
                "problem": extract_md_value(block, "要解决的问题"),
                "page_types": extract_md_value(block, "主要页型"),
            }
        )
    return sections


def parse_outline_entries(text: str) -> list[dict[str, str]]:
    headings = list(re.finditer(r"(?m)^##\s+第\s+(\d+)\s+页\s*$", text))
    entries: list[dict[str, str]] = []
    for idx, match in enumerate(headings):
        start = match.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        block = text[start:end]
        entry: dict[str, str] = {"page_num": match.group(1)}
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            if "：" in stripped:
                key, value = stripped[2:].split("：", 1)
            elif ":" in stripped:
                key, value = stripped[2:].split(":", 1)
            else:
                continue
            entry[normalize_text(key)] = normalize_text(value)
        entries.append(entry)
    return entries


def parse_page_brief(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        payload = stripped[2:]
        if "：" in payload:
            key, value = payload.split("：", 1)
        elif ":" in payload:
            key, value = payload.split(":", 1)
        else:
            continue
        result[normalize_text(key)] = normalize_text(value)
    return result


def normalize_title_key(value: str) -> str:
    return re.sub(r"\s+", "", normalize_text(value)).lower()


def normalize_pattern_token(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip("`").lower()


def is_complex_page(page: dict[str, Any]) -> bool:
    advanced = normalize_pattern_token(page.get("advanced_pattern") or "")
    if not advanced:
        return False
    return advanced not in {"无", "none", "n/a", "na"}


def strip_leading_label(value: str) -> str:
    text = normalize_text(value)
    match = re.match(r"^[^：:]{1,16}[：:]\s*(.+)$", text)
    return normalize_text(match.group(1)) if match else text


def merge_unique_texts(values: list[str], *, limit: int = 12) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = rewrite_soft_blacklist_terms(strip_leading_label(value))
        key = normalize_title_key(text)
        if not key or key in seen or contains_planning_tone(text):
            continue
        seen.add(key)
        merged.append(text)
        if len(merged) >= limit:
            break
    return merged


def model_items(model: dict[str, Any], field_name: str) -> list[str]:
    raw_items = model.get(f"{field_name}_items")
    if isinstance(raw_items, list):
        return merge_unique_texts([str(item) for item in raw_items], limit=16)
    text = normalize_text(str(model.get(field_name) or ""))
    return merge_unique_texts([text], limit=16) if text else []


def parse_slide_heading_line(line: str) -> tuple[int | None, str]:
    stripped = line.strip()
    match = re.match(r"^####\s+Slide\s+(\d+)\s*-\s*(.+)$", stripped, flags=re.IGNORECASE)
    if match:
        return int(match.group(1)), normalize_text(match.group(2))
    match = re.match(r"^####\s+第\s*(\d+)\s*页\s*(.+)$", stripped)
    if match:
        return int(match.group(1)), normalize_text(match.group(2))
    match = re.match(r"^####\s+(\d+)\s*[-_.:：]?\s*(.+)$", stripped)
    if match:
        return int(match.group(1)), normalize_text(match.group(2))
    return None, ""


def update_markdown_slide_block(
    path: Path,
    slide_num: int,
    updater: callable,
) -> bool:
    text = read_text(path)
    if not text.strip():
        return False
    matches = list(re.finditer(r"(?m)^####\s+.+$", text))
    if not matches:
        return False
    for idx, match in enumerate(matches):
        heading_line = match.group(0)
        current_slide, _ = parse_slide_heading_line(heading_line)
        if current_slide != slide_num:
            continue
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = text[start:end]
        updated = updater(block)
        if not updated or updated == block:
            return False
        write_text(path, text[:start] + updated + text[end:])
        return True
    return False


def replace_line_in_block(block: str, pattern: str, replacement: str) -> tuple[str, bool]:
    updated, count = re.subn(pattern, replacement, block, count=1, flags=re.MULTILINE)
    return updated, count > 0


def collect_model_semantic_points(model: dict[str, Any]) -> list[str]:
    if not model:
        return []
    ordered_fields = [
        "sub_judgment",
        "key_nodes",
        "key_relations",
        "evidence_plan",
        "closure",
        "argument_spine",
        "visual_focus",
    ]
    values: list[str] = []
    for field_name in ordered_fields:
        values.extend(model_items(model, field_name))
    return merge_unique_texts(values, limit=12)


GENERIC_MODEL_EVIDENCE_PATTERNS = (
    "证据 a ->",
    "证据 b ->",
    "将直接证据挂到",
    "将结果证据放在",
    "结果证据放在结果区",
    "关键证据需要按主证据与辅助证据分层呈现",
    "数据、截图或背书材料必须直接服务于主判断",
    "结论区需要把证据翻译成管理可理解的判断与动作",
    "kpi 与原始证据共同支撑判断",
    "普通列表或兜底内容页无法稳定承载",
    "证据聚合后足以支撑当前主判断成立",
)


def is_generic_model_evidence_item(text: str) -> bool:
    value = normalize_text(rewrite_soft_blacklist_terms(text)).lower()
    if not value:
        return True
    return any(pattern in value for pattern in GENERIC_MODEL_EVIDENCE_PATTERNS)


def load_source_markdown(project_dir: Path) -> str:
    source_dir = project_dir / "sources"
    parts: list[str] = []
    for path in sorted(source_dir.glob("*.md")):
        text = read_text(path)
        if text.strip():
            parts.append(text)
    return "\n\n".join(parts)


def detect_source_report_date(project_dir: Path, source_markdown: str) -> str:
    source_dir = project_dir / "sources"
    preferred_files = sorted(source_dir.glob("*.docx")) + sorted(source_dir.glob("*.pdf")) + sorted(source_dir.glob("*.md"))
    for path in preferred_files:
        match = re.search(r"(20\d{2})(\d{2})(\d{2})", path.stem)
        if match:
            return normalize_cover_date("".join(match.groups()))
    for pattern in (
        r"(20\d{2})年(\d{1,2})月(\d{1,2})日",
        r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})",
    ):
        match = re.search(pattern, source_markdown)
        if match:
            return normalize_cover_date(".".join(match.groups()))
    return ""


def resolve_project_metadata(project_dir: Path, brief_text: str, source_markdown: str) -> dict[str, Any]:
    metadata_path = project_dir / "notes" / "metadata_lock.json"
    metadata = read_json(metadata_path)
    report_date_candidates = [
        metadata.get("report_date", ""),
        metadata.get("date", ""),
        extract_md_value(brief_text, "报告日期"),
        extract_md_value(brief_text, "汇报日期"),
        extract_md_value(brief_text, "日期"),
        detect_source_report_date(project_dir, source_markdown),
        DEFAULT_DATE,
    ]
    report_date = next((normalize_cover_date(str(item)) for item in report_date_candidates if normalize_cover_date(str(item))), DEFAULT_DATE)
    metadata["report_date"] = report_date
    write_text(metadata_path, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    return metadata


def extract_markdown_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?m)^(#{1,6})\s+(.+?)\s*$", text))
    if not matches:
        return []
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = normalize_text(match.group(2))
        body = text[start:end]
        sections.append((heading, body))
    return sections


def extract_meaningful_lines(text: str, *, limit: int = 8) -> list[str]:
    points: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("![") or line.startswith("|") or line.startswith("> ["):
            continue
        if re.match(r"^#{1,6}\s+", line):
            continue
        line = re.sub(r"^\s*[-*]+\s*", "", line)
        line = re.sub(r"^\s*\d+[.)、]\s*", "", line)
        line = re.sub(r"<br\s*/?>", "；", line, flags=re.IGNORECASE)
        line = re.sub(r"</?[^>]+>", "", line)
        line = normalize_text(line)
        if not line or len(line) < 6:
            continue
        if any(pattern in line for pattern in ("项目时间", "测试时段", "项目范围", "本次红蓝对抗共发现安全问题")):
            continue
        for item in split_points(line, limit=4):
            candidate = rewrite_soft_blacklist_terms(item)
            if not candidate or len(candidate) < 6:
                continue
            if candidate in points:
                continue
            points.append(candidate)
            if len(points) >= limit:
                return points
    return points


def source_query_priority(text: str) -> tuple[int, int]:
    value = normalize_text(text)
    score = 0
    if any(token in value for token in ("获取", "路径", "钓鱼", "后台", "权限", "敏感信息", "通用口令", "整改", "闭环")):
        score += 4
    if any(token in value for token in ("Thinkphp", "log4j2", "Nacos", "xxl-job", "AWS")):
        score += 5
    if any(token in value for token in ("整体回顾", "整体攻击路径分析", "攻击路径概述")):
        score -= 2
    if value.endswith("等") or " 等" in value:
        score -= 1
    return score, len(value)


def collect_source_support_points(project_dir: Path, heading_queries: list[str], *, limit: int = 8) -> list[str]:
    source_text = load_source_markdown(project_dir)
    if not source_text.strip():
        return []
    sections = extract_markdown_sections(source_text)
    if not sections:
        return []

    ordered_queries = sorted(
        [query for query in heading_queries if normalize_text(query)],
        key=source_query_priority,
        reverse=True,
    )
    points: list[str] = []
    seen_headings: set[str] = set()
    for query in ordered_queries:
        cleaned_query = normalize_text(query).replace(" 等", "").replace("等", "")
        query_key = normalize_title_key(strip_display_prefix(cleaned_query))
        if not query_key:
            continue
        for heading, body in sections:
            heading_key = normalize_title_key(heading)
            if not heading_key or heading_key in seen_headings:
                continue
            if query_key == heading_key or query_key in heading_key or heading_key in query_key:
                seen_headings.add(heading_key)
                points.extend(extract_meaningful_lines(body, limit=max(4, limit)))
                break
        if len(points) >= limit:
            break
    return merge_unique_texts(points, limit=limit)


def build_model_supporting_evidence(
    model: dict[str, Any],
    outline_entry: dict[str, str],
    page_brief: dict[str, str],
    source_points: list[str] | None = None,
) -> str:
    candidates: list[str] = []
    candidates.extend(
        [
            outline_entry.get("支撑证据", ""),
            page_brief.get("支撑证据", ""),
        ]
    )
    if source_points:
        candidates.extend(source_points[:4])
    if model:
        evidence_items = model_items(model, "evidence_plan")
        relation_items = model_items(model, "key_relations")
        sub_items = model_items(model, "sub_judgment")
        candidates.extend(item for item in evidence_items[:3] if not is_generic_model_evidence_item(item))
        candidates.extend(item for item in relation_items[:2] if not is_generic_model_evidence_item(item))
        candidates.extend(item for item in sub_items[:2] if not is_generic_model_evidence_item(item))
    merged = merge_unique_texts(candidates, limit=8)
    return "；".join(merged)


def resolve_complex_page_model(
    project_dir: Path,
    page: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[str]]:
    if not is_complex_page(page):
        return {}, [], []

    model_path = project_dir / "notes" / "complex_page_models.md"
    if not model_path.exists():
        return {}, [f"复杂页缺少建模文件：{model_path}"], []

    content = read_text(model_path)
    blocks = extract_model_blocks(content)
    if not blocks:
        return {}, [f"复杂页建模文件为空或未识别到页面：{model_path}"], []

    page_num = int(page.get("page_num", 0) or 0)
    page_title = normalize_text(str(page.get("title") or ""))
    target_key = normalize_title_key(page_title)
    matched_heading = ""
    matched_block = ""

    preferred_headings = [
        f"第 {page_num} 页 {page_title}",
        f"第{page_num}页 {page_title}",
        page_title,
    ]
    for heading in preferred_headings:
        if heading in blocks:
            matched_heading = heading
            matched_block = blocks[heading]
            break

    if not matched_block:
        for heading, block in blocks.items():
            parsed = parse_model_block(heading, block)
            model_page_num = parsed.get("page_num")
            model_page_title = normalize_title_key(str(parsed.get("page_title") or heading))
            if model_page_num == page_num and model_page_title == target_key:
                matched_heading = heading
                matched_block = block
                break

    if not matched_block:
        return {}, [f"复杂页未找到当前页建模：第 {page_num} 页 {page_title}"], []

    parsed_model = parse_model_block(matched_heading, matched_block)
    blockers, warnings = validate_model_block(matched_heading, matched_block)
    return parsed_model, blockers, warnings


def split_points(text: str, *, limit: int = 8) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    parts = re.split(r"[；;。|\n]", cleaned)
    if len([item for item in parts if normalize_text(item)]) <= 1:
        parts = re.split(r"[、，,]", cleaned)
    results: list[str] = []
    for part in parts:
        item = normalize_text(part)
        if not item or item in results:
            continue
        results.append(item)
        if len(results) >= limit:
            break
    return results


def compress_argument_label(text: str, fallback: str, *, limit: int, level: int = 0) -> str:
    value = rewrite_soft_blacklist_terms(strip_leading_label(text))
    value = re.split(r"[；;。]", value)[0]
    value = re.sub(r"^(说明|证明|体现|表明|当前|继续|聚焦|围绕|针对)", "", value)
    value = re.sub(r"(会持续放大.*|可反复形成.*|需要统一收口.*|在多个系统中重复出现.*)$", "", value)
    value = re.split(r"(?:说明|证明|体现|表明|需要|必须|会|可|能|已|仍|并|且|从而|以及)", value)[0]
    if level >= 1:
        value = value.replace("问题", "")
        value = value.replace("结果", "")
        value = value.replace("风险", "")
        value = value.replace("体系", "")
        value = value.replace("结构", "")
    value = normalize_text(value).strip("，、；：: ")
    return compact_security_label(value or fallback, limit, min(2, level))


def derive_argument_titles(
    ctx: PageContext,
    fallback_titles: list[str],
    *,
    limit: int,
    level: int = 0,
) -> list[str]:
    candidates: list[str] = []
    for field_name in ("key_nodes", "sub_judgment", "key_relations", "evidence_plan"):
        for item in model_items(ctx.complex_model, field_name):
            candidates.extend(split_points(item, limit=limit * 3))
    candidates.extend(split_points(ctx.proof_goal, limit=limit * 2))
    candidates.extend(split_points(ctx.core_judgment, limit=limit * 2))

    titles: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        label = compress_argument_label(candidate, "", limit=12 if level == 0 else 10, level=level)
        key = normalize_title_key(label)
        if not key or key in seen or contains_planning_tone(label):
            continue
        seen.add(key)
        titles.append(label)
        if len(titles) >= limit:
            break

    for fallback in fallback_titles:
        label = compact_security_label(fallback, 12 if level == 0 else 10, min(2, level))
        key = normalize_title_key(label)
        if not key or key in seen:
            continue
        seen.add(key)
        titles.append(label)
        if len(titles) >= limit:
            break
    return titles[:limit]


def patch_design_spec_page_fields(
    project_dir: Path,
    slide_num: int,
    *,
    advanced_pattern: str = "",
    preferred_template: str = "",
) -> bool:
    design_spec_path = project_dir / "design_spec.md"

    def updater(block: str) -> str:
        updated = block
        if advanced_pattern:
            updated, _ = replace_line_in_block(
                updated,
                r"^- \*\*高级正文模式\*\*:\s*`?[^`\n]+`?\s*$",
                f"- **高级正文模式**: `{advanced_pattern}`",
            )
        if preferred_template:
            updated, _ = replace_line_in_block(
                updated,
                r"^- \*\*优先页型\*\*:\s*`?[^`\n]+`?\s*$",
                f"- **优先页型**: `{preferred_template}`",
            )
        return updated

    return update_markdown_slide_block(design_spec_path, slide_num, updater)


def patch_page_outline_fields(
    project_dir: Path,
    slide_num: int,
    *,
    advanced_pattern: str = "",
    preferred_template: str = "",
    is_complex: bool | None = None,
) -> bool:
    changed_any = False
    for outline_path in (project_dir / "notes" / "page_outline.md", project_dir / "page_outline.md"):
        if not outline_path.exists():
            continue
        text = read_text(outline_path)
        matches = list(re.finditer(r"(?m)^##\s+第\s*(\d+)\s*页\s*$", text))
        if not matches:
            continue

        updated_text = text
        changed = False
        for idx, match in enumerate(matches):
            if int(match.group(1)) != int(slide_num):
                continue
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            block = text[start:end]
            updated = block
            if advanced_pattern:
                updated, did_change = replace_line_in_block(
                    updated,
                    r"^- (?:当前高级正文模式|高级正文模式)：.*$",
                    f"- 当前高级正文模式：{advanced_pattern}",
                )
                changed = changed or did_change
            if preferred_template:
                updated, did_change = replace_line_in_block(
                    updated,
                    r"^- 推荐页型：.*$",
                    f"- 推荐页型：{preferred_template}",
                )
                changed = changed or did_change
            if is_complex is not None:
                updated, did_change = replace_line_in_block(
                    updated,
                    r"^- 是否复杂页：.*$",
                    f"- 是否复杂页：{'是' if is_complex else '否'}",
                )
                changed = changed or did_change
            if changed and updated != block:
                updated_text = text[:start] + updated + text[end:]
                write_text(outline_path, updated_text)
                changed_any = True
            break
    return changed_any


def pattern_structure_type(pattern: str) -> str:
    return PATTERN_STRUCTURE_TYPES.get(pattern, "混合结构")


def patch_complex_model_fields(
    project_dir: Path,
    slide_num: int,
    *,
    page_title: str,
    advanced_pattern: str,
    preferred_template: str,
    previous_pattern: str = "",
    previous_template: str = "",
) -> bool:
    model_path = project_dir / "notes" / "complex_page_models.md"
    if not model_path.exists():
        return False

    structure_type = pattern_structure_type(advanced_pattern)
    previous_hint = ""
    if previous_pattern or previous_template:
        previous_hint = (
            f"；不再沿用 `{previous_pattern or '原模式'}` / `{previous_template or '原骨架'}`，"
            "以避免与相邻复杂页形成同构重复"
        )

    def updater(block: str) -> str:
        updated = block
        updated, _ = replace_line_in_block(
            updated,
            r"^- 主结构类型：.*$",
            f"- 主结构类型：{structure_type}",
        )
        updated, _ = replace_line_in_block(
            updated,
            r"^- 结构选择理由：.*$",
            f"- 结构选择理由：本页当前切换为 `{advanced_pattern}`，优先采用 `{structure_type}` 结构表达《{page_title}》的主判断与证据关系{previous_hint}。",
        )
        updated, _ = replace_line_in_block(
            updated,
            r"^- 为什么不用其他结构：.*$",
            f"- 为什么不用其他结构：继续沿用相邻页同类骨架会削弱推进关系，因此本页改用 `{preferred_template}` 承担差异化表达。",
        )
        if "推荐重型骨架" in updated:
            updated, _ = replace_line_in_block(
                updated,
                r"^- 推荐重型骨架：.*$",
                f"- 推荐重型骨架：`{preferred_template}`",
            )
        else:
            lines = updated.rstrip().splitlines()
            lines.extend([f"- 推荐重型骨架：`{preferred_template}`", ""])
            updated = "\n".join(lines)
        return updated

    return update_markdown_slide_block(model_path, slide_num, updater)


def patch_page_brief_fields(brief_path: Path, *, advanced_pattern: str = "", preferred_template: str = "") -> bool:
    if not brief_path.exists():
        return False
    text = read_text(brief_path)
    if not text.strip():
        return False
    updated = text
    changed = False
    if preferred_template:
        updated, did_change = replace_line_in_block(
            updated,
            r"^- 优先页型：`?[^`\n]+`?$",
            f"- 优先页型：`{preferred_template}`",
        )
        changed = changed or did_change
    if advanced_pattern:
        updated, did_change = replace_line_in_block(
            updated,
            r"^- 高级正文模式：`?[^`\n]+`?$",
            f"- 高级正文模式：{advanced_pattern}",
        )
        changed = changed or did_change
    if changed and updated != text:
        write_text(brief_path, updated)
    return changed


def sync_reframed_execution_artifacts(
    ctx: PageContext,
    *,
    slide_num: int,
    advanced_pattern: str,
    preferred_template: str,
    previous_pattern: str = "",
    previous_template: str = "",
) -> list[str]:
    changed_items: list[str] = []
    if patch_page_outline_fields(
        ctx.project_dir,
        slide_num,
        advanced_pattern=advanced_pattern,
        preferred_template=preferred_template,
        is_complex=True,
    ):
        changed_items.append("page_outline")

    if patch_complex_model_fields(
        ctx.project_dir,
        slide_num,
        page_title=ctx.page_title,
        advanced_pattern=advanced_pattern,
        preferred_template=preferred_template,
        previous_pattern=previous_pattern,
        previous_template=previous_template,
    ):
        changed_items.append("complex_page_models")

    try:
        build_svg_execution_pack(ctx.project_dir)
        changed_items.extend(item for item in ("svg_execution_queue", "svg_generation_status", "page_briefs") if item not in changed_items)
    except Exception:
        brief_candidates = []
        brief_path_str = str(ctx.page.get("brief_path") or "").strip()
        if brief_path_str:
            brief_path = Path(brief_path_str)
            brief_candidates.append(brief_path)
        expected_svg = str(ctx.page.get("expected_svg") or "").strip()
        if expected_svg:
            brief_candidates.append(ctx.project_dir / "notes" / "page_briefs" / expected_svg.replace(".svg", ".md"))
        for candidate in brief_candidates:
            if candidate and candidate.exists() and patch_page_brief_fields(
                candidate,
                advanced_pattern=advanced_pattern,
                preferred_template=preferred_template,
            ):
                changed_items.append("page_brief")
                break

    if "expected_svg" in ctx.page and str(ctx.page["expected_svg"]).endswith(".svg"):
        ctx.page["brief_path"] = str(
            ctx.project_dir / "notes" / "page_briefs" / str(ctx.page["expected_svg"]).replace(".svg", ".md")
        )
    return changed_items


def _trim_incomplete_tail(text: str) -> str:
    value = normalize_text(text).rstrip("，、；：: ")
    while value and value[-1] in {"与", "及", "并", "和", "对", "向", "将", "使", "令", "把", "在", "于"}:
        value = value[:-1].rstrip("，、；：: ")
    return normalize_text(value)


def shorten(text: str, limit: int) -> str:
    text = normalize_text(text)
    if len(text) <= limit:
        return text
    if limit <= 1:
        return text[:limit]
    candidate = text[:limit].rstrip("，、；：: ")
    safe_breaks = [candidate.rfind(token) for token in "，、；：: "]
    break_pos = max(safe_breaks) if safe_breaks else -1
    if break_pos >= max(4, limit // 2):
        candidate = candidate[:break_pos]
    candidate = _trim_incomplete_tail(candidate)
    return candidate or text[:limit].rstrip("，、；：: ")


def wrap_text(
    text: str,
    max_chars: int,
    max_lines: int = 3,
    *,
    respect_points: bool = True,
) -> list[str]:
    content = normalize_text(text)
    if not content:
        return []
    points = split_points(content, limit=max_lines * 2) if respect_points else []
    if points and all(len(point) <= max_chars for point in points[:max_lines]):
        return [shorten(point, max_chars) for point in points[:max_lines]]

    lines: list[str] = []
    current = ""
    for char in content:
        current += char
        should_break = len(current) >= max_chars
        punctuation_break = char in "，、；。:：)" and len(current) >= max(8, max_chars - 6)
        if should_break or punctuation_break:
            lines.append(current.strip())
            current = ""
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current.strip())
    if not lines:
        lines = [shorten(content, max_chars)]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if len(lines) == max_lines and "".join(lines) != content:
        lines[-1] = shorten(lines[-1], max_chars)
    return lines


def slot_budget_capacity(rule: SlotBudgetRule) -> int:
    return max(rule.max_chars, rule.max_chars * max(rule.max_lines, 1))


def slot_budget_rules(ctx: PageContext, tuning: RenderTuning) -> list[SlotBudgetRule]:
    template_name = ctx.template_path.name
    title_width = 18 if tuning.semantic_headline <= 1 else 15
    if template_name == "05_case.svg":
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("CASE_BACKGROUND_TITLE", 12, 1, mode="label"),
            SlotBudgetRule("CASE_BACKGROUND_HEADLINE", 10, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CASE_BACKGROUND", 14, 5, mode="sentence", severity="blocker"),
            SlotBudgetRule("CASE_FLOW_TITLE", 20, 1, mode="label"),
            SlotBudgetRule("CASE_LANE_A_TITLE", 14, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CASE_SOLUTION", 18, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("CASE_LANE_B_TITLE", 14, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CASE_PROCESS", 18, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("CASE_RESULT_TITLE", 14, 1, mode="label"),
            SlotBudgetRule("CASE_RESULT_HEADLINE", 12, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CASE_RESULTS", 16, 6, mode="sentence", severity="blocker"),
            SlotBudgetRule("CASE_IMAGE_TITLE", 18, 1, mode="label"),
            SlotBudgetRule("CASE_IMAGE", 20, 2, mode="evidence"),
            SlotBudgetRule("CASE_CLIENT_TITLE", 18, 1, mode="label"),
            SlotBudgetRule("CASE_CLIENT", 32, 2, mode="action", severity="blocker"),
            SlotBudgetRule("CASE_VALUE_BAND", 18, 1, mode="label", severity="blocker"),
        ]
    if template_name == "07_data.svg":
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("PROOF_CONTEXT", 20, 1, mode="sentence"),
            SlotBudgetRule("PROOF_HEADLINE", title_width, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("PROOF_SUBLINE", 18, 1, mode="sentence"),
            SlotBudgetRule("PROOF_CANVAS", 12, 2, mode="label", severity="blocker"),
            SlotBudgetRule("DATA_NOTE_1", 20, 2, mode="evidence", severity="blocker"),
            SlotBudgetRule("DATA_NOTE_2", 20, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("DATA_NOTE_3", 20, 2, mode="action", severity="blocker"),
            SlotBudgetRule("PROOF_RELATION_1", 12, 1, mode="sentence"),
            SlotBudgetRule("PROOF_RELATION_2", 12, 1, mode="sentence"),
            SlotBudgetRule("PROOF_SUMMARY_1", 18, 1, mode="sentence"),
            SlotBudgetRule("PROOF_SUMMARY_2", 18, 1, mode="sentence"),
            SlotBudgetRule("PROOF_SUMMARY_3", 18, 1, mode="action"),
        ]
    if template_name == "09_comparison.svg":
        lane_limit = 14 if tuning.compact_attack_chain == 0 else 12
        lane_title_limit = 10 if tuning.compact_attack_chain == 0 else 8
        result_limit = 26 if tuning.compact_attack_chain == 0 else 22
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("COMPARE_HEADLINE", 18 if tuning.compact_attack_chain == 0 else 14, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_TITLE_A", lane_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("COMPARE_TITLE_B", lane_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_A_1", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_A_2", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_A_3", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_A_4", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_B_1", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_B_2", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_B_3", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_CONTENT_B_4", lane_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("COMPARE_RESULT", result_limit, 2, mode="action", severity="blocker"),
        ]
    if template_name == "08_product.svg":
        feature_limit = 10 if tuning.compact_service_map == 0 else 8
        evidence_limit = 18 if tuning.compact_service_map == 0 else 14
        name_limit = 14 if tuning.compact_service_map == 0 else 12
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("PRODUCT_NAME", name_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("PRODUCT_FEATURE_1", feature_limit, 1, mode="label"),
            SlotBudgetRule("PRODUCT_FEATURE_2", feature_limit, 1, mode="label"),
            SlotBudgetRule("PRODUCT_FEATURE_3", feature_limit, 1, mode="label"),
            SlotBudgetRule("PRODUCT_FEATURE_4", feature_limit, 1, mode="label"),
            SlotBudgetRule("PRODUCT_FEATURE_5", feature_limit, 1, mode="label"),
            SlotBudgetRule("PRODUCT_FEATURE_6", feature_limit, 1, mode="label"),
            SlotBudgetRule("PRODUCT_IMAGE", evidence_limit, 2, mode="evidence", severity="blocker"),
            SlotBudgetRule("PRODUCT_VALUE", evidence_limit, 2, mode="action", severity="blocker"),
        ]
    if template_name == "12_grid.svg":
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("GRID_SUMMARY", 24 if tuning.compact_matrix == 0 else 22, 2, mode="sentence"),
        ]
    if template_name == "16_table.svg":
        insight_limit = 18 if tuning.compact_matrix == 0 else 14
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("TABLE_INSIGHT_1", insight_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("TABLE_INSIGHT_2", insight_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("TABLE_INSIGHT_3", insight_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("TABLE_HIGHLIGHT", insight_limit, 2, mode="action", severity="blocker"),
            SlotBudgetRule("CLOSURE_STEP_1", 16, 1, mode="action"),
            SlotBudgetRule("CLOSURE_STEP_2", 16, 1, mode="action"),
            SlotBudgetRule("CLOSURE_STEP_3", 16, 1, mode="action"),
        ]
    if template_name == "17_service_overview.svg":
        title_limit = 16 if tuning.compact_service_map == 0 else 12
        lead_limit = 32 if tuning.compact_service_map == 0 else 24
        platform_desc_limit = 16 if tuning.compact_service_map == 0 else 14
        domain_title_limit = 14 if tuning.compact_service_map == 0 else 10
        domain_desc_limit = 24 if tuning.compact_service_map == 0 else 18
        value_limit = 16 if tuning.compact_service_map == 0 else 12
        driver_limit = 28 if tuning.compact_service_map == 0 else 20
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("OVERVIEW_LEAD", lead_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("PLATFORM_NAME", title_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("PLATFORM_DESC", platform_desc_limit, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("DOMAIN_ATTACK_TITLE", domain_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("DOMAIN_ATTACK_DESC", domain_desc_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("DOMAIN_DEFENSE_TITLE", domain_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("DOMAIN_DEFENSE_DESC", domain_desc_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("DOMAIN_TRAINING_TITLE", domain_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("DOMAIN_TRAINING_DESC", domain_desc_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("VALUE_1", value_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("VALUE_2", value_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("VALUE_3", value_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("DRIVER_POINT_1", driver_limit, 1, mode="action", severity="blocker"),
            SlotBudgetRule("DRIVER_POINT_2", driver_limit, 1, mode="action", severity="blocker"),
        ]
    if template_name == "18_domain_capability_map.svg":
        capability_title_limit = 12
        capability_desc_limit = 16
        return [
            SlotBudgetRule("PAGE_TITLE", title_width, 2, mode="title", severity="blocker"),
            SlotBudgetRule("METHOD_NOTE", 44 if tuning.compact_service_map == 0 else 32, 2, mode="action", severity="blocker"),
            SlotBudgetRule("SCENE_POINT_1", 11, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("SCENE_POINT_2", 11, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("SCENE_POINT_3", 11, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("CAPABILITY_1_TITLE", capability_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CAPABILITY_2_TITLE", capability_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CAPABILITY_3_TITLE", capability_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CAPABILITY_4_TITLE", capability_title_limit, 2, mode="label", severity="blocker"),
            SlotBudgetRule("CAPABILITY_1_DESC", capability_desc_limit, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("CAPABILITY_2_DESC", capability_desc_limit, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("CAPABILITY_3_DESC", capability_desc_limit, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("CAPABILITY_4_DESC", capability_desc_limit, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("OUTCOME_1", 16, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("OUTCOME_2", 16, 3, mode="sentence", severity="blocker"),
            SlotBudgetRule("OUTCOME_3", 16, 3, mode="action", severity="blocker"),
        ]
    if template_name == "19_result_leading_case.svg":
        title_limit = 16 if tuning.semantic_headline == 1 else (12 if tuning.semantic_headline > 1 else 18)
        headline_semantic_level = max(tuning.semantic_headline, tuning.semantic_argument)
        if tuning.compact_header_bundle > 0 or headline_semantic_level > 0:
            headline_limit = 18 if tuning.compact_header_bundle <= 1 else 15
        else:
            headline_limit = 22 if tuning.compact_header_bundle == 1 else 14
        subline_limit = 16 if tuning.compact_header_bundle == 0 else 10
        action_limit = 7 if tuning.compact_attack_chain > 1 else 8
        return [
            SlotBudgetRule("PAGE_TITLE", title_limit, 1 if tuning.semantic_headline > 0 else 2, mode="title", severity="blocker"),
            SlotBudgetRule("RESULT_HEADLINE", headline_limit, 2, mode="sentence", severity="blocker"),
            SlotBudgetRule("HEADLINE_SUBLINE", subline_limit, 1, mode="sentence"),
            SlotBudgetRule("CLIENT_CONTEXT", 18 if tuning.compact_header_bundle == 0 else 12, 1, mode="label"),
            SlotBudgetRule("ACTION_1", action_limit, 2, mode="label"),
            SlotBudgetRule("ACTION_2", action_limit, 2, mode="label"),
            SlotBudgetRule("ACTION_3", action_limit, 2, mode="label"),
            SlotBudgetRule("RESULT_1", 6 if tuning.compact_attack_chain > 1 else 8, 2, mode="sentence"),
            SlotBudgetRule("RESULT_2", 24 if tuning.compact_attack_chain == 0 else 18, 2, mode="sentence"),
            SlotBudgetRule("RESULT_3", 24 if tuning.compact_attack_chain == 0 else 18, 2, mode="action"),
            SlotBudgetRule("CLOSURE_1", 18 if tuning.compact_attack_chain == 0 else 14, 2, mode="action"),
            SlotBudgetRule("CLOSURE_2", 18 if tuning.compact_attack_chain == 0 else 14, 2, mode="action"),
            SlotBudgetRule("CLOSURE_3", 18 if tuning.compact_attack_chain == 0 else 14, 2, mode="action"),
        ]
    return []


def fit_slot_value(text: str, rule: SlotBudgetRule) -> str:
    value = normalize_text(text)
    if not value:
        return ""
    respect_points = True
    capacity = slot_budget_capacity(rule)
    if rule.mode == "label":
        candidate = compact_security_label(value, capacity, 1)
    elif rule.mode == "evidence":
        candidate = compact_evidence_sentence(value, capacity, 1)
    elif rule.mode == "action":
        candidate = compact_action_result(value, capacity, 1)
        respect_points = not looks_like_closure_sentence(candidate)
    elif rule.mode == "title":
        candidate = shorten(value, capacity)
        respect_points = False
    else:
        candidate = compact_security_sentence(value, capacity, 1)
    lines = wrap_text(candidate, rule.max_chars, rule.max_lines, respect_points=respect_points)
    return "".join(lines) if lines else candidate


def slot_text_overflows(text: str, rule: SlotBudgetRule) -> bool:
    value = normalize_text(text)
    if not value:
        return False
    rendered = "".join(wrap_text(value, rule.max_chars, rule.max_lines))
    return normalize_text(rendered) != value


def apply_slot_budget_contract(
    ctx: PageContext,
    values: dict[str, str],
    tuning: RenderTuning,
) -> tuple[dict[str, str], list[str], list[str], list[str]]:
    updated = dict(values)
    repairs: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    for rule in slot_budget_rules(ctx, tuning):
        original = normalize_text(str(updated.get(rule.key) or ""))
        if not original:
            continue
        fitted = fit_slot_value(original, rule)
        if fitted and normalize_text(fitted) != original:
            updated[rule.key] = fitted
            repairs.append(f"{rule.key} 压缩到 {rule.max_chars}x{rule.max_lines}")
        final_text = normalize_text(str(updated.get(rule.key) or ""))
        if slot_text_overflows(final_text, rule):
            message = f"{rule.key} 仍超出槽位预算 {rule.max_chars}x{rule.max_lines}"
            if rule.severity == "blocker":
                blockers.append(message)
            else:
                warnings.append(message)
    return updated, repairs, blockers, warnings


def escape_xml(text: str) -> str:
    return html.escape(text or "", quote=False)


def apply_aliases(text: str, aliases: list[tuple[str, str]]) -> str:
    value = normalize_text(text)
    for old, new in aliases:
        value = value.replace(old, new)
    return value


def compact_security_label(text: str, limit: int, level: int = 0) -> str:
    value = apply_aliases(text, SECURITY_LABEL_ALIASES)
    if level >= 1:
        for filler in SECURITY_LABEL_FILLERS:
            value = value.replace(filler, "")
        value = re.sub(r"(证据|动作|结果|资产){2,}", r"\1", value)
        value = normalize_text(value)
    if level >= 2:
        value = value.replace("核心触达", "触达")
        value = value.replace("权限放大", "提权放大")
        value = value.replace("连续突破控制", "突破控制")
        value = normalize_text(value)
    return shorten(value or text, limit)


def compact_security_sentence(text: str, limit: int, level: int = 0) -> str:
    value = apply_aliases(text, SECURITY_LABEL_ALIASES)
    if level >= 1:
        value = re.sub(r"[。；;]+$", "", value)
        value = re.split(r"[；;。]", value)[0]
        value = value.replace("通过", "")
        value = value.replace("说明", "")
        value = normalize_text(value)
    return shorten(value or text, limit)


def cleanup_evidence_fragment(text: str) -> str:
    value = rewrite_soft_blacklist_terms(normalize_text(text))
    value = re.sub(r"^证据\s*[A-Za-z0-9一二三四五六七八九十]+\s*(?:->|[:：-])\s*", "", value, flags=re.I)
    value = re.sub(r"^(截图|结果|样例|案例)\s*[A-Za-z0-9一二三四五六七八九十]+\s*(?:->|[:：-])\s*", "", value, flags=re.I)
    value = re.sub(r"^(将|把|需|需要|应|建议|请)\S{0,8}(证据|截图|结果)\S{0,8}(放在|挂在|放入|置于|呈现|展示).*$", "", value)
    return normalize_text(value)


def infer_evidence_tech(text: str) -> str:
    value = normalize_text(text)
    lowered = value.lower()
    if "thinkphp" in lowered:
        return "ThinkPHP RCE"
    if "log4j2" in lowered or "log4j" in lowered:
        return "Log4j2 RCE"
    if "nacos" in lowered:
        return "Nacos 后台"
    if "xxl-job" in lowered or "xxljob" in lowered:
        return "XXL-JOB 后台"
    if "敏感信息泄露" in value:
        return "敏感信息泄露"
    return ""


def infer_evidence_result(text: str) -> str:
    value = normalize_text(text)
    lowered = value.lower()
    compact = re.sub(r"\s+", "", lowered)
    compact_value = re.sub(r"\s+", "", value)
    if "webshell" in compact:
        return "已获取 Webshell"
    if "内存马" in value:
        return "已写入内存马"
    if "敏感信息泄露" in value or ("敏感信息" in value and any(token in value for token in ("泄露", "遍历", "获取"))):
        return "已验证敏感信息泄露"
    if "办公pc" in compact and "权限" in compact_value:
        return "已获取办公 PC 权限"
    if "数据库" in value and any(token in value for token in ("账号", "账户", "口令", "密码", "凭证")):
        return "已获取数据库口令"
    if "数据库权限" in value or ("数据库" in value and "权限" in value):
        return "已获取数据库权限"
    if "服务器权限" in value or ("服务器" in value and any(token in value for token in ("控制", "接管", "权限"))):
        return "已获取服务器权限"
    if "后台权限" in value:
        return "已获取后台权限"
    if any(token in value for token in ("域控", "域管", "横向移动", "横向扩散", "横向")):
        return "已形成权限突破"
    if "权限" in value:
        return "已形成权限突破"
    if "远程代码执行" in value or "远程执行" in value:
        return "已验证远程执行"
    return ""


def compact_evidence_result(result: str) -> str:
    value = normalize_text(result)
    mapping = {
        "已获取 Webshell": "Webshell",
        "已写入内存马": "内存马",
        "已验证敏感信息泄露": "敏感信息泄露",
        "已获取办公 PC 权限": "办公 PC 权限",
        "已获取数据库口令": "数据库口令",
        "已获取数据库权限": "数据库权限",
        "已获取服务器权限": "服务器权限",
        "已获取后台权限": "后台权限",
        "已形成权限突破": "权限突破",
        "已验证远程执行": "远程执行",
    }
    return mapping.get(value, value)


def compact_evidence_sentence(text: str, limit: int, level: int = 0) -> str:
    value = cleanup_evidence_fragment(text)
    if not value:
        return ""
    fragments = [cleanup_evidence_fragment(item) for item in split_points(value, limit=6)]
    fragments = [
        item
        for item in fragments
        if item
        and not contains_planning_tone(item)
        and not is_generic_model_evidence_item(item)
    ]
    if not fragments:
        fragments = [value]
    candidates: list[str] = []
    overall_label = derive_example_label(value, "关键证据")
    overall_tech = infer_evidence_tech(value)
    overall_result = infer_evidence_result(value)
    overall_terse_result = compact_evidence_result(overall_result)
    for candidate in (
        "，".join(part for part in (overall_tech, overall_terse_result) if part),
        overall_terse_result,
        "，".join(part for part in (overall_label, overall_terse_result) if part),
    ):
        candidate = normalize_text(candidate)
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    for fragment in fragments[:4]:
        normalized = normalize_text(fragment)
        if not normalized:
            continue
        ip_match = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", normalized)
        ip = ip_match.group(0) if ip_match else ""
        label = derive_example_label(normalized, "关键证据")
        tech = infer_evidence_tech(normalized)
        result = infer_evidence_result(normalized)
        terse_result = compact_evidence_result(result)

        detail_candidates = [
            "，".join(part for part in (f"{ip} {tech}".strip(), terse_result) if part),
            "，".join(part for part in (tech, terse_result) if part),
            terse_result,
            "，".join(part for part in (f"{ip} {tech}".strip(), result) if part),
            "，".join(part for part in (f"{label} {tech}".strip() if tech and tech not in label else label, result) if part),
            "，".join(part for part in (tech, result) if part),
            "，".join(part for part in (label, result) if part),
            normalized,
        ]
        for candidate in detail_candidates:
            candidate = normalize_text(candidate)
            if candidate and candidate not in candidates:
                candidates.append(candidate)

    if not candidates:
        candidates = [value]

    for candidate in candidates:
        compacted = compact_security_sentence(candidate, limit, min(level, 1))
        if compacted == candidate and len(compacted) <= limit:
            return compacted
    for candidate in candidates:
        if len(candidate) <= limit:
            return candidate

    keyword_summary = []
    primary = derive_example_label(value, "关键证据")
    if primary:
        keyword_summary.append(primary)
    result = infer_evidence_result(value)
    if result:
        keyword_summary.append(compact_evidence_result(result))
    fallback = "，".join(keyword_summary) if keyword_summary else value
    return compact_security_sentence(fallback, limit, max(1, level))


def compact_action_result(text: str, limit: int, level: int = 0) -> str:
    value = apply_aliases(text, SECURITY_LABEL_ALIASES)
    value = re.sub(r"[。]+$", "", value)
    if level >= 1:
        value = value.replace("通过", "")
        value = value.replace("说明", "")
        value = normalize_text(value)
    return shorten(value or text, limit)


def normalize_toc_desc(text: str, limit: int, level: int = 0) -> str:
    value = compact_security_sentence(text, limit + 6, min(level, 1))
    value = re.split(r"[，、]", value)[0]
    value = normalize_text(value)
    if level >= 1:
        value = re.sub(r"^(围绕|聚焦|展示|说明|总结|沉淀)", "", value)
        value = normalize_text(value)
    return shorten(value or "章节概览", limit)


def rewrite_soft_blacklist_terms(text: str) -> str:
    value = normalize_text(text)
    for old, new in SOFT_BLACKLIST_REWRITES.items():
        value = value.replace(old, new)
    return normalize_text(value)


def contains_planning_tone(text: str) -> bool:
    value = normalize_text(text)
    return any(pattern in value for pattern in PLANNING_TONE_PATTERNS)


def looks_like_judgment_sentence(text: str) -> bool:
    value = re.sub(r"\s+", "", rewrite_soft_blacklist_terms(text))
    if len(value) < 6:
        return False
    if value in GENERIC_JUDGMENT_PHRASES:
        return False
    return any(marker in value for marker in JUDGMENT_MARKERS)


def looks_like_closure_sentence(text: str) -> bool:
    value = re.sub(r"\s+", "", rewrite_soft_blacklist_terms(text))
    if len(value) < 4:
        return False
    if any(pattern in value for pattern in GENERIC_CLOSURE_PATTERNS):
        return False
    return any(marker in value for marker in CLOSURE_ACTION_MARKERS)


def semantic_headline_text(ctx: PageContext, *, limit: int, level: int = 0) -> str:
    candidates: list[str] = [
        ctx.core_judgment,
        ctx.page_intent,
        ctx.proof_goal,
    ]
    for field_name in ("sub_judgment", "argument_spine", "key_relations"):
        candidates.extend(model_items(ctx.complex_model, field_name))
    for candidate in candidates:
        text = rewrite_soft_blacklist_terms(strip_leading_label(candidate))
        if text and looks_like_judgment_sentence(text):
            return compact_security_sentence(text, limit, min(2, level))
    fallback = rewrite_soft_blacklist_terms(strip_leading_label(ctx.core_judgment or ctx.page_title))
    if fallback and level > 0 and not looks_like_judgment_sentence(fallback):
        fallback = f"{strip_display_prefix(ctx.page_title) or '当前链路'}已形成可验证风险"
    return compact_security_sentence(fallback or ctx.page_title, limit, min(2, level))


def semantic_keyword_set(text: str) -> set[str]:
    value = normalize_text(rewrite_soft_blacklist_terms(text))
    if not value:
        return set()
    fragments: list[str] = []
    for item in re.split(r"[，。；：、“”‘’（）()【】/\|\-\s]+", value):
        if not item:
            continue
        fragments.extend(
            part
            for part in re.split(
                r"(?:与|和|及|并|共同|导致|形成|放大|推进|整改|复测|验证|切断|封堵|收口|治理|补齐|安排|并非|而是|使|缺少|滞后|存在)",
                item,
            )
            if part
        )
    keywords: set[str] = set()
    def add_keyword_variants(raw_value: str) -> None:
        raw_value = normalize_text(raw_value).strip("，、；：: ")
        if len(raw_value) < 2:
            return
        variants = {raw_value}
        prefix_stripped = re.sub(
            r"^(整体|总体|核心|关键|主要|本次|当前|后续|进一步|继续|先|再|最后|优先|应|需|需要|必须|收口|切断|封堵|阻断|补强|治理|整改|复测|验证|安排|补齐|压降|确认|判断|证明|说明|聚焦|围绕|按)",
            "",
            raw_value,
        )
        if prefix_stripped and prefix_stripped != raw_value:
            variants.add(prefix_stripped)
        suffix_stripped = re.sub(
            r"(总览|概览|概述|摘要|分析|拆解|矩阵|路径|链路|案例|结构|页面|模块|动作|结果|问题|治理|整改|闭环|风险|判断|证明)$",
            "",
            raw_value,
        )
        if suffix_stripped and suffix_stripped != raw_value:
            variants.add(suffix_stripped)
        combined = re.sub(
            r"(总览|概览|概述|摘要|分析|拆解|矩阵|路径|链路|案例|结构|页面|模块|动作|结果|问题|治理|整改|闭环|风险|判断|证明)$",
            "",
            prefix_stripped,
        )
        if combined and combined != raw_value:
            variants.add(combined)
        if raw_value.startswith("非") and len(raw_value) >= 3:
            variants.add(raw_value[1:])
        if "后的" in raw_value:
            before, after = raw_value.split("后的", 1)
            if before:
                variants.add(before)
            if after:
                variants.add(after)
        for candidate in variants:
            candidate = normalize_text(candidate).strip("，、；：: ")
            if len(candidate) < 2 or candidate in SEMANTIC_KEYWORD_STOPWORDS:
                continue
            keywords.add(candidate)

    for fragment in fragments:
        add_keyword_variants(fragment)
    if not keywords:
        compact = re.sub(r"[^\w\u4e00-\u9fff]+", "", value)
        if len(compact) >= 2:
            keywords.add(compact)
    return keywords


def semantic_overlap_score(text_a: str, text_b: str) -> int:
    compact_a = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalize_text(rewrite_soft_blacklist_terms(text_a)))
    compact_b = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalize_text(rewrite_soft_blacklist_terms(text_b)))
    if not compact_a or not compact_b:
        return 0
    if compact_a in compact_b or compact_b in compact_a:
        return 4
    keywords_a = semantic_keyword_set(text_a)
    keywords_b = semantic_keyword_set(text_b)
    overlap = keywords_a & keywords_b
    if overlap:
        return len(overlap)
    parts_a = {normalize_text(item) for item in split_points(text_a, limit=6) if normalize_text(item)}
    parts_b = {normalize_text(item) for item in split_points(text_b, limit=6) if normalize_text(item)}
    return len(parts_a & parts_b)


def case_chain_headline_text(ctx: PageContext, *, limit: int, level: int = 0) -> str:
    base = rewrite_soft_blacklist_terms(strip_leading_label(ctx.core_judgment or ctx.page_title))
    track_type = attack_track_type(ctx.page_title)
    if level <= 0:
        return compact_security_sentence(base, limit, 0)

    if track_type == "internal":
        candidate = "凭证暴露、管理面失守与弱审计放大内网风险"
    elif track_type == "internet":
        candidate = "互联网暴露面与高危漏洞形成初始进入能力"
    elif track_type == "social":
        candidate = "社工钓鱼路径与系统侧路径相互补充"
    elif any(token in ctx.page_title for token in ("证据", "证明", "总览")):
        candidate = "证据已支撑关键路径与结果判断"
    else:
        candidate = base

    if semantic_overlap_score(candidate, base) <= 0:
        candidate = base
    return compact_security_sentence(candidate or base, limit, min(2, level))


def default_closure_message(ctx: PageContext, index: int, *, allow_action_override: bool = True) -> str:
    track_type = attack_track_type(ctx.page_title)
    if track_type == "internal":
        defaults = [
            "先收口凭证暴露与管理面失守",
            "再补齐弱审计并切断横向扩散",
            "最后复测验证内网主链失效",
        ]
    elif track_type == "internet":
        defaults = [
            "先封堵互联网暴露面与高危漏洞",
            "再清理外网入口与初始落点",
            "最后复测验证初始进入失效",
        ]
    elif track_type == "social":
        defaults = [
            "先收口社工钓鱼路径",
            "再切断账号转化与终端落点",
            "最后复测验证人员侧入口失效",
        ]
    elif any(token in ctx.page_title for token in ("证据", "证明", "总览")):
        defaults = [
            "先确认关键路径与结果判断证据已闭合",
            "再把关键路径与结果判断逐一对应",
            "最后按关键路径证据优先级推进整改",
        ]
    else:
        defaults = [
            "先封堵高风险入口与暴露面",
            "再切断凭证复用与横向扩散",
            "最后复测验证核心链路失效",
        ]
    action = rewrite_soft_blacklist_terms(strip_leading_label(page_action_text(ctx)))
    if allow_action_override and index == 0 and action:
        if ctx.core_judgment and semantic_overlap_score(action, ctx.core_judgment) <= 0:
            action = ""
        if looks_like_closure_sentence(action):
            return action
        if any(token in action for token in ("整改", "推进", "封堵", "压降", "治理", "补齐", "收口")):
            return f"优先{action}" if not action.startswith(("先", "再", "最后", "优先")) else action
    return defaults[min(index, len(defaults) - 1)]


def semantic_closure_text(
    ctx: PageContext,
    text: str,
    *,
    index: int,
    allow_action_override: bool = True,
) -> str:
    value = rewrite_soft_blacklist_terms(strip_leading_label(text))
    value = re.sub(r"[。；;]+$", "", value)
    if any(pattern in value for pattern in GENERIC_CLOSURE_PATTERNS):
        value = ""
    if not value:
        return default_closure_message(ctx, index, allow_action_override=allow_action_override)
    if looks_like_closure_sentence(value):
        return value
    if not any(marker in value for marker in CLOSURE_ACTION_MARKERS):
        return default_closure_message(ctx, index, allow_action_override=allow_action_override)
    prefix = ("先", "再", "最后")[min(index, 2)]
    return f"{prefix}{value}" if not value.startswith(("先", "再", "最后", "优先")) else value


def derive_section_index(section_name: str, sections: list[dict[str, str]], page_title: str) -> int:
    candidates = [
        normalize_text(section_name),
        strip_display_prefix(page_title),
    ]
    for idx, section in enumerate(sections, start=1):
        section_title = normalize_text(section.get("title", ""))
        if not section_title:
            continue
        for candidate in candidates:
            if candidate and (candidate == section_title or section_title in candidate or candidate in section_title):
                return idx
    return 1


def is_redundant_section_desc(title: str, desc: str) -> bool:
    clean_title = normalize_text(strip_display_prefix(title))
    clean_desc = normalize_text(desc)
    if not clean_title or not clean_desc:
        return False
    if clean_desc == clean_title or clean_desc in clean_title or clean_title in clean_desc:
        return True
    title_core = re.sub(r"(附录|章节|整体|概述|分析|总结|详情|建议|与|及|的|：|:)", "", clean_title)
    desc_core = re.sub(r"(附录|章节|整体|概述|分析|总结|详情|建议|与|及|的|：|:)", "", clean_desc)
    if desc_core and title_core and (desc_core in title_core or title_core in desc_core):
        return True
    return False


def derive_section_desc(section_name: str, sections: list[dict[str, str]], fallback: str) -> str:
    section_title = normalize_text(section_name)
    title_for_rules = section_title or normalize_text(fallback)
    for keywords, desc in SECTION_DESC_RULES:
        if all(keyword in title_for_rules for keyword in keywords):
            return desc

    for section in sections:
        title = normalize_text(section.get("title", ""))
        if not title:
            continue
        if section_title and not (section_title == title or title in section_title or section_title in title):
            continue
        for key in ("goal", "problem", "page_types"):
            candidate = rewrite_soft_blacklist_terms(section.get(key, ""))
            if (
                candidate
                and not contains_planning_tone(candidate)
                and len(candidate) <= 24
                and not is_redundant_section_desc(section_title or title, candidate)
            ):
                return candidate
        break

    fallback_text = rewrite_soft_blacklist_terms(fallback)
    if contains_planning_tone(fallback_text):
        fallback_text = ""
    if is_redundant_section_desc(section_title or fallback_text, fallback_text):
        fallback_text = ""
    return fallback_text or "章节重点概览"


def build_toc_desc(section_title: str, raw_desc: str) -> str:
    desc = rewrite_soft_blacklist_terms(raw_desc)
    if desc and not contains_planning_tone(desc):
        return desc
    return derive_section_desc(section_title, [{"title": section_title}], "")


def derive_page_guide_label(ctx: PageContext) -> str:
    template_name = ctx.template_path.name
    page_title = strip_display_prefix(ctx.page_title)
    track_type = attack_track_type(page_title)
    if template_name == "07_data.svg":
        if any(token in page_title for token in ("成果", "战果", "结果")):
            return "关键结果摘要"
        if any(token in page_title for token in ("社工", "钓鱼")):
            return "人员风险摘要"
        return "关键结论摘要"
    if template_name == "12_grid.svg":
        if any(token in page_title for token in ("成果", "结果")):
            return "已形成高风险结果"
        if any(token in page_title for token in ("风险总览", "暴露面")):
            return "风险集中需优先排序"
        if any(token in page_title for token in ("整改", "建议", "闭环", "优先级")):
            return "治理动作拆解"
        return "问题结构拆解"
    if template_name == "19_result_leading_case.svg":
        if track_type == "internal":
            return "内网链路拆解"
        if track_type == "internet":
            return "互联网链路拆解"
        if track_type == "social":
            return "社工链路拆解"
        return "典型链路拆解"
    if template_name == "05_case.svg":
        return "典型案例拆解"
    return ""


def filter_semantic_points(text: str, *, limit: int = 6) -> list[str]:
    blocked_tokens = ["概述", "分析", "整体回顾", "总体判断", "攻击路径概述", "整体攻击路径分析"]
    points: list[str] = []
    for item in split_points(text, limit=limit * 2):
        rewritten = rewrite_soft_blacklist_terms(item)
        if not rewritten:
            continue
        if any(token in rewritten and len(rewritten) <= len(token) + 4 for token in blocked_tokens):
            continue
        points.append(rewritten)
        if len(points) >= limit:
            break
    return points


def semantic_points_with_fallback(ctx: PageContext, *, limit: int = 6) -> list[str]:
    candidates: list[str] = []
    candidates.extend(ctx.semantic_points)
    candidates.extend(filter_semantic_points(ctx.supporting_evidence, limit=limit * 2))
    candidates.extend(filter_semantic_points(ctx.page_intent, limit=limit))
    candidates.extend(filter_semantic_points(ctx.proof_goal, limit=limit))
    candidates.extend(filter_semantic_points(ctx.next_relation, limit=max(2, limit // 2)))
    return merge_unique_texts(candidates, limit=limit)


def page_action_text(ctx: PageContext) -> str:
    closure_items = model_items(ctx.complex_model, "closure")
    for item in closure_items:
        if any(keyword in item for keyword in ("建议动作", "整改", "复测", "优先", "推进", "封堵")):
            return strip_leading_label(item)
    if closure_items:
        return strip_leading_label(closure_items[-1])
    return ctx.desired_action or ctx.goal or ctx.next_relation


def closure_messages(ctx: PageContext, *, limit: int = 3, repair_level: int = 0) -> list[str]:
    candidates = [strip_leading_label(item) for item in model_items(ctx.complex_model, "closure")]
    if not candidates:
        candidates = [
            "先封堵入口与弱控制点",
            "再切断横向扩散与放大条件",
            "最后复测确认核心链路失效",
        ]
    if repair_level > 0 and attack_track_type(ctx.page_title) == "overview" and any(
        token in ctx.page_title for token in ("证据", "证明", "总览")
    ):
        candidates = [
            default_closure_message(ctx, index, allow_action_override=False)
            for index in range(limit)
        ]
    if repair_level > 0:
        candidates = [
            semantic_closure_text(ctx, item, index=index, allow_action_override=False)
            for index, item in enumerate(candidates[:limit])
        ]
    merged = merge_unique_texts(candidates, limit=limit)
    while len(merged) < limit:
        fallback = default_closure_message(
            ctx,
            len(merged),
            allow_action_override=repair_level <= 0,
        )
        merged = merge_unique_texts(merged + [fallback], limit=limit)
    if repair_level > 0:
        repaired = [
            semantic_closure_text(ctx, item, index=index, allow_action_override=False)
            for index, item in enumerate(merged[:limit])
        ]
        merged = merge_unique_texts(repaired, limit=limit)
        while len(merged) < limit:
            merged = merge_unique_texts(
                merged + [default_closure_message(ctx, len(merged), allow_action_override=False)],
                limit=limit,
            )
        judgment = normalize_text(ctx.core_judgment)
        if judgment:
            anchored: list[str] = []
            for index, item in enumerate(merged[:limit]):
                if semantic_overlap_score(item, judgment) <= 0 and index == 0:
                    anchored.append(strip_leading_label(ctx.core_judgment))
                else:
                    anchored.append(item)
            merged = merge_unique_texts(anchored, limit=limit)
    return merged[:limit]


def header_page_title(ctx: PageContext) -> str:
    title = strip_display_prefix(ctx.page_title)
    if ctx.template_id == "security_service" and is_complex_page(ctx.page):
        if ctx.template_path.name == "05_case.svg":
            if any(token in title for token in ("整体回顾", "项目范围")):
                return "本轮范围、对象与周期已足以支撑后续结论"
            if any(token in title for token in ("社工", "钓鱼")):
                return "社工钓鱼路径与系统侧路径相互补充"
            return semantic_headline_text(ctx, limit=28, level=1)
        if ctx.template_path.name == "07_data.svg":
            if any(token in title for token in ("重要成果", "关键结果")):
                return "外网突破、内网横向和人员受骗已构成高风险结果"
            if any(token in title for token in ("攻击链总览", "整体攻击路径分析")):
                return "多条入口最终汇聚相似控制结果"
            if "内网突破" in title:
                return "后台权限、未授权访问和凭证问题叠加"
            return semantic_headline_text(ctx, limit=28, level=1)
        if ctx.template_path.name == "08_product.svg":
            if "风险结构总览" in title:
                return "四类控制薄弱域共同构成主要根因"
            if any(token in title for token in ("互联网侧", "检测与防护")):
                return "持续检测与及时修补不足使高危入口长期暴露"
            return semantic_headline_text(ctx, limit=28, level=1)
        if ctx.template_path.name == "16_table.svg":
            if any(token in title for token in ("异常登陆", "异常登录", "审计问题")):
                return "异常登录审计缺失与高危端口暴露放大驻留风险"
            if any(token in title for token in ("治理矩阵", "优先级排序")):
                return "先封堵互联网入口、凭证风险和内网放大条件"
            return semantic_headline_text(ctx, limit=28, level=1)
        if ctx.template_path.name == "09_comparison.svg":
            return semantic_headline_text(ctx, limit=28, level=1)
        if ctx.template_path.name == "17_service_overview.svg":
            return semantic_headline_text(ctx, limit=28, level=1)
        if ctx.template_path.name == "18_domain_capability_map.svg" and "风险结构总览" in title:
            return "互联网暴露、审计不足与凭证/人员薄弱构成主要根因"
        if ctx.template_path.name == "18_domain_capability_map.svg" and "审计问题" in title:
            return "审计缺失与高危端口暴露放大内网驻留风险"
        if ctx.template_path.name == "18_domain_capability_map.svg" and "安全意识" in title:
            return "人员识别与响应薄弱持续稀释系统侧治理效果"
        if ctx.template_path.name == "18_domain_capability_map.svg" and any(token in title for token in ("互联网侧系统安全检测与防护待加强", "检测与防护待加强")):
            return "持续检测与及时修补不足使高危入口长期暴露"
        if ctx.template_path.name == "18_domain_capability_map.svg" and "整改复测机制" in title:
            return "责任动作复测回看缺一不可"
        if ctx.template_path.name == "18_domain_capability_map.svg" and "长亭安服价值" in title:
            return "把复杂风险翻译成可验证、可排序、可闭环动作"
        if ctx.template_path.name == "08_product.svg" and any(token in title for token in ("通用口令", "通用密码")):
            return "通用口令与权限复用放大多点扩散"
        if ctx.template_path.name == "10_timeline.svg" and any(token in title for token in ("整改路线图", "分阶段推进计划")):
            return "先压高风险入口，再补齐监测审计与制度能力"
        segments = [normalize_text(part) for part in re.split(r"[/／]", title) if normalize_text(part)]
        if segments:
            return segments[0]
    return title or ctx.page_title


def derive_example_label(text: str, fallback: str) -> str:
    value = rewrite_soft_blacklist_terms(text)
    keyword_patterns = [
        (r"thinkphp", "ThinkPHP"),
        (r"log4j2?", "Log4j2"),
        (r"nacos", "Nacos"),
        (r"xxl-?job", "XXL-JOB"),
        (r"钓鱼", "钓鱼链"),
        (r"敏感信息泄露", "敏感信息"),
        (r"后台权限", "后台权限"),
        (r"远程代码执行", "远程执行"),
    ]
    lowered = value.lower()
    for pattern, label in keyword_patterns:
        if re.search(pattern, lowered):
            if "colmo" in lowered:
                return "COLMO " + label
            if "美的光伏" in value:
                return "光伏平台 " + label
            return label

    segments = [segment.strip() for segment in re.split(r"[-/:：]", value) if segment.strip()]
    for segment in segments:
        if 2 <= len(segment) <= 14 and not segment.isdigit():
            return compact_security_label(segment, 12, 1)
    return compact_security_label(fallback, 12, 1)


def attack_track_type(title: str) -> str:
    value = normalize_text(title)
    if "互联网" in value:
        return "internet"
    if "内网" in value:
        return "internal"
    if "社工" in value or "钓鱼" in value:
        return "social"
    return "overview"


def get_svg_attr(attrs: str, name: str) -> str:
    match = re.search(rf'\b{name}="([^"]*)"', attrs)
    return match.group(1) if match else ""


def set_svg_attr(attrs: str, name: str, value: str | int | float) -> str:
    value_text = str(value)
    pattern = rf'(\b{name}=")([^"]*)(")'
    if re.search(pattern, attrs):
        return re.sub(pattern, rf"\g<1>{value_text}\g<3>", attrs)
    return attrs + f' {name}="{value_text}"'


def rewrite_text_node(
    svg_text: str,
    x: int,
    y: int,
    *,
    lines: list[str] | None = None,
    font_size: int | None = None,
    y_override: int | None = None,
    line_height: int | None = None,
) -> str:
    pattern = re.compile(
        rf'<text(?P<attrs>[^>]*\bx="{x}"[^>]*\by="{y}"[^>]*)>(?P<content>.*?)</text>'
    )

    def repl(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        content = match.group("content")
        if font_size is not None:
            attrs = set_svg_attr(attrs, "font-size", font_size)
        if y_override is not None:
            attrs = set_svg_attr(attrs, "y", y_override)
        if lines is None:
            return f"<text{attrs}>{content}</text>"
        cleaned = [normalize_text(item) for item in lines if normalize_text(item)]
        if not cleaned:
            return f"<text{attrs}></text>"
        if len(cleaned) == 1:
            return f"<text{attrs}>{escape_xml(cleaned[0])}</text>"
        x_value = get_svg_attr(attrs, "x") or str(x)
        step = line_height or max(12, int((font_size or int(float(get_svg_attr(attrs, 'font-size') or 12))) * 1.15))
        parts = [f"<text{attrs}>"]
        for idx, line in enumerate(cleaned):
            dy = "0" if idx == 0 else str(step)
            parts.append(f'<tspan x="{x_value}" dy="{dy}">{escape_xml(line)}</tspan>')
        parts.append("</text>")
        return "".join(parts)

    return pattern.sub(repl, svg_text, count=1)


def rewrite_semantic_header_title(
    svg_text: str,
    title: str,
    *,
    width: int = 18,
    font_size: int = 20,
    y_override: int = 78,
    line_height: int = 20,
) -> str:
    return rewrite_text_node(
        svg_text,
        84,
        82,
        lines=wrap_text(title, width, 2, respect_points=False),
        font_size=font_size,
        y_override=y_override,
        line_height=line_height,
    )


def text_element(
    x: float,
    y: float,
    lines: list[str],
    *,
    fill: str,
    font_size: int,
    font_family: str,
    font_weight: str = "normal",
    anchor: str = "start",
    line_height: int | None = None,
) -> str:
    if not lines:
        return ""
    line_height = line_height or int(font_size * 1.35)
    attrs = [
        f'x="{int(round(x))}"',
        f'y="{int(round(y))}"',
        f'fill="{fill}"',
        f'font-family="{font_family}"',
        f'font-size="{font_size}"',
    ]
    if font_weight != "normal":
        attrs.append(f'font-weight="{font_weight}"')
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if len(lines) == 1:
        return f"<text {' '.join(attrs)}>{escape_xml(lines[0])}</text>"

    parts = [f"<text {' '.join(attrs)}>"]
    for idx, line in enumerate(lines):
        dy = 0 if idx == 0 else line_height
        if idx == 0:
            parts.append(f'<tspan x="{int(round(x))}" dy="0">{escape_xml(line)}</tspan>')
        else:
            parts.append(f'<tspan x="{int(round(x))}" dy="{dy}">{escape_xml(line)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


def parse_safe_box(template_text: str) -> tuple[float, float, float, float]:
    match = re.search(r'data-content-safe-box="([\d.]+),([\d.]+),([\d.]+),([\d.]+)"', template_text)
    if not match:
        return (60.0, 125.0, 1160.0, 480.0)
    return tuple(float(match.group(i)) for i in range(1, 5))  # type: ignore[return-value]


def theme_for_template(template_id: str) -> dict[str, str]:
    if template_id == "chaitin":
        return {
            "lead_fill": "#0E1620",
            "lead_opacity": "0.88",
            "card_fill": "#111B27",
            "card_opacity": "0.92",
            "accent": "#6BFF85",
            "accent_secondary": "#22D3EE",
            "accent_soft": "#A7F35A",
            "body": "#D6DEE8",
            "muted": "#8D9AAB",
            "stroke": "#213042",
        }
    return {
        "lead_fill": "#0563C1",
        "lead_opacity": "0.08",
        "card_fill": "#FFFFFF",
        "card_opacity": "0.94",
        "accent": "#0563C1",
        "accent_secondary": "#4472C4",
        "accent_soft": "#ED7D31",
        "body": "#44546A",
        "muted": "#7C8AA0",
        "stroke": "#D9E2F3",
    }


def render_standard_content_area(ctx: PageContext, tuning: RenderTuning) -> str:
    x, y, w, h = parse_safe_box(ctx.template_text)
    theme = theme_for_template(ctx.template_id)
    lead_h = 42 if tuning.compact_standard < 2 else 38
    top_gap = 20 if tuning.compact_standard == 0 else 28
    mid_gap = 20 if tuning.compact_standard == 0 else 16
    card_y = y + lead_h + top_gap
    card_h = min(176, max(118, int(h * 0.44) - tuning.compact_standard * 14))
    card_gap = 20 if tuning.compact_standard == 0 else 16
    card_w = (w - card_gap * 2) / 3.0
    footer_y = card_y + card_h + mid_gap
    footer_h = max(56, min(78, int(y + h - footer_y)))
    content_char_limit = 18 if tuning.compact_standard == 0 else 16
    content_line_limit = 4 if tuning.compact_standard == 0 else 3
    footer_line_limit = 2 if tuning.compact_standard == 0 else 1

    evidence_points = semantic_points_with_fallback(ctx, limit=6)
    evidence_preview = "；".join(evidence_points[:2]) if evidence_points else ""
    action_text = page_action_text(ctx)
    if "问题拆解" in ctx.page_title or "问题" in ctx.page_title:
        cards = [
            ("问题现状", evidence_preview or ctx.page_intent or ctx.page_title),
            ("风险判断", ctx.core_judgment or ctx.proof_goal or ctx.page_intent),
            ("优先动作", action_text or "先处理高风险入口，再推进复测闭环"),
        ]
        footer_label = "管理收束"
        footer_text = ctx.proof_goal or ctx.next_relation or ctx.goal
    elif "案例" in ctx.page_title:
        cards = [
            ("案例切面", evidence_preview or ctx.page_intent or ctx.page_title),
            ("结果判断", ctx.core_judgment or ctx.proof_goal),
            ("治理动作", action_text or ctx.goal or ctx.next_relation),
        ]
        footer_label = "本页收束"
        footer_text = ctx.proof_goal or ctx.next_relation or ctx.goal
    else:
        cards = [
            ("核心现状", ctx.page_intent or evidence_preview or ctx.page_title),
            ("关键判断", ctx.core_judgment or ctx.proof_goal or ctx.page_title),
            ("推进动作", action_text or ctx.goal or ctx.next_relation),
        ]
        footer_label = "管理收束"
        footer_text = ctx.proof_goal or ctx.next_relation or ctx.goal

    parts = [
        f'<rect x="{int(x)}" y="{int(y)}" width="{int(w)}" height="{lead_h}" rx="12" '
        f'fill="{theme["lead_fill"]}" fill-opacity="{theme["lead_opacity"]}" />',
        text_element(
            x + 24,
            y + 26,
            wrap_text(ctx.core_judgment or ctx.page_title, 44, 1),
            fill=theme["accent"],
            font_size=16,
            font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
            font_weight="bold",
        ),
    ]

    for idx, (label, content) in enumerate(cards):
        card_x = x + idx * (card_w + card_gap)
        accent = [theme["accent"], theme["accent_secondary"], theme["accent_soft"]][idx]
        parts.extend(
            [
                f'<rect x="{int(card_x)}" y="{int(card_y)}" width="{int(card_w)}" height="{int(card_h)}" '
                f'rx="16" fill="{theme["card_fill"]}" fill-opacity="{theme["card_opacity"]}" />',
                f'<rect x="{int(card_x)}" y="{int(card_y)}" width="{int(card_w)}" height="8" '
                f'rx="16" fill="{accent}" />',
                text_element(
                    card_x + 22,
                    card_y + 34,
                    [label],
                    fill=accent,
                    font_size=13,
                    font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
                    font_weight="bold",
                ),
                text_element(
                    card_x + 22,
                    card_y + 70,
                    wrap_text(content, content_char_limit, content_line_limit),
                    fill=theme["body"],
                    font_size=14,
                    font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
                ),
            ]
        )

    parts.extend(
        [
            f'<rect x="{int(x)}" y="{int(footer_y)}" width="{int(w)}" height="{int(footer_h)}" rx="14" '
            f'fill="{theme["card_fill"]}" fill-opacity="{theme["card_opacity"]}" />',
            text_element(
                x + 22,
                footer_y + 26,
                [footer_label],
                fill=theme["accent"],
                font_size=13,
                font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
                font_weight="bold",
            ),
            text_element(
                x + 112,
                footer_y + 26,
                wrap_text(footer_text, 48, footer_line_limit),
                fill=theme["body"],
                font_size=13,
                font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
            ),
        ]
    )
    return "\n".join(part for part in parts if part)


def render_attack_chain_content_area(ctx: PageContext, tuning: RenderTuning) -> str:
    x, y, w, h = parse_safe_box(ctx.template_text)
    theme = theme_for_template(ctx.template_id)
    points = semantic_points_with_fallback(ctx, limit=6)
    defaults = ["入口暴露", "关键动作", "放大条件", "结果落点"]
    while len(points) < 4:
        points.append(defaults[len(points)])
    node_labels = ["入口节点", "关键动作", "放大条件", "控制结果"]
    node_xs = []
    gap = 20
    node_y = y + 80
    node_h = 118
    node_w = (w - gap * 3) / 4.0
    node_char_limit = 12 if tuning.compact_attack_chain == 0 else 10

    parts = [
        f'<rect x="{int(x)}" y="{int(y)}" width="{int(w)}" height="44" rx="12" '
        f'fill="{theme["lead_fill"]}" fill-opacity="{theme["lead_opacity"]}" />',
        text_element(
            x + 22,
            y + 28,
            wrap_text(ctx.core_judgment or ctx.page_title, 54, 1),
            fill=theme["accent"],
            font_size=16,
            font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
            font_weight="bold",
        ),
    ]

    for idx in range(4):
        card_x = x + idx * (node_w + gap)
        node_xs.append(card_x)
        accent = [theme["accent"], theme["accent_secondary"], theme["accent_soft"], theme["accent_soft"]][idx]
        parts.extend(
            [
                f'<rect x="{int(card_x)}" y="{int(node_y)}" width="{int(node_w)}" height="{int(node_h)}" rx="16" '
                f'fill="{theme["card_fill"]}" fill-opacity="{theme["card_opacity"]}" />',
                f'<rect x="{int(card_x)}" y="{int(node_y)}" width="{int(node_w)}" height="8" rx="16" fill="{accent}" />',
                text_element(
                    card_x + node_w / 2,
                    node_y + 34,
                    [node_labels[idx]],
                    fill=accent,
                    font_size=12,
                    font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
                    font_weight="bold",
                    anchor="middle",
                ),
                text_element(
                    card_x + node_w / 2,
                    node_y + 68,
                    wrap_text(points[idx], node_char_limit, 3),
                    fill=theme["body"],
                    font_size=15,
                    font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
                    font_weight="bold",
                    anchor="middle",
                ),
            ]
        )
        if idx < 3:
            line_x1 = card_x + node_w
            line_x2 = card_x + node_w + gap
            mid_y = node_y + node_h / 2
            parts.extend(
                [
                    f'<line x1="{int(line_x1)}" y1="{int(mid_y)}" x2="{int(line_x2)}" y2="{int(mid_y)}" '
                    f'stroke="{theme["accent_secondary"]}" stroke-width="3" stroke-dasharray="8 6" />',
                    f'<polygon points="{int(line_x2 - 2)},{int(mid_y)} {int(line_x2 - 14)},{int(mid_y - 7)} '
                    f'{int(line_x2 - 14)},{int(mid_y + 7)}" fill="{theme["accent_secondary"]}" />',
                ]
            )

    evidence_y = node_y + node_h + 24
    evidence_h = max(120, int(h - (evidence_y - y) - 18))
    evidence_points = points[:2] + [ctx.core_judgment or ctx.proof_goal]
    evidence_titles = ["关键证据", "结果证据", "管理判断"]
    rail_gap = 18
    rail_w = (w - rail_gap * 2) / 3.0
    evidence_char_limit = 18 if tuning.compact_attack_chain == 0 else 15
    for idx in range(3):
        rail_x = x + idx * (rail_w + rail_gap)
        accent = [theme["accent"], theme["accent_secondary"], theme["accent_soft"]][idx]
        parts.extend(
            [
                f'<rect x="{int(rail_x)}" y="{int(evidence_y)}" width="{int(rail_w)}" height="{int(evidence_h)}" rx="14" '
                f'fill="{theme["card_fill"]}" fill-opacity="{theme["card_opacity"]}" />',
                text_element(
                    rail_x + 20,
                    evidence_y + 28,
                    [evidence_titles[idx]],
                    fill=accent,
                    font_size=13,
                    font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
                    font_weight="bold",
                ),
                text_element(
                    rail_x + 20,
                    evidence_y + 58,
                    wrap_text(evidence_points[idx], evidence_char_limit, 4),
                    fill=theme["body"],
                    font_size=13,
                    font_family="Microsoft YaHei, PingFang SC, Arial, sans-serif",
                ),
            ]
        )

    return "\n".join(part for part in parts if part)


def derive_security_domains(ctx: PageContext) -> list[str]:
    text = " ".join([ctx.core_judgment, ctx.supporting_evidence, ctx.page_intent])
    mapping = [
        ("身份", "身份与认证"),
        ("边界", "边界暴露"),
        ("横向", "横向移动"),
        ("权限", "权限控制"),
        ("核心资产", "核心资产"),
        ("终端", "终端主机"),
        ("弱口令", "弱口令入口"),
    ]
    results: list[str] = []
    for key, label in mapping:
        if key in text and label not in results:
            results.append(label)
    defaults = ["身份与认证", "边界暴露", "横向移动", "核心资产"]
    for item in defaults:
        if item not in results:
            results.append(item)
        if len(results) >= 4:
            break
    return results[:4]


def pick_points(text: str, limit: int = 6) -> list[str]:
    return split_points(text, limit=limit)


def first_point(text: str, fallback: str) -> str:
    points = pick_points(text, limit=1)
    return points[0] if points else fallback


def build_data_page_slots(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    page_title = ctx.page_title
    evidence_points = semantic_points_with_fallback(ctx, limit=6)
    compact_level = min(2, tuning.compact_standard)
    action_text = page_action_text(ctx)

    if "整体回顾" in page_title or "项目范围" in page_title:
        anchors = [("范围", "演练对象"), ("结果", "关键成果"), ("动作", "整改推进")]
        return apply_data_page_argument_overrides(ctx, tuning, {
            "PROOF_CONTEXT": "项目范围与结果概览",
            "PROOF_HEADLINE": "已验证多条高风险主线",
            "PROOF_SUBLINE": "",
            "DATA_VALUE_1": anchors[0][0],
            "DATA_LABEL_1": anchors[0][1],
            "DATA_VALUE_2": anchors[1][0],
            "DATA_LABEL_2": anchors[1][1],
            "DATA_VALUE_3": anchors[2][0],
            "DATA_LABEL_3": anchors[2][1],
            "PROOF_NODE_1": "项目范围",
            "PROOF_CANVAS": "整体结果可信",
            "PROOF_NODE_3": "管理判断",
            "PROOF_RELATION_1": "先确认边界",
            "PROOF_RELATION_2": "再进入结果判断",
            "DATA_NOTE_1": compact_evidence_sentence(evidence_points[0] if evidence_points else first_point(ctx.supporting_evidence, "整体回顾"), 24, compact_level),
            "DATA_NOTE_2": compact_security_sentence(ctx.core_judgment, 24, compact_level),
            "DATA_NOTE_3": compact_security_sentence(action_text, 24, compact_level),
            "PROOF_SUMMARY_1": "先看项目范围",
            "PROOF_SUMMARY_2": "再看关键结果",
            "PROOF_SUMMARY_3": "最后明确动作",
        })

    if "重要成果" in page_title or "关键结果" in page_title:
        source_text = load_source_markdown(ctx.project_dir)
        critical_count = re.search(r'严重\s*(\d+)个', source_text)
        high_count = re.search(r'高危\s*(\d+)个', source_text)
        direct_note = evidence_points[2] if len(evidence_points) > 2 else (evidence_points[0] if evidence_points else "ThinkPHP / log4j2 已形成外网入口突破")
        result_note = evidence_points[3] if len(evidence_points) > 3 else (evidence_points[1] if len(evidence_points) > 1 else "Nacos / AWS / 数据库权限已进一步放大结果")
        management_note = "应按外网入口、内网权限与人员风险三线立即整改复测。"
        return {
            "PROOF_CONTEXT": "关键结果已形成",
            "PROOF_HEADLINE": compact_security_sentence(
                "外网突破、内网横向和人员受骗已共同构成可信的高风险结果",
                34,
                compact_level,
            ),
            "PROOF_SUBLINE": "",
            "DATA_VALUE_1": critical_count.group(1) if critical_count else "3",
            "DATA_LABEL_1": "严重结果",
            "DATA_VALUE_2": high_count.group(1) if high_count else "20",
            "DATA_LABEL_2": "高危问题",
            "DATA_VALUE_3": "3",
            "DATA_LABEL_3": "主风险轨道",
            "PROOF_NODE_1": "外网突破",
            "PROOF_CANVAS": "入口突破 -> 内网扩散 -> 人员命中",
            "PROOF_NODE_3": "高风险判断",
            "PROOF_RELATION_1": "结果已真实落地",
            "PROOF_RELATION_2": "影响已足以排序动作",
            "DATA_NOTE_1": compact_evidence_sentence(direct_note, 24, compact_level),
            "DATA_NOTE_2": compact_evidence_sentence(result_note, 24, compact_level),
            "DATA_NOTE_3": compact_security_sentence(management_note, 24, compact_level),
            "PROOF_SUMMARY_1": "外网突破已形成高风险结果",
            "PROOF_SUMMARY_2": "内网横向与人员命中已被验证",
            "PROOF_SUMMARY_3": "据此按结果影响优先整改复测",
        }

    if "攻击链总览" in page_title or "整体攻击路径分析" in page_title:
        return apply_data_page_argument_overrides(ctx, tuning, {
            "PROOF_CONTEXT": "多入口汇聚判断",
            "PROOF_HEADLINE": "多条入口最终汇聚相似控制结果，说明风险具备结构性和可复制性",
            "PROOF_SUBLINE": "",
            "DATA_VALUE_1": "6",
            "DATA_LABEL_1": "主入口类型",
            "DATA_VALUE_2": "3",
            "DATA_LABEL_2": "放大条件",
            "DATA_VALUE_3": "3",
            "DATA_LABEL_3": "结果触达",
            "PROOF_NODE_1": "外网与人员入口",
            "PROOF_CANVAS": "外网突破 -> 内网放大 -> 结果触达",
            "PROOF_NODE_3": "控制结果",
            "PROOF_RELATION_1": "入口并非孤立存在",
            "PROOF_RELATION_2": "最终汇聚相似控制结果",
            "DATA_NOTE_1": compact_evidence_sentence(
                evidence_points[0] if evidence_points else "互联网与人员侧入口同时存在",
                24,
                compact_level,
            ),
            "DATA_NOTE_2": compact_evidence_sentence(
                evidence_points[1] if len(evidence_points) > 1 else "管理面与凭证问题共同放大风险",
                24,
                compact_level,
            ),
            "DATA_NOTE_3": compact_security_sentence(
                action_text or "应按主链路优先封堵入口、压降放大条件并复测",
                24,
                compact_level,
            ),
            "PROOF_SUMMARY_1": "多条入口已汇聚相似控制结果",
            "PROOF_SUMMARY_2": "放大条件让风险具备可复制性",
            "PROOF_SUMMARY_3": "应按主链路优先封堵并复测",
        })

    if "社工" in page_title or "钓鱼" in page_title:
        return apply_data_page_argument_overrides(ctx, tuning, {
            "PROOF_CONTEXT": "人员侧入口已确认",
            "PROOF_HEADLINE": "社工钓鱼入口可与系统侧路径叠加",
            "PROOF_SUBLINE": "",
            "DATA_VALUE_1": "3",
            "DATA_LABEL_1": "触达角色",
            "DATA_VALUE_2": "2",
            "DATA_LABEL_2": "转化步骤",
            "DATA_VALUE_3": "1",
            "DATA_LABEL_3": "主入口",
            "PROOF_NODE_1": "钓鱼触达",
            "PROOF_CANVAS": "人员触达 -> 账号转化 -> 入口形成",
            "PROOF_NODE_3": "入口形成",
            "PROOF_RELATION_1": "先形成人员入口",
            "PROOF_RELATION_2": "再与系统侧汇合",
            "DATA_NOTE_1": compact_evidence_sentence(
                "采招、客服与 HR 三类角色均被触达",
                24,
                compact_level,
            ),
            "DATA_NOTE_2": compact_security_sentence(
                "社工入口可与系统侧路径叠加，放大整体攻击成功率",
                24,
                compact_level,
            ),
            "DATA_NOTE_3": compact_security_sentence(
                "先收口社工钓鱼路径入口",
                24,
                compact_level,
            ),
            "PROOF_SUMMARY_1": "先确认触达角色",
            "PROOF_SUMMARY_2": "再判断账号转化",
            "PROOF_SUMMARY_3": "最后收口社工钓鱼路径",
        })

    if "结果归因" in page_title:
        source_text = load_source_markdown(ctx.project_dir)
        screenshot_count = re.search(r'(\d+)\s*张原始截图', source_text)
        return apply_data_page_argument_overrides(ctx, tuning, {
            "PROOF_CONTEXT": "结果已具备管理判断",
            "PROOF_HEADLINE": "关键结果并非偶发，而是控制薄弱叠加后的必然输出",
            "PROOF_SUBLINE": "",
            "DATA_VALUE_1": screenshot_count.group(1) if screenshot_count else "78",
            "DATA_LABEL_1": "证据素材",
            "DATA_VALUE_2": "3",
            "DATA_LABEL_2": "结果类型",
            "DATA_VALUE_3": "3",
            "DATA_LABEL_3": "治理优先级",
            "PROOF_NODE_1": "关键结果",
            "PROOF_CANVAS": "控制薄弱 -> 链路放大 -> 结果输出",
            "PROOF_NODE_3": "治理排序",
            "PROOF_RELATION_1": "先看结果输出",
            "PROOF_RELATION_2": "再看治理排序",
            "DATA_NOTE_1": compact_evidence_sentence(
                "关键结果已经由截图、日志与控制结果共同证明",
                24,
                compact_level,
            ),
            "DATA_NOTE_2": compact_security_sentence(
                "关键结果并非技术偶发，而是控制薄弱叠加后的必然输出",
                24,
                compact_level,
            ),
            "DATA_NOTE_3": compact_security_sentence(
                "应按结果影响优先推进外网、内网与人员侧治理",
                24,
                compact_level,
            ),
            "PROOF_SUMMARY_1": "先确认关键结果并非技术偶发",
            "PROOF_SUMMARY_2": "再证明控制薄弱叠加形成结果输出",
            "PROOF_SUMMARY_3": "最后按结果影响排序治理优先级",
        })

    if "内网突破" in page_title:
        anchors = [("3", "后台权限点"), ("2", "放大条件"), ("1", "高影响结果")]
        return apply_data_page_argument_overrides(ctx, tuning, {
            "PROOF_CONTEXT": "内网突破典型案例",
            "PROOF_HEADLINE": compact_security_sentence(
                "后台权限、未授权访问和凭证问题叠加，足以形成高影响结果",
                34,
                compact_level,
            ),
            "PROOF_SUBLINE": "",
            "DATA_VALUE_1": anchors[0][0],
            "DATA_LABEL_1": anchors[0][1],
            "DATA_VALUE_2": anchors[1][0],
            "DATA_LABEL_2": anchors[1][1],
            "DATA_VALUE_3": anchors[2][0],
            "DATA_LABEL_3": anchors[2][1],
            "PROOF_NODE_1": "后台权限",
            "PROOF_CANVAS": "链路可持续放大",
            "PROOF_NODE_3": "高影响结果",
            "PROOF_RELATION_1": "后台与未授权构成进入点",
            "PROOF_RELATION_2": "凭证问题继续放大结果",
            "DATA_NOTE_1": compact_evidence_sentence(evidence_points[0] if evidence_points else "后台权限已获取", 24, compact_level),
            "DATA_NOTE_2": compact_evidence_sentence(evidence_points[1] if len(evidence_points) > 1 else "横向链路已形成", 24, compact_level),
            "DATA_NOTE_3": compact_security_sentence(
                action_text or "先收口后台权限与未授权访问，再压降凭证放大条件",
                24,
                compact_level,
            ),
            "PROOF_SUMMARY_1": "后台权限与未授权已成进入点",
            "PROOF_SUMMARY_2": "凭证问题继续放大高影响结果",
            "PROOF_SUMMARY_3": "优先收口后台与凭证并复测",
        })

    return apply_data_page_argument_overrides(ctx, tuning, {
        "PROOF_CONTEXT": compact_evidence_sentence(ctx.supporting_evidence, 22, compact_level),
        "PROOF_HEADLINE": compact_security_sentence(ctx.core_judgment, 20, compact_level),
        "PROOF_SUBLINE": "",
        "DATA_VALUE_1": "现状",
        "DATA_LABEL_1": "当前判断",
        "DATA_VALUE_2": "证明",
        "DATA_LABEL_2": "关键证据",
        "DATA_VALUE_3": "动作",
        "DATA_LABEL_3": "治理推进",
        "PROOF_NODE_1": "问题现状",
        "PROOF_CANVAS": "关键判断已成立",
        "PROOF_NODE_3": "整改推进",
        "PROOF_RELATION_1": "证据支撑判断",
        "PROOF_RELATION_2": "判断转化动作",
        "DATA_NOTE_1": compact_evidence_sentence(evidence_points[0] if evidence_points else first_point(ctx.supporting_evidence, "关键证据"), 24, compact_level),
        "DATA_NOTE_2": compact_security_sentence(ctx.core_judgment, 24, compact_level),
        "DATA_NOTE_3": compact_security_sentence(action_text, 24, compact_level),
        "PROOF_SUMMARY_1": "先看现状",
        "PROOF_SUMMARY_2": "再看证明",
        "PROOF_SUMMARY_3": "最后看动作",
    })


def build_case_page_slots(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    compact_level = min(2, max(tuning.compact_standard, tuning.semantic_argument))
    closure_level = max(tuning.semantic_argument, tuning.semantic_closure)
    evidence_points = semantic_points_with_fallback(ctx, limit=6)
    closure_points = closure_messages(ctx, limit=3, repair_level=max(1, closure_level))
    evidence_labels = merge_unique_texts(
        [
            compact_evidence_sentence(item, 20, 1)
            for item in evidence_points
            if compact_evidence_sentence(item, 20, 1)
        ],
        limit=3,
    )
    evidence_summary = " / ".join(evidence_labels) or compact_security_sentence(
        ctx.supporting_evidence or ctx.core_judgment,
        32,
        compact_level,
    )
    action_text = page_action_text(ctx)

    background_title = "输入边界"
    background_headline = "案例背景"
    flow_title = "协同判断主线"
    lane_a_title = "问题确认 / 甲方侧"
    lane_b_title = "攻防推进 / 攻击队"
    result_title = "管理判断"
    result_headline = "结果可信"
    image_title = "代表证据 / 关键样例"
    client_title = "管理收束 / 下一步"
    value_band = "当前结论已具备可信基础"
    background = ctx.page_intent or ctx.proof_goal or ctx.core_judgment
    solution = ctx.proof_goal or ctx.page_intent or ctx.core_judgment
    process = action_text or closure_points[0]
    results = ctx.core_judgment or ctx.proof_goal
    case_image = evidence_summary
    case_client = "；".join(closure_points[:2])

    if any(token in ctx.page_title for token in ("整体回顾", "项目范围")):
        background_title = "范围与代表性"
        background_headline = "本轮基础"
        flow_title = "范围确认与结果归集"
        lane_a_title = "范围确认 / 甲方侧"
        lane_b_title = "结果归集 / 攻击队"
        result_title = "可信结果"
        result_headline = "真实攻防基础已建立"
        image_title = "范围代表性证据"
        client_title = "进入成果与风险判断"
        value_band = "范围与结果基础已建立"
        background = "本轮演练覆盖核心对象、时间窗口与关键场景，具备代表性。"
        solution = "确认演练对象、边界与周期，统一成果口径。"
        process = "归并外网突破、服务器权限与敏感信息等关键结果。"
        results = "ThinkPHP RCE、Log4j2 RCE 与 Nacos 后台权限已共同证明结论来自真实攻防。"
        case_image = evidence_summary or "ThinkPHP / Log4j2 / Nacos 证据"
        case_client = "本轮范围具备代表性，可直接进入关键成果与风险结构判断。"
    elif any(token in ctx.page_title for token in ("社工", "钓鱼")):
        background_title = "人员侧入口"
        background_headline = "触达证据"
        flow_title = "社工路径协同主线"
        lane_a_title = "攻击侧协同 / 触达诱导"
        lane_b_title = "员工侧联动 / 求证处置"
        result_title = "结果证明"
        result_headline = "社工命中结果已被验证"
        image_title = "截图证据 / 命中样例"
        client_title = "协同收口 / 复测动作"
        value_band = "人员侧入口与协同断点已被验证"
        background = "采招、客服与 HR 三类角色已被社工路径触达，人员侧入口真实存在。"
        solution = "攻击侧通过在线客服、微信添加和问题材料分阶段诱导，完成触达与转化。"
        process = "员工侧缺少身份核验、异常上报与协同联动，使社工路径可与系统侧链路叠加。"
        results = "客服平台、采招与 HR 命中结果已证明人员侧风险会放大整体攻击成功率。"
        case_image = "客服平台截图 / 微信添加记录 / 角色命中结果"
        case_client = "社工路径与系统侧叠加，整体风险会被放大。"

    return {
        "CASE_BACKGROUND": shorten(background, 72),
        "CASE_SOLUTION": shorten(solution, 78),
        "CASE_PROCESS": shorten(process, 78),
        "CASE_RESULTS": shorten(results, 84),
        "CASE_IMAGE": shorten(case_image, 40),
        "CASE_CLIENT": shorten(case_client, 80),
        "CASE_BACKGROUND_TITLE": compact_security_label(background_title, 12, compact_level),
        "CASE_BACKGROUND_HEADLINE": compact_security_label(background_headline, 14, compact_level),
        "CASE_FLOW_TITLE": compact_security_label(flow_title, 20, compact_level),
        "CASE_LANE_A_TITLE": compact_security_label(lane_a_title, 18, compact_level),
        "CASE_LANE_B_TITLE": compact_security_label(lane_b_title, 18, compact_level),
        "CASE_RESULT_TITLE": compact_security_label(result_title, 14, compact_level),
        "CASE_RESULT_HEADLINE": compact_security_label(result_headline, 16, compact_level),
        "CASE_IMAGE_TITLE": compact_security_label(image_title, 18, compact_level),
        "CASE_CLIENT_TITLE": compact_security_label(client_title, 18, compact_level),
        "CASE_VALUE_BAND": compact_security_label(value_band, 18, compact_level),
    }


def build_timeline_slots(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    compact_level = min(2, tuning.compact_standard)
    if "整改" in ctx.page_title or "路线图" in ctx.page_title or "推进计划" in ctx.page_title:
        nodes = [
            ("风险确认", "确认高危主链"),
            ("紧急止血", "先封堵外网入口"),
            ("关键修复", "治理凭证与管理面"),
            ("监测补强", "补齐审计与告警"),
            ("复测闭环", "验证整改效果"),
        ]
        return {
            "TIME_NODE_1": nodes[0][0],
            "TIME_DESC_1": nodes[0][1],
            "TIME_NODE_2": nodes[1][0],
            "TIME_DESC_2": nodes[1][1],
            "TIME_NODE_3": nodes[2][0],
            "TIME_DESC_3": nodes[2][1],
            "TIME_NODE_4": nodes[3][0],
            "TIME_DESC_4": nodes[3][1],
            "TIME_NODE_5": nodes[4][0],
            "TIME_DESC_5": nodes[4][1],
            "TIME_SUMMARY_TITLE": "整改推进总原则",
            "TIME_SUMMARY_CONTENT": compact_security_sentence(
                "先压高风险入口，再做监测补强，最后复测闭环。",
                34,
                compact_level,
            ),
        }

    points = semantic_points_with_fallback(ctx, limit=5)
    while len(points) < 5:
        points.append(ctx.core_judgment or "阶段推进")
    return {
        "TIME_NODE_1": "阶段 1",
        "TIME_DESC_1": compact_security_sentence(points[0], 10, compact_level),
        "TIME_NODE_2": "阶段 2",
        "TIME_DESC_2": compact_security_sentence(points[1], 10, compact_level),
        "TIME_NODE_3": "阶段 3",
        "TIME_DESC_3": compact_security_sentence(points[2], 10, compact_level),
        "TIME_NODE_4": "阶段 4",
        "TIME_DESC_4": compact_security_sentence(points[3], 10, compact_level),
        "TIME_NODE_5": "阶段 5",
        "TIME_DESC_5": compact_security_sentence(points[4], 10, compact_level),
        "TIME_SUMMARY_TITLE": compact_security_label(ctx.page_title, 12, compact_level),
        "TIME_SUMMARY_CONTENT": compact_security_sentence(ctx.core_judgment, 34, compact_level),
    }


def build_matrix_rows(ctx: PageContext) -> list[list[str]]:
    domains = derive_security_domains(ctx)
    rows: list[list[str]] = []
    priorities = ["P1", "P1", "P2", "P2"]
    for idx, domain in enumerate(domains):
        rows.append(
            [
                priorities[idx],
                domain,
                shorten(f"{domain} 仍存在高风险暴露", 14),
                shorten(f"优先收敛 {domain} 关键控制点", 16),
                shorten("复测确认链路不再可贯通", 16),
            ]
        )
    return rows


def apply_data_page_argument_overrides(
    ctx: PageContext,
    tuning: RenderTuning,
    values: dict[str, str],
) -> dict[str, str]:
    if tuning.semantic_argument <= 0:
        return values

    preserve_specialized_data_page = any(
        token in ctx.page_title
        for token in (
            "项目范围",
            "整体回顾",
            "重要成果",
            "关键结果",
            "攻击链总览",
            "整体攻击路径分析",
            "社工",
            "钓鱼",
            "结果归因",
            "内网突破",
        )
    )
    closure_level = max(tuning.semantic_argument, tuning.semantic_closure)
    argument_titles = derive_argument_titles(
        ctx,
        [
            values.get("PROOF_NODE_1", "现状锚点"),
            values.get("PROOF_CANVAS", "结构判断"),
            values.get("PROOF_NODE_3", "整改动作"),
        ],
        limit=3,
        level=tuning.semantic_argument,
    )
    closure_points = closure_messages(ctx, limit=3, repair_level=closure_level)
    while len(argument_titles) < 3:
        argument_titles.append(f"论点 {len(argument_titles) + 1}")

    if preserve_specialized_data_page:
        values["PROOF_HEADLINE"] = compact_security_sentence(
            values.get("PROOF_HEADLINE", semantic_headline_text(ctx, limit=28, level=max(1, tuning.semantic_headline))),
            30,
            min(2, tuning.semantic_argument),
        )
        values["PROOF_NODE_1"] = compact_security_label(values.get("PROOF_NODE_1", argument_titles[0]), 12, tuning.semantic_argument)
        values["PROOF_CANVAS"] = compact_security_label(values.get("PROOF_CANVAS", argument_titles[1]), 18, tuning.semantic_argument)
        values["PROOF_NODE_3"] = compact_security_label(values.get("PROOF_NODE_3", argument_titles[2]), 12, tuning.semantic_argument)
    else:
        values["PROOF_HEADLINE"] = compact_security_sentence(
            semantic_headline_text(ctx, limit=22, level=max(1, tuning.semantic_headline)),
            22,
            min(2, tuning.semantic_argument),
        )
        values["PROOF_NODE_1"] = compact_security_label(argument_titles[0], 12, tuning.semantic_argument)
        values["PROOF_CANVAS"] = compact_security_label(argument_titles[1], 16, tuning.semantic_argument)
        values["PROOF_NODE_3"] = compact_security_label(argument_titles[2], 12, tuning.semantic_argument)
    relation1_source = values.get("PROOF_RELATION_1", "先确认当前主问题")
    if not preserve_specialized_data_page:
        relation1_source = ctx.proof_goal or relation1_source
    values["PROOF_RELATION_1"] = compact_security_sentence(relation1_source, 14, min(2, tuning.semantic_argument))
    relation2_source = values.get("PROOF_RELATION_2", "再推进到下一步动作")
    if not preserve_specialized_data_page:
        relation2_source = ctx.next_relation or page_action_text(ctx) or relation2_source
    values["PROOF_RELATION_2"] = compact_security_sentence(
        relation2_source,
        14,
        min(2, tuning.semantic_argument),
    )
    values["DATA_NOTE_2"] = compact_security_sentence(ctx.core_judgment or values.get("DATA_NOTE_2", ""), 24, min(2, tuning.semantic_argument))
    if preserve_specialized_data_page:
        values["DATA_NOTE_3"] = compact_security_sentence(values.get("DATA_NOTE_3", closure_points[0]), 24, min(2, closure_level))
    else:
        values["DATA_NOTE_3"] = compact_security_sentence(closure_points[0], 24, min(2, closure_level))
    if preserve_specialized_data_page:
        values["PROOF_SUMMARY_1"] = compact_security_sentence(values.get("PROOF_SUMMARY_1", argument_titles[0]), 16, min(2, tuning.semantic_argument))
        values["PROOF_SUMMARY_2"] = compact_security_sentence(values.get("PROOF_SUMMARY_2", argument_titles[1]), 16, min(2, tuning.semantic_argument))
        values["PROOF_SUMMARY_3"] = compact_security_sentence(values.get("PROOF_SUMMARY_3", closure_points[0]), 18, min(2, closure_level))
    else:
        values["PROOF_SUMMARY_1"] = compact_security_sentence(argument_titles[0], 14, min(2, tuning.semantic_argument))
        values["PROOF_SUMMARY_2"] = compact_security_sentence(argument_titles[1], 14, min(2, tuning.semantic_argument))
        values["PROOF_SUMMARY_3"] = compact_security_sentence(closure_points[0], 16, min(2, closure_level))
    return values


def resolve_progression_variant(ctx: PageContext) -> tuple[str, str, str] | None:
    pattern = normalize_pattern_token(ctx.page.get("advanced_pattern") or "")
    template_name = Path(str(ctx.page.get("preferred_template") or ctx.template_path.name)).name
    track_type = attack_track_type(ctx.page_title)

    mapped = PROGRESSION_PATTERN_ALTERNATIVES.get((pattern, template_name))
    if mapped:
        return mapped

    if template_name == "16_table.svg":
        return (
            "matrix_defense_map",
            "12_grid.svg",
            "把连续表格矩阵页切换为网格结构页，避免相邻正文重复同构",
        )
    if template_name == "12_grid.svg":
        return (
            "governance_control_matrix",
            "16_table.svg",
            "把连续网格页切换为治理动作矩阵页，拉开相邻复杂页形态差异",
        )
    if template_name == "07_data.svg":
        next_template = "05_case.svg" if track_type == "social" else "19_result_leading_case.svg"
        return (
            "evidence_attached_case_chain",
            next_template,
            "把连续摘要证明页切换为案例链页，形成更明确的推进关系",
        )
    if template_name == "09_comparison.svg":
        return (
            "evidence_attached_case_chain",
            "19_result_leading_case.svg",
            "把连续泳道页切换为案例链页，避免连续推进页重复",
        )
    return None


def should_reframe_for_adjacent_progression(ctx: PageContext) -> bool:
    slide_num = int(ctx.page.get("page_num", 0) or 0)
    if slide_num <= 1:
        return False
    try:
        state, _ = load_or_init_state(ctx.project_dir)
        state = sync_state_with_files(state, ctx.project_dir)
    except Exception:
        return False

    previous_page = None
    for item in state.get("pages", []):
        try:
            page_num = int(item.get("page_num", 0) or 0)
        except (TypeError, ValueError):
            continue
        if page_num == slide_num - 1:
            previous_page = item
            break
    if not previous_page or not is_complex_page(previous_page):
        return False

    current_pattern = normalize_pattern_token(ctx.page.get("advanced_pattern") or "")
    previous_pattern = normalize_pattern_token(previous_page.get("advanced_pattern") or "")
    current_template = Path(str(ctx.page.get("preferred_template") or ctx.template_path.name)).name
    previous_template = Path(str(previous_page.get("preferred_template") or "")).name

    return bool(current_pattern and current_pattern == previous_pattern and current_template == previous_template)


def apply_adjacent_progression_reframe(ctx: PageContext) -> list[str]:
    slide_num = int(ctx.page.get("page_num", 0) or 0)
    if slide_num <= 0:
        return []
    if not should_reframe_for_adjacent_progression(ctx):
        return []

    variant = resolve_progression_variant(ctx)
    if not variant:
        return []
    new_pattern, new_template, reason = variant
    previous_pattern = str(ctx.page.get("advanced_pattern") or "").strip().strip("`")
    previous_template = Path(str(ctx.page.get("preferred_template") or ctx.template_path.name)).name

    changed = False
    try:
        next_template_path = resolve_template_path(ctx.template_id, new_template)
    except FileNotFoundError:
        return []

    if previous_pattern != new_pattern:
        ctx.page["advanced_pattern"] = new_pattern
        changed = True
    if previous_template != new_template:
        ctx.page["preferred_template"] = new_template
        changed = True
    if not changed:
        return []

    patch_design_spec_page_fields(
        ctx.project_dir,
        slide_num,
        advanced_pattern=new_pattern,
        preferred_template=new_template,
    )
    synced = sync_reframed_execution_artifacts(
        ctx,
        slide_num=slide_num,
        advanced_pattern=new_pattern,
        preferred_template=new_template,
        previous_pattern=previous_pattern,
        previous_template=previous_template,
    )
    append_execution_event(
        ctx,
        "progression_reframe",
        slide_num=slide_num,
        reason=reason,
        from_pattern=previous_pattern or "无",
        to_pattern=new_pattern,
        from_template=previous_template or ctx.template_path.name,
        to_template=new_template,
        synced_artifacts=synced,
    )
    ctx.template_path = next_template_path
    ctx.template_text = sync_template_assets(
        read_text(ctx.template_path),
        ctx.template_path,
        ctx.project_dir,
        ctx.template_id,
    )
    ctx.page["page_family"] = "complex"
    if synced:
        return [
            reason,
            f"同步更新当前页规划为 `{new_pattern}` / `{new_template}`",
            f"同步刷新产物：{', '.join(synced)}",
        ]
    return [reason, f"同步更新当前页规划为 `{new_pattern}` / `{new_template}`"]


def apply_template_reframe(
    ctx: PageContext,
    *,
    new_template: str,
    reason: str,
    issue_code: str,
) -> list[str]:
    slide_num = int(ctx.page.get("page_num", 0) or 0)
    previous_pattern = str(ctx.page.get("advanced_pattern") or "").strip().strip("`")
    previous_template = Path(str(ctx.page.get("preferred_template") or ctx.template_path.name)).name
    if not slide_num or previous_template == new_template:
        return []
    try:
        next_template_path = resolve_template_path(ctx.template_id, new_template)
    except FileNotFoundError:
        return []

    ctx.page["preferred_template"] = new_template
    patch_design_spec_page_fields(
        ctx.project_dir,
        slide_num,
        advanced_pattern=previous_pattern,
        preferred_template=new_template,
    )
    synced = sync_reframed_execution_artifacts(
        ctx,
        slide_num=slide_num,
        advanced_pattern=previous_pattern,
        preferred_template=new_template,
        previous_pattern=previous_pattern,
        previous_template=previous_template,
    )
    append_execution_event(
        ctx,
        "progression_reframe",
        slide_num=slide_num,
        reason=reason,
        issue_code=issue_code,
        from_pattern=previous_pattern or "无",
        to_pattern=previous_pattern or "无",
        from_template=previous_template or ctx.template_path.name,
        to_template=new_template,
        synced_artifacts=synced,
    )
    ctx.template_path = next_template_path
    ctx.template_text = sync_template_assets(
        read_text(ctx.template_path),
        ctx.template_path,
        ctx.project_dir,
        ctx.template_id,
    )
    if synced:
        return [
            reason,
            f"同步改用 `{new_template}` 重新承载当前页",
            f"同步刷新产物：{', '.join(synced)}",
        ]
    return [reason, f"同步改用 `{new_template}` 重新承载当前页"]


def build_grid_slots(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    points = semantic_points_with_fallback(ctx, limit=6)
    while len(points) < 6:
        points.append(ctx.core_judgment or ctx.page_intent or ctx.page_title)
    title_limit = 16 if tuning.compact_matrix == 0 else 12
    desc_limit = 18 if tuning.compact_matrix == 0 else 12
    summary_limit = 24 if tuning.compact_matrix == 0 else 16
    titles = [
        "外网暴露面",
        "内网扩散面",
        "人员侧风险",
        "直接证据",
        "治理优先级",
        "整改闭环",
    ]
    if "重要成果" in ctx.page_title or "关键结果" in ctx.page_title:
        titles = [
            "外网结果",
            "内网结果",
            "人员命中",
            "权限证明",
            "影响结果",
            "复测动作",
        ]
    elif "关键证据总览" in ctx.page_title or "证据证明" in ctx.page_title:
        titles = [
            "外网证据",
            "内网证据",
            "人员证据",
            "控制结果",
            "关键截图",
            "后续动作",
        ]
    elif "风险总览" in ctx.page_title:
        titles = [
            "互联网侧",
            "内网侧",
            "人员侧",
            "控制薄弱域",
            "治理优先级",
            "闭环要求",
        ]
    if tuning.semantic_argument > 0:
        titles = derive_argument_titles(ctx, titles, limit=6, level=tuning.semantic_argument)
    values = {}
    for idx, title in enumerate(titles, start=1):
        label_level = max(tuning.compact_matrix, tuning.semantic_argument)
        values[f"GRID_CARD_{idx}"] = compact_security_label(title, title_limit, label_level)
        values[f"GRID_DESC_{idx}"] = compact_evidence_sentence(points[idx - 1], desc_limit, label_level)
    summary_text = ctx.core_judgment or ctx.proof_goal or ctx.goal
    if "重要成果" in ctx.page_title or "关键结果" in ctx.page_title:
        summary_text = "外网突破、内网横向和人员受骗等结果已构成高风险判断，立即整改复测。"
    elif "关键证据总览" in ctx.page_title or "证据证明" in ctx.page_title:
        summary_text = "关键证据已足以支撑关键路径与结果判断，应直接进入问题归因与整改排序。"
    elif "风险总览" in ctx.page_title:
        summary_limit = 28 if tuning.compact_matrix == 0 else 24
        summary_text = "应按结果影响而不是按条目数量排序（优先）。"
    summary_level = max(tuning.compact_matrix, tuning.semantic_argument)
    values["GRID_SUMMARY"] = compact_security_sentence(summary_text, summary_limit, summary_level)
    return values


def build_product_tree_slots(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    points = semantic_points_with_fallback(ctx, limit=6)
    compact_level = tuning.compact_service_map
    feature_limit = 10 if compact_level == 0 else 8
    feature_defaults = [
        "互联网暴露",
        "内网审计弱",
        "凭证治理弱",
        "权限复用",
        "人员意识弱",
        "闭环动作缺",
    ]
    product_name = compact_security_label(strip_display_prefix(ctx.page_title), 16 if compact_level == 0 else 12, compact_level)
    product_tagline = compact_security_label("根因结构已成型", 10 if compact_level == 0 else 8, compact_level)
    product_value = compact_security_sentence("根因不是单点漏洞，而是多域控制同时偏弱。", 18 if compact_level == 0 else 14, compact_level)
    product_image = compact_security_sentence("证据与根因在此归集", 12 if compact_level == 0 else 10, compact_level)

    if "风险结构总览" in ctx.page_title:
        feature_defaults = [
            "互联网暴露面",
            "内网审计不足",
            "凭证治理薄弱",
            "权限复用扩散",
            "人员意识不足",
            "整改闭环缺口",
        ]
        points = feature_defaults[:6]
        product_name = compact_security_label("四类控制薄弱域共同构成主要根因", 20 if compact_level == 0 else 16, compact_level)
        product_tagline = compact_security_label("主要根因结构树", 10 if compact_level == 0 else 8, compact_level)
        product_value = compact_security_sentence("真正需要治理的是互联网暴露、审计不足、凭证薄弱与人员意识缺口的叠加。", 26 if compact_level == 0 else 20, compact_level)
        product_image = compact_security_sentence("四类根因与代表证据在此归集", 16 if compact_level == 0 else 12, compact_level)
    elif "互联网侧" in ctx.page_title:
        feature_defaults = ["未授权暴露", "远程执行口", "弱口令入口", "持续检测缺失", "及时修补滞后", "高危入口持续"]
        while len(points) < 6:
            points.append(feature_defaults[len(points)])
        points = feature_defaults[:6]
        product_name = compact_security_label("检测缺失使高危入口持续存在", 18 if compact_level == 0 else 14, compact_level)
        product_tagline = compact_security_label("外网入口根因树", 10 if compact_level == 0 else 8, compact_level)
        product_value = compact_security_sentence("优先收口高危入口并补齐持续检测复测。", 18 if compact_level == 0 else 14, compact_level)
        product_image = compact_security_sentence("外网证据与入口结果在此归集", 14 if compact_level == 0 else 11, compact_level)
    elif "审计" in ctx.page_title:
        feature_defaults = ["异常登录弱", "横移感知弱", "留痕缺失", "告警迟滞", "日志分散", "复盘困难"]
        while len(points) < 6:
            points.append(feature_defaults[len(points)])
        points = feature_defaults[:6]
        product_name = compact_security_label("审计缺失使异常登录持续失察", 18 if compact_level == 0 else 14, compact_level)
        product_tagline = compact_security_label("审计缺失根因树", 10 if compact_level == 0 else 8, compact_level)
        product_value = compact_security_sentence("应补齐审计留痕、关联告警与复测验证。", 20 if compact_level == 0 else 16, compact_level)
        product_image = compact_security_sentence("审计证据与异常行为在此归集", 14 if compact_level == 0 else 11, compact_level)
    elif any(token in ctx.page_title for token in ("通用口令", "通用密码")):
        feature_defaults = [
            "通用口令持续存活",
            "弱密码复用扩散",
            "权限复用继续放大",
            "高危资产反复暴露",
            "治理动作存在断点",
            "复测收口仍不足",
        ]
        while len(points) < 6:
            points.append(feature_defaults[len(points)])
        points = feature_defaults[:6]
        product_name = compact_security_label("口令复用放大多点扩散", 18 if compact_level == 0 else 14, compact_level)
        product_tagline = compact_security_label("凭证治理根因树", 10 if compact_level == 0 else 8, compact_level)
        product_value = compact_security_sentence("先收口通用口令与权限复用。", 16 if compact_level == 0 else 12, compact_level)
        product_image = compact_security_sentence("口令复用证据归集", 12 if compact_level == 0 else 10, compact_level)
    elif "安全意识" in ctx.page_title:
        feature_defaults = ["钓鱼触达", "意识薄弱", "验证不足", "账号转化", "培训缺口", "闭环不足"]
        while len(points) < 6:
            points.append(feature_defaults[len(points)])
        points = feature_defaults[:6]
        product_name = compact_security_label("意识薄弱使社工入口持续可用", 18 if compact_level == 0 else 14, compact_level)
        product_tagline = compact_security_label("人员入口根因树", 10 if compact_level == 0 else 8, compact_level)
        product_value = compact_security_sentence("应同步补强意识宣导、验证机制与复测抽检。", 20 if compact_level == 0 else 16, compact_level)
        product_image = compact_security_sentence("人员侧证据与转化结果在此归集", 14 if compact_level == 0 else 11, compact_level)
    else:
        while len(points) < 6:
            points.append(feature_defaults[len(points)])
    return {
        "PRODUCT_NAME": product_name,
        "PRODUCT_TAGLINE": product_tagline,
        "PRODUCT_FEATURE_1": compact_security_label(points[0], feature_limit, compact_level),
        "PRODUCT_FEATURE_2": compact_security_label(points[1], feature_limit, compact_level),
        "PRODUCT_FEATURE_3": compact_security_label(points[2], feature_limit, compact_level),
        "PRODUCT_FEATURE_4": compact_security_label(points[3], feature_limit, compact_level),
        "PRODUCT_FEATURE_5": compact_security_label(points[4], feature_limit, compact_level),
        "PRODUCT_FEATURE_6": compact_security_label(points[5], feature_limit, compact_level),
        "PRODUCT_IMAGE": product_image,
        "PRODUCT_VALUE": product_value,
    }


def build_domain_capability_slots(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    points = semantic_points_with_fallback(ctx, limit=7)
    compact_level = tuning.compact_service_map
    title_limit = 14 if compact_level == 0 else 10
    desc_limit = 12 if compact_level == 0 else 10
    domain_label = compact_security_label(strip_display_prefix(ctx.page_title), 14 if compact_level == 0 else 10, compact_level)
    capability_titles = [
        "识别定级",
        "压降高危",
        "复测验证",
        "持续优化",
    ]
    capability_descs: list[str] | None = None
    outcome_title = "结果输出"

    if "风险结构总览" in ctx.page_title:
        domain_label = "风险结构总览"
        scene_title = "问题输入"
        scene_points = [
            "互联网侧高危入口持续暴露",
            "内网异常登录与审计失察并存",
            "凭证复用与人员侧入口同时存在",
        ]
        capability_titles = [
            "互联网暴露形成初始入口",
            "审计不足放大横向失察",
            "凭证治理薄弱放大权限复用",
            "人员意识不足保留社工入口",
        ]
        capability_descs = [
            "未授权、远程执行与弱口令入口可直达",
            "异常登录未告警，横向行为难发现",
            "通用口令与通用密码放大资产扩散",
            "钓鱼触达与验证薄弱并存",
        ]
        outcome_title = "结构判断"
        outcome_points = [
            "问题已归并到四个薄弱域",
            "共同指向结构性根因",
            "整改按入口、放大链路与结果影响排序",
        ]
        method_note = "应按四类薄弱域排序整改，并复测高风险链路。"
    elif "审计问题" in ctx.page_title:
        domain_label = "审计放大机制"
        scene_title = "问题输入"
        scene_points = [
            "异常登录未形成有效留痕与告警",
            "高危管理端口暴露且限源不足",
            "横向行为与驻留过程难被及时发现",
        ]
        capability_titles = [
            "异常登录审计缺失",
            "高危端口限源不足",
            "日志告警联动薄弱",
            "驻留扩散条件持续存在",
        ]
        capability_descs = [
            "敏感系统登录与失败操作未被稳定记录",
            "管理面暴露让攻击者更易反复尝试",
            "异常行为难被串联识别并及时拦截",
            "驻留与横向放大缺少有效发现节点",
        ]
        outcome_title = "管理判断"
        outcome_points = [
            "攻击者更容易保持驻留",
            "横向移动与异常操作更难及时发现",
            "应先补审计留痕，再收口高危端口并复测",
        ]
        method_note = "先补异常登录审计，再收口高危端口并复测。"
    elif "安全意识" in ctx.page_title:
        domain_label = "人员侧放大机制"
        scene_title = "问题输入"
        scene_points = [
            "采招、客服与 HR 角色均被社工触达",
            "在线客服与微信添加成为主要诱导路径",
            "人员识别与响应动作明显不足",
        ]
        capability_titles = [
            "社工触达路径持续可用",
            "身份求证与验证动作不足",
            "终端与账号响应处置偏慢",
            "系统治理效果被持续稀释",
        ]
        capability_descs = [
            "客服平台与沟通场景提供稳定诱导入口",
            "员工缺少多一步核验与上报动作",
            "受害终端与账号处置未能及时跟进",
            "人员侧薄弱会反复抵消系统侧治理收益",
        ]
        outcome_title = "管理判断"
        outcome_points = [
            "社工路径仍能稳定命中关键角色",
            "人员侧问题会持续放大整体攻击成功率",
            "应同步补强识别培训、求证机制与抽检复测",
        ]
        method_note = "先提升人员识别与响应能力，再做求证抽检复测。"
    elif any(token in ctx.page_title for token in ("互联网侧系统安全检测与防护待加强", "检测与防护待加强")):
        domain_label = "互联网暴露放大机制"
        scene_title = "入口持续存在"
        scene_points = [
            "未授权、远程执行与弱口令入口仍可被外部直接尝试",
            "持续检测、暴露面梳理与修补动作未形成稳定节奏",
            "高危入口被发现后缺少快速封堵与复测回看",
        ]
        capability_titles = [
            "持续检测无法稳定发现高危入口",
            "补丁修复与限源动作推进滞后",
            "高危暴露面缺少闭环验证",
            "入口问题会持续成为首层风险",
        ]
        capability_descs = [
            "外部暴露面依旧存在可直接利用的未授权、远程执行与弱口令问题",
            "发现问题后未能快速修补、限源或下线高危服务",
            "整改后缺少复测，导致入口问题容易反复出现",
            "因此互联网侧应始终放在首层高优先级进行治理",
        ]
        outcome_title = "管理判断"
        outcome_points = [
            "高危入口会持续提供初始进入机会",
            "互联网侧问题应先于后续放大条件处理",
            "先补持续检测与修补节奏，再收口暴露面并复测",
        ]
        method_note = "先补持续检测与补丁修复，再收口互联网暴露面并复测。"
    elif "整改复测机制" in ctx.page_title:
        domain_label = "整改闭环机制"
        scene_title = "闭环不是单次整改"
        scene_points = [
            "问题责任必须落到系统和责任人",
            "整改动作要持续跟踪直到高危入口失效",
            "复测和回看结果必须回流到优化动作",
        ]
        capability_titles = [
            "责任到人",
            "动作落地",
            "复测验证",
            "回看优化",
        ]
        capability_descs = [
            "明确责任系统、责任人和完成标准，避免问题悬空",
            "围绕高危入口与放大链路推进整改，不做一次性处理",
            "以复测结果确认风险真正失效，而不是只看动作完成",
            "把结果回流到制度、规则和持续运营，避免问题反复出现",
        ]
        outcome_title = "管理判断"
        outcome_points = [
            "责任、动作和复测要形成联动闭环",
            "整改完成必须以复测和回看结果为准",
            "缺任一环节风险都可能重复暴露",
        ]
        method_note = "把责任、动作、复测、回看持续运转，才能避免风险重复暴露。"
    elif "长亭安服价值" in ctx.page_title:
        scene_title = "安服价值落点"
        scene_points = ["问题可解释", "动作可排序", "闭环可验证"]
        outcome_points = ["让结论更可信", "让整改更可执行", "让价值更可感知"]
        method_note = "把复杂风险翻译成可验证、可排序、可闭环动作。"
    else:
        while len(points) < 7:
            points.append("关键动作")
        scene_title = "核心场景"
        scene_points = [points[0], points[1], points[2]]
        outcome_points = [points[4], points[5], ctx.core_judgment or points[6]]
        method_note = page_action_text(ctx) or ctx.goal or "按识别-处置-验证-回看推进闭环。"
    if capability_descs is None:
        capability_descs = [
            scene_points[0],
            scene_points[1],
            scene_points[2],
            "形成持续治理",
        ]
    return {
        "DOMAIN_LABEL": domain_label,
        "SCENE_TITLE": compact_security_label(scene_title, 10 if compact_level == 0 else 8, compact_level),
        "SCENE_POINT_1": compact_security_sentence(scene_points[0], desc_limit, compact_level),
        "SCENE_POINT_2": compact_security_sentence(scene_points[1], desc_limit, compact_level),
        "SCENE_POINT_3": compact_security_sentence(scene_points[2], desc_limit, compact_level),
        "CAPABILITY_1_TITLE": compact_security_label(capability_titles[0], title_limit + 4 if "风险结构总览" in ctx.page_title else title_limit, compact_level),
        "CAPABILITY_1_DESC": compact_security_sentence(capability_descs[0], desc_limit + (2 if "风险结构总览" in ctx.page_title else 0), compact_level),
        "CAPABILITY_2_TITLE": compact_security_label(capability_titles[1], title_limit + 4 if "风险结构总览" in ctx.page_title else title_limit, compact_level),
        "CAPABILITY_2_DESC": compact_security_sentence(capability_descs[1], desc_limit + (2 if "风险结构总览" in ctx.page_title else 0), compact_level),
        "CAPABILITY_3_TITLE": compact_security_label(capability_titles[2], title_limit + 4 if "风险结构总览" in ctx.page_title else title_limit, compact_level),
        "CAPABILITY_3_DESC": compact_security_sentence(capability_descs[2], desc_limit + (2 if "风险结构总览" in ctx.page_title else 0), compact_level),
        "CAPABILITY_4_TITLE": compact_security_label(capability_titles[3], title_limit + 4 if "风险结构总览" in ctx.page_title else title_limit, compact_level),
        "CAPABILITY_4_DESC": compact_security_sentence(capability_descs[3], desc_limit + (2 if "风险结构总览" in ctx.page_title else 0), compact_level),
        "OUTCOME_TITLE": compact_security_label(outcome_title, 12 if compact_level == 0 else 10, compact_level),
        "OUTCOME_1": compact_security_sentence(outcome_points[0], desc_limit, compact_level),
        "OUTCOME_2": compact_security_sentence(outcome_points[1], desc_limit, compact_level),
        "OUTCOME_3": compact_security_sentence(outcome_points[2], desc_limit, compact_level),
        "METHOD_NOTE": compact_security_sentence(
            method_note,
            30 if "风险结构总览" in ctx.page_title and compact_level == 0 else (24 if compact_level == 0 else 18),
            compact_level,
        ),
    }


def build_comparison_slots(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    compact_level = min(2, max(tuning.compact_attack_chain, tuning.semantic_argument))
    evidence_points = semantic_points_with_fallback(ctx, limit=6)
    track_type = attack_track_type(ctx.page_title)
    labels = [derive_example_label(point, f"路径 {idx}") for idx, point in enumerate(evidence_points[:2], start=1)]
    while len(labels) < 2:
        fallback = {
            "internet": "入口链",
            "internal": "管理面链",
            "social": "钓鱼链",
            "overview": "代表路径",
        }.get(track_type, "代表路径")
        labels.append(fallback if len(labels) == 0 else "放大链")
    preserve_specific_labels = track_type in {"internet", "internal", "social"}
    if tuning.semantic_argument > 0 and not preserve_specific_labels:
        labels = derive_argument_titles(ctx, labels, limit=2, level=tuning.semantic_argument)
        while len(labels) < 2:
            labels.append("代表路径" if len(labels) == 0 else "关键放大点")

    if track_type == "internet":
        labels = [labels[0], "外网入口"]
        lane_a = [labels[0], "命令执行", "外网落点", "内网延伸"] if tuning.semantic_argument > 0 else [labels[0], "命令执行", "服务器权限", "可继续打内网"]
        lane_b = [labels[1], "远程执行", "第二落点", "持续驻留"] if tuning.semantic_argument > 0 else [labels[1], "远程执行", "形成第二落点", "老组件即入口"]
        result = "互联网侧暴露面与高危漏洞组合，已形成稳定初始进入能力；应优先收口并复测。"
    elif track_type == "internal":
        lane_a = [labels[0], "办公网落点", "管理面放大", "关键环境触达"] if tuning.semantic_argument > 0 else [labels[0], "后台接管", "横向扩展", "可触达关键环境"]
        lane_b = [labels[1], "情报扩展", "凭证复用", "云侧结果"] if tuning.semantic_argument > 0 else [labels[1], "权限复用", "扩大控制域", "影响范围继续放大"]
        result = "管理面与凭证问题已形成持续放大能力；应优先切断管理面和横向链路。"
    elif track_type == "social":
        lane_a = [labels[0], "邮件触达", "终端上线", "形成内网入口"] if tuning.semantic_argument > 0 else [labels[0], "钓鱼触达", "凭证获取", "形成内部入口"]
        lane_b = [labels[1], "链接点击", "账号转化", "后台延伸"] if tuning.semantic_argument > 0 else [labels[1], "链接点击", "账号接管", "成功率继续放大"]
        result = "社工链路可与系统侧路径叠加；应同步补强意识与验证机制。"
    else:
        lane_a = ["互联网入口", "远程执行", "外网落点", "结果已出现"]
        lane_b = ["内网/人员侧", "权限放大", "横向扩展", "关键资产触达"]
        result = "多条入口已汇聚相似控制结果；应按主链路优先推进整改。"

    lane_limit = 14 if compact_level == 0 else 12
    result_limit = 44 if tuning.compact_attack_chain == 0 else 36
    return {
        "COMPARE_HEADLINE": compact_security_sentence(
            semantic_headline_text(ctx, limit=30, level=max(1, tuning.semantic_headline))
            if tuning.semantic_argument > 0
            else (ctx.core_judgment or result),
            30,
            compact_level,
        ),
        "COMPARE_TITLE_A": compact_security_label(labels[0], 10 if compact_level == 0 else 8, compact_level),
        "COMPARE_TITLE_B": compact_security_label(labels[1], 10 if compact_level == 0 else 8, compact_level),
        "COMPARE_CONTENT_A_1": compact_security_sentence(lane_a[0], lane_limit, compact_level),
        "COMPARE_CONTENT_A_2": compact_security_sentence(lane_a[1], lane_limit, compact_level),
        "COMPARE_CONTENT_A_3": compact_security_sentence(lane_a[2], lane_limit, compact_level),
        "COMPARE_CONTENT_A_4": compact_security_sentence(lane_a[3], lane_limit, compact_level),
        "COMPARE_CONTENT_B_1": compact_security_sentence(lane_b[0], lane_limit, compact_level),
        "COMPARE_CONTENT_B_2": compact_security_sentence(lane_b[1], lane_limit, compact_level),
        "COMPARE_CONTENT_B_3": compact_security_sentence(lane_b[2], lane_limit, compact_level),
        "COMPARE_CONTENT_B_4": compact_security_sentence(lane_b[3], lane_limit, compact_level),
        "COMPARE_RESULT": compact_action_result(result, result_limit, compact_level),
    }


def build_security_service_slot_map(ctx: PageContext, template_name: str, tuning: RenderTuning) -> dict[str, str]:
    points = semantic_points_with_fallback(ctx, limit=6)
    if template_name == "05_case.svg":
        return build_case_page_slots(ctx, tuning)

    if template_name == "07_data.svg":
        return build_data_page_slots(ctx, tuning)

    if template_name == "09_comparison.svg":
        return build_comparison_slots(ctx, tuning)

    if template_name == "10_timeline.svg":
        return build_timeline_slots(ctx, tuning)

    if template_name == "12_grid.svg":
        return build_grid_slots(ctx, tuning)

    if template_name == "08_product.svg":
        return build_product_tree_slots(ctx, tuning)

    if template_name == "18_domain_capability_map.svg":
        return build_domain_capability_slots(ctx, tuning)

    if template_name == "17_service_overview.svg":
        values = points + split_points(ctx.page_intent) + split_points(ctx.proof_goal)
        while len(values) < 8:
            values.append(ctx.core_judgment or ctx.goal or ctx.page_title)
        title_limit = 14 if tuning.compact_service_map == 0 else 12
        desc_limit = 36 if tuning.compact_service_map == 0 else 24
        value_limit = 18 if tuning.compact_service_map == 0 else 14
        return {
            "OVERVIEW_LEAD": compact_security_sentence(ctx.core_judgment or ctx.page_intent, 52 if tuning.compact_service_map == 0 else 36, tuning.compact_service_map),
            "PLATFORM_NAME": shorten(ctx.page_title or ctx.goal, 20),
            "PLATFORM_DESC": compact_security_sentence(ctx.proof_goal or ctx.goal, 36 if tuning.compact_service_map == 0 else 24, tuning.compact_service_map),
            "DOMAIN_ATTACK_TITLE": compact_security_label(values[0], title_limit, tuning.compact_service_map),
            "DOMAIN_ATTACK_DESC": compact_security_sentence(values[1], desc_limit, tuning.compact_service_map),
            "DOMAIN_DEFENSE_TITLE": compact_security_label(values[2], title_limit, tuning.compact_service_map),
            "DOMAIN_DEFENSE_DESC": compact_security_sentence(values[3], desc_limit, tuning.compact_service_map),
            "DOMAIN_TRAINING_TITLE": compact_security_label(values[4], title_limit, tuning.compact_service_map),
            "DOMAIN_TRAINING_DESC": compact_security_sentence(values[5], desc_limit, tuning.compact_service_map),
            "VALUE_1": compact_security_label(values[0], value_limit, tuning.compact_service_map),
            "VALUE_2": compact_security_label(values[2], value_limit, tuning.compact_service_map),
            "VALUE_3": compact_security_label(values[4], value_limit, tuning.compact_service_map),
            "DRIVER_TITLE": "本页收束",
            "DRIVER_POINT_1": compact_security_sentence(ctx.goal or ctx.next_relation, 28 if tuning.compact_service_map == 0 else 20, tuning.compact_service_map),
            "DRIVER_POINT_2": compact_security_sentence(page_action_text(ctx) or ctx.next_relation, 28 if tuning.compact_service_map == 0 else 20, tuning.compact_service_map),
        }

    if template_name == "16_table.svg":
        rows = build_matrix_rows(ctx)
        compact_level = max(tuning.compact_matrix, tuning.semantic_argument)
        closure_level = max(tuning.semantic_argument, tuning.semantic_closure)
        closure_points = closure_messages(ctx, limit=3, repair_level=closure_level) if closure_level > 0 else []
        insight_limit = 16 if compact_level == 0 else 12
        row_limits = [14, 14, 14, 16, 16] if compact_level == 0 else [10, 10, 10, 12, 12]
        values: dict[str, str] = {
            "PRIORITY_1": "P1 先压高风险入口",
            "PRIORITY_2": "P2 先做链路收敛",
            "PRIORITY_3": "P3 做闭环复测",
            "TABLE_INSIGHT_1": compact_security_sentence(ctx.core_judgment or ctx.goal, insight_limit, compact_level),
            "TABLE_INSIGHT_2": compact_security_sentence("资源优先投入高放大链路", insight_limit, compact_level),
            "TABLE_INSIGHT_3": compact_security_sentence("以复测结果定义整改完成", insight_limit, compact_level),
            "TABLE_HIGHLIGHT": compact_security_sentence(page_action_text(ctx) or "先聚焦关键域，再推进跨域闭环", 20 if compact_level == 0 else 16, compact_level),
            "CLOSURE_STEP_1": shorten(closure_points[0] if closure_points else "先识别高风险域", 16),
            "CLOSURE_STEP_2": shorten(closure_points[1] if len(closure_points) > 1 else "再压降可放大链路", 16),
            "CLOSURE_STEP_3": shorten(closure_points[2] if len(closure_points) > 2 else "最后复测验证闭环", 16),
        }
        if any(token in ctx.page_title for token in ("异常登陆", "异常登录", "审计问题")):
            values.update({
                "PRIORITY_1": "P1 先补异常登录审计",
                "PRIORITY_2": "P2 收口高危端口暴露",
                "PRIORITY_3": "P3 复测驻留与横向失效",
                "TABLE_INSIGHT_1": compact_security_sentence("异常登录审计缺失与高危端口暴露共同放大驻留风险", insight_limit + 2, compact_level),
                "TABLE_INSIGHT_2": compact_security_sentence("先补登录留痕、限源和告警联动", insight_limit + 2, compact_level),
                "TABLE_INSIGHT_3": compact_security_sentence("以驻留与横向链路失效作为完成标准", insight_limit + 2, compact_level),
                "TABLE_HIGHLIGHT": compact_security_sentence("不是平均治理，而是优先切断驻留放大条件", 22 if compact_level == 0 else 18, compact_level),
                "CLOSURE_STEP_1": "先补异常登录审计",
                "CLOSURE_STEP_2": "再收口高危端口",
                "CLOSURE_STEP_3": "最后复测驻留失效",
            })
        if any(token in ctx.page_title for token in ("治理矩阵", "优先级排序")):
            values.update({
                "PRIORITY_1": "P1 封堵互联网入口",
                "PRIORITY_2": "P2 压降凭证风险",
                "PRIORITY_3": "P3 收口内网放大条件",
                "TABLE_HIGHLIGHT": compact_security_sentence("优先按结果链路而不是平均投入资源", 20 if compact_level == 0 else 16, compact_level),
                "CLOSURE_STEP_1": "先封堵互联网入口",
                "CLOSURE_STEP_2": "再压降凭证风险",
                "CLOSURE_STEP_3": "最后收口内网放大",
            })
        for row_idx, row in enumerate(rows, start=1):
            for col_idx, item in enumerate(row, start=1):
                limit = row_limits[col_idx - 1]
                if col_idx in {2, 3, 4, 5}:
                    values[f"TABLE_ROW_{row_idx}_COL_{col_idx}"] = compact_security_label(item, limit, compact_level)
                else:
                    values[f"TABLE_ROW_{row_idx}_COL_{col_idx}"] = shorten(item, limit)
        return values

    if template_name == "19_result_leading_case.svg":
        semantic_points = semantic_points_with_fallback(ctx, limit=5)
        closure_points = closure_messages(ctx, limit=3, repair_level=tuning.semantic_closure)
        while len(semantic_points) < 3:
            defaults = ["入口确认", "关键利用", "结果证明"]
            semantic_points.append(defaults[len(semantic_points)])
        labels = [derive_example_label(item, item) for item in semantic_points[:3]]
        track_type = attack_track_type(ctx.page_title)
        if track_type == "social":
            actions = ["钓鱼触达", "凭证获取", "账号接管"]
            results = ["内部入口形成", "成功率被放大", "需要立即补强意识与验证"]
        elif track_type == "internal":
            actions = ["管理面接管", "权限复用", "影响继续扩散"]
            results = ["关键环境已受影响", "放大条件已成立", "应优先切断管理面与凭证链"]
        else:
            actions = ["入口确认", "关键利用", "结果核验"]
            results = ["关键结果已出现", "链路证据已闭合", "应按主链优先级推进整改"]
        headline_level = max(tuning.semantic_headline, tuning.semantic_argument)
        proof_subline = normalize_text(ctx.proof_goal or page_action_text(ctx) or closure_points[0])
        if tuning.compact_header_bundle > 0 or headline_level > 0:
            proof_subline = ""
        else:
            proof_subline = semantic_closure_text(ctx, proof_subline, index=0)
            subline_limit = 16 if tuning.compact_header_bundle == 0 else 10
            proof_subline = compact_security_sentence(proof_subline, subline_limit, tuning.compact_header_bundle)
        headline_limit = 34 if tuning.compact_header_bundle == 0 else (24 if tuning.compact_header_bundle == 1 else 18)
        metric_label = "攻击步骤" if tuning.compact_header_bundle == 0 else "步骤"
        result_headline = (
            case_chain_headline_text(ctx, limit=headline_limit, level=headline_level)
            if headline_level > 0
            else compact_security_sentence(ctx.core_judgment or ctx.page_title, headline_limit, tuning.compact_header_bundle)
        )
        return {
            "CLIENT_CONTEXT": compact_security_label(ctx.scenario or ctx.industry or ctx.section_name, 18 if tuning.compact_header_bundle == 0 else 12, tuning.compact_header_bundle),
            "RESULT_HEADLINE": result_headline,
            "HEADLINE_SUBLINE": proof_subline,
            "KEY_METRIC": str(len(semantic_points)),
            "KEY_METRIC_LABEL": metric_label,
            "CHALLENGE_1": compact_security_label(labels[0], 12 if tuning.compact_attack_chain == 0 else 9, tuning.compact_attack_chain),
            "CHALLENGE_2": compact_security_label(labels[1], 12 if tuning.compact_attack_chain == 0 else 9, tuning.compact_attack_chain),
            "CHALLENGE_3": compact_security_label(labels[2], 12 if tuning.compact_attack_chain == 0 else 9, tuning.compact_attack_chain),
            "ACTION_1": compact_security_label(actions[0], 12 if tuning.compact_attack_chain == 0 else 8, tuning.compact_attack_chain),
            "ACTION_2": compact_security_label(actions[1], 12 if tuning.compact_attack_chain == 0 else 8, tuning.compact_attack_chain),
            "ACTION_3": compact_security_label(actions[2], 12 if tuning.compact_attack_chain == 0 else 8, tuning.compact_attack_chain),
            "RESULT_1": compact_security_sentence(results[0], 14 if tuning.compact_attack_chain == 0 else 10, tuning.compact_attack_chain),
            "RESULT_2": compact_security_sentence(results[1], 24 if tuning.compact_attack_chain == 0 else 18, tuning.compact_attack_chain),
            "RESULT_3": compact_security_sentence(results[2], 24 if tuning.compact_attack_chain == 0 else 18, tuning.compact_attack_chain),
            "RESULT_JUDGMENT": compact_security_sentence(ctx.core_judgment or ctx.goal, 24 if tuning.compact_attack_chain == 0 else 18, tuning.compact_attack_chain),
            "EVIDENCE_HINT_1": compact_security_label("关键动作已有直接证据", 18 if tuning.compact_attack_chain == 0 else 14, tuning.compact_attack_chain),
            "EVIDENCE_HINT_2": compact_security_label("结果区已形成影响证明", 18 if tuning.compact_attack_chain == 0 else 14, tuning.compact_attack_chain),
            "CLOSURE_1": compact_security_sentence(closure_points[0], 18 if tuning.compact_attack_chain == 0 else 14, tuning.compact_attack_chain),
            "CLOSURE_2": compact_security_sentence(closure_points[1], 18 if tuning.compact_attack_chain == 0 else 14, tuning.compact_attack_chain),
            "CLOSURE_3": compact_security_sentence(closure_points[2], 18 if tuning.compact_attack_chain == 0 else 14, tuning.compact_attack_chain),
        }

    return {}


def postprocess_rendered_svg(
    ctx: PageContext,
    svg_text: str,
    tuning: RenderTuning,
    placeholder_values: dict[str, str],
) -> str:
    template_name = ctx.template_path.name
    if template_name == "05_case.svg":
        title_font = 20 if tuning.semantic_headline <= 1 else 18
        title_width = 18 if tuning.semantic_headline <= 1 else 15
        svg_text = rewrite_semantic_header_title(
            svg_text,
            placeholder_values.get("PAGE_TITLE", ""),
            width=title_width,
            font_size=title_font,
            y_override=78,
            line_height=20,
        )
        svg_text = rewrite_text_node(svg_text, 84, 218, lines=[placeholder_values.get("CASE_BACKGROUND_TITLE", "")], font_size=13, y_override=218, line_height=14)
        svg_text = rewrite_text_node(
            svg_text,
            84,
            244,
            lines=wrap_text(placeholder_values.get("CASE_BACKGROUND_HEADLINE", ""), 10, 2),
            font_size=18,
            y_override=240,
            line_height=18,
        )
        svg_text = rewrite_text_node(
            svg_text,
            84,
            286,
            lines=wrap_text(placeholder_values.get("CASE_BACKGROUND", ""), 14, 5),
            font_size=12,
            y_override=282,
            line_height=15,
        )
        svg_text = rewrite_text_node(svg_text, 352, 218, lines=[placeholder_values.get("CASE_FLOW_TITLE", "")], font_size=16, y_override=218, line_height=18)
        svg_text = rewrite_text_node(
            svg_text,
            376,
            278,
            lines=wrap_text(placeholder_values.get("CASE_LANE_A_TITLE", ""), 14, 2),
            font_size=12,
            y_override=276,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            376,
            316,
            lines=wrap_text(placeholder_values.get("CASE_SOLUTION", ""), 18, 3),
            font_size=12,
            y_override=308,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            376,
            418,
            lines=wrap_text(placeholder_values.get("CASE_LANE_B_TITLE", ""), 14, 2),
            font_size=12,
            y_override=416,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            376,
            456,
            lines=wrap_text(placeholder_values.get("CASE_PROCESS", ""), 18, 3),
            font_size=12,
            y_override=448,
            line_height=15,
        )
        svg_text = rewrite_text_node(svg_text, 906, 218, lines=[placeholder_values.get("CASE_RESULT_TITLE", "")], font_size=13, y_override=218, line_height=14)
        svg_text = rewrite_text_node(
            svg_text,
            906,
            244,
            lines=wrap_text(placeholder_values.get("CASE_RESULT_HEADLINE", ""), 12, 2),
            font_size=18,
            y_override=240,
            line_height=18,
        )
        svg_text = rewrite_text_node(
            svg_text,
            928,
            306,
            lines=wrap_text(placeholder_values.get("CASE_RESULTS", ""), 16, 6),
            font_size=12,
            y_override=300,
            line_height=15,
        )
        svg_text = rewrite_text_node(svg_text, 84, 560, lines=[placeholder_values.get("CASE_IMAGE_TITLE", "")], font_size=13, y_override=560, line_height=14)
        svg_text = rewrite_text_node(
            svg_text,
            309,
            588,
            lines=wrap_text(placeholder_values.get("CASE_IMAGE", ""), 20, 2),
            font_size=13,
            y_override=582,
            line_height=15,
        )
        svg_text = rewrite_text_node(svg_text, 604, 560, lines=[placeholder_values.get("CASE_CLIENT_TITLE", "")], font_size=15, y_override=560, line_height=16)
        svg_text = rewrite_text_node(
            svg_text,
            604,
            594,
            lines=wrap_text(placeholder_values.get("CASE_CLIENT", ""), 32, 2),
            font_size=13,
            y_override=588,
            line_height=16,
        )
        svg_text = rewrite_text_node(svg_text, 1045, 491, lines=[placeholder_values.get("CASE_VALUE_BAND", "")], font_size=12, y_override=491, line_height=14)
    elif template_name == "19_result_leading_case.svg":
        if tuning.semantic_headline > 0:
            title_font = 20 if tuning.semantic_headline == 1 else 18
            title_width = 16 if tuning.semantic_headline == 1 else 12
            svg_text = rewrite_text_node(
                svg_text,
                84,
                82,
                lines=wrap_text(placeholder_values.get("PAGE_TITLE", ""), title_width, 1),
                font_size=title_font,
                y_override=78,
                line_height=20,
            )
        headline_semantic_level = max(tuning.semantic_headline, tuning.semantic_argument)
        if tuning.compact_header_bundle > 0 or headline_semantic_level > 0:
            if headline_semantic_level > 0:
                headline_font = 19 if tuning.compact_header_bundle <= 1 else 17
                headline_y = 232 if tuning.compact_header_bundle <= 1 else 228
                headline_width = 18 if tuning.compact_header_bundle <= 1 else 15
                headline_line_height = 21 if tuning.compact_header_bundle <= 1 else 18
            else:
                headline_font = 20 if tuning.compact_header_bundle == 1 else 13
                headline_y = 233 if tuning.compact_header_bundle == 1 else 225
                headline_width = 22 if tuning.compact_header_bundle == 1 else 14
                headline_line_height = 22 if tuning.compact_header_bundle == 1 else 16
            svg_text = rewrite_text_node(svg_text, 84, 239, font_size=headline_font)
            svg_text = rewrite_text_node(
                svg_text,
                84,
                239,
                lines=wrap_text(placeholder_values.get("RESULT_HEADLINE", ""), headline_width, 2),
                font_size=headline_font,
                y_override=headline_y,
                line_height=headline_line_height,
            )
            svg_text = rewrite_text_node(
                svg_text,
                84,
                210,
                font_size=11 if tuning.compact_header_bundle > 1 else 12,
                y_override=196 if tuning.compact_header_bundle > 1 else None,
            )
            svg_text = rewrite_text_node(
                svg_text,
                84,
                258,
                font_size=11,
                y_override=260 if tuning.compact_header_bundle > 1 else None,
            )
            if tuning.compact_header_bundle > 1 and tuning.semantic_headline == 0:
                svg_text = svg_text.replace(
                    '<rect x="84" y="247" width="146" height="3" fill="#ED7D31" rx="2" />',
                    '<rect x="84" y="249" width="120" height="3" fill="#ED7D31" rx="2" />',
                )
        # The short accent bar regularly collides with the compacted headline/subline bundle
        # after multi-line rewrites and PPT export. Keep the headline readable first.
        svg_text = svg_text.replace(
            '<rect x="84" y="247" width="146" height="3" fill="#ED7D31" rx="2" />',
            '',
        )
        svg_text = svg_text.replace(
            '<rect x="84" y="249" width="120" height="3" fill="#ED7D31" rx="2" />',
            '',
        )
        metric_font = 28 if tuning.compact_header_bundle == 0 else 26
        metric_y = 240 if tuning.compact_header_bundle == 0 else 242
        metric_label_y = 255 if tuning.compact_header_bundle == 0 else 258
        subline_y = 256 if tuning.compact_header_bundle == 0 else 254
        svg_text = svg_text.replace(
            'font-size="32" font-weight="bold" fill="#ED7D31" data-slot="key-metric">',
            f'font-size="{metric_font}" font-weight="bold" fill="#ED7D31" data-slot="key-metric">'
        )
        svg_text = svg_text.replace(
            'y="232" text-anchor="middle" font-family="Arial" font-size="28"',
            f'y="{metric_y}" text-anchor="middle" font-family="Arial" font-size="{metric_font}"'
        )
        svg_text = svg_text.replace(
            'y="252" text-anchor="middle" font-family="Microsoft YaHei, 微软雅黑, Arial" font-size="13"',
            f'y="{metric_label_y}" text-anchor="middle" font-family="Microsoft YaHei, 微软雅黑, Arial" font-size="13"'
        )
        svg_text = svg_text.replace(
            'y="258" font-family="Microsoft YaHei, 微软雅黑, Arial" font-size="12"',
            f'y="{subline_y}" font-family="Microsoft YaHei, 微软雅黑, Arial" font-size="12"'
        )
        if tuning.compact_attack_chain > 0:
            for x in (185, 393, 601):
                svg_text = rewrite_text_node(svg_text, x, 360, font_size=10)
            action_font = 13 if tuning.compact_attack_chain == 1 else 12
            action_y = 446 if tuning.compact_attack_chain == 1 else 442
            svg_text = rewrite_text_node(
                svg_text,
                172,
                450,
                lines=wrap_text(placeholder_values.get("ACTION_1", ""), 7 if tuning.compact_attack_chain > 1 else 8, 2),
                font_size=action_font,
                y_override=action_y,
                line_height=14,
            )
            svg_text = rewrite_text_node(
                svg_text,
                364,
                450,
                lines=wrap_text(placeholder_values.get("ACTION_2", ""), 7 if tuning.compact_attack_chain > 1 else 8, 2),
                font_size=action_font,
                y_override=action_y,
                line_height=14,
            )
            svg_text = rewrite_text_node(
                svg_text,
                556,
                450,
                lines=wrap_text(placeholder_values.get("ACTION_3", ""), 7 if tuning.compact_attack_chain > 1 else 8, 2),
                font_size=action_font,
                y_override=action_y,
                line_height=14,
            )
            svg_text = rewrite_text_node(
                svg_text,
                748,
                450,
                lines=wrap_text(placeholder_values.get("RESULT_1", ""), 6 if tuning.compact_attack_chain > 1 else 8, 2),
                font_size=action_font,
                y_override=action_y,
                line_height=14,
            )
            svg_text = rewrite_text_node(svg_text, 364, 511, font_size=10)
            svg_text = rewrite_text_node(svg_text, 556, 511, font_size=10)
            svg_text = rewrite_text_node(svg_text, 252, 593, font_size=11)
            svg_text = rewrite_text_node(svg_text, 640, 593, font_size=11)
            svg_text = rewrite_text_node(svg_text, 1028, 593, font_size=11)
    elif template_name == "12_grid.svg":
        svg_text = rewrite_semantic_header_title(
            svg_text,
            placeholder_values.get("PAGE_TITLE", ""),
            width=18 if tuning.semantic_headline <= 1 else 15,
            font_size=20 if tuning.semantic_headline <= 1 else 18,
            y_override=78,
            line_height=20,
        )
        headline_level = max(1, tuning.semantic_headline, tuning.semantic_argument)
        grid_headline = semantic_headline_text(ctx, limit=28, level=headline_level)
        grid_headline_lines = wrap_text(
            grid_headline,
            18 if tuning.compact_matrix == 0 else 14,
            2,
        )
        svg_text = rewrite_text_node(
            svg_text,
            86,
            216,
            lines=grid_headline_lines,
            font_size=18,
            y_override=212 if tuning.compact_matrix == 0 else 210,
            line_height=20,
        )
        if len(grid_headline_lines) > 1:
            svg_text = svg_text.replace(
                '<line x1="86" y1="226" x2="1190" y2="226" stroke="#D9E2F3" stroke-width="1.5" />',
                '',
            )
        if "重要成果" in ctx.page_title or "关键结果" in ctx.page_title:
            svg_text = rewrite_text_node(
                svg_text,
                88,
                577,
                lines=["高风险判断 / 复测动作"],
                font_size=15,
                y_override=577,
                line_height=16,
            )
        elif "关键证据总览" in ctx.page_title or "证据证明" in ctx.page_title:
            svg_text = rewrite_text_node(
                svg_text,
                88,
                577,
                lines=["结果判断 / 下一步"],
                font_size=15,
                y_override=577,
                line_height=16,
            )
        svg_text = rewrite_text_node(
            svg_text,
            88,
            604,
            lines=wrap_text(placeholder_values.get("GRID_SUMMARY", ""), 24 if tuning.compact_matrix == 0 else 22, 2),
            font_size=13 if tuning.compact_matrix == 0 else 12,
            y_override=598 if tuning.compact_matrix == 0 else 594,
            line_height=15,
        )
        if tuning.compact_matrix > 0:
            for y in (292, 434):
                for x in (110, 489, 868):
                    svg_text = rewrite_text_node(svg_text, x, y, font_size=14 if tuning.compact_matrix == 1 else 13)
            for y in (320, 462):
                for x in (110, 489, 868):
                    svg_text = rewrite_text_node(svg_text, x, y, font_size=11 if tuning.compact_matrix == 1 else 10)
    elif template_name == "07_data.svg":
        header_title = placeholder_values.get("PAGE_TITLE", "")
        svg_text = rewrite_semantic_header_title(
            svg_text,
            header_title,
            width=18 if tuning.semantic_headline <= 1 else 15,
            font_size=20 if tuning.semantic_headline <= 1 else 18,
            y_override=78,
            line_height=20,
        )
        headline_lines = wrap_text(
            placeholder_values.get("PROOF_HEADLINE", ""),
            18 if tuning.semantic_headline <= 1 else 15,
            2,
        )
        svg_text = rewrite_text_node(
            svg_text,
            84,
            210,
            lines=wrap_text(placeholder_values.get("PROOF_CONTEXT", ""), 20, 1),
            font_size=12,
            y_override=208,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            84,
            236,
            lines=headline_lines,
            font_size=18 if len(headline_lines) > 1 else 20,
            y_override=228 if len(headline_lines) > 1 else 236,
            line_height=20,
        )
        svg_text = rewrite_text_node(
            svg_text,
            84,
            255,
            lines=wrap_text(placeholder_values.get("PROOF_SUBLINE", ""), 18, 1),
            font_size=11,
            y_override=257,
            line_height=13,
        )
        svg_text = svg_text.replace(
            '<rect x="84" y="247" width="140" height="3" fill="#ED7D31" rx="2" />',
            '',
        )
        for x in (874, 1005, 1136):
            svg_text = rewrite_text_node(svg_text, x, 229, font_size=22)
        for x in (874, 1005, 1136):
            svg_text = rewrite_text_node(svg_text, x, 244, font_size=11)
        svg_text = rewrite_text_node(
            svg_text,
            425,
            437,
            lines=wrap_text(placeholder_values.get("PROOF_CANVAS", ""), 12, 2),
            font_size=13,
            y_override=428,
            line_height=16,
        )
        proof_title = "当前主判断"
        left_title = "当前入口"
        mid_title = "放大条件"
        right_title = "结果影响"
        evidence_title = "结果证据 / 管理动作"
        note_1_title = "直接证据"
        note_2_title = "结果判断"
        note_3_title = "优先动作"
        if any(token in ctx.page_title for token in ("重要成果", "关键结果")):
            proof_title = "关键结果已形成第一层证明"
            left_title = "外网结果"
            mid_title = "内网放大"
            right_title = "人员 / 影响"
            evidence_title = "结果证据 / 优先动作"
            note_1_title = "入口结果"
            note_2_title = "影响结果"
            note_3_title = "整改收束"
        elif any(token in ctx.page_title for token in ("攻击链总览", "整体攻击路径分析")):
            proof_title = "入口-放大-结果主链"
            left_title = "入口落点"
            mid_title = "放大条件"
            right_title = "控制结果"
            evidence_title = "结果证据 / 管理动作"
            note_1_title = "入口样例"
            note_2_title = "放大条件"
            note_3_title = "优先动作"
        elif "内网突破" in ctx.page_title:
            proof_title = "后台权限 -> 放大条件 -> 高影响结果"
            left_title = "后台权限"
            mid_title = "放大条件"
            right_title = "高影响结果"
            evidence_title = "结果证据 / 收口动作"
            note_1_title = "后台 / 未授权"
            note_2_title = "凭证 / 放大"
            note_3_title = "收口 / 复测"
        svg_text = rewrite_text_node(svg_text, 86, 319, lines=[proof_title], font_size=16, y_override=319, line_height=18)
        svg_text = rewrite_text_node(svg_text, 161, 364, lines=[left_title], font_size=12, y_override=364, line_height=14)
        svg_text = rewrite_text_node(svg_text, 426, 364, lines=[mid_title], font_size=12, y_override=364, line_height=14)
        svg_text = rewrite_text_node(svg_text, 691, 364, lines=[right_title], font_size=12, y_override=364, line_height=14)
        svg_text = rewrite_text_node(svg_text, 844, 319, lines=[evidence_title], font_size=16, y_override=319, line_height=18)
        svg_text = rewrite_text_node(svg_text, 866, 365, lines=[note_1_title], font_size=12, y_override=365, line_height=14)
        svg_text = rewrite_text_node(svg_text, 866, 426, lines=[note_2_title], font_size=12, y_override=426, line_height=14)
        svg_text = rewrite_text_node(svg_text, 866, 487, lines=[note_3_title], font_size=12, y_override=487, line_height=14)
        note_1_lines = wrap_text(placeholder_values.get("DATA_NOTE_1", ""), 20, 2)
        note_2_lines = wrap_text(placeholder_values.get("DATA_NOTE_2", ""), 20, 2)
        note_3_lines = wrap_text(placeholder_values.get("DATA_NOTE_3", ""), 20, 2)
        note_line_height = 11
        svg_text = rewrite_text_node(
            svg_text,
            866,
            384,
            lines=note_1_lines,
            font_size=10 if len(note_1_lines) > 1 else 11,
            y_override=381 if len(note_1_lines) > 1 else 378,
            line_height=note_line_height,
        )
        svg_text = rewrite_text_node(
            svg_text,
            866,
            445,
            lines=note_2_lines,
            font_size=10 if len(note_2_lines) > 1 else 11,
            y_override=442 if len(note_2_lines) > 1 else 439,
            line_height=note_line_height,
        )
        svg_text = rewrite_text_node(
            svg_text,
            866,
            506,
            lines=note_3_lines,
            font_size=10 if len(note_3_lines) > 1 else 11,
            y_override=503 if len(note_3_lines) > 1 else 500,
            line_height=note_line_height,
        )
        svg_text = rewrite_text_node(svg_text, 230, 508, lines=[shorten(placeholder_values.get("PROOF_RELATION_1", ""), 12)], font_size=10, y_override=508, line_height=12)
        svg_text = rewrite_text_node(svg_text, 620, 508, lines=[shorten(placeholder_values.get("PROOF_RELATION_2", ""), 12)], font_size=10, y_override=508, line_height=12)
        svg_text = rewrite_text_node(svg_text, 252, 585, lines=[shorten(placeholder_values.get("PROOF_SUMMARY_1", ""), 18)], font_size=11, y_override=585, line_height=13)
        svg_text = rewrite_text_node(svg_text, 640, 585, lines=[shorten(placeholder_values.get("PROOF_SUMMARY_2", ""), 18)], font_size=11, y_override=585, line_height=13)
        svg_text = rewrite_text_node(svg_text, 1028, 585, lines=[shorten(placeholder_values.get("PROOF_SUMMARY_3", ""), 18)], font_size=11, y_override=585, line_height=13)
    elif template_name == "09_comparison.svg":
        svg_text = rewrite_semantic_header_title(
            svg_text,
            placeholder_values.get("PAGE_TITLE", ""),
            width=18 if tuning.semantic_headline <= 1 else 15,
            font_size=20 if tuning.semantic_headline <= 1 else 18,
            y_override=78,
            line_height=20,
        )
        headline_lines = wrap_text(
            placeholder_values.get("COMPARE_HEADLINE", ""),
            18 if tuning.compact_attack_chain == 0 else 14,
            2,
        )
        svg_text = rewrite_text_node(
            svg_text,
            86,
            216,
            lines=headline_lines,
            font_size=18 if tuning.compact_attack_chain == 0 else 16,
            y_override=210 if len(headline_lines) > 1 else 216,
            line_height=18,
        )
        if len(headline_lines) > 1:
            svg_text = svg_text.replace(
                '<line x1="86" y1="226" x2="1190" y2="226" stroke="#D9E2F3" stroke-width="1.5" />',
                '',
            )
        svg_text = rewrite_text_node(
            svg_text,
            132,
            338,
            lines=wrap_text(placeholder_values.get("COMPARE_TITLE_A", ""), 10 if tuning.compact_attack_chain == 0 else 8, 2),
            font_size=14 if tuning.compact_attack_chain == 0 else 13,
            y_override=332,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            132,
            454,
            lines=wrap_text(placeholder_values.get("COMPARE_TITLE_B", ""), 10 if tuning.compact_attack_chain == 0 else 8, 2),
            font_size=14 if tuning.compact_attack_chain == 0 else 13,
            y_override=448,
            line_height=15,
        )
        for x, key in (
            (230, "COMPARE_CONTENT_A_1"),
            (450, "COMPARE_CONTENT_A_2"),
            (670, "COMPARE_CONTENT_A_3"),
            (890, "COMPARE_CONTENT_A_4"),
        ):
            svg_text = rewrite_text_node(
                svg_text,
                x,
                338,
                lines=wrap_text(placeholder_values.get(key, ""), 14 if tuning.compact_attack_chain == 0 else 12, 2),
                font_size=12 if tuning.compact_attack_chain == 0 else 11,
                y_override=324,
                line_height=15,
            )
        for x, key in (
            (230, "COMPARE_CONTENT_B_1"),
            (450, "COMPARE_CONTENT_B_2"),
            (670, "COMPARE_CONTENT_B_3"),
            (890, "COMPARE_CONTENT_B_4"),
        ):
            svg_text = rewrite_text_node(
                svg_text,
                x,
                454,
                lines=wrap_text(placeholder_values.get(key, ""), 14 if tuning.compact_attack_chain == 0 else 12, 2),
                font_size=12 if tuning.compact_attack_chain == 0 else 11,
                y_override=440,
                line_height=15,
            )
        svg_text = rewrite_text_node(
            svg_text,
            88,
            591,
            lines=wrap_text(placeholder_values.get("COMPARE_RESULT", ""), 26 if tuning.compact_attack_chain == 0 else 22, 2),
            font_size=14 if tuning.compact_attack_chain == 0 else 13,
            y_override=584 if tuning.compact_attack_chain == 0 else 580,
            line_height=16,
        )
    elif template_name == "16_table.svg":
        priority_title = "整改优先级判断"
        matrix_title = "薄弱域 -> 当前暴露 -> 处置矩阵"
        decision_title = "整改管理收束"
        decision_card_1 = "管理判断"
        decision_card_2 = "关键动作"
        decision_card_3 = "完成标准"
        if any(token in ctx.page_title for token in ("异常登陆", "异常登录", "审计问题")):
            priority_title = "驻留风险优先级判断"
            matrix_title = "审计缺失 -> 暴露状态 -> 处置矩阵"
            decision_title = "驻留风险管理收束"
            decision_card_1 = "驻留判断"
            decision_card_2 = "先压动作"
            decision_card_3 = "完成标准"
        svg_text = rewrite_semantic_header_title(
            svg_text,
            placeholder_values.get("PAGE_TITLE", ""),
            width=18 if tuning.semantic_headline <= 1 else 15,
            font_size=20 if tuning.semantic_headline <= 1 else 18,
            y_override=78,
            line_height=20,
        )
        svg_text = rewrite_text_node(svg_text, 86, 207, lines=[priority_title], font_size=12, y_override=207, line_height=14)
        svg_text = rewrite_text_node(svg_text, 86, 319, lines=[matrix_title], font_size=16, y_override=319, line_height=18)
        svg_text = rewrite_text_node(svg_text, 122, 364, lines=["优先级"], font_size=11, y_override=364, line_height=13)
        svg_text = rewrite_text_node(svg_text, 239, 364, lines=["薄弱域"], font_size=11, y_override=364, line_height=13)
        svg_text = rewrite_text_node(svg_text, 386, 364, lines=["当前暴露"], font_size=11, y_override=364, line_height=13)
        svg_text = rewrite_text_node(svg_text, 552, 364, lines=["处置动作"], font_size=11, y_override=364, line_height=13)
        svg_text = rewrite_text_node(svg_text, 756, 364, lines=["复测闭环"], font_size=11, y_override=364, line_height=13)
        svg_text = rewrite_text_node(svg_text, 934, 216, lines=[decision_title], font_size=15, y_override=216, line_height=16)
        svg_text = rewrite_text_node(svg_text, 956, 264, lines=[decision_card_1], font_size=12, y_override=264, line_height=14)
        svg_text = rewrite_text_node(svg_text, 956, 342, lines=[decision_card_2], font_size=12, y_override=342, line_height=14)
        svg_text = rewrite_text_node(svg_text, 956, 420, lines=[decision_card_3], font_size=12, y_override=420, line_height=14)
        svg_text = rewrite_text_node(
            svg_text,
            956,
            289,
            lines=wrap_text(placeholder_values.get("TABLE_INSIGHT_1", ""), 18 if tuning.compact_matrix == 0 else 14, 2),
            font_size=11,
            y_override=284,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            956,
            367,
            lines=wrap_text(placeholder_values.get("TABLE_INSIGHT_2", ""), 18 if tuning.compact_matrix == 0 else 14, 2),
            font_size=11,
            y_override=362,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            956,
            445,
            lines=wrap_text(placeholder_values.get("TABLE_INSIGHT_3", ""), 18 if tuning.compact_matrix == 0 else 14, 2),
            font_size=11,
            y_override=440,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            956,
            506,
            lines=wrap_text(placeholder_values.get("TABLE_HIGHLIGHT", ""), 18 if tuning.compact_matrix == 0 else 14, 2),
            font_size=11,
            y_override=500,
            line_height=14,
        )
        svg_text = rewrite_text_node(svg_text, 208, 585, lines=[shorten(placeholder_values.get("CLOSURE_STEP_1", ""), 16)], font_size=11, y_override=585, line_height=13)
        svg_text = rewrite_text_node(svg_text, 475, 585, lines=[shorten(placeholder_values.get("CLOSURE_STEP_2", ""), 16)], font_size=11, y_override=585, line_height=13)
        svg_text = rewrite_text_node(svg_text, 742, 585, lines=[shorten(placeholder_values.get("CLOSURE_STEP_3", ""), 16)], font_size=11, y_override=585, line_height=13)
        for x in (205, 475, 745):
            svg_text = rewrite_text_node(svg_text, x, 238, font_size=11)
        if tuning.compact_matrix > 0:
            for y in (406, 440, 474, 508):
                for x in (98, 182, 332, 476, 664):
                    svg_text = rewrite_text_node(svg_text, x, y, font_size=10)
            for y in (289, 367, 445, 506, 585):
                for x in (956, 208, 475, 742):
                    svg_text = rewrite_text_node(svg_text, x, y, font_size=11)
    elif template_name == "17_service_overview.svg":
        svg_text = rewrite_semantic_header_title(
            svg_text,
            placeholder_values.get("PAGE_TITLE", ""),
            width=18 if tuning.semantic_headline <= 1 else 15,
            font_size=20 if tuning.semantic_headline <= 1 else 18,
            y_override=78,
            line_height=20,
        )
        lead_lines = wrap_text(
            placeholder_values.get("OVERVIEW_LEAD", ""),
            32 if tuning.compact_service_map == 0 else 24,
            2,
        )
        svg_text = rewrite_text_node(
            svg_text,
            84,
            151,
            lines=lead_lines,
            font_size=12 if tuning.compact_service_map == 0 else 11,
            y_override=143 if len(lead_lines) > 1 else 149,
            line_height=13,
        )
        platform_name_lines = wrap_text(
            placeholder_values.get("PLATFORM_NAME", ""),
            16 if tuning.compact_service_map == 0 else 12,
            2,
        )
        svg_text = rewrite_text_node(
            svg_text,
            84,
            258,
            lines=platform_name_lines,
            font_size=19 if tuning.compact_service_map == 0 else 18,
            y_override=250 if len(platform_name_lines) > 1 else 258,
            line_height=18,
        )
        platform_desc_lines = wrap_text(
            placeholder_values.get("PLATFORM_DESC", ""),
            16 if tuning.compact_service_map == 0 else 14,
            3,
        )
        svg_text = rewrite_text_node(
            svg_text,
            84,
            304,
            lines=platform_desc_lines,
            font_size=11 if tuning.compact_service_map == 0 else 10,
            y_override=292 if len(platform_desc_lines) > 1 else 300,
            line_height=13,
        )
        for y, title_key, desc_key in (
            (277, "DOMAIN_ATTACK_TITLE", "DOMAIN_ATTACK_DESC"),
            (365, "DOMAIN_DEFENSE_TITLE", "DOMAIN_DEFENSE_DESC"),
            (453, "DOMAIN_TRAINING_TITLE", "DOMAIN_TRAINING_DESC"),
        ):
            svg_text = rewrite_text_node(
                svg_text,
                428,
                y,
                lines=wrap_text(placeholder_values.get(title_key, ""), 14 if tuning.compact_service_map == 0 else 10, 2),
                font_size=14 if tuning.compact_service_map == 0 else 13,
                y_override=y - 2,
                line_height=15,
            )
            svg_text = rewrite_text_node(
                svg_text,
                428,
                y + 27,
                lines=wrap_text(placeholder_values.get(desc_key, ""), 24 if tuning.compact_service_map == 0 else 18, 2),
                font_size=10,
                y_override=y + 22,
                line_height=12,
            )
        for y, key in (
            (291, "VALUE_1"),
            (369, "VALUE_2"),
            (447, "VALUE_3"),
        ):
            svg_text = rewrite_text_node(
                svg_text,
                938,
                y,
                lines=wrap_text(placeholder_values.get(key, ""), 16 if tuning.compact_service_map == 0 else 12, 2),
                font_size=13 if tuning.compact_service_map == 0 else 12,
                y_override=y - 5,
                line_height=14,
            )
        svg_text = rewrite_text_node(svg_text, 84, 578, font_size=15 if tuning.compact_service_map == 0 else 14)
        svg_text = rewrite_text_node(
            svg_text,
            116,
            609,
            lines=[shorten(placeholder_values.get("DRIVER_POINT_1", ""), 28 if tuning.compact_service_map == 0 else 20)],
            font_size=13 if tuning.compact_service_map == 0 else 12,
            y_override=609,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            650,
            609,
            lines=[shorten(placeholder_values.get("DRIVER_POINT_2", ""), 28 if tuning.compact_service_map == 0 else 20)],
            font_size=13 if tuning.compact_service_map == 0 else 12,
            y_override=609,
            line_height=14,
        )
    elif template_name == "18_domain_capability_map.svg":
        scene_zone_title = "关键输入 / 直接约束"
        capability_zone_title = "核心动作 / 闭环能力"
        method_label = "推进方法"
        if any(token in ctx.page_title for token in ("互联网侧系统安全检测与防护待加强", "检测与防护待加强")):
            scene_zone_title = "互联网暴露 / 直接证据"
            capability_zone_title = "持续检测与修补缺口"
            method_label = "优先动作"
        elif "整改复测机制" in ctx.page_title:
            scene_zone_title = "闭环输入 / 责任前提"
            capability_zone_title = "责任-动作-复测-回看闭环"
            method_label = "闭环要求"
        elif "长亭安服价值" in ctx.page_title:
            scene_zone_title = "价值输入 / 管理问题"
            capability_zone_title = "能力输出 / 执行抓手"
            method_label = "交付价值"
        svg_text = rewrite_semantic_header_title(
            svg_text,
            placeholder_values.get("PAGE_TITLE", ""),
            width=18 if tuning.semantic_headline <= 1 else 15,
            font_size=20 if tuning.semantic_headline <= 1 else 18,
            y_override=78,
            line_height=20,
        )
        svg_text = rewrite_text_node(svg_text, 84, 220, lines=[scene_zone_title], font_size=15, y_override=220, line_height=16)
        svg_text = rewrite_text_node(svg_text, 356, 220, lines=[capability_zone_title], font_size=15, y_override=220, line_height=16)
        svg_text = rewrite_text_node(svg_text, 132, 614, lines=[method_label], font_size=11, y_override=614, line_height=13)
        svg_text = rewrite_text_node(
            svg_text,
            206,
            617,
            lines=wrap_text(
                placeholder_values.get("METHOD_NOTE", ""),
                44 if tuning.compact_service_map == 0 else 32,
                2,
                respect_points=False,
            ),
            font_size=13 if tuning.compact_service_map == 0 else 12,
            y_override=611,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            116,
            328,
            lines=wrap_text(placeholder_values.get("SCENE_POINT_1", ""), 11, 3),
            font_size=11,
            y_override=316,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            116,
            398,
            lines=wrap_text(placeholder_values.get("SCENE_POINT_2", ""), 11, 3),
            font_size=11,
            y_override=386,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            116,
            468,
            lines=wrap_text(placeholder_values.get("SCENE_POINT_3", ""), 11, 3),
            font_size=11,
            y_override=456,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            380,
            278,
            lines=wrap_text(placeholder_values.get("CAPABILITY_1_TITLE", ""), 12, 2),
            font_size=13,
            y_override=272,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            660,
            278,
            lines=wrap_text(placeholder_values.get("CAPABILITY_2_TITLE", ""), 12, 2),
            font_size=13,
            y_override=272,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            380,
            424,
            lines=wrap_text(placeholder_values.get("CAPABILITY_3_TITLE", ""), 12, 2),
            font_size=13,
            y_override=418,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            660,
            424,
            lines=wrap_text(placeholder_values.get("CAPABILITY_4_TITLE", ""), 12, 2),
            font_size=13,
            y_override=418,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            380,
            315,
            lines=wrap_text(placeholder_values.get("CAPABILITY_1_DESC", ""), 16, 3),
            font_size=11,
            y_override=309,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            660,
            315,
            lines=wrap_text(placeholder_values.get("CAPABILITY_2_DESC", ""), 16, 3),
            font_size=11,
            y_override=309,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            380,
            461,
            lines=wrap_text(placeholder_values.get("CAPABILITY_3_DESC", ""), 16, 3),
            font_size=11,
            y_override=455,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            660,
            461,
            lines=wrap_text(placeholder_values.get("CAPABILITY_4_DESC", ""), 16, 3),
            font_size=11,
            y_override=455,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            956,
            294,
            lines=wrap_text(placeholder_values.get("OUTCOME_1", ""), 16, 3),
            font_size=12,
            y_override=286,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            956,
            384,
            lines=wrap_text(placeholder_values.get("OUTCOME_2", ""), 16, 3),
            font_size=12,
            y_override=376,
            line_height=14,
        )
        svg_text = rewrite_text_node(
            svg_text,
            956,
            474,
            lines=wrap_text(placeholder_values.get("OUTCOME_3", ""), 16, 3),
            font_size=12,
            y_override=466,
            line_height=14,
        )
    elif template_name == "08_product.svg":
        svg_text = rewrite_semantic_header_title(
            svg_text,
            placeholder_values.get("PAGE_TITLE", ""),
            width=18 if tuning.semantic_headline <= 1 else 15,
            font_size=20 if tuning.semantic_headline <= 1 else 18,
            y_override=78,
            line_height=20,
        )
        if "风险结构总览" in ctx.page_title:
            tree_title = "四类控制薄弱域如何共同放大结果"
            evidence_title = "根因证据 / 管理收束"
        elif "互联网侧" in ctx.page_title:
            tree_title = "检测缺失使高危入口持续存在"
            evidence_title = "外网证据 / 整改收束"
        elif "审计" in ctx.page_title:
            tree_title = "审计缺失使异常登录持续失察"
            evidence_title = "审计证据 / 整改收束"
        elif any(token in ctx.page_title for token in ("通用口令", "通用密码")):
            tree_title = "口令复用使高危资产持续暴露"
            evidence_title = "口令证据 / 整改收束"
        elif "安全意识" in ctx.page_title:
            tree_title = "意识薄弱使社工入口持续可用"
            evidence_title = "人员证据 / 整改收束"
        else:
            tree_title = "根因结构拆解"
            evidence_title = "证据证明 / 结论收束"
        svg_text = rewrite_text_node(
            svg_text,
            86,
            216,
            lines=wrap_text(tree_title, 18 if tuning.compact_service_map == 0 else 14, 2),
            font_size=16,
            y_override=216,
            line_height=18,
        )
        svg_text = rewrite_text_node(
            svg_text,
            410,
            280,
            lines=wrap_text(placeholder_values.get("PRODUCT_NAME", ""), 14 if tuning.compact_service_map == 0 else 12, 2),
            font_size=16,
            y_override=272,
            line_height=16,
        )
        svg_text = rewrite_text_node(
            svg_text,
            814,
            216,
            lines=[evidence_title],
            font_size=16,
            y_override=216,
            line_height=18,
        )
        svg_text = rewrite_text_node(
            svg_text,
            1005,
            347,
            lines=wrap_text(placeholder_values.get("PRODUCT_IMAGE", ""), 18 if tuning.compact_service_map == 0 else 14, 2),
            font_size=13 if tuning.compact_service_map == 0 else 12,
            y_override=341,
            line_height=15,
        )
        svg_text = rewrite_text_node(
            svg_text,
            838,
            522,
            lines=wrap_text(placeholder_values.get("PRODUCT_VALUE", ""), 18 if tuning.compact_service_map == 0 else 14, 2),
            font_size=13 if tuning.compact_service_map == 0 else 12,
            y_override=544,
            line_height=15,
        )
    elif template_name == "02_toc.svg" and tuning.compact_toc > 0:
        title_rows = [185, 265, 345, 425]
        desc_rows = [208, 288, 368, 448]
        if "TOC_ITEM_5_TITLE" in placeholder_values:
            title_rows.append(505)
            desc_rows.append(528)
        for y in title_rows:
            svg_text = rewrite_text_node(svg_text, 200, y, font_size=20 if tuning.compact_toc == 1 else 18)
        for y in desc_rows:
            svg_text = rewrite_text_node(svg_text, 200, y, font_size=12)
    return svg_text


def render_chaitin_page_subtitle(ctx: PageContext, tuning: RenderTuning) -> str:
    subtitle = normalize_text(ctx.core_judgment or ctx.proof_goal)
    if not subtitle:
        return ""
    limit = 48 if tuning.compact_standard == 0 else 32
    return (
        '<text x="56" y="122" fill="#8D9AAB" '
        'font-family="PingFang SC, Microsoft YaHei, Arial, sans-serif" '
        f'font-size="15">{escape_xml(shorten(subtitle, limit))}</text>'
    )


def derive_toc_items(ctx: PageContext, tuning: RenderTuning, max_items: int = 4) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    title_limit = 18 if tuning.compact_toc == 0 else 14
    desc_limit = 30 if tuning.compact_toc == 0 else 18
    for section in ctx.storyline_sections[:max_items]:
        section_title = section.get("title", "")
        raw_desc = section.get("goal") or section.get("problem") or section.get("page_types") or ""
        items.append(
            {
                "title": shorten(section_title, title_limit),
                "desc": normalize_toc_desc(build_toc_desc(section_title, raw_desc), desc_limit, tuning.compact_toc),
            }
        )
    if len(items) < max_items:
        for entry in ctx.outline_entries[2:]:
            title = normalize_text(entry.get("页面类型", "") or entry.get("推荐页型", ""))
            if not title:
                continue
            raw_desc = entry.get("页面意图", "") or entry.get("证明目标", "")
            items.append(
                {
                    "title": shorten(title, title_limit),
                    "desc": normalize_toc_desc(build_toc_desc(title, raw_desc), desc_limit, tuning.compact_toc),
                }
            )
            if len(items) >= max_items:
                break
    while len(items) < max_items:
        items.append({"title": f"章节 {len(items) + 1}", "desc": "待补充"})
    return items[:max_items]


def derive_section_name(page_num: int, sections: list[dict[str, str]], title: str) -> str:
    if not sections:
        return title
    lowered_title = title.lower()
    for section in sections:
        if section["title"] and section["title"].lower() in lowered_title:
            return section["title"]
    if page_num <= 2:
        return sections[0]["title"]
    bucket = min(len(sections) - 1, max(0, math.floor(((page_num - 3) / max(1, len(sections))) )))
    return sections[bucket]["title"]


def sync_template_assets(template_text: str, template_path: Path, project_dir: Path, template_id: str) -> str:
    image_hrefs = re.findall(r'href="([^"]+)"', template_text)
    for href in image_hrefs:
        if "{{" in href or href.startswith("data:") or href.startswith("http://") or href.startswith("https://"):
            continue
        source = (template_path.parent / href).resolve()
        if not source.exists() or not source.is_file():
            continue
        target = project_dir / "images" / "template_assets" / template_id / href
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
        relative_href = Path("..") / "images" / "template_assets" / template_id / href
        template_text = template_text.replace(f'href="{href}"', f'href="{relative_href.as_posix()}"')
    return template_text


def resolve_template_path(template_id: str, preferred_template: str) -> Path:
    template_dir = ROOT / "templates" / "layouts" / template_id
    preferred_path = template_dir / preferred_template
    if preferred_template and preferred_path.exists():
        return preferred_path
    fallback = template_dir / "03_content.svg"
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"Template SVG not found for `{template_id}` / `{preferred_template}`")


def common_placeholder_map(ctx: PageContext, tuning: RenderTuning) -> dict[str, str]:
    cover_limit = 40 if tuning.compact_cover == 0 else 28
    chapter_title = strip_display_prefix(ctx.page_title)
    page_title = header_page_title(ctx)
    semantic_header_templates = {
        "05_case.svg",
        "07_data.svg",
        "09_comparison.svg",
        "08_product.svg",
        "16_table.svg",
        "17_service_overview.svg",
        "18_domain_capability_map.svg",
        "19_result_leading_case.svg",
    }
    if ctx.template_path.name in semantic_header_templates and is_complex_page(ctx.page):
        page_title_limit = 32
    else:
        page_title_limit = 16 if tuning.semantic_headline > 0 and is_complex_page(ctx.page) else (24 if is_complex_page(ctx.page) else 28)
    chapter_num = derive_section_index(ctx.section_name, ctx.storyline_sections, ctx.page_title)
    chapter_desc_source = derive_section_desc(
        ctx.section_name,
        ctx.storyline_sections,
        ctx.core_judgment or ctx.proof_goal or ctx.page_intent,
    )
    closing_message = page_action_text(ctx) or ctx.goal or "欢迎继续沟通后续合作与整改推进。"
    return {
        "TITLE": shorten(ctx.project_name or ctx.page_title, 28),
        "SUBTITLE": shorten(ctx.core_judgment or ctx.scenario or ctx.goal, cover_limit),
        "ENGLISH_SUBTITLE": "CHAITIN SECURITY SERVICE" if ctx.template_id in {"chaitin", "security_service"} else "PPT MASTER",
        "ORG_INFO": shorten(ctx.project_name or ctx.scenario or ctx.industry, 48),
        "DATE": ctx.report_date or DEFAULT_DATE,
        "PAGE_TITLE": shorten(page_title, page_title_limit),
        "PAGE_NUM": str(ctx.page["page_num"]),
        "PAGE_GUIDE_LABEL": derive_page_guide_label(ctx),
        "SECTION_NAME": shorten(ctx.section_name or ctx.page_title, 18),
        "CHAPTER_NUM": f"{chapter_num:02d}",
        "CHAPTER_TITLE": shorten(chapter_title or ctx.page_title, 18 if tuning.compact_cover == 0 else 14),
        "CHAPTER_DESC": shorten(chapter_desc_source, 24 if tuning.compact_cover == 0 else 18),
        "THANK_YOU": "感谢聆听",
        "CLOSING_MESSAGE": shorten(closing_message, 42),
        "CONTACT_INFO": "长亭安全服务团队",
        "COPYRIGHT": f"© {datetime.now().year} Chaitin",
    }


def fill_unknown_placeholders(placeholders: list[str], values: dict[str, str], ctx: PageContext) -> dict[str, str]:
    queue = [
        ctx.core_judgment,
        ctx.page_intent,
        ctx.proof_goal,
        ctx.supporting_evidence,
        "；".join(ctx.semantic_points[:3]),
        ctx.goal,
        page_action_text(ctx),
        ctx.next_relation,
    ]
    queue = [shorten(item, 32) for item in queue if normalize_text(item)]
    if not queue:
        queue = [shorten(ctx.page_title, 28)]
    cursor = 0
    for name in placeholders:
        if name in values:
            continue
        values[name] = queue[cursor % len(queue)]
        cursor += 1
    return values


def replace_placeholders(template_text: str, values: dict[str, str]) -> str:
    placeholders = sorted(set(re.findall(r"{{([A-Z0-9_]+)}}", template_text)))
    for name in placeholders:
        value = values.get(name, "")
        if name == "CONTENT_AREA" and value and "<" in value:
            text_wrapper = re.compile(
                r'<text(?P<attrs>[^>]*)>\s*{{CONTENT_AREA}}\s*</text>',
                flags=re.S,
            )
            if text_wrapper.search(template_text):
                template_text = text_wrapper.sub(value, template_text, count=1)
                continue
        if name not in RAW_PLACEHOLDERS:
            value = escape_xml(value)
        template_text = template_text.replace("{{" + name + "}}", value)
    return template_text


def build_page_context(project_dir: Path, page: dict[str, Any], template_id: str) -> PageContext:
    brief_text = read_text(project_dir / "project_brief.md")
    storyline_text = read_text(project_dir / "notes" / "storyline.md")
    outline_text = read_text(project_dir / "notes" / "page_outline.md")
    page_context_min = read_page_context_min(project_dir, str(page.get("expected_svg") or ""))
    page_payload = page_context_min if isinstance(page_context_min, dict) else {}
    page_brief_text = read_text(Path(page["brief_path"])) if str(page.get("brief_path") or "").strip() else ""
    source_markdown = load_source_markdown(project_dir)

    missing_artifacts = []
    if not brief_text.strip():
        missing_artifacts.append("project_brief.md")
    if not storyline_text.strip():
        missing_artifacts.append("notes/storyline.md")
    if not outline_text.strip():
        missing_artifacts.append("notes/page_outline.md")
    if missing_artifacts:
        joined = ", ".join(missing_artifacts)
        raise ValueError(
            f"执行前置资料缺失：{joined}。请先完成 /plan -> produce，或执行 build_storyline / bootstrap-agent 后再生成 SVG。"
        )

    storyline_sections = parse_storyline_sections(storyline_text)
    outline_entries = parse_outline_entries(outline_text)
    page_brief = parse_page_brief(page_brief_text)
    outline_entry = next((item for item in outline_entries if item.get("page_num") == str(page["page_num"])), {})
    if not storyline_sections:
        raise ValueError("`notes/storyline.md` 未解析到章节规划，不能继续生成页面。")
    if not outline_entries:
        raise ValueError("`notes/page_outline.md` 未解析到页面规划，不能继续生成页面。")
    if not outline_entry:
        raise ValueError(f"`notes/page_outline.md` 缺少第 {page['page_num']} 页定义，不能继续生成页面。")
    complex_model = dict(page_payload.get("complex_model") or {})
    if complex_model:
        model_blockers: list[str] = []
        model_warnings: list[str] = []
    else:
        complex_model, model_blockers, model_warnings = resolve_complex_page_model(project_dir, page)

    template_path = resolve_template_path(template_id, str(page.get("preferred_template") or ""))
    template_text = sync_template_assets(read_text(template_path), template_path, project_dir, template_id)
    metadata_lock = resolve_project_metadata(project_dir, brief_text, source_markdown)
    missing_assets = find_missing_asset_refs(template_text, base_dir=project_dir / "svg_output")
    template_asset_blockers: list[str] = []
    template_asset_warnings: list[str] = []
    for href in missing_assets:
        message = f"模板资源缺失：{href}"
        if str(page.get("page_family") or page.get("execution_policy", {}).get("page_family") or "").strip() == "fixed":
            template_asset_blockers.append(message)
        else:
            template_asset_warnings.append(message)

    raw_project_name = extract_md_value(brief_text, "项目名称") or project_dir.name
    project_name = derive_display_project_name(project_dir, raw_project_name)
    scenario = extract_md_value(brief_text, "场景")
    industry = extract_md_value(brief_text, "行业")
    audience = extract_md_value(brief_text, "主要受众")
    goal = extract_md_value(brief_text, "核心目标")
    desired_action = extract_md_value(brief_text, "期待对方采取的动作")
    format_key = extract_md_value(brief_text, "输出格式") or "ppt169"
    page_title = normalize_text(page["title"])
    section_name = derive_section_name(int(page["page_num"]), storyline_sections, page_title)
    page_role = normalize_text(str(page_payload.get("page_role") or complex_model.get("page_role") or "")) or outline_entry.get("页面角色", "") or page_brief.get("页面角色", "")
    page_intent = normalize_text(str(page_payload.get("page_intent") or complex_model.get("page_intent") or "")) or outline_entry.get("页面意图", "") or page_brief.get("页面意图", "")
    proof_goal = normalize_text(str(page_payload.get("proof_goal") or complex_model.get("proof_goal") or "")) or outline_entry.get("证明目标", "") or page_brief.get("证明目标", "")
    core_judgment = normalize_text(str(page_payload.get("core_judgment") or complex_model.get("main_judgment") or "")) or outline_entry.get("核心判断", "") or page_brief.get("主判断", "")
    evidence_highlights = select_evidence_highlights([str(item) for item in (page_payload.get("evidence_highlights") or [])], limit=4)
    semantic_points = merge_unique_texts(
        evidence_highlights + [str(item) for item in (page_payload.get("semantic_points") or [])],
        limit=12,
    )
    supporting_evidence = normalize_text(str(page_payload.get("supporting_evidence") or ""))
    if not supporting_evidence and evidence_highlights:
        supporting_evidence = "；".join(evidence_highlights)
    refresh_evidence = payload_evidence_needs_refresh(
        semantic_points,
        supporting_evidence,
        evidence_highlights,
    )
    if refresh_evidence:
        source_queries: list[str] = []
        if any(token in page_title for token in ("成果", "关键结果")):
            source_queries.extend(["获取重要成果", "互联网侧攻击路径概述", "内网侧攻击路径概述"])
        if any(token in page_title for token in ("风险总览", "暴露面")):
            source_queries.extend(["整体回顾及成果总结", "互联网侧系统安全检测与防护待加强", "内网系统异常登陆行为审计问题"])
        source_queries.extend(split_points(outline_entry.get("支撑证据", ""), limit=10))
        source_queries.extend(split_points(page_brief.get("支撑证据", ""), limit=10))
        source_queries.extend([page_title, outline_entry.get("页面类型", ""), outline_entry.get("核心判断", "")])
        source_points = collect_source_support_points(project_dir, source_queries, limit=10)
        evidence_highlights = select_evidence_highlights(
            source_points + collect_model_semantic_points(complex_model) + evidence_highlights,
            limit=4,
        )
        semantic_points = merge_unique_texts(
            evidence_highlights + source_points + collect_model_semantic_points(complex_model),
            limit=12,
        )
        supporting_evidence = build_model_supporting_evidence(complex_model, outline_entry, page_brief, source_points)
    else:
        evidence_highlights = select_evidence_highlights(
            evidence_highlights + semantic_points + split_points(supporting_evidence, limit=6),
            limit=4,
        )
    relations = dict(page_payload.get("relations") or {})

    return PageContext(
        project_dir=project_dir,
        page=page,
        template_id=template_id,
        template_path=template_path,
        template_text=template_text,
        project_name=project_name,
        industry=industry,
        scenario=scenario,
        audience=audience,
        goal=goal,
        desired_action=desired_action,
        section_name=section_name,
        page_title=page_title,
        page_role=page_role,
        page_intent=page_intent,
        proof_goal=proof_goal,
        core_judgment=core_judgment,
        supporting_evidence=supporting_evidence,
        evidence_highlights=evidence_highlights,
        complex_model=complex_model,
        semantic_points=semantic_points,
        model_blockers=model_blockers,
        model_warnings=model_warnings,
        prev_relation=normalize_text(str(relations.get("prev_relation") or "")) or page_brief.get("与上一页关系", ""),
        next_relation=normalize_text(str(relations.get("next_relation") or "")) or page_brief.get("与下一页关系", ""),
        storyline_sections=storyline_sections,
        outline_entries=outline_entries,
        format_key=format_key,
        report_date=str(metadata_lock.get("report_date") or DEFAULT_DATE),
        metadata_lock=metadata_lock,
        template_asset_blockers=template_asset_blockers,
        template_asset_warnings=template_asset_warnings,
        execution_events=[],
    )


def build_placeholder_values(ctx: PageContext, tuning: RenderTuning) -> tuple[dict[str, str], str]:
    placeholders = sorted(set(re.findall(r"{{([A-Z0-9_]+)}}", ctx.template_text)))
    values = common_placeholder_map(ctx, tuning)
    renderer = "semantic-placeholder-fill"

    template_name = ctx.template_path.name

    toc_slots = 0
    for name in placeholders:
        match = re.match(r"TOC_ITEM_(\d+)_TITLE", name)
        if match:
            toc_slots = max(toc_slots, int(match.group(1)))
    toc_items = derive_toc_items(ctx, tuning, max_items=toc_slots or 4)
    for idx, item in enumerate(toc_items, start=1):
        values[f"TOC_ITEM_{idx}_TITLE"] = item["title"]
        values[f"TOC_ITEM_{idx}_DESC"] = item["desc"]
        values[f"ITEM_{idx:02d}_TITLE"] = item["title"]
        values[f"ITEM_{idx:02d}_SUBTITLE"] = item["desc"]

    if template_name == "01_cover.svg":
        values["TITLE"] = shorten(ctx.project_name, 26)
        values["SUBTITLE"] = shorten(ctx.scenario or ctx.goal or ctx.core_judgment, 40 if tuning.compact_cover == 0 else 24)
        values["ORG_INFO"] = shorten(ctx.industry or ctx.audience or "长亭安全服务", 36)
        renderer = "fixed-cover-fill"
    elif template_name == "02_toc.svg":
        renderer = "fixed-toc-fill"
    elif template_name == "02_chapter.svg":
        renderer = "fixed-chapter-fill"
    elif template_name == "04_ending.svg":
        renderer = "fixed-ending-fill"

    if "PAGE_SUBTITLE" in placeholders and ctx.template_id == "chaitin":
        values["PAGE_SUBTITLE"] = render_chaitin_page_subtitle(ctx, tuning)
        renderer = "content-template-fill"

    if "CONTENT_AREA" in placeholders:
        if (ctx.page.get("advanced_pattern") or "无") in {"attack_case_chain", "evidence_attached_case_chain"}:
            values["CONTENT_AREA"] = render_attack_chain_content_area(ctx, tuning)
            renderer = "content-area-attack-chain"
        else:
            values["CONTENT_AREA"] = render_standard_content_area(ctx, tuning)
            renderer = "content-area-standard"

    values.update(build_security_service_slot_map(ctx, template_name, tuning))
    values = fill_unknown_placeholders(placeholders, values, ctx)
    return values, renderer


def _build_fit_precheck_quality(svg_path: Path) -> dict[str, Any]:
    return {
        "file": svg_path.name,
        "path": str(svg_path),
        "exists": True,
        "errors": [],
        "warnings": [],
        "issues": [],
        "info": {
            "qa_short_circuit": True,
            "qa_short_circuit_reason": "fit_precheck_failed",
        },
        "blocking_issue_count": 0,
        "passed": False,
    }


def has_low_signal_evidence(ctx: PageContext) -> bool:
    evidence_candidates = []
    evidence_candidates.extend(ctx.evidence_highlights[:4])
    evidence_candidates.extend(ctx.semantic_points[:4])
    evidence_candidates.extend(split_points(ctx.supporting_evidence, limit=4))
    for candidate in evidence_candidates:
        normalized = normalize_text(candidate)
        if not normalized:
            continue
        if contains_planning_tone(normalized):
            return True
        compacted = compact_evidence_sentence(normalized, 14, 1)
        if not compacted:
            return True
        if len(compacted) <= 4:
            return True
        if compacted in {"关键证据", "证据", "风险", "结果", "判断"}:
            return True
    return not bool(ctx.evidence_highlights)


def select_evidence_highlights(candidates: list[str], *, limit: int = 4) -> list[str]:
    evidence_markers = ("thinkphp", "log4j", "webshell", "内存马", "权限", "漏洞", "敏感", "数据库", "服务器", "钓鱼", "rce", "ip", "后台")
    ranked: list[tuple[int, int, str, str]] = []
    seen: set[str] = set()
    for item in candidates:
        compacted = compact_evidence_sentence(item, 22, 1)
        normalized = normalize_text(compacted)
        if not normalized or normalized in seen:
            continue
        if contains_planning_tone(normalized):
            continue
        if len(normalized) <= 4 or normalized in {"关键证据", "证据", "风险", "结果", "判断"}:
            continue
        seen.add(normalized)
        marker_score = sum(2 for marker in evidence_markers if marker in normalized.lower())
        digit_score = 1 if re.search(r"\d", normalized) else 0
        length_score = 1 if len(normalized) >= 8 else 0
        ranked.append((marker_score + digit_score + length_score, len(normalized), normalized, compacted))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[3] for item in ranked[:limit]]


def payload_evidence_needs_refresh(
    semantic_points: list[str],
    supporting_evidence: str,
    evidence_highlights: list[str] | None = None,
) -> bool:
    evidence_markers = ("thinkphp", "log4j", "webshell", "内存马", "权限", "漏洞", "敏感信息", "数据库", "服务器", "钓鱼", "rce", "ip", "后台")
    highlight_points = [normalize_text(item) for item in (evidence_highlights or []) if normalize_text(item)]
    if not semantic_points or not supporting_evidence:
        return True
    if not highlight_points:
        return True
    if contains_planning_tone(supporting_evidence):
        return True
    support_points = split_points(supporting_evidence, limit=4)
    if not support_points:
        return True
    if not any(any(marker in item.lower() for marker in evidence_markers) for item in support_points):
        return True
    weak_support_count = 0
    for item in support_points[:4]:
        compacted = compact_evidence_sentence(item, 14, 1)
        normalized = normalize_text(compacted)
        if not normalized or len(normalized) <= 4 or normalized in {"关键证据", "证据", "风险", "结果", "判断"}:
            weak_support_count += 1
            continue
        if contains_planning_tone(normalized):
            weak_support_count += 1
    if weak_support_count >= len(support_points[:4]):
        return True
    compacted_points = [compact_evidence_sentence(item, 14, 1) for item in semantic_points[:4] if normalize_text(item)]
    if not compacted_points:
        return True
    weak_count = 0
    for item in compacted_points:
        normalized = normalize_text(item)
        if not normalized:
            weak_count += 1
            continue
        if len(normalized) <= 4:
            weak_count += 1
            continue
        if normalized in {"关键证据", "证据", "风险", "结果", "判断"}:
            weak_count += 1
            continue
        if contains_planning_tone(normalized):
            weak_count += 1
    if weak_count >= len(compacted_points):
        return True
    return not any(any(marker in item.lower() for marker in evidence_markers) for item in highlight_points[:4])


def apply_pre_slot_soft_qa(
    ctx: PageContext,
    tuning: RenderTuning,
    page_policy: dict[str, Any],
    signals: list[str],
) -> list[str]:
    if not should_enable_soft_qa(page_policy, signals):
        return []

    applied: list[str] = []
    page_family = str(page_policy.get("page_family") or ctx.page.get("page_family") or "")
    complex_class = str(page_policy.get("complex_class") or "")
    headline_overlap = semantic_overlap_score(ctx.core_judgment or ctx.page_title, ctx.page_title)
    judgment_ready = looks_like_judgment_sentence(ctx.core_judgment)

    if complex_class == "heavy_complex" or "complex_model_warning" in signals or "complex_model_blocker" in signals:
        if tuning.semantic_argument == 0:
            tuning.semantic_argument = 1
            applied.append("首轮先强化复杂页模块标题与论证主线")
        if tuning.semantic_closure == 0:
            tuning.semantic_closure = 1
            applied.append("首轮先把复杂页页尾收束改成动作闭环")

    if "low_signal_evidence" in signals or not ctx.evidence_highlights:
        if tuning.semantic_argument == 0:
            tuning.semantic_argument = 1
            applied.append("首轮优先收紧证据槽位，避免泛化表述进入卡片")
        if tuning.semantic_closure == 0:
            tuning.semantic_closure = 1
            applied.append("首轮直接用证据导向的收束语，减少空泛结论")

    if not judgment_ready or headline_overlap <= 0:
        if tuning.semantic_headline == 0:
            tuning.semantic_headline = 1
            applied.append("首轮先强化主判断 headline，避免标题只复述章节名")

    if page_family == "complex" and "preflight_warning" in signals and tuning.semantic_argument == 0:
        tuning.semantic_argument = 1
        applied.append("首轮先提升复杂页论证结构，降低相邻页表达重叠")

    if applied:
        append_execution_event(
            ctx,
            "pre_slot_soft_qa",
            signals=list(signals),
            actions=list(applied),
            target=ctx.page.get("expected_svg", ctx.page_title),
        )
    return applied


def slot_budget_repaired_keys(repairs: list[str]) -> set[str]:
    keys: set[str] = set()
    for item in repairs:
        key = str(item.split(" 压缩到", 1)[0]).strip()
        if key:
            keys.add(key)
    return keys


def apply_slot_budget_pre_tuning(
    ctx: PageContext,
    tuning: RenderTuning,
    repaired_keys: set[str],
) -> list[str]:
    template_name = ctx.template_path.name
    applied: list[str] = []
    if template_name == "07_data.svg":
        pressure_keys = {"PROOF_HEADLINE", "PROOF_CANVAS", "DATA_NOTE_1", "DATA_NOTE_2", "DATA_NOTE_3"}
        if repaired_keys & pressure_keys and tuning.compact_standard == 0:
            tuning.compact_standard = 1
            applied.append("首轮按槽位预算收紧摘要证明页证据堆栈")
    elif template_name == "05_case.svg":
        pressure_keys = {"CASE_BACKGROUND", "CASE_SOLUTION", "CASE_PROCESS", "CASE_RESULTS", "CASE_CLIENT"}
        if repaired_keys & pressure_keys and tuning.compact_standard == 0:
            tuning.compact_standard = 1
            applied.append("首轮按槽位预算收紧案例页正文与收束区")
    elif template_name == "09_comparison.svg":
        pressure_keys = {
            "COMPARE_HEADLINE",
            "COMPARE_TITLE_A",
            "COMPARE_TITLE_B",
            "COMPARE_CONTENT_A_1",
            "COMPARE_CONTENT_A_2",
            "COMPARE_CONTENT_A_3",
            "COMPARE_CONTENT_A_4",
            "COMPARE_CONTENT_B_1",
            "COMPARE_CONTENT_B_2",
            "COMPARE_CONTENT_B_3",
            "COMPARE_CONTENT_B_4",
            "COMPARE_RESULT",
        }
        if repaired_keys & pressure_keys and tuning.compact_attack_chain == 0:
            tuning.compact_attack_chain = 1
            applied.append("首轮按槽位预算收紧对比链页泳道与结果区")
    elif template_name == "08_product.svg":
        pressure_keys = {"PRODUCT_NAME", "PRODUCT_IMAGE", "PRODUCT_VALUE"}
        if repaired_keys & pressure_keys and tuning.compact_service_map == 0:
            tuning.compact_service_map = 1
            applied.append("首轮按槽位预算收紧根因树页标题与证据区")
    elif template_name == "16_table.svg":
        pressure_keys = {"TABLE_INSIGHT_1", "TABLE_INSIGHT_2", "TABLE_INSIGHT_3", "TABLE_HIGHLIGHT", "CLOSURE_STEP_1", "CLOSURE_STEP_2", "CLOSURE_STEP_3"}
        if repaired_keys & pressure_keys and tuning.compact_matrix == 0:
            tuning.compact_matrix = 1
            applied.append("首轮按槽位预算收紧治理矩阵页右侧判断区")
    elif template_name == "17_service_overview.svg":
        pressure_keys = {
            "OVERVIEW_LEAD",
            "PLATFORM_NAME",
            "PLATFORM_DESC",
            "DOMAIN_ATTACK_TITLE",
            "DOMAIN_ATTACK_DESC",
            "DOMAIN_DEFENSE_TITLE",
            "DOMAIN_DEFENSE_DESC",
            "DOMAIN_TRAINING_TITLE",
            "DOMAIN_TRAINING_DESC",
            "VALUE_1",
            "VALUE_2",
            "VALUE_3",
            "DRIVER_POINT_1",
            "DRIVER_POINT_2",
        }
        if repaired_keys & pressure_keys and tuning.compact_service_map == 0:
            tuning.compact_service_map = 1
            applied.append("首轮按槽位预算收紧服务总览页头部与域卡片")
    elif template_name == "18_domain_capability_map.svg":
        pressure_keys = {
            "METHOD_NOTE",
            "SCENE_POINT_1",
            "SCENE_POINT_2",
            "SCENE_POINT_3",
            "CAPABILITY_1_TITLE",
            "CAPABILITY_2_TITLE",
            "CAPABILITY_3_TITLE",
            "CAPABILITY_4_TITLE",
            "CAPABILITY_1_DESC",
            "CAPABILITY_2_DESC",
            "CAPABILITY_3_DESC",
            "CAPABILITY_4_DESC",
            "OUTCOME_1",
            "OUTCOME_2",
            "OUTCOME_3",
        }
        if repaired_keys & pressure_keys and tuning.compact_service_map == 0:
            tuning.compact_service_map = 1
            applied.append("首轮按槽位预算收紧能力地图页说明区")
    elif template_name == "19_result_leading_case.svg":
        header_keys = {"PAGE_TITLE", "RESULT_HEADLINE", "HEADLINE_SUBLINE", "CLIENT_CONTEXT"}
        body_keys = {"ACTION_1", "ACTION_2", "ACTION_3", "RESULT_1", "RESULT_2", "RESULT_3", "CLOSURE_1", "CLOSURE_2", "CLOSURE_3"}
        if repaired_keys & header_keys and tuning.compact_header_bundle == 0:
            tuning.compact_header_bundle = 1
            applied.append("首轮按槽位预算收紧案例链页头部")
        if repaired_keys & body_keys and tuning.compact_attack_chain == 0:
            tuning.compact_attack_chain = 1
            applied.append("首轮按槽位预算收紧案例链节点与收束区")
    return applied


def preflight_slot_budget_contract(
    ctx: PageContext,
    tuning: RenderTuning,
) -> tuple[list[str], list[str], list[str]]:
    normalized_repairs: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    seen_repairs: set[str] = set()
    for _ in range(3):
        values, _ = build_placeholder_values(ctx, tuning)
        _, repairs, blockers, warnings = apply_slot_budget_contract(ctx, values, tuning)
        for item in repairs[:10]:
            line = f"按槽位预算预压缩：{item}"
            if line not in seen_repairs:
                normalized_repairs.append(line)
                seen_repairs.add(line)
        tuning_repairs = apply_slot_budget_pre_tuning(ctx, tuning, slot_budget_repaired_keys(repairs))
        if not tuning_repairs:
            break
        for item in tuning_repairs:
            line = f"按槽位预算预收紧：{item}"
            if line not in seen_repairs:
                normalized_repairs.append(line)
                seen_repairs.add(line)
    return normalized_repairs[:10], blockers[:8], warnings[:8]


def collect_soft_qa_signals(
    ctx: PageContext,
    page_policy: dict[str, Any],
    *,
    fit_issues: list[str] | None = None,
    quality: dict[str, Any] | None = None,
    round_index: int | None = None,
) -> list[str]:
    signals: list[str] = []
    if ctx.model_blockers:
        signals.append("complex_model_blocker")
    if ctx.model_warnings:
        signals.append("complex_model_warning")
    if page_policy.get("preflight_warnings"):
        signals.append("preflight_warning")
    if has_low_signal_evidence(ctx):
        signals.append("low_signal_evidence")
    if any(event.get("type") in {"semantic_argument_rewrite", "semantic_headline_rewrite", "semantic_closure_rewrite"} for event in ctx.execution_events):
        signals.append("semantic_auto_rewrite")
    if fit_issues and round_index == 1:
        signals.append("first_round_text_fit")
    if quality is not None and round_index == 1:
        if int(quality.get("blocking_issue_count", 0) or 0) > 0 or not bool(quality.get("passed", False)):
            signals.append("first_round_quality")
    deduped: list[str] = []
    seen: set[str] = set()
    for signal in signals:
        if signal in seen:
            continue
        seen.add(signal)
        deduped.append(signal)
    return deduped


def should_enable_soft_qa(page_policy: dict[str, Any], signals: list[str]) -> bool:
    mode = str(page_policy.get("soft_qa_mode") or "never")
    if mode == "always":
        return True
    if mode == "on_signal":
        return bool(signals)
    return False


def _filter_quality_by_tier(quality: dict[str, Any], qa_tier: str, *, soft_qa_enabled: bool) -> dict[str, Any]:
    if qa_tier == "complex_full" and soft_qa_enabled:
        return quality

    ignored_codes = set()
    if not soft_qa_enabled:
        ignored_codes.update(SOFT_QA_CODES)
    if qa_tier in {"brand_skeleton", "layout_and_density"}:
        ignored_codes.update(
            {
                *SOFT_QA_CODES,
            }
        )
    if qa_tier == "brand_skeleton":
        ignored_codes.update({"dense_content", "chinese_readability", "line_break_punctuation"})

    filtered = dict(quality)
    filtered_issues: list[dict[str, Any]] = []
    for issue in quality.get("issues", []) or []:
        code = str(issue.get("code") or "")
        if code in ignored_codes:
            continue
        filtered_issues.append(issue)

    filtered["issues"] = filtered_issues
    filtered["errors"] = [
        str(issue.get("message") or "")
        for issue in filtered_issues
        if str(issue.get("severity") or "").lower() == "error"
    ]
    filtered["warnings"] = [
        str(issue.get("message") or "")
        for issue in filtered_issues
        if str(issue.get("severity") or "").lower() != "error"
    ]
    filtered["blocking_issue_count"] = sum(1 for issue in filtered_issues if issue.get("blocking"))
    filtered["passed"] = len(filtered["errors"]) == 0 and filtered["blocking_issue_count"] == 0
    info = dict(filtered.get("info") or {})
    info["qa_tier_applied"] = qa_tier
    filtered["info"] = info
    return filtered


def run_single_page_checks(
    svg_path: Path,
    ctx: PageContext,
    *,
    page_policy: dict[str, Any],
    soft_qa_enabled: bool,
    checker: SVGQualityChecker | None = None,
) -> tuple[list[str], dict[str, Any], SVGQualityChecker | None, dict[str, int]]:
    check_started = time.perf_counter()
    text_fit_started = time.perf_counter()
    fit_issues = check_svg(svg_path)
    text_fit_ms = elapsed_ms(text_fit_started)
    qa_tier = str(page_policy.get("qa_tier") or "complex_full")

    # Fixed / standard pages first consume the cheap text-fit gate.
    # If layout is already broken, skip the heavier semantic checker for this round.
    if fit_issues and qa_tier != "complex_full":
        return (
            fit_issues,
            _build_fit_precheck_quality(svg_path),
            checker,
            {
                "text_fit_ms": text_fit_ms,
                "quality_ms": 0,
                "total_ms": elapsed_ms(check_started),
            },
        )

    if checker is None:
        checker = SVGQualityChecker(str(ctx.project_dir / "design_spec.md"))
    quality_started = time.perf_counter()
    quality = checker.check_file(str(svg_path), expected_format=ctx.format_key)
    quality_ms = elapsed_ms(quality_started)
    quality = _filter_quality_by_tier(quality, qa_tier, soft_qa_enabled=soft_qa_enabled)
    return (
        fit_issues,
        quality,
        checker,
        {
            "text_fit_ms": text_fit_ms,
            "quality_ms": quality_ms,
            "total_ms": elapsed_ms(check_started),
        },
    )


def render_preview_snapshot(
    svg_path: Path,
    ctx: PageContext,
    round_index: int,
) -> tuple[Path, str]:
    preview_dir = ctx.project_dir / "visual_qc" / svg_path.parent.name
    preview_path = preview_dir / f"{svg_path.stem}.r{round_index:02d}.png"
    preview_dir.mkdir(parents=True, exist_ok=True)
    try:
        render_svg_preview(svg_path, preview_path, 2.0)
    except Exception as exc:
        return preview_path, f"{type(exc).__name__}: {exc}"
    return preview_path, ""


def render_page(ctx: PageContext, tuning: RenderTuning) -> tuple[str, str]:
    placeholder_values, renderer = build_placeholder_values(ctx, tuning)
    placeholder_values, slot_repairs, slot_blockers, slot_warnings = apply_slot_budget_contract(
        ctx,
        placeholder_values,
        tuning,
    )
    if slot_repairs or slot_blockers or slot_warnings:
        append_execution_event(
            ctx,
            "slot_budget_compaction",
            repairs=list(slot_repairs[:12]),
            blockers=list(slot_blockers[:8]),
            warnings=list(slot_warnings[:8]),
            target=ctx.page.get("expected_svg", ctx.page_title),
        )
    svg_text = replace_placeholders(ctx.template_text, placeholder_values)
    if ctx.template_path.name in {
        "05_case.svg",
        "07_data.svg",
        "09_comparison.svg",
        "08_product.svg",
        "12_grid.svg",
        "16_table.svg",
        "17_service_overview.svg",
        "18_domain_capability_map.svg",
        "19_result_leading_case.svg",
    }:
        renderer = f"structured-template-fill:{ctx.template_path.name}"
    svg_text = postprocess_rendered_svg(ctx, svg_text, tuning, placeholder_values)
    if not svg_text.endswith("\n"):
        svg_text += "\n"
    return svg_text, renderer


def issue_codes(quality: dict[str, Any]) -> set[str]:
    return {str(item.get("code", "")) for item in (quality.get("issues") or []) if item.get("code")}


def fit_issue_mentions_rect(fit_issues: list[str], rect_signature: str) -> bool:
    return any(rect_signature in issue for issue in fit_issues)


def apply_repair_rules(
    ctx: PageContext,
    tuning: RenderTuning,
    fit_issues: list[str],
    quality: dict[str, Any],
    *,
    allow_runtime_progression_reframe: bool = False,
) -> list[str]:
    applied: list[str] = []
    codes = issue_codes(quality)

    if "complex_page_argument_cohesion" in codes:
        tuning.semantic_argument += 1
        tuning.semantic_closure = max(tuning.semantic_closure, 1)
        append_execution_event(
            ctx,
            "semantic_argument_rewrite",
            issue_code="complex_page_argument_cohesion",
            target=ctx.page.get("expected_svg", ctx.page_title),
        )
        applied.append("按主判断重写模块标题并同步页尾收束")

    if "adjacent_complex_progression" in codes and allow_runtime_progression_reframe:
        progression_repairs = apply_adjacent_progression_reframe(ctx)
        if progression_repairs:
            tuning.progression_reframe += 1
            tuning.semantic_argument = max(tuning.semantic_argument, 1)
            tuning.semantic_headline = max(tuning.semantic_headline, 1)
            applied.extend(progression_repairs)

    template_name = ctx.template_path.name

    if (
        template_name == "17_service_overview.svg"
        and "长亭安服价值" in ctx.page_title
        and codes & {"complex_page_structure", "complex_page_headline"}
    ):
        reframed = apply_template_reframe(
            ctx,
            new_template="18_domain_capability_map.svg",
            reason="价值总览页需要能力地图式闭环表达，切换为分域能力地图骨架",
            issue_code="complex_page_structure",
        )
        if reframed:
            tuning.compact_service_map = max(tuning.compact_service_map, 1)
            applied.extend(reframed)
            template_name = ctx.template_path.name

    if (
        template_name == "17_service_overview.svg"
        and normalize_pattern_token(str(ctx.page.get("advanced_pattern") or "")) == "attack_tree_architecture"
        and codes & {"complex_page_structure", "complex_page_argument_cohesion"}
    ):
        reframed = apply_template_reframe(
            ctx,
            new_template="08_product.svg",
            reason="服务总览骨架难以承载根因拆解，切换为根因树骨架承接凭证治理问题",
            issue_code="complex_page_structure",
        )
        if reframed:
            tuning.compact_service_map = max(tuning.compact_service_map, 1)
            applied.extend(reframed)
            template_name = ctx.template_path.name

    if template_name == "19_result_leading_case.svg":
        is_evidence_overview_case = attack_track_type(ctx.page_title) == "overview" and any(
            token in ctx.page_title for token in ("证据", "证明", "总览")
        )
        if "complex_page_headline" in codes:
            tuning.semantic_headline += 1
            append_execution_event(
                ctx,
                "semantic_headline_rewrite",
                issue_code="complex_page_headline",
                target=ctx.page.get("expected_svg", ctx.page_title),
            )
            applied.append("弱化页头标题并重新强化主判断 headline")
        if "complex_page_closure" in codes:
            tuning.semantic_closure += 1
            append_execution_event(
                ctx,
                "semantic_closure_rewrite",
                issue_code="complex_page_closure",
                target=ctx.page.get("expected_svg", ctx.page_title),
            )
            applied.append("改写底部收束语为整改/复测动作")
        headline_pressure = fit_issue_mentions_rect(fit_issues, "rect (60,182,760,82)")
        overview_header_compacted = False
        if "complex_page_argument_cohesion" in codes and is_evidence_overview_case:
            tuning.compact_header_bundle += 1
            applied.append("概览型案例链页同步压缩主判断标题")
            overview_header_compacted = True
        if not overview_header_compacted and (codes & {"headline_bundle_collision", "top_stack_collision"} or headline_pressure):
            tuning.compact_header_bundle += 1
            applied.append("压缩攻击链页头部标题组")
        elif codes & {"edge_pressure_card", "card_overflow"} and len(normalize_text(ctx.core_judgment or ctx.page_title)) > 18:
            if not is_evidence_overview_case:
                tuning.compact_header_bundle += 1
                applied.append("继续压缩攻击链页主判断标题")
        chain_compact_codes = {"card_overflow", "dense_content", "template_safe_area", "logo_safe_zone"}
        if fit_issues or codes & chain_compact_codes or (not is_evidence_overview_case and "edge_pressure_card" in codes):
            tuning.compact_attack_chain += 1
            applied.append("压缩攻击链节点文案并收紧证据轨")
    elif template_name in {"12_grid.svg", "16_table.svg"}:
        if fit_issues or codes & {"card_overflow", "edge_pressure_card", "dense_content", "template_safe_area"}:
            tuning.compact_matrix += 1
            applied.append("压缩矩阵页表格字段并收紧决策栏")
    elif template_name in {"08_product.svg", "17_service_overview.svg", "18_domain_capability_map.svg"}:
        if fit_issues or codes & {"card_overflow", "edge_pressure_card", "dense_content", "template_safe_area", "logo_safe_zone"}:
            tuning.compact_service_map += 1
            applied.append("压缩能力地图页域描述并收紧底部驱动条")
    elif template_name == "02_toc.svg":
        if fit_issues or codes & {"toc_consistency", "card_overflow", "edge_pressure_card"}:
            tuning.compact_toc += 1
            applied.append("统一目录页副标题并收紧目录卡片字号")
    elif template_name in {"01_cover.svg", "02_chapter.svg", "04_ending.svg"}:
        if fit_issues or codes & {"headline_bundle_collision", "top_stack_collision", "edge_pressure_card"}:
            tuning.compact_cover += 1
            applied.append("压缩固定页标题组与说明文案")
    else:
        if fit_issues or codes & {"card_overflow", "edge_pressure_card", "dense_content", "takeaway_separation", "template_safe_area", "logo_safe_zone"}:
            tuning.compact_standard += 1
            applied.append("压缩正文卡片并拉开 takeaway 与正文间距")

    return applied


def evaluate_render_outcome(
    fit_issues: list[str],
    quality: dict[str, Any],
    *,
    preview_error: str = "",
) -> tuple[str, int, bool]:
    blocking_count = int(quality.get("blocking_issue_count", 0) or 0)
    if preview_error:
        if "SVG preview renderer unavailable" in preview_error:
            preview_error = ""
        else:
            return "blocked", max(1, blocking_count), False
    passed = not fit_issues and blocking_count == 0 and bool(quality.get("passed", False))
    return ("generated" if passed else "qa_failed"), blocking_count, passed


def summarize_tuning(tuning: RenderTuning) -> str:
    items = [
        ("cover", tuning.compact_cover),
        ("toc", tuning.compact_toc),
        ("standard", tuning.compact_standard),
        ("matrix", tuning.compact_matrix),
        ("service_map", tuning.compact_service_map),
        ("attack_chain", tuning.compact_attack_chain),
        ("header_bundle", tuning.compact_header_bundle),
        ("semantic_headline", tuning.semantic_headline),
        ("semantic_closure", tuning.semantic_closure),
        ("semantic_argument", tuning.semantic_argument),
        ("progression_reframe", tuning.progression_reframe),
    ]
    active = [f"{name}={value}" for name, value in items if value > 0]
    return "未触发压缩调优" if not active else " / ".join(active)


def summarize_execution_events(events: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for event in events:
        event_type = str(event.get("type") or "")
        if event_type == "progression_reframe":
            lines.append(
                f"- progression_reframe：第 {event.get('slide_num')} 页从 `{event.get('from_pattern')}` / `{event.get('from_template')}` "
                f"切换为 `{event.get('to_pattern')}` / `{event.get('to_template')}`；同步产物：{', '.join(event.get('synced_artifacts') or []) or '无'}"
            )
        elif event_type == "semantic_argument_rewrite":
            lines.append(f"- semantic_argument_rewrite：命中 `{event.get('issue_code')}`，已重写模块标题与页尾收束")
        elif event_type == "semantic_headline_rewrite":
            lines.append(f"- semantic_headline_rewrite：命中 `{event.get('issue_code')}`，已强化主判断 headline")
        elif event_type == "semantic_closure_rewrite":
            lines.append(f"- semantic_closure_rewrite：命中 `{event.get('issue_code')}`，已改写页尾收束语")
        elif event_type == "slot_budget_compaction":
            lines.append(
                f"- slot_budget_compaction：首轮出图前已按槽位预算压缩字段；动作：{'；'.join(event.get('repairs') or []) or '无'}"
            )
        elif event_type == "pre_slot_soft_qa":
            lines.append(
                f"- pre_slot_soft_qa：首轮出图前已前移软性语义修正；动作：{'；'.join(event.get('actions') or []) or '无'}"
            )
    return lines


def build_execution_trace(
    ctx: PageContext,
    output_path: Path,
    report_path: Path,
    attempts: list[dict[str, Any]],
    tuning: RenderTuning,
    auto_repair_enabled: bool,
    max_auto_repair_rounds: int,
    status: str,
    *,
    input_fingerprint: str,
    timing: dict[str, int],
) -> dict[str, Any]:
    page_policy = resolve_page_execution_policy(ctx.page)
    repair_rounds_used = sum(1 for item in attempts if item.get("applied_repairs"))
    event_type_counts: dict[str, int] = {}
    for event in ctx.execution_events:
        event_type = str(event.get("type") or "other")
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

    normalized_attempts: list[dict[str, Any]] = []
    for attempt in attempts:
        quality = dict(attempt.get("quality") or {})
        normalized_attempts.append(
            {
                "round": attempt.get("round"),
                "renderer": attempt.get("renderer"),
                "status": attempt.get("status"),
                "text_fit_issue_count": attempt.get("text_fit_issue_count"),
                "blocking_issue_count": attempt.get("blocking_issue_count"),
                "quality_passed": attempt.get("quality_passed"),
                "preview_path": attempt.get("preview_path"),
                "preview_error": attempt.get("preview_error"),
                "soft_qa_enabled": bool(attempt.get("soft_qa_enabled", False)),
                "soft_qa_signals": list(attempt.get("soft_qa_signals") or []),
                "pre_slot_repairs": list(attempt.get("pre_slot_repairs") or []),
                "tuning_summary": attempt.get("tuning_summary"),
                "applied_repairs": list(attempt.get("applied_repairs") or []),
                "repair_stop_reason": attempt.get("repair_stop_reason") or "",
                "timing": dict(attempt.get("timing") or {}),
                "issue_codes": [
                    str(item.get("code", ""))
                    for item in (quality.get("issues") or [])
                    if item.get("code")
                ],
            }
        )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "page": str(ctx.page.get("expected_svg") or ""),
        "page_num": str(ctx.page.get("page_num") or ""),
        "page_title": ctx.page_title,
        "status": status,
        "output": str(output_path),
        "report": str(report_path),
        "template_id": ctx.template_id,
        "template_name": ctx.template_path.name,
        "advanced_pattern": str(ctx.page.get("advanced_pattern") or "无"),
        "preferred_template": str(ctx.page.get("preferred_template") or ctx.template_path.name),
        "execution_policy": page_policy,
        "auto_repair_enabled": auto_repair_enabled,
        "max_auto_repair_rounds": max_auto_repair_rounds,
        "auto_repair_rounds_used": repair_rounds_used,
        "input_fingerprint": input_fingerprint,
        "cache_hit": False,
        "timing": timing,
        "tuning_summary": summarize_tuning(tuning),
        "attempt_count": len(attempts),
        "attempts": normalized_attempts,
        "execution_events": ctx.execution_events,
        "event_type_counts": event_type_counts,
        "model_blockers": ctx.model_blockers,
        "model_warnings": ctx.model_warnings,
    }


def render_report(
    ctx: PageContext,
    output_path: Path,
    attempts: list[dict[str, Any]],
    tuning: RenderTuning,
    auto_repair_enabled: bool,
    max_auto_repair_rounds: int,
    status: str,
    *,
    input_fingerprint: str,
    timing: dict[str, int],
) -> str:
    page_policy = resolve_page_execution_policy(ctx.page)
    final_attempt = attempts[-1]
    final_renderer = str(final_attempt.get("renderer", ""))
    fit_issues = list(final_attempt.get("fit_issues") or [])
    quality = dict(final_attempt.get("quality") or {})
    preview_path = str(final_attempt.get("preview_path") or "")
    preview_error = str(final_attempt.get("preview_error") or "")
    repair_rounds_used = sum(1 for item in attempts if item.get("applied_repairs"))
    issue_lines = []
    for issue in fit_issues[:8]:
        issue_lines.append(f"- text_fit: {issue}")
    for issue in (quality.get("issues") or [])[:8]:
        issue_lines.append(
            f"- {issue.get('severity')}: {issue.get('code')} - {issue.get('message')}"
        )
    if not issue_lines:
        issue_lines.append("- 当前自动检查未发现阻塞项。")
    if preview_error:
        issue_lines.append(f"- preview_render: {preview_error}")

    if not auto_repair_enabled:
        repair_summary = "已关闭自动修复，仅执行单轮渲染与检查。"
    elif repair_rounds_used == 0 and status == "generated":
        repair_summary = "首轮已通过，无需自动修复。"
    elif repair_rounds_used == 0:
        repair_summary = "已开启自动修复，但当前问题未命中可自动修复规则。"
    elif status == "generated":
        repair_summary = f"共执行 {repair_rounds_used} 轮自动修复后通过。"
    else:
        repair_summary = f"共执行 {repair_rounds_used} 轮自动修复后，当前仍未通过。"

    attempt_lines: list[str] = []
    for attempt in attempts:
        attempt_lines.extend(
            [
                f"### 第 {attempt['round']} 轮",
                f"- 渲染器：`{attempt['renderer']}`",
                f"- 状态：`{attempt['status']}`",
                f"- text_fit_issue_count：{attempt['text_fit_issue_count']}",
                f"- blocking_issue_count：{attempt['blocking_issue_count']}",
                f"- quality_passed：{attempt['quality_passed']}",
                f"- preview：`{attempt.get('preview_path') or '未生成'}`",
                f"- soft_qa_enabled：{bool(attempt.get('soft_qa_enabled', False))}",
                f"- soft_qa_signals：{'；'.join(attempt.get('soft_qa_signals') or []) or '无'}",
                f"- pre_slot_repairs：{'；'.join(attempt.get('pre_slot_repairs') or []) or '无'}",
                f"- 本轮调优：{attempt['tuning_summary']}",
                f"- 耗时：render={format_duration_ms((attempt.get('timing') or {}).get('render_ms', 0))} / "
                f"text_fit={format_duration_ms((attempt.get('timing') or {}).get('text_fit_ms', 0))} / "
                f"quality={format_duration_ms((attempt.get('timing') or {}).get('quality_ms', 0))} / "
                f"preview={format_duration_ms((attempt.get('timing') or {}).get('preview_ms', 0))} / "
                f"repair={format_duration_ms((attempt.get('timing') or {}).get('repair_ms', 0))} / "
                f"total={format_duration_ms((attempt.get('timing') or {}).get('total_ms', 0))}",
            ]
        )
        preview_error_text = str(attempt.get("preview_error") or "")
        if preview_error_text:
            attempt_lines.append(f"- preview_error：{preview_error_text}")
        applied_repairs = attempt.get("applied_repairs") or []
        if applied_repairs:
            attempt_lines.append(f"- 已应用修复：{'；'.join(applied_repairs)}")
        stop_reason = str(attempt.get("repair_stop_reason") or "")
        if stop_reason:
            attempt_lines.append(f"- 停止原因：{stop_reason}")
        if attempt is not attempts[-1]:
            attempt_lines.append("")

    model_lines = [
        f"- 高级正文模式：{ctx.page.get('advanced_pattern') or '无'}",
        f"- 模型标题：{ctx.complex_model.get('heading', '未命中复杂页模型') if ctx.complex_model else '未命中复杂页模型'}",
        f"- model_blocker_count：{len(ctx.model_blockers)}",
        f"- model_warning_count：{len(ctx.model_warnings)}",
    ]
    if ctx.semantic_points:
        model_lines.append(f"- 语义抽取：{'；'.join(ctx.semantic_points[:6])}")
    if ctx.model_blockers:
        model_lines.extend(f"- blocker: {item}" for item in ctx.model_blockers[:8])
    if ctx.model_warnings:
        model_lines.extend(f"- warning: {item}" for item in ctx.model_warnings[:8])
    event_lines = summarize_execution_events(ctx.execution_events)
    if not event_lines:
        event_lines = ["- 本页未触发需要沉淀的自动重构 / 自动修复事件。"]

    notes = [
        "- 这一步已由脚本直接写出当前页 SVG，不再只是停留在 prompt / context pack。",
        "- 但当前仍属于“可用 starter 页面 + 自动检查”，不是最终软性质量完全自动闭环。",
    ]
    if final_renderer == "complex-model-gate":
        notes = [
            "- 当前页在进入绘制前先经过复杂页语义门禁，本轮因模型质量不足被拦截。",
            "- 修补 `notes/complex_page_models.md` 后，再重新进入当前页渲染。",
        ]

    return "\n".join(
        [
            "# 当前页自动执行报告",
            "",
            f"- 页面：`{ctx.page['expected_svg']}`",
            f"- 模板：`{ctx.template_id}` / `{ctx.template_path.name}`",
            f"- 最终渲染器：`{final_renderer}`",
            f"- 执行通道：`{page_policy.get('render_lane', 'unknown')}` / QA=`{page_policy.get('qa_tier', 'unknown')}`",
            f"- Preview 策略：`{page_policy.get('preview_strategy', 'always')}`",
            f"- Soft QA：`{page_policy.get('soft_qa_mode', 'never')}`",
            f"- 输出：`{output_path}`",
            f"- Preview：`{preview_path or '未生成'}`",
            f"- 自动状态建议：`{status}`",
            "",
            "## 页面上下文",
            f"- 标题：{ctx.page_title}",
            f"- 页面角色：{ctx.page_role or '待补齐'}",
            f"- 页面意图：{ctx.page_intent or '待补齐'}",
            f"- 证明目标：{ctx.proof_goal or '待补齐'}",
            f"- 主判断：{ctx.core_judgment or '待补齐'}",
            f"- 支撑证据：{ctx.supporting_evidence or '待补齐'}",
            f"- 高价值证据摘要：{'；'.join(ctx.evidence_highlights[:4]) or '待补齐'}",
            f"- 模板稳定度：{page_policy.get('template_stability', 'unknown')}",
            f"- 前置阻断：{'；'.join(page_policy.get('preflight_blockers') or []) or '无'}",
            f"- 预警：{'；'.join(page_policy.get('preflight_warnings') or []) or '无'}",
            "",
            "## 复杂页语义门禁",
            *model_lines,
            "",
            "## 自动检查",
            f"- text_fit_issue_count：{len(fit_issues)}",
            f"- blocking_issue_count：{quality.get('blocking_issue_count', 0)}",
            f"- quality_passed：{quality.get('passed', False)}",
            f"- preview_render_error：{preview_error or '无'}",
            f"- auto_repair_enabled：{auto_repair_enabled}",
            f"- max_auto_repair_rounds：{max_auto_repair_rounds}",
            f"- layout_locked：{page_policy.get('layout_locked', True)}",
            f"- 自动修复结论：{repair_summary}",
            f"- 输入指纹：`{input_fingerprint[:12]}`",
            f"- 总耗时：{format_duration_ms(timing.get('total_ms', 0))}",
            f"- 上下文构建：{format_duration_ms(timing.get('context_ms', 0))}",
            f"- 预检耗时：{format_duration_ms(timing.get('preflight_ms', 0))}",
            f"- 写报告：{format_duration_ms(timing.get('report_write_ms', 0))}",
            f"- 写轨迹：{format_duration_ms(timing.get('trace_write_ms', 0))}",
            f"- 汇总刷新：{format_duration_ms(timing.get('summary_write_ms', 0))}",
            f"- 最终调优：{summarize_tuning(tuning)}",
            "",
            "## 自动修复 / 重构轨迹",
            *event_lines,
            "",
            "## 轮次记录",
            *attempt_lines,
            "",
            "## 发现",
            *issue_lines,
            "",
            "## 说明",
            *notes,
        ]
    ) + "\n"


def command_render(args: argparse.Namespace) -> None:
    command_started = time.perf_counter()
    project_dir = Path(args.project_path).expanduser().resolve()
    state, paths = load_or_init_state(project_dir)
    state = sync_state_with_files(state, project_dir)
    if args.page:
        page = find_page(state, args.page)
    else:
        page = next_actionable_page(state)
    if page is None:
        raise SystemExit("当前没有可执行页面。")

    template_id = detect_template_id(project_dir)
    if not template_id:
        raise SystemExit("未识别到模板，请先确认 project_brief / template recommendation。")

    context_started = time.perf_counter()
    page_policy = resolve_page_execution_policy(page)
    ctx = build_page_context(project_dir, page, template_id)
    output_path = project_dir / "svg_output" / page["expected_svg"]
    report_dir = project_dir / "notes" / "page_execution"
    report_path = report_dir / page["expected_svg"].replace(".svg", ".md")
    trace_path = report_dir / page["expected_svg"].replace(".svg", ".json")
    auto_repair_enabled = not args.no_auto_repair
    if args.max_auto_repair_rounds is None:
        max_auto_repair_rounds = max(0, int(page_policy.get("default_auto_repair_rounds", 1) or 0))
    else:
        max_auto_repair_rounds = max(0, int(args.max_auto_repair_rounds))
    input_fingerprint = build_page_input_fingerprint(
        ctx,
        page_policy,
        auto_repair_enabled=auto_repair_enabled,
        max_auto_repair_rounds=max_auto_repair_rounds,
    )
    context_ms = elapsed_ms(context_started)
    current_status = str(page.get("status") or "")
    if current_status not in {"qa_failed", "blocked"} and not getattr(args, "force", False):
        reusable_trace = load_reusable_success_trace(
            trace_path,
            output_path,
            input_fingerprint=input_fingerprint,
        )
        if reusable_trace:
            reusable_status = "completed" if str(page.get("status") or "") == "completed" else "generated"
            page["execution_policy"] = page_policy
            page["status"] = reusable_status
            page["last_update"] = datetime.now().isoformat(timespec="seconds")
            page["note"] = args.note or f"命中页面缓存；复用已通过 QA 的现有出图（inputs={input_fingerprint[:12]}）"
            if reusable_status == "completed":
                if state.get("current_page") == page["expected_svg"]:
                    state["current_page"] = ""
                state["overall_status"] = "ready"
            else:
                state["current_page"] = page["expected_svg"]
                state["overall_status"] = "in_progress"
            save_state_bundle(state, project_dir, paths)
            append_log(
                paths["log"],
                f"{page['expected_svg']} 命中页面缓存 -> {reusable_status}（inputs={input_fingerprint[:12]}）",
            )
            last_attempt = (reusable_trace.get("attempts") or [{}])[-1]
            summary = {
                "page": page["expected_svg"],
                "output": str(output_path),
                "report": str(report_path),
                "trace": str(trace_path),
                "renderer": str(last_attempt.get("renderer") or reusable_trace.get("template_name") or ""),
                "status": reusable_status,
                "execution_policy": page_policy,
                "preview": str(last_attempt.get("preview_path") or ""),
                "text_fit_issue_count": int(last_attempt.get("text_fit_issue_count", 0) or 0),
                "blocking_issue_count": int(last_attempt.get("blocking_issue_count", 0) or 0),
                "attempt_count": int(reusable_trace.get("attempt_count", 0) or 0),
                "auto_repair_enabled": auto_repair_enabled,
                "auto_repair_rounds_used": int(reusable_trace.get("auto_repair_rounds_used", 0) or 0),
                "tuning": str(reusable_trace.get("tuning_summary") or ""),
                "execution_event_count": len(reusable_trace.get("execution_events") or []),
                "execution_event_types": sorted((reusable_trace.get("event_type_counts") or {}).keys()),
                "model_blockers": reusable_trace.get("model_blockers") or [],
                "model_warnings": reusable_trace.get("model_warnings") or [],
                "cache_hit": True,
                "skipped_render": True,
                "input_fingerprint": input_fingerprint,
                "timing": dict(reusable_trace.get("timing") or {}),
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return

    tuning = RenderTuning()
    seen_signatures: set[tuple[int, ...]] = set()
    attempts: list[dict[str, Any]] = []
    status = "qa_failed"
    blocking_count = 0
    checker: SVGQualityChecker | None = None
    soft_qa_signals = collect_soft_qa_signals(ctx, page_policy)
    soft_qa_enabled = should_enable_soft_qa(page_policy, soft_qa_signals)

    page["attempts"] = int(page.get("attempts", 0)) + 1
    page["status"] = "in_progress"
    page["last_update"] = datetime.now().isoformat(timespec="seconds")
    state["current_page"] = page["expected_svg"]
    state["overall_status"] = "in_progress"
    page["execution_policy"] = page_policy

    preflight_started = time.perf_counter()
    if _coerce_bool(page_policy.get("allow_preflight_progression_reframe")):
        preflight_repairs = apply_adjacent_progression_reframe(ctx)
        if preflight_repairs:
            ctx = build_page_context(project_dir, page, template_id)
            page_policy = resolve_page_execution_policy(ctx.page)
            page["execution_policy"] = page_policy
            soft_qa_signals = collect_soft_qa_signals(ctx, page_policy)
            soft_qa_enabled = should_enable_soft_qa(page_policy, soft_qa_signals)

    pre_slot_repairs = apply_pre_slot_soft_qa(ctx, tuning, page_policy, soft_qa_signals)
    slot_budget_repairs, slot_budget_blockers, slot_budget_warnings = preflight_slot_budget_contract(ctx, tuning)
    if slot_budget_repairs:
        pre_slot_repairs.extend(slot_budget_repairs)
    seen_signatures.add(tuning.signature())

    preflight_blockers = list(page_policy.get("preflight_blockers") or [])
    preflight_warnings = list(page_policy.get("preflight_warnings") or [])
    preflight_blockers.extend(slot_budget_blockers)
    preflight_warnings.extend(slot_budget_warnings)
    if ctx.template_asset_blockers:
        preflight_blockers.extend(ctx.template_asset_blockers)
    if ctx.template_asset_warnings:
        preflight_warnings.extend(ctx.template_asset_warnings)
    page_policy["preflight_blockers"] = preflight_blockers
    page_policy["preflight_warnings"] = preflight_warnings
    if preflight_blockers:
        blocking_count = len(preflight_blockers)
        status = "blocked"
        attempts.append(
            {
                "round": 0,
                "renderer": "preflight-layout-gate",
                "status": status,
                "text_fit_issue_count": 0,
                "blocking_issue_count": blocking_count,
                "quality_passed": False,
                "fit_issues": [],
                "quality": {
                    "passed": False,
                    "blocking_issue_count": blocking_count,
                    "issues": [
                        {
                            "severity": "error",
                            "code": "preflight_layout_repetition",
                            "message": item,
                            "blocking": True,
                        }
                        for item in preflight_blockers
                    ] + [
                        {
                            "severity": "warning",
                            "code": "preflight_layout_warning",
                            "message": item,
                            "blocking": False,
                        }
                        for item in preflight_warnings[:8]
                    ],
                },
                "applied_repairs": [],
                "tuning_summary": summarize_tuning(tuning),
                "preview_path": "",
                "preview_error": "",
                "soft_qa_enabled": soft_qa_enabled,
                "soft_qa_signals": list(soft_qa_signals),
                "pre_slot_repairs": list(pre_slot_repairs),
                "timing": {"total_ms": 0},
                "repair_stop_reason": "当前页命中前置重复布局硬规则，已阻止进入渲染。",
            }
        )

    if not attempts and is_complex_page(page) and ctx.model_blockers:
        blocking_count = len(ctx.model_blockers)
        status = "blocked"
        attempts.append(
            {
                "round": 0,
                "renderer": "complex-model-gate",
                "status": status,
                "text_fit_issue_count": 0,
                "blocking_issue_count": blocking_count,
                "quality_passed": False,
                "fit_issues": [],
                "quality": {
                    "passed": False,
                    "blocking_issue_count": blocking_count,
                    "issues": [
                        {
                            "severity": "error",
                            "code": "complex_model_blocked",
                            "message": item,
                        }
                        for item in ctx.model_blockers
                    ] + [
                        {
                            "severity": "warning",
                            "code": "complex_model_warning",
                            "message": item,
                        }
                        for item in ctx.model_warnings[:8]
                    ],
                },
                "applied_repairs": [],
                "tuning_summary": summarize_tuning(tuning),
                "preview_path": "",
                "preview_error": "",
                "soft_qa_enabled": soft_qa_enabled,
                "soft_qa_signals": list(soft_qa_signals),
                "pre_slot_repairs": list(pre_slot_repairs),
                "timing": {"total_ms": 0},
                "repair_stop_reason": "复杂页建模未通过当前页门禁，已阻止进入渲染。",
            }
        )

    preflight_ms = elapsed_ms(preflight_started)
    if not attempts:
        total_attempt_limit = 1 if not auto_repair_enabled else 1 + max_auto_repair_rounds
        for round_index in range(1, total_attempt_limit + 1):
            attempt_started = time.perf_counter()
            render_started = time.perf_counter()
            svg_text, renderer = render_page(ctx, tuning)
            render_ms = elapsed_ms(render_started)
            write_started = time.perf_counter()
            write_text(output_path, svg_text)
            write_svg_ms = elapsed_ms(write_started)

            fit_issues, quality, checker, check_timing = run_single_page_checks(
                output_path,
                ctx,
                page_policy=page_policy,
                soft_qa_enabled=soft_qa_enabled,
                checker=checker,
            )
            preview_path: Path | None = None
            preview_error = ""
            preview_ms = 0
            preview_strategy = str(page_policy.get("preview_strategy") or "always")
            preview_required = preview_strategy == "always"
            if not preview_required:
                preview_required = bool(fit_issues) or int(quality.get("blocking_issue_count", 0) or 0) > 0
            if preview_required:
                preview_started = time.perf_counter()
                preview_path, preview_error = render_preview_snapshot(output_path, ctx, round_index)
                preview_ms = elapsed_ms(preview_started)
            evaluate_started = time.perf_counter()
            status, blocking_count, passed = evaluate_render_outcome(
                fit_issues,
                quality,
                preview_error=preview_error,
            )
            evaluate_ms = elapsed_ms(evaluate_started)
            round_soft_qa_signals = collect_soft_qa_signals(
                ctx,
                page_policy,
                fit_issues=fit_issues,
                quality=quality,
                round_index=round_index,
            )
            attempts.append(
                {
                    "round": round_index,
                    "renderer": renderer,
                    "status": status,
                    "text_fit_issue_count": len(fit_issues),
                    "blocking_issue_count": blocking_count,
                    "quality_passed": bool(quality.get("passed", False)),
                    "fit_issues": fit_issues[:8],
                    "quality": quality,
                    "applied_repairs": [],
                    "tuning_summary": summarize_tuning(tuning),
                    "preview_path": str(preview_path) if preview_path else "",
                    "preview_error": preview_error,
                    "soft_qa_enabled": soft_qa_enabled,
                    "soft_qa_signals": list(round_soft_qa_signals),
                    "pre_slot_repairs": list(pre_slot_repairs) if round_index == 1 else [],
                    "timing": {
                        "render_ms": render_ms,
                        "write_svg_ms": write_svg_ms,
                        "text_fit_ms": int(check_timing.get("text_fit_ms", 0) or 0),
                        "quality_ms": int(check_timing.get("quality_ms", 0) or 0),
                        "preview_ms": preview_ms,
                        "evaluate_ms": evaluate_ms,
                        "repair_ms": 0,
                        "total_ms": 0,
                    },
                }
            )
            if passed:
                attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)
                break
            if status == "blocked":
                attempts[-1]["repair_stop_reason"] = "当前页 preview 渲染失败或被页级门禁阻断。"
                attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)
                break
            soft_qa_signals = round_soft_qa_signals
            soft_qa_enabled = should_enable_soft_qa(page_policy, soft_qa_signals)
            if not auto_repair_enabled or round_index >= total_attempt_limit:
                attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)
                break

            previous_signature = tuning.signature()
            repair_started = time.perf_counter()
            applied_repairs = apply_repair_rules(
                ctx,
                tuning,
                fit_issues,
                quality,
                allow_runtime_progression_reframe=_coerce_bool(
                    page_policy.get("allow_runtime_progression_reframe")
                ),
            )
            attempts[-1]["applied_repairs"] = applied_repairs
            attempts[-1]["timing"]["repair_ms"] = elapsed_ms(repair_started)
            new_signature = tuning.signature()
            if not applied_repairs:
                if "adjacent_complex_progression" in issue_codes(quality):
                    attempts[-1]["repair_stop_reason"] = "当前页命中相邻复杂页重构建议，但当前执行策略已冻结 render 阶段骨架切换。"
                    attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)
                    break
                attempts[-1]["repair_stop_reason"] = "当前问题未命中可自动修复规则。"
                attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)
                break
            if new_signature == previous_signature:
                attempts[-1]["repair_stop_reason"] = "自动修复未产生新的调优参数。"
                attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)
                break
            if new_signature in seen_signatures:
                attempts[-1]["repair_stop_reason"] = "自动修复进入重复调优，停止继续重试。"
                attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)
                break
            seen_signatures.add(new_signature)
            attempts[-1]["timing"]["total_ms"] = elapsed_ms(attempt_started)

    attempt_stage_totals = summarize_attempt_stage_totals(attempts)
    timing_summary = {
        "context_ms": context_ms,
        "preflight_ms": preflight_ms,
        "attempt_total_ms": attempt_stage_totals["total_ms"],
        "report_write_ms": 0,
        "trace_write_ms": 0,
        "summary_write_ms": 0,
        "total_ms": 0,
    }

    timing_summary["total_ms"] = elapsed_ms(command_started)
    report_write_started = time.perf_counter()
    write_text(
        report_path,
        render_report(
            ctx,
            output_path,
            attempts,
            tuning,
            auto_repair_enabled,
            max_auto_repair_rounds,
            status,
            input_fingerprint=input_fingerprint,
            timing=timing_summary,
        ),
    )
    timing_summary["report_write_ms"] = elapsed_ms(report_write_started)
    timing_summary["total_ms"] = elapsed_ms(command_started)
    # Keep finalization to a single report/trace/summary write sequence to avoid
    # self-referential rewrites that add latency without changing render output.
    trace = build_execution_trace(
        ctx,
        output_path,
        report_path,
        attempts,
        tuning,
        auto_repair_enabled,
        max_auto_repair_rounds,
        status,
        input_fingerprint=input_fingerprint,
        timing=timing_summary,
    )
    trace_write_started = time.perf_counter()
    write_text(trace_path, json.dumps(trace, ensure_ascii=False, indent=2) + "\n")
    timing_summary["trace_write_ms"] = elapsed_ms(trace_write_started)
    summary_write_started = time.perf_counter()
    write_project_timing_summary(project_dir)
    timing_summary["summary_write_ms"] = elapsed_ms(summary_write_started)
    timing_summary["total_ms"] = elapsed_ms(command_started)

    page["status"] = status
    page["last_update"] = datetime.now().isoformat(timespec="seconds")
    repair_rounds_used = sum(1 for item in attempts if item.get("applied_repairs"))
    page_event_types = sorted({str(event.get("type") or "") for event in ctx.execution_events if event.get("type")})
    page["note"] = args.note or (
        "独立执行器已处理当前页；"
        f"status={status}, blocking={blocking_count}, text_fit={attempts[-1]['text_fit_issue_count']}, "
        f"attempts={len(attempts)}, auto_repair_rounds={repair_rounds_used}, lane={page_policy.get('render_lane', 'unknown')}, "
        f"total_ms={timing_summary['total_ms']}"
        + (f", events={','.join(page_event_types)}" if page_event_types else "")
    )
    page["advanced_pattern"] = str(ctx.page.get("advanced_pattern") or page.get("advanced_pattern") or "无")
    page["preferred_template"] = str(ctx.page.get("preferred_template") or page.get("preferred_template") or "")
    page["page_family"] = str(ctx.page.get("page_family") or page.get("page_family") or "")
    page["brief_path"] = str(ctx.page.get("brief_path") or page.get("brief_path") or "")
    if ctx.execution_events:
        page["last_execution_events"] = ctx.execution_events[-6:]
    state["current_page"] = page["expected_svg"]
    state["overall_status"] = "in_progress"
    save_state_bundle(state, project_dir, paths)
    append_log(
        paths["log"],
        f"{page['expected_svg']} 使用独立执行器出图 -> {status}"
        f"（轮次={len(attempts)}，自动修复={repair_rounds_used}，总耗时={format_duration_ms(timing_summary['total_ms'])}）",
    )
    for line in summarize_execution_events(ctx.execution_events):
        append_log(paths["log"], f"{page['expected_svg']} {line.lstrip('- ').strip()}")

    summary = {
        "page": page["expected_svg"],
        "output": str(output_path),
        "report": str(report_path),
        "trace": str(trace_path),
        "renderer": attempts[-1]["renderer"],
        "status": status,
        "execution_policy": page_policy,
        "preview": attempts[-1].get("preview_path", ""),
        "text_fit_issue_count": attempts[-1]["text_fit_issue_count"],
        "blocking_issue_count": blocking_count,
        "attempt_count": len(attempts),
        "auto_repair_enabled": auto_repair_enabled,
        "auto_repair_rounds_used": repair_rounds_used,
        "tuning": summarize_tuning(tuning),
        "execution_event_count": len(ctx.execution_events),
        "execution_event_types": page_event_types,
        "model_blockers": ctx.model_blockers,
        "model_warnings": ctx.model_warnings,
        "cache_hit": False,
        "input_fingerprint": input_fingerprint,
        "timing": timing_summary,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="为当前页直接生成 starter SVG，并做即时 QA 快照。")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--force", action="store_true", help="忽略页面缓存，强制重跑当前页渲染")
    parser.add_argument("--page", default="", help="可选：页码、页面标题或 SVG 文件名")
    parser.add_argument("--note", default="", help="写入执行状态的备注")
    parser.add_argument(
        "--max-auto-repair-rounds",
        type=int,
        default=None,
        help="可选覆盖默认自动修复轮数；未指定时按页面执行策略决定",
    )
    parser.add_argument(
        "--no-auto-repair",
        action="store_true",
        help="关闭 QA 失败后的自动修复与重渲染",
    )
    parser.set_defaults(func=command_render)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
