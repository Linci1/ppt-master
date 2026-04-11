#!/usr/bin/env python3
"""Auto-repair execution-layer planning artifacts before SVG generation."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

try:
    from build_project_design_spec import (
        build_page_block,
        build_relation_text,
        clean_optional_text,
        infer_fallback_reason,
        infer_page_role,
        load_advanced_page_strategy,
        normalize_inline_text,
        resolve_page_plan,
    )
    from build_production_packet import complex_mode_defaults
    from check_complex_page_model import validate as validate_complex_page_model
    from design_spec_validator import DesignSpecValidator
    from template_semantics import fixed_template_matches_entry
except ImportError:
    TOOLS_DIR = Path(__file__).resolve().parent
    import sys

    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from build_project_design_spec import (  # type: ignore
        build_page_block,
        build_relation_text,
        clean_optional_text,
        infer_fallback_reason,
        infer_page_role,
        load_advanced_page_strategy,
        normalize_inline_text,
        resolve_page_plan,
    )
    from build_production_packet import complex_mode_defaults  # type: ignore
    from check_complex_page_model import validate as validate_complex_page_model  # type: ignore
    from design_spec_validator import DesignSpecValidator  # type: ignore
    from template_semantics import fixed_template_matches_entry  # type: ignore


PAGE_HEADING_RE = re.compile(r"(?im)^####\s+(.+)$")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_first_value(block: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        pattern = rf"(?im)^\s*-\s*\*\*{re.escape(label)}\*\*\s*[:：]\s*(.+)$"
        match = re.search(pattern, block)
        if match:
            return normalize_inline_text(match.group(1))
    return ""


def split_content_outline(content: str) -> tuple[str, str, str]:
    match = re.search(r"(?ms)(^## VIII\. Content Outline\s*$\n)(.*?)(?=^## IX\.)", content)
    if not match:
        raise ValueError("design_spec.md 中未找到 `## VIII. Content Outline` 段落")
    return content[:match.start(2)], match.group(2), content[match.end(2):]


def parse_design_spec_entries(content: str) -> tuple[list[dict[str, str]], dict[str, str]]:
    _, outline_body, _ = split_content_outline(content)
    blocks = []
    matches = list(PAGE_HEADING_RE.finditer(outline_body))
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(outline_body)
        heading = match.group(1).strip()
        block = outline_body[start:end]
        title_match = re.match(r"第\s*(\d+)\s*页\s*(.+)", heading)
        page_num = title_match.group(1) if title_match else str(idx + 1)
        page_title = title_match.group(2).strip() if title_match else heading
        entry = {
            "page_num": page_num,
            "页面类型": page_title,
            "页面意图": extract_first_value(block, ("页面意图", "Page Intent")),
            "证明目标": extract_first_value(block, ("证明目标", "Proof Goal")),
            "核心判断": extract_first_value(block, ("Core Judgment", "核心判断")),
            "支撑证据": extract_first_value(block, ("Supporting Evidence", "支撑证据")),
            "推荐页型": extract_first_value(block, ("Recommended Page Type", "推荐页型")),
            "当前高级正文模式": extract_first_value(block, ("高级正文模式", "Advanced Pattern")),
            "当前优先页型": extract_first_value(block, ("优先页型", "Preferred Template")),
            "当前页面角色": extract_first_value(block, ("页面角色", "Page Role")),
            "当前与上一页关系": extract_first_value(block, ("与上一页关系", "Relation To Previous Page")),
            "当前与下一页关系": extract_first_value(block, ("与下一页关系", "Relation To Next Page")),
            "当前回退原因": extract_first_value(block, ("回退原因", "Fallback Reason")),
        }
        blocks.append(entry)

    meta = {
        "audience": normalize_inline_text(
            extract_first_value(content, ("Target Audience", "目标受众")) or extract_root_line(content, "Target Audience")
        ),
        "goal": normalize_inline_text(
            extract_first_value(content, ("Core Goal", "核心目标")) or extract_root_line(content, "Core Goal")
        ),
        "priority_messages": normalize_inline_text(extract_root_line(content, "Priority Messages")),
        "primary_template": normalize_inline_text(extract_root_line(content, "Preferred Template")),
    }
    return blocks, meta


def extract_root_line(content: str, label: str) -> str:
    match = re.search(rf"(?im)^\s*-\s*{re.escape(label)}\s*:\s*(.+)$", content)
    return match.group(1).strip() if match else ""


def rebuild_design_spec(design_spec_path: Path) -> tuple[Path, list[str]]:
    content = read_text(design_spec_path)
    entries, meta = parse_design_spec_entries(content)
    strategy = load_advanced_page_strategy(meta["primary_template"])
    analysis_stub: dict[str, Any] = {
        "primary_template": meta["primary_template"],
        "complex_pages": [],
        "outline_entries": entries,
        "answers": {
            "audience": meta["audience"],
            "goal": meta["goal"],
        },
    }

    changes: list[str] = []
    repaired_blocks: list[str] = []
    total_pages = len(entries)
    for index, entry in enumerate(entries):
        current_pattern = clean_optional_text(entry.get("当前高级正文模式") or "") or "无"
        current_template = clean_optional_text(entry.get("当前优先页型") or "")
        advanced_pattern, preferred_template, _matched = resolve_page_plan(analysis_stub, entry)
        page_num = int(entry["page_num"]) if str(entry.get("page_num", "")).isdigit() else None
        preserve_fixed_template = bool(
            current_template
            and fixed_template_matches_entry(
                current_template,
                entry,
                page_num=page_num,
                total_pages=total_pages,
            )
        )
        if preserve_fixed_template:
            preferred_template = current_template

        if current_pattern in {"无", "none", ""} and advanced_pattern not in {"无", "none"}:
            changes.append(f"design_spec: 第 {entry['page_num']} 页《{entry['页面类型']}》补判高级正文模式 `{advanced_pattern}`")
        if current_pattern not in {"", "无", "none"} and current_pattern != advanced_pattern:
            changes.append(f"design_spec: 第 {entry['page_num']} 页《{entry['页面类型']}》高级正文模式从 `{current_pattern}` 调整为 `{advanced_pattern}`")
        if current_template and current_template != preferred_template:
            changes.append(f"design_spec: 第 {entry['page_num']} 页《{entry['页面类型']}》优先页型从 `{current_template}` 调整为 `{preferred_template}`")

        if strategy and preferred_template in {"03_content.svg", "11_list.svg"} and not entry.get("当前回退原因"):
            changes.append(f"design_spec: 第 {entry['page_num']} 页《{entry['页面类型']}》补充回退原因")

        entry_for_build = dict(entry)
        entry_for_build["优先页型"] = preferred_template or current_template
        entry_for_build["高级正文模式"] = advanced_pattern
        if current_template:
            entry_for_build["推荐页型"] = entry.get("推荐页型") or current_template
        repaired_blocks.extend(build_page_block(analysis_stub, entry_for_build, index, priorities=[]))

    prefix, _outline_body, suffix = split_content_outline(content)
    new_content = prefix + "\n".join(repaired_blocks) + "\n" + suffix
    write_text(design_spec_path, new_content)
    return design_spec_path, changes


def parse_complex_design_spec_pages(design_spec_content: str) -> list[dict[str, str]]:
    entries, _meta = parse_design_spec_entries(design_spec_content)
    pages: list[dict[str, str]] = []
    total_pages = len(entries)
    for index, entry in enumerate(entries):
        title = f"第 {entry['page_num']} 页 {entry['页面类型']}"
        advanced_pattern = entry.get("当前高级正文模式") or "无"
        advanced_pattern = re.sub(r"[`*]", "", advanced_pattern).strip()
        preferred_template = clean_optional_text(entry.get("当前优先页型") or "")
        page_num = int(entry["page_num"]) if str(entry.get("page_num", "")).isdigit() else None
        if preferred_template in {"01_cover.svg", "02_toc.svg", "02_chapter.svg", "04_ending.svg"} and fixed_template_matches_entry(
            preferred_template,
            entry,
            page_num=page_num,
            total_pages=total_pages,
        ):
            continue
        if advanced_pattern in {"", "无", "none"}:
            continue
        pages.append(
            {
                "title": title,
                "page_num": entry["page_num"],
                "page_title": entry["页面类型"],
                "page_intent": entry["页面意图"],
                "proof_goal": entry["证明目标"],
                "main_judgment": entry["核心判断"],
                "evidence": entry["支撑证据"],
                "recommended_page_type": entry["推荐页型"],
                "advanced_pattern": advanced_pattern,
                "preferred_template": preferred_template,
                "index": str(index),
            }
        )
    return pages


def pattern_structure_type(pattern: str) -> str:
    mapping = {
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
    return mapping.get(pattern, "混合结构")


def pattern_mode_label(pattern: str) -> str:
    if pattern in {"attack_case_chain", "evidence_attached_case_chain"}:
        return "攻击链 / 复杂案例链"
    if pattern in {"matrix_defense_map", "governance_control_matrix"}:
        return "治理矩阵 / 总览页"
    if pattern in {"evidence_cockpit", "evidence_wall"}:
        return "证据证明页"
    if pattern in {"layered_system_map", "attack_tree_architecture", "maturity_model"}:
        return "分层结构 / 攻击树"
    if pattern in {"swimlane_collaboration", "multi_lane_execution_chain"}:
        return "多泳道协同页"
    if pattern == "operation_loop":
        return "闭环运营 / 机制图"
    if pattern == "timeline_roadmap":
        return "阶段演进 / 路线图"
    return "复杂正文页"


def preferred_page_role(page: dict[str, str], total_pages: int) -> str:
    page_num = int(page["page_num"]) if page["page_num"].isdigit() else 1
    text = " ".join([page["page_title"], page["page_intent"], page["proof_goal"], page["main_judgment"]])
    if any(keyword in text for keyword in ("总览", "概览", "框架", "体系", "地图")) or page_num <= 4:
        return "概览页"
    if any(keyword in text for keyword in ("证据", "证明", "结果", "数据", "案例")):
        return "证明页"
    if page_num >= max(total_pages - 1, 1) or any(keyword in text for keyword in ("建议", "闭环", "路径", "整改", "收束")):
        return "收束页"
    return "推进页"


def default_sub_judgments(page: dict[str, str]) -> list[str]:
    pattern = page["advanced_pattern"]
    if pattern in {"attack_case_chain", "evidence_attached_case_chain"}:
        return [
            "攻击入口具备形成初始落点的稳定条件。",
            "放大条件使攻击链可以继续推进而非停留在单点发现。",
            "结果已经指向关键资产、关键权限或可持续影响。",
        ]
    if pattern in {"matrix_defense_map", "governance_control_matrix"}:
        return [
            "高风险项并非平均分布，而是集中在少数关键域。",
            "控制薄弱点决定了治理优先级与动作顺序。",
            "优先级排序应直接映射到整改投入与复测安排。",
        ]
    if pattern in {"operation_loop", "timeline_roadmap"}:
        return [
            "当前机制不是单次动作，而是需要持续运转的过程。",
            "关键环节之间存在先后与反馈关系，缺一会导致闭环失效。",
            "只有把结果回流到优化动作，页面结论才完整成立。",
        ]
    if pattern in {"swimlane_collaboration", "multi_lane_execution_chain"}:
        return [
            "至少两类角色需要并行推进，单角色无法完成交付闭环。",
            "阶段动作需要按泳道拆开，才能看清职责和协同点。",
            "结果必须落到协同效率、交付质量或落地动作上。",
        ]
    if pattern in {"evidence_cockpit", "evidence_wall"}:
        return [
            "关键证据需要按主证据与辅助证据分层呈现。",
            "数据、截图或背书材料必须直接服务于主判断。",
            "结论区需要把证据翻译成管理可理解的判断与动作。",
        ]
    return [
        "本页需要先建立结构认知，而不是只罗列事实。",
        "结构中的关键关系决定了读者能否快速理解判断。",
        "最终结论必须收束到风险、价值或动作要求上。",
    ]


def default_argument_spine(page: dict[str, str]) -> dict[str, str]:
    pattern = page["advanced_pattern"]
    if pattern in {"attack_case_chain", "evidence_attached_case_chain"}:
        return {
            "现象 / 入口": "从外部入口或弱控制点形成初始落点。",
            "放大机制 / 关键条件": "凭证、管理面或横向能力使链路继续放大。",
            "结果 / 影响": "攻击结果已接近或触达核心资产与关键权限。",
            "管理判断 / 动作要求": "应优先封堵入口、凭证与放大条件，再做复测闭环。",
        }
    if pattern in {"matrix_defense_map", "governance_control_matrix"}:
        return {
            "现象 / 入口": "不同风险域呈现出明显的风险集中差异。",
            "放大机制 / 关键条件": "控制成熟度不足和高频暴露共同放大整体风险。",
            "结果 / 影响": "高风险区域决定治理投入优先级与顺序。",
            "管理判断 / 动作要求": "应按集中度先压降高风险域，再推进跨域闭环。",
        }
    if pattern in {"operation_loop", "timeline_roadmap"}:
        return {
            "现象 / 入口": "当前工作由多个环节连续组成，不能按单点动作理解。",
            "放大机制 / 关键条件": "输入、处置、验证、优化之间存在依赖与反馈。",
            "结果 / 影响": "任一关键环节失效都会削弱整体机制效果。",
            "管理判断 / 动作要求": "应把关键动作纳入闭环并设定复盘与优化机制。",
        }
    if pattern in {"swimlane_collaboration", "multi_lane_execution_chain"}:
        return {
            "现象 / 入口": "任务需要客户侧、长亭侧或多角色共同推进。",
            "放大机制 / 关键条件": "阶段动作存在前后依赖，协同断点会拖慢整体交付。",
            "结果 / 影响": "协同效率直接决定结果输出与落地质量。",
            "管理判断 / 动作要求": "应按阶段和角色双维度明确动作与交接。",
        }
    if pattern in {"evidence_cockpit", "evidence_wall"}:
        return {
            "现象 / 入口": "当前判断需要更多直接证据和结果证据支撑。",
            "放大机制 / 关键条件": "证据质量与分层方式决定结论可信度。",
            "结果 / 影响": "证据聚合后足以支撑当前主判断成立。",
            "管理判断 / 动作要求": "应围绕主证据先落动作，再补充旁证验证。",
        }
    return {
        "现象 / 入口": "先交代这页处理的对象、范围与问题入口。",
        "放大机制 / 关键条件": "说明哪些关键条件让结构关系成立。",
        "结果 / 影响": "把结构关系翻译成结果与影响。",
        "管理判断 / 动作要求": "最终落到管理判断、风险结论或动作要求。",
    }


def generic_defaults_for_empty(values: dict[str, str], structure_type: str) -> dict[str, str]:
    fallback = {
        "入口节点": "问题入口 / 主题入口",
        "动作节点": "关键动作 / 关键环节",
        "放大条件": "影响因素 / 约束条件",
        "结果节点": "结果输出 / 影响结果",
        "证据节点": "截图 / 数据 / 事实",
        "判断节点 / 控制节点": "管理判断 / 后续动作",
        "主链因果": f"入口 -> {structure_type}主结构 -> 结果",
        "辅助依赖": "上下游关系与条件约束共同支撑主结构成立",
        "放大关系": "关键条件会放大问题影响或结果差异",
        "并行 / 汇聚": "多个分支可并行展开并最终汇聚到主判断",
        "反馈 / 闭环": "结果应回指到优化与验证动作",
    }
    return {key: value or fallback[key] for key, value in values.items()}


def build_complex_model_block(page: dict[str, str], prev_title: str | None, next_title: str | None, total_pages: int) -> str:
    pattern = page["advanced_pattern"]
    structure_type = pattern_structure_type(pattern)
    mode_label = pattern_mode_label(pattern)
    defaults = complex_mode_defaults(mode_label)
    nodes = generic_defaults_for_empty(defaults.get("nodes", {}), structure_type)
    relations = generic_defaults_for_empty(defaults.get("relations", {}), structure_type)
    compression = {
        "标题句": defaults.get("compression", {}).get("标题句") or "标题必须直接表达判断，不能只写中性主题。",
        "节点文案": defaults.get("compression", {}).get("节点文案") or "节点文案压缩成对象 + 动作 / 状态变化。",
        "证据说明句": defaults.get("compression", {}).get("证据说明句") or "证据说明必须直接回答它证明哪个判断。",
        "页尾收束句": defaults.get("compression", {}).get("页尾收束句") or "页尾必须收束到风险判断或动作要求。",
    }
    closure = {
        "管理判断": defaults.get("closure", {}).get("管理判断") or "当前页已具备支撑管理判断的结构基础。",
        "风险判断": defaults.get("closure", {}).get("风险判断") or "若不处理关键控制点，问题会继续放大或重复出现。",
        "建议动作": defaults.get("closure", {}).get("建议动作") or "优先围绕主结构中的关键控制点安排整改与复测。",
    }
    focus = defaults.get("focus", []) or ["主判断", "主结构", "证据与收束"]
    while len(focus) < 3:
        focus.append(f"焦点 {len(focus) + 1}")
    page_role = preferred_page_role(page, total_pages)
    previous_relation, next_relation = build_relation_text(prev_title, page["page_title"], next_title, page_role)
    sub_judgments = default_sub_judgments(page)
    argument_spine = default_argument_spine(page)
    preferred_template = page.get("preferred_template") or "待补齐"

    return "\n".join(
        [
            f"#### {page['title']}",
            f"- 页面角色：{page_role}",
            f"- 页面意图：{normalize_inline_text(page['page_intent'])}",
            f"- 证明目标：{normalize_inline_text(page['proof_goal'])}",
            f"- 主判断：{normalize_inline_text(page['main_judgment'])}",
            "- 分判断：",
            f"  1. {sub_judgments[0]}",
            f"  2. {sub_judgments[1]}",
            f"  3. {sub_judgments[2]}",
            "- 论证主线：",
            f"  - 现象 / 入口：{argument_spine['现象 / 入口']}",
            f"  - 放大机制 / 关键条件：{argument_spine['放大机制 / 关键条件']}",
            f"  - 结果 / 影响：{argument_spine['结果 / 影响']}",
            f"  - 管理判断 / 动作要求：{argument_spine['管理判断 / 动作要求']}",
            f"- 主结构类型：{structure_type}",
            f"- 结构选择理由：本页命中 `{pattern}`，因此优先采用 `{structure_type}` 结构来表达《{page['page_title']}》的主判断与证据关系。",
            f"- 为什么不用其他结构：普通列表或兜底内容页无法稳定承载《{page['page_title']}》所需的结构关系与跨区阅读顺序。",
            "- 关键节点：",
            f"  - 入口节点：{nodes['入口节点']}",
            f"  - 动作节点：{nodes['动作节点']}",
            f"  - 放大条件：{nodes['放大条件']}",
            f"  - 结果节点：{nodes['结果节点']}",
            f"  - 证据节点：{nodes['证据节点']}",
            f"  - 判断节点 / 控制节点：{nodes['判断节点 / 控制节点']}",
            "- 关键关系：",
            f"  - 主链因果：{relations['主链因果']}",
            f"  - 辅助依赖：{relations['辅助依赖']}",
            f"  - 放大关系：{relations['放大关系']}",
            f"  - 并行 / 汇聚：{relations['并行 / 汇聚']}",
            f"  - 反馈 / 闭环：{relations['反馈 / 闭环']}",
            "- 证据挂载计划：",
            f"  - 现有支撑证据：{normalize_inline_text(page['evidence'])}",
            "  - 证据 A -> 节点 / 分判断：将直接证据挂到最能支撑主判断的主结构节点。",
            "  - 证据 B -> 节点 / 分判断：将结果证据放在结果区或页尾收束区，避免与主结构抢焦点。",
            "- 证据分级：",
            "  - 直接证据：最能证明关键节点已真实发生的截图、日志或现场结果。",
            "  - 结果证据：可证明影响范围、结果落点或业务影响的数据与结论。",
            "  - 旁证 / 背景证据：用于解释上下文、规模和约束条件的辅助材料。",
            "- 文本压缩计划：",
            f"  - 标题句：{compression['标题句']}",
            f"  - 节点文案：{compression['节点文案']}",
            f"  - 证据说明句：{compression['证据说明句']}",
            f"  - 页尾收束句：{compression['页尾收束句']}",
            "- 视觉焦点排序：",
            f"  1. {focus[0]}",
            f"  2. {focus[1]}",
            f"  3. {focus[2]}",
            "- 页面收束方式：",
            f"  - 管理判断：{closure['管理判断']}",
            f"  - 风险判断：{closure['风险判断']}",
            f"  - 建议动作：{closure['建议动作']}",
            f"- 与上一页关系：{previous_relation}",
            f"- 与下一页关系：{next_relation}",
            f"- 推荐重型骨架：`{preferred_template}`",
            "",
        ]
    )


def rebuild_complex_page_models(project_path: Path, design_spec_path: Path) -> tuple[Path, list[str]]:
    design_spec_content = read_text(design_spec_path)
    pages = parse_complex_design_spec_pages(design_spec_content)
    model_path = project_path / "notes" / "complex_page_models.md"
    changes: list[str] = []

    if not pages:
        content = "# 复杂页建模草稿\n\n- 当前 design_spec.md 未声明需要复杂页建模的页面。\n"
        write_text(model_path, content)
        changes.append("complex_models: 当前未命中复杂页，已刷新为无复杂页状态")
        return model_path, changes

    lines = [
        "# 复杂页建模草稿",
        "",
        "> 该文件已由自动修补流程补强，用于在进入 Executor 前先把复杂页逻辑补完整。",
        "> 页面标题必须与 `design_spec.md` 完全一致；若标题改动，请先同步两处再继续执行。",
        "",
    ]
    for index, page in enumerate(pages):
        prev_title = pages[index - 1]["page_title"] if index > 0 else None
        next_title = pages[index + 1]["page_title"] if index + 1 < len(pages) else None
        lines.append(build_complex_model_block(page, prev_title, next_title, len(pages)))
        changes.append(f"complex_models: 重建《{page['title']}》的复杂页建模块")

    write_text(model_path, "\n".join(lines).rstrip() + "\n",)
    return model_path, changes


def repair_execution_artifacts(project_path: str | Path) -> dict[str, Any]:
    project_dir = Path(project_path).expanduser().resolve()
    design_spec_path = project_dir / "design_spec.md"
    if not design_spec_path.exists():
        raise FileNotFoundError(f"design_spec.md not found: {design_spec_path}")

    repaired_design_spec_path, design_changes = rebuild_design_spec(design_spec_path)
    model_path, model_changes = rebuild_complex_page_models(project_dir, repaired_design_spec_path)

    validator = DesignSpecValidator()
    design_ok, design_errors, design_warnings = validator.validate_file(str(repaired_design_spec_path))
    complex_ok, complex_errors, complex_warnings, _summary = validate_complex_page_model(project_dir)

    report_path = project_dir / "notes" / "auto_repair_report.md"
    report_lines = [
        "# 自动修补报告",
        "",
        "## 1. 本轮修改",
    ]
    all_changes = design_changes + model_changes
    report_lines.extend(f"- {item}" for item in all_changes) if all_changes else report_lines.append("- 本轮未检测到需要自动修补的项")
    report_lines.extend(
        [
            "",
            "## 2. design_spec 校验结果",
            f"- 结果：{'通过' if design_ok else '失败'}",
        ]
    )
    report_lines.extend(f"- ERROR: {item}" for item in design_errors) if design_errors else report_lines.append("- 无错误")
    report_lines.extend(f"- WARN: {item}" for item in design_warnings) if design_warnings else report_lines.append("- 无警告")
    report_lines.extend(
        [
            "",
            "## 3. complex_page_models 校验结果",
            f"- 结果：{'通过' if complex_ok else '失败'}",
        ]
    )
    report_lines.extend(f"- ERROR: {item}" for item in complex_errors) if complex_errors else report_lines.append("- 无错误")
    report_lines.extend(f"- WARN: {item}" for item in complex_warnings) if complex_warnings else report_lines.append("- 无警告")
    write_text(report_path, "\n".join(report_lines) + "\n")

    return {
        "design_spec": str(repaired_design_spec_path),
        "complex_models": str(model_path),
        "report": str(report_path),
        "changes": all_changes,
        "design_ok": design_ok,
        "design_errors": design_errors,
        "design_warnings": design_warnings,
        "complex_ok": complex_ok,
        "complex_errors": complex_errors,
        "complex_warnings": complex_warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="自动修补 design_spec 与复杂页建模中的执行层 warning/弱项。")
    parser.add_argument("project_path", help="项目路径")
    args = parser.parse_args()

    result = repair_execution_artifacts(args.project_path)
    print(f"design_spec: {result['design_spec']}")
    print(f"complex_models: {result['complex_models']}")
    print(f"report: {result['report']}")
    print(f"design_spec_check: {'pass' if result['design_ok'] else 'fail'}")
    print(f"complex_model_check: {'pass' if result['complex_ok'] else 'fail'}")
    if result["changes"]:
        print("changes:")
        for item in result["changes"]:
            print(f"  - {item}")


if __name__ == "__main__":
    main()
