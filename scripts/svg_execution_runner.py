#!/usr/bin/env python3
"""Stateful SVG execution runner for ppt-master."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from build_svg_execution_pack import (
        PAGE_CONTEXT_DIRNAME,
        build_page_brief_text,
        build_svg_execution_pack,
        execution_policy,
        expected_svg_name,
        page_family,
        parse_design_spec_pages,
        prepare_execution_pages,
        qa_focus,
    )
except ImportError:
    import sys

    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from build_svg_execution_pack import (  # type: ignore
        PAGE_CONTEXT_DIRNAME,
        build_page_brief_text,
        build_svg_execution_pack,
        execution_policy,
        expected_svg_name,
        page_family,
        parse_design_spec_pages,
        prepare_execution_pages,
        qa_focus,
    )


STATE_FILENAME = "svg_execution_state.json"
CURRENT_BUNDLE_FILENAME = "svg_current_bundle.md"
CURRENT_TASK_FILENAME = "svg_current_task.md"
CURRENT_PROMPT_FILENAME = "svg_current_prompt.md"
CURRENT_CONTEXT_PACK_FILENAME = "svg_current_context_pack.md"
CURRENT_REVIEW_FILENAME = "svg_current_review.md"
LOG_FILENAME = "svg_execution_log.md"
STATUS_FILENAME = "svg_generation_status.md"
ALLOWED_STATUSES = {"pending", "in_progress", "generated", "qa_failed", "blocked", "completed"}
FINALIZE_GATE_HINT = (
    "当前全部页面已完成，可进入 finalize / export / QA；但是否允许导出，"
    "以 `ppt_agent.py status <project_path>` 或 `project_manager.py validate <project_path>` 的 export gate 为准。"
)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def remove_path_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    prefix = f"- {now_iso()}："
    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")
    else:
        content = "# SVG 执行日志\n\n"
    content += f"{prefix}{message}\n"
    log_path.write_text(content, encoding="utf-8")


def build_state(project_dir: Path) -> dict[str, Any]:
    design_spec_path = project_dir / "design_spec.md"
    if not design_spec_path.exists():
        raise FileNotFoundError(f"design_spec.md not found: {design_spec_path}")

    build_svg_execution_pack(project_dir)
    pages = prepare_execution_pages(parse_design_spec_pages(design_spec_path))
    page_items: list[dict[str, Any]] = []
    for page in pages:
        expected_name = expected_svg_name(page)
        policy = execution_policy(page)
        preflight_blockers = list(page.get("preflight_blockers") or [])
        page_items.append(
            {
                "page_num": page["page_num"],
                "title": page["title"],
                "expected_svg": expected_name,
                "page_family": page_family(page),
                "preferred_template": page.get("preferred_template", ""),
                "advanced_pattern": page.get("advanced_pattern", "无"),
                "qa_focus": qa_focus(page),
                "template_stability": page.get("template_stability", ""),
                "preflight_blockers": preflight_blockers,
                "preflight_warnings": list(page.get("preflight_warnings") or []),
                "execution_policy": policy,
                "brief_path": str(project_dir / "notes" / "page_briefs" / expected_name.replace(".svg", ".md")),
                "context_min_path": str(page_context_min_path(project_dir, expected_name)),
                "status": "blocked" if preflight_blockers else "pending",
                "attempts": 0,
                "last_update": now_iso(),
                "note": f"预检阻断：{preflight_blockers[0]}" if preflight_blockers else "",
            }
        )
    return {
        "version": 1,
        "project_path": str(project_dir),
        "started_at": now_iso(),
        "updated_at": now_iso(),
        "overall_status": "ready",
        "current_page": "",
        "pages": page_items,
    }


def state_paths(project_dir: Path) -> dict[str, Path]:
    notes_dir = project_dir / "notes"
    return {
        "state": notes_dir / STATE_FILENAME,
        "current_bundle": notes_dir / CURRENT_BUNDLE_FILENAME,
        "current_task": notes_dir / CURRENT_TASK_FILENAME,
        "current_prompt": notes_dir / CURRENT_PROMPT_FILENAME,
        "current_context": notes_dir / CURRENT_CONTEXT_PACK_FILENAME,
        "current_review": notes_dir / CURRENT_REVIEW_FILENAME,
        "log": notes_dir / LOG_FILENAME,
        "status_md": notes_dir / STATUS_FILENAME,
    }


def load_or_init_state(project_dir: Path, *, force: bool = False) -> tuple[dict[str, Any], dict[str, Path]]:
    paths = state_paths(project_dir)
    if force or not paths["state"].exists():
        state = build_state(project_dir)
    else:
        state = read_json(paths["state"])
        if not state:
            state = build_state(project_dir)
    return state, paths


def sync_state_with_files(state: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    design_spec_path = project_dir / "design_spec.md"
    refreshed_pages = prepare_execution_pages(parse_design_spec_pages(design_spec_path))
    old_page_map = {str(page.get("expected_svg") or ""): page for page in state.get("pages", [])}
    merged_pages: list[dict[str, Any]] = []
    for page in refreshed_pages:
        expected_name = expected_svg_name(page)
        policy = execution_policy(page)
        previous = old_page_map.get(expected_name, {})
        preflight_blockers = list(page.get("preflight_blockers") or [])
        note = str(previous.get("note") or "")
        if preflight_blockers:
            note = f"预检阻断：{preflight_blockers[0]}"
        elif note.startswith("预检阻断："):
            note = ""
        merged_pages.append(
            {
                "page_num": page["page_num"],
                "title": page["title"],
                "expected_svg": expected_name,
                "page_family": page_family(page),
                "preferred_template": page.get("preferred_template", ""),
                "advanced_pattern": page.get("advanced_pattern", "无"),
                "qa_focus": qa_focus(page),
                "template_stability": page.get("template_stability", ""),
                "preflight_blockers": preflight_blockers,
                "preflight_warnings": list(page.get("preflight_warnings") or []),
                "execution_policy": policy,
                "brief_path": str(project_dir / "notes" / "page_briefs" / expected_name.replace(".svg", ".md")),
                "context_min_path": str(page_context_min_path(project_dir, expected_name)),
                "status": str(previous.get("status") or ("blocked" if preflight_blockers else "pending")),
                "attempts": int(previous.get("attempts", 0) or 0),
                "last_update": str(previous.get("last_update") or now_iso()),
                "note": note,
            }
        )
    state["pages"] = merged_pages

    svg_output = project_dir / "svg_output"
    svg_final = project_dir / "svg_final"
    for page in state.get("pages", []):
        page["page_family"] = page_family(page)
        page["execution_policy"] = execution_policy(page)
        final_exists = (svg_final / page["expected_svg"]).exists()
        output_exists = (svg_output / page["expected_svg"]).exists()
        final_path = svg_final / page["expected_svg"]
        output_path = svg_output / page["expected_svg"]
        current_status = page.get("status", "pending")
        if final_exists:
            if output_exists and current_status in {"generated", "qa_failed", "blocked"}:
                try:
                    state_ts = 0.0
                    try:
                        state_ts = datetime.fromisoformat(str(page.get("last_update", ""))).timestamp()
                    except ValueError:
                        state_ts = 0.0
                    latest_work_ts = max(output_path.stat().st_mtime, state_ts)
                    if latest_work_ts >= final_path.stat().st_mtime:
                        page["status"] = current_status
                    else:
                        page["status"] = "completed"
                except OSError:
                    page["status"] = current_status
            elif current_status in {"qa_failed", "blocked"}:
                try:
                    state_ts = datetime.fromisoformat(str(page.get("last_update", ""))).timestamp()
                except ValueError:
                    state_ts = 0.0
                try:
                    if state_ts >= final_path.stat().st_mtime:
                        page["status"] = current_status
                    else:
                        page["status"] = "completed"
                except OSError:
                    page["status"] = current_status
            else:
                page["status"] = "completed"
        elif output_exists:
            if current_status in {"in_progress", "generated", "qa_failed", "blocked", "completed"}:
                page["status"] = current_status
            else:
                page["status"] = "generated"
        elif page.get("preflight_blockers"):
            page["status"] = "blocked"
            page["note"] = f"预检阻断：{(page.get('preflight_blockers') or [''])[0]}"
        elif current_status not in ALLOWED_STATUSES:
            page["status"] = "pending"
        elif not page.get("preflight_blockers") and str(page.get("note") or "").startswith("预检阻断："):
            page["note"] = ""
        page["last_update"] = now_iso()

    pending = [page for page in state.get("pages", []) if page["status"] in {"pending", "in_progress", "generated", "qa_failed", "blocked"}]
    if not pending:
        state["overall_status"] = "completed"
        state["current_page"] = ""
    else:
        in_progress = next((page for page in state["pages"] if page["status"] == "in_progress"), None)
        if in_progress:
            state["overall_status"] = "in_progress"
            state["current_page"] = in_progress["expected_svg"]
        else:
            next_page = next_actionable_page(state)
            state["overall_status"] = "ready" if next_page else "completed"
            state["current_page"] = next_page["expected_svg"] if next_page else ""
    state["updated_at"] = now_iso()
    return state


def next_actionable_page(state: dict[str, Any]) -> dict[str, Any] | None:
    for page in state.get("pages", []):
        if page["status"] == "in_progress":
            return page
    for status in ("qa_failed", "blocked", "pending", "generated"):
        for page in state.get("pages", []):
            if page["status"] == status:
                return page
    return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def page_context_min_path(project_dir: Path, expected_svg: str) -> Path:
    return project_dir / "notes" / PAGE_CONTEXT_DIRNAME / f"{expected_svg.replace('.svg', '')}.json"


def read_page_context_min(project_dir: Path, expected_svg: str) -> dict[str, Any]:
    path = page_context_min_path(project_dir, expected_svg)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def extract_block_by_heading(text: str, heading_pattern: str, next_heading_pattern: str) -> str:
    match = re.search(
        rf"(?ms)^{heading_pattern}\s*$\n(.*?)(?=^{next_heading_pattern}\s*$|\Z)",
        text,
    )
    if not match:
        return ""
    return match.group(0).strip()


def extract_page_outline_block(project_dir: Path, page_num: str) -> str:
    text = read_text(project_dir / "notes" / "page_outline.md")
    return extract_block_by_heading(text, rf"##\s+第\s+{page_num}\s+页", r"##\s+第\s+\d+\s+页")


def extract_design_spec_page_block(project_dir: Path, page_num: str, title: str) -> str:
    text = read_text(project_dir / "design_spec.md")
    block = extract_block_by_heading(
        text,
        rf"####\s+第\s*{page_num}\s*页\s*{re.escape(title)}",
        r"####\s+第\s*\d+\s*页.+",
    )
    if block:
        return block
    return extract_block_by_heading(
        text,
        rf"####\s+第\s*{page_num}\s*页.+",
        r"####\s+第\s*\d+\s*页.+",
    )


def extract_complex_model_block(project_dir: Path, page_num: str, title: str) -> str:
    text = read_text(project_dir / "notes" / "complex_page_models.md")
    if not text:
        return ""
    block = extract_block_by_heading(
        text,
        rf"####\s+第\s*{page_num}\s*页\s*{re.escape(title)}",
        r"####\s+第\s*\d+\s*页.+",
    )
    if block:
        return block
    return extract_block_by_heading(
        text,
        rf"####\s+{re.escape(title)}",
        r"####\s+.+",
    )


def detect_template_id(project_dir: Path) -> str:
    text = "\n".join(
        [
            read_text(project_dir / "project_brief.md"),
            read_text(project_dir / "notes" / "template_domain_recommendation.md"),
        ]
    )
    lower = text.lower()
    if "security_service" in lower or "长亭安服" in text:
        return "security_service"
    if "chaitin" in lower or "长亭通用墨绿色" in text:
        return "chaitin"
    return ""


def template_doc_paths(template_id: str) -> list[str]:
    if template_id == "security_service":
        base = "/Users/ciondlin/skills/ppt-master/templates/layouts/security_service"
        return [
            f"{base}/design_spec.md",
            f"{base}/qa_profile.md",
            f"{base}/advanced_page_patterns.md",
            f"{base}/complex_graph_semantics.md",
            f"{base}/complex_case_chain_modeling.md",
            f"{base}/soft_content_qa_framework.md",
        ]
    if template_id == "chaitin":
        base = "/Users/ciondlin/skills/ppt-master/templates/layouts/chaitin"
        return [
            f"{base}/design_spec.md",
            f"{base}/qa_profile.md",
            f"{base}/generation_checklist.md",
            f"{base}/ppt_logic_reference.md",
            f"{base}/text_prompt_snippets.md",
        ]
    return []


def template_display_name(template_id: str) -> str:
    if template_id == "security_service":
        return "长亭安服"
    if template_id == "chaitin":
        return "长亭通用墨绿色"
    return "通用模板"


def strip_primary_heading(markdown: str) -> str:
    lines = markdown.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def render_current_prompt_markdown(state: dict[str, Any], project_dir: Path) -> str:
    current = next_actionable_page(state)
    if current is None:
        return "\n".join(
            [
                "# 当前 SVG 执行 Prompt",
                "",
                FINALIZE_GATE_HINT,
            ]
        ) + "\n"

    complex_needed = current.get("page_family") == "complex" or (current.get("advanced_pattern") or "无") not in {"", "无", "none"}
    lines = [
        "# 当前 SVG 执行 Prompt",
        "",
        f"当前只处理这一页：`{current['expected_svg']}`。",
        "",
        "## 最短执行指令",
        f"- 页面标题：{current['title']}",
        f"- 输出路径：`{project_dir / 'svg_output' / current['expected_svg']}`",
        f"- 执行总包：`{project_dir / 'notes' / CURRENT_BUNDLE_FILENAME}`",
        f"- QA 卡：`{project_dir / 'notes' / 'svg_current_review.md'}`",
        f"- 兼容上下文包：`{project_dir / 'notes' / 'svg_current_context_pack.md'}`",
        "",
        "## 执行要求",
        "1. 默认先读 `svg_current_bundle.md`；若需要拆分视图，再回到 `svg_current_context_pack.md`。",
        "2. 只生成当前页；完成后立即按 `svg_current_review.md` 做当页门禁。",
        "3. 若缺字段，再回退全量文档；不要默认重读整份设计文档。",
        "4. 若通过，优先用 `svg-exec complete` 自动推进下一页。",
        "",
        "## 推荐命令",
        "```bash",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec render {project_dir} --page {current['expected_svg']}",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec complete {project_dir} --page {current['expected_svg']} --note \"本页已通过 QA\"",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status qa_failed --note \"需要继续修正\"",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status blocked --note \"规划层信息不足\"",
        "```",
    ]
    if complex_needed:
        lines.extend(
            [
                "",
                "## 复杂页附加要求",
                "- 先确认复杂页建模完整，再开始画图。",
                "- 结构、证据、主判断不成立时，不得硬画复杂图。",
            ]
        )
    return "\n".join(lines) + "\n"


def render_current_bundle_markdown(state: dict[str, Any], project_dir: Path) -> str:
    current = next_actionable_page(state)
    if current is None:
        return "\n".join(
            [
                "# 当前 SVG 执行总包",
                "",
                FINALIZE_GATE_HINT,
            ]
        ) + "\n"

    task_panel = strip_primary_heading(render_current_task_markdown(state, project_dir))
    prompt_panel = strip_primary_heading(render_current_prompt_markdown(state, project_dir))
    context_panel = strip_primary_heading(render_current_context_pack_markdown(state, project_dir))
    lines = [
        "# 当前 SVG 执行总包",
        "",
        "这份 bundle 是当前页执行主入口；默认先读这份，再按需要打开独立 QA 卡。",
        "",
        f"- 当前页：`{current['expected_svg']}`",
        f"- QA 卡：`{project_dir / 'notes' / CURRENT_REVIEW_FILENAME}`",
        f"- 兼容视图：`{project_dir / 'notes' / CURRENT_TASK_FILENAME}` / "
        f"`{project_dir / 'notes' / CURRENT_PROMPT_FILENAME}` / "
        f"`{project_dir / 'notes' / CURRENT_CONTEXT_PACK_FILENAME}`",
        "",
        "## 1. 当前任务",
        "",
        task_panel,
        "",
        "## 2. 执行 Prompt",
        "",
        prompt_panel,
        "",
        "## 3. 最小上下文包",
        "",
        context_panel,
    ]
    return "\n".join(lines).strip() + "\n"


def render_current_context_pack_markdown(state: dict[str, Any], project_dir: Path) -> str:
    current = next_actionable_page(state)
    if current is None:
        return "\n".join(
            [
                "# 当前 SVG 执行上下文包",
                "",
                FINALIZE_GATE_HINT,
            ]
        ) + "\n"

    page_context = read_page_context_min(project_dir, current["expected_svg"])
    page_brief = read_text(Path(current["brief_path"])).strip()
    template_id = detect_template_id(project_dir)
    template_docs = template_doc_paths(template_id)
    complex_needed = current.get("page_family") == "complex" or (current.get("advanced_pattern") or "无") not in {"", "无", "none"}
    template_rules = dict(page_context.get("template_rules") or {})
    previous_neighbor = dict((page_context.get("neighbors") or {}).get("previous") or {})
    next_neighbor = dict((page_context.get("neighbors") or {}).get("next") or {})
    relations = dict(page_context.get("relations") or {})
    complex_model = dict(page_context.get("complex_model") or {})

    lines = [
        "# 当前 SVG 执行上下文包",
        "",
        "请按下面这份最小执行包完成当前页 SVG 生成与当页 QA；除非缺字段，不要回退到整份上下文原文。",
        "",
        "## 当前页任务",
        f"- 项目路径：`{project_dir}`",
        f"- 当前页：`{current['expected_svg']}`",
        f"- 输出目标：`{project_dir / 'svg_output' / current['expected_svg']}`",
        f"- 页面标题：{current['title']}",
        f"- 页面家族：`{current['page_family']}`",
        f"- 优先页型：`{current.get('preferred_template') or '待补齐'}`",
        f"- 高级正文模式：{current.get('advanced_pattern') or '无'}",
        f"- 当前状态：`{current.get('status')}`",
        f"- 尝试次数：{current.get('attempts', 0)}",
        f"- QA 重点：{current.get('qa_focus') or '待补齐'}",
        f"- 最小上下文：`{current.get('context_min_path') or page_context_min_path(project_dir, current['expected_svg'])}`",
        "",
        "## 必读输入文件",
        f"- `/Users/ciondlin/skills/ppt-master/references/executor-base.md`",
        f"- `/Users/ciondlin/skills/ppt-master/references/executor-visual-review.md`",
        f"- `{current.get('context_min_path') or page_context_min_path(project_dir, current['expected_svg'])}`",
        f"- `{current['brief_path']}`",
    ]
    if not page_context:
        lines.append(f"- `{project_dir / 'design_spec.md'}`")
    if complex_needed and not complex_model:
        lines.append(f"- `{project_dir / 'notes' / 'complex_page_models.md'}`")
    if template_docs:
        lines.extend(["", "## 推荐补读模板文档"])
        lines.extend(f"- `{path}`" for path in template_docs)

    lines.extend(
        [
            "",
            "## 执行动作",
            "1. 先用最小上下文锁定当前页的页面意图、证明目标、主判断、证据和邻页关系。",
            "2. 再用 page brief 确认当前页执行提醒与 QA 重点。",
            "3. 如果当前页是复杂页，必须先确认复杂页建模块完整，再开始画图。",
            f"4. 生成 `{current['expected_svg']}` 到 `svg_output/`。",
            "5. 当页完成后，立即按 executor visual review 的 8 项门禁做自检并修正。",
            "6. 若通过当页检查，将状态更新为 `generated` 或 `completed`；若失败，则更新为 `qa_failed` 或 `blocked`。",
            "",
            "## 状态回写命令",
            "```bash",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status generated --note \"当前页已出图，待复核\"",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status completed --note \"当前页已通过 QA\"",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status qa_failed --note \"需要继续修正\"",
            f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec next {project_dir}",
            "```",
        ]
    )

    lines.extend(
        [
            "",
            "## 当前页最小上下文",
            "",
            f"- 页面角色：{page_context.get('page_role') or current.get('page_role') or '待补齐'}",
            f"- 页面意图：{page_context.get('page_intent') or '待补齐'}",
            f"- 证明目标：{page_context.get('proof_goal') or '待补齐'}",
            f"- 主判断：{page_context.get('core_judgment') or '待补齐'}",
            f"- 支撑证据：{page_context.get('supporting_evidence') or '待补齐'}",
            f"- 高价值证据摘要：{'；'.join(page_context.get('evidence_highlights') or []) or '待补齐'}",
            f"- 与上一页关系：{relations.get('prev_relation') or '无'}",
            f"- 与下一页关系：{relations.get('next_relation') or '无'}",
        ]
    )

    lines.extend(
        [
            "",
            "## 邻页摘要",
            "",
            f"- 上一页：{previous_neighbor.get('page_num') or '-'} / {previous_neighbor.get('title') or '无'} / {previous_neighbor.get('summary') or '无'}",
            f"- 下一页：{next_neighbor.get('page_num') or '-'} / {next_neighbor.get('title') or '无'} / {next_neighbor.get('summary') or '无'}",
        ]
    )

    lines.extend(
        [
            "",
            "## 模板规则摘要",
            "",
            f"- 执行通道：`{template_rules.get('render_lane') or (current.get('execution_policy') or {}).get('render_lane', '未指定')}`",
            f"- QA 层级：`{template_rules.get('qa_tier') or (current.get('execution_policy') or {}).get('qa_tier', '未指定')}`",
            f"- Soft QA：`{template_rules.get('soft_qa_mode') or (current.get('execution_policy') or {}).get('soft_qa_mode', '未指定')}`",
            f"- 模板稳定度：`{template_rules.get('template_stability') or current.get('template_stability') or '未指定'}`",
            f"- 复杂页分级：`{template_rules.get('complex_class') or (current.get('execution_policy') or {}).get('complex_class', '未指定')}`",
            f"- Preview 策略：`{template_rules.get('preview_strategy') or (current.get('execution_policy') or {}).get('preview_strategy', '未指定')}`",
            f"- 预警：{'；'.join(template_rules.get('preflight_warnings') or []) or '无'}",
        ]
    )

    lines.extend(["", "## 当前页 Brief（人工提醒）", "", page_brief or "待补齐"])
    if complex_needed:
        lines.extend(
            [
                "",
                "## 当前页 Complex Model 摘要",
                "",
                json.dumps(complex_model, ensure_ascii=False, indent=2) if complex_model else "待补齐",
            ]
        )
    if not page_context:
        lines.extend(
            [
                "",
                "## 回退说明",
                "",
                "当前缺少最小上下文包，执行器会回退读取 `design_spec.md` / `complex_page_models.md` 等全量文件。",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def render_current_review_markdown(state: dict[str, Any], project_dir: Path) -> str:
    current = next_actionable_page(state)
    if current is None:
        return "\n".join(
            [
                "# 当前页 QA 审核卡",
                "",
                FINALIZE_GATE_HINT,
            ]
        ) + "\n"

    template_id = detect_template_id(project_dir)
    template_name = template_display_name(template_id)
    complex_needed = current.get("page_family") == "complex" or (current.get("advanced_pattern") or "无") not in {"", "无", "none"}
    family_label = {
        "fixed": "固定骨架页",
        "standard": "常规正文页",
        "complex": "复杂正文页",
    }.get(current.get("page_family"), "正文页")

    soft_judgment_line = "文案是否像成熟安服顾问在做判断，而不是把原文缩写后贴上来"
    if template_id == "chaitin":
        soft_judgment_line = "文案是否像长亭正式品牌表达，而不是模板化空话或报告摘抄"

    lines = [
        "# 当前页 QA 审核卡",
        "",
        "这份卡片用于当前页出图后的当页审核。不要等整套导出后才看这些问题。",
        "",
        "## 当前页信息",
        f"- 当前页：`{current['expected_svg']}`",
        f"- 页面标题：{current['title']}",
        f"- 模板：`{template_name}`",
        f"- 页面家族：`{family_label}`",
        f"- 优先页型：`{current.get('preferred_template') or '待补齐'}`",
        f"- 高级正文模式：`{current.get('advanced_pattern') or '无'}`",
        f"- QA 重点：{current.get('qa_focus') or '待补齐'}",
        "",
        "## A. 硬性版式门",
        "- 品牌骨架 / Logo / 页码 / 装饰条 / 安全区：pass / fix / blocked",
        "- 中文断句与可读性：pass / fix",
        "- 贴边感 / 拥挤感 / 模块呼吸空间：pass / fix",
        "- 卡片内文本溢出风险 / 注释碰撞 / 模块重叠：pass / fix",
        "- takeaway / 摘要条 与下层正文是否打架：pass / fix",
        "- 信息密度是否仍可讲，而不是像截图文档：pass / fix",
        "- 同家族页面的一致性是否维持：pass / fix",
        "",
        "## B. 软性内容门",
        "- 这一页的页面角色是否清楚：概览 / 推进 / 证明 / 收束",
        "- 主判断能否一句话说清，并且与标题一致",
        f"- {soft_judgment_line}",
        "- 图形 / 流程 / 证据是否真的支撑主判断，而不是只是把元素摆复杂",
        "- 术语是否准确，有无错词、自造词、黑话或不合逻辑命名",
        "- 这一页是否在为下一页做推进，而不是内容堆砌后戛然而止",
        "",
        "## C. 当前页结论规则",
        "- 命中 `blocked`：说明规划层信息不够、主判断不成立、复杂页建模不完整，回写 `blocked`。",
        "- 命中任一 `fix`：说明当前页存在明确问题但可修，回写 `qa_failed`，修完再审。",
        "- 全部通过，但还未完成当前页人工复核记录：可先回写 `generated`。",
        "- 全部通过，且当前页已完成人工复核：回写 `completed`。",
        "",
        "## 推荐回写命令",
        "```bash",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status qa_failed --note \"本页 QA 未通过，需继续修正\"",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status blocked --note \"本页判断链或规划信息不足\"",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec mark {project_dir} --page {current['expected_svg']} --status generated --note \"本页已出图，待最终复核\"",
        f"python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py svg-exec complete {project_dir} --page {current['expected_svg']} --note \"本页通过硬性与软性 QA\"",
        "```",
    ]

    if complex_needed:
        lines.extend(
            [
                "",
                "## D. 复杂页附加门",
                "- 主链路 / 主结构 / 证据挂载是否成立，而不是只是在页面上堆很多框",
                "- 复杂图的阅读顺序是否明确，用户是否能在 3-5 秒内找到起点、主路径和结论",
                "- 模块之间是否存在真实因果、层级或协同关系，而不是平铺罗列",
                "- 复杂图旁边的解释文字是否压缩成判断句，而不是说明书",
            ]
        )

    return "\n".join(lines) + "\n"


def render_status_markdown(state: dict[str, Any]) -> str:
    pages = state.get("pages", [])
    counts: dict[str, int] = {}
    for item in pages:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    lines = [
        "# SVG 执行状态",
        "",
        f"- Project: `{state['project_path']}`",
        f"- Overall Status: `{state['overall_status']}`",
        f"- Current Page: `{state.get('current_page') or '无'}`",
        f"- Updated At: `{state['updated_at']}`",
        "",
        "## 状态汇总",
        f"- pending: {counts.get('pending', 0)}",
        f"- in_progress: {counts.get('in_progress', 0)}",
        f"- generated: {counts.get('generated', 0)}",
        f"- qa_failed: {counts.get('qa_failed', 0)}",
        f"- blocked: {counts.get('blocked', 0)}",
        f"- completed: {counts.get('completed', 0)}",
        "",
        "## 页面进度",
    ]
    for page in pages:
        icon = {
            "pending": "[ ]",
            "in_progress": "[>]",
            "generated": "[~]",
            "qa_failed": "[!]",
            "blocked": "[x]",
            "completed": "[v]",
        }.get(page["status"], "[ ]")
        note = f" - {page['note']}" if page.get("note") else ""
        lines.append(f"- {icon} {page['expected_svg']} ({page['status']}){note}")
    if pages and all(page["status"] == "completed" for page in pages):
        lines.extend(["", "## 导出提示", f"- {FINALIZE_GATE_HINT}"])
    return "\n".join(lines) + "\n"


def render_current_task_markdown(state: dict[str, Any], project_dir: Path) -> str:
    current = next_actionable_page(state)
    if current is None:
        return "\n".join(
            [
                "# 当前 SVG 任务",
                "",
                f"- 当前状态：{FINALIZE_GATE_HINT}",
            ]
        ) + "\n"

    page_briefs_dir = project_dir / "notes" / "page_briefs"
    brief_path = page_briefs_dir / current["expected_svg"].replace(".svg", ".md")
    extra = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    return "\n".join(
        [
            "# 当前 SVG 任务",
            "",
            f"- 当前页：`{current['expected_svg']}`",
            f"- 页面标题：{current['title']}",
            f"- 页面家族：`{current['page_family']}`",
            f"- 执行通道：`{(current.get('execution_policy') or {}).get('render_lane', '未指定')}`",
            f"- 模板稳定度：`{current.get('template_stability') or (current.get('execution_policy') or {}).get('template_stability', '未指定')}`",
            f"- 默认自动修复轮数：{(current.get('execution_policy') or {}).get('default_auto_repair_rounds', '未指定')}",
            f"- Preview 策略：`{(current.get('execution_policy') or {}).get('preview_strategy', '未指定')}`",
            f"- 优先页型：`{current.get('preferred_template') or '待补齐'}`",
            f"- 高级正文模式：{current.get('advanced_pattern') or '无'}",
            f"- QA 重点：{current.get('qa_focus') or '待补齐'}",
            f"- 最小上下文：`{current.get('context_min_path') or page_context_min_path(project_dir, current['expected_svg'])}`",
            f"- 前置阻断：{'；'.join(current.get('preflight_blockers') or []) or '无'}",
            f"- 预警：{'；'.join(current.get('preflight_warnings') or []) or '无'}",
            "",
            "## 推荐动作",
            "1. 先读本页 page brief。",
            "2. 若是复杂页，先确认复杂页建模已齐备。",
            "3. 可优先尝试 `ppt_agent.py svg-exec render <project_path> --page <当前页>` 生成 starter SVG。",
            "4. 默认先看 `svg_current_bundle.md` 中整理好的当前页执行总包；必要时再看独立 prompt 视图。",
            "5. 生成或修复当前页 SVG 后，再执行 `svg_execution_runner.py mark ...` 更新状态。",
            "",
            "## Page Brief",
            "",
            extra or "当前未找到 page brief，请先重新执行 `ppt_agent.py run <project_path>`。",
        ]
    ) + "\n"


def save_state_bundle(state: dict[str, Any], project_dir: Path, paths: dict[str, Path]) -> None:
    state["updated_at"] = now_iso()
    write_text(paths["state"], json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    write_text(paths["status_md"], render_status_markdown(state))
    write_text(paths["current_bundle"], render_current_bundle_markdown(state, project_dir))
    write_text(paths["current_review"], render_current_review_markdown(state, project_dir))
    remove_path_if_exists(paths["current_task"])
    remove_path_if_exists(paths["current_prompt"])
    remove_path_if_exists(paths["current_context"])


def find_page(state: dict[str, Any], page_ref: str) -> dict[str, Any]:
    ref = page_ref.strip()
    for page in state.get("pages", []):
        if page["expected_svg"] == ref or page["page_num"] == ref or page["title"] == ref:
            return page
    raise ValueError(f"Page not found: {page_ref}")


def first_next_pending_page(state: dict[str, Any], completed_page: dict[str, Any] | None = None) -> dict[str, Any] | None:
    pages = state.get("pages", [])
    start_index = -1
    if completed_page is not None:
        for idx, page in enumerate(pages):
            if page["expected_svg"] == completed_page["expected_svg"]:
                start_index = idx
                break
    for idx in range(start_index + 1, len(pages)):
        page = pages[idx]
        if page["status"] in {"pending", "qa_failed", "blocked"}:
            return page
    for idx in range(0, start_index + 1):
        page = pages[idx]
        if page["status"] in {"pending", "qa_failed", "blocked"}:
            return page
    return None


def activate_page(state: dict[str, Any], page: dict[str, Any], note: str = "") -> None:
    page["status"] = "in_progress"
    page["attempts"] = int(page.get("attempts", 0)) + 1
    page["last_update"] = now_iso()
    if note:
        page["note"] = note
    state["current_page"] = page["expected_svg"]
    state["overall_status"] = "in_progress"


def command_init(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_path).expanduser().resolve()
    state, paths = load_or_init_state(project_dir, force=args.force)
    state = sync_state_with_files(state, project_dir)
    save_state_bundle(state, project_dir, paths)
    append_log(paths["log"], "初始化 / 刷新 SVG 执行状态。")
    print(f"state: {paths['state']}")
    print(f"status_md: {paths['status_md']}")
    print(f"current_bundle: {paths['current_bundle']}")
    print(f"current_review: {paths['current_review']}")
    print(f"log: {paths['log']}")


def command_sync(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_path).expanduser().resolve()
    state, paths = load_or_init_state(project_dir)
    state = sync_state_with_files(state, project_dir)
    save_state_bundle(state, project_dir, paths)
    append_log(paths["log"], "根据 svg_output/svg_final 同步执行状态。")
    print(f"status_md: {paths['status_md']}")
    print(f"current_bundle: {paths['current_bundle']}")
    print(f"current_review: {paths['current_review']}")


def command_next(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_path).expanduser().resolve()
    state, paths = load_or_init_state(project_dir)
    state = sync_state_with_files(state, project_dir)
    current = next_actionable_page(state)
    if current is None:
        save_state_bundle(state, project_dir, paths)
        append_log(paths["log"], "尝试推进下一页，但当前已全部完成。")
        print("all_pages_completed")
        print(FINALIZE_GATE_HINT)
        return
    if current["status"] != "in_progress":
        activate_page(state, current, note=args.note)
    save_state_bundle(state, project_dir, paths)
    append_log(paths["log"], f"推进到当前任务页：{current['expected_svg']}")
    print(f"current_page: {current['expected_svg']}")
    print(f"current_bundle: {paths['current_bundle']}")
    print(f"current_review: {paths['current_review']}")


def command_mark(args: argparse.Namespace) -> None:
    status_value = getattr(args, "status", "") or getattr(args, "status_value", "")
    if status_value not in ALLOWED_STATUSES:
        raise SystemExit(f"Unsupported status: {status_value}")
    project_dir = Path(args.project_path).expanduser().resolve()
    state, paths = load_or_init_state(project_dir)
    state = sync_state_with_files(state, project_dir)
    page = find_page(state, args.page)
    page["status"] = status_value
    page["last_update"] = now_iso()
    if args.note:
        page["note"] = args.note
    if status_value == "in_progress":
        activate_page(state, page, note=args.note)
    elif state.get("current_page") == page["expected_svg"] and status_value in {"completed", "generated", "blocked", "qa_failed"}:
        state["current_page"] = ""
    state = sync_state_with_files(state, project_dir)
    save_state_bundle(state, project_dir, paths)
    append_log(paths["log"], f"{page['expected_svg']} -> {status_value}" + (f"（{args.note}）" if args.note else ""))
    print(f"updated: {page['expected_svg']} -> {status_value}")


def command_complete(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_path).expanduser().resolve()
    state, paths = load_or_init_state(project_dir)
    state = sync_state_with_files(state, project_dir)
    if args.page:
        page = find_page(state, args.page)
    else:
        page = next_actionable_page(state)
        if page is None:
            save_state_bundle(state, project_dir, paths)
            append_log(paths["log"], "尝试 complete，但当前已全部完成。")
            print("all_pages_completed")
            print(FINALIZE_GATE_HINT)
            return
    page["status"] = "completed"
    page["last_update"] = now_iso()
    if args.note:
        page["note"] = args.note
    if state.get("current_page") == page["expected_svg"]:
        state["current_page"] = ""
    next_page = first_next_pending_page(state, completed_page=page)
    if next_page is not None:
        activate_page(state, next_page, note="由上一页 complete 自动推进")
        next_page_name = next_page["expected_svg"]
    else:
        state = sync_state_with_files(state, project_dir)
        next_page_name = ""
    save_state_bundle(state, project_dir, paths)
    append_log(
        paths["log"],
        f"{page['expected_svg']} -> completed" + (f"（{args.note}）" if args.note else "") + (f"，自动推进到 {next_page_name}" if next_page_name else "，已全部完成"),
    )
    print(f"completed: {page['expected_svg']}")
    if next_page_name:
        print(f"next_page: {next_page_name}")
        print(f"current_bundle: {paths['current_bundle']}")
        print(f"current_review: {paths['current_review']}")
    else:
        print("all_pages_completed")
        print(FINALIZE_GATE_HINT)


def command_summary(args: argparse.Namespace) -> None:
    project_dir = Path(args.project_path).expanduser().resolve()
    state, paths = load_or_init_state(project_dir)
    state = sync_state_with_files(state, project_dir)
    save_state_bundle(state, project_dir, paths)
    print(render_status_markdown(state).strip())
    print(f"\n- current_bundle: `{paths['current_bundle']}`")
    print(f"- current_review: `{paths['current_review']}`")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理正式 SVG 逐页执行状态。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="初始化或重建 SVG 执行状态")
    init_parser.add_argument("project_path")
    init_parser.add_argument("--force", action="store_true", help="忽略已有状态，按当前 design_spec 重建")
    init_parser.set_defaults(func=command_init)

    sync_parser = subparsers.add_parser("sync", help="根据 svg_output/svg_final 同步状态")
    sync_parser.add_argument("project_path")
    sync_parser.set_defaults(func=command_sync)

    next_parser = subparsers.add_parser("next", help="推进到下一张待处理页面")
    next_parser.add_argument("project_path")
    next_parser.add_argument("--note", default="", help="给本轮启动附加说明")
    next_parser.set_defaults(func=command_next)

    complete_parser = subparsers.add_parser("complete", help="将当前页标记完成，并自动推进到下一页")
    complete_parser.add_argument("project_path")
    complete_parser.add_argument("--page", default="", help="可选：页码、页面标题或预期 SVG 文件名；默认使用当前页")
    complete_parser.add_argument("--note", default="", help="完成备注")
    complete_parser.set_defaults(func=command_complete)

    mark_parser = subparsers.add_parser("mark", help="手动标记某一页状态")
    mark_parser.add_argument("project_path")
    mark_parser.add_argument("--page", required=True, help="页码、页面标题或预期 SVG 文件名")
    mark_parser.add_argument("--status", required=True, help="pending/in_progress/generated/qa_failed/blocked/completed")
    mark_parser.add_argument("--note", default="", help="附加备注")
    mark_parser.set_defaults(func=command_mark)

    summary_parser = subparsers.add_parser("summary", help="输出当前 SVG 执行状态摘要")
    summary_parser.add_argument("project_path")
    summary_parser.set_defaults(func=command_summary)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
