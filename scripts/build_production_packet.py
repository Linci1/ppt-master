#!/usr/bin/env python3
"""Build production readiness, Strategist packet, and complex-page scaffolds."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from template_semantics import infer_fixed_template
except ImportError:
    import sys

    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from template_semantics import infer_fixed_template  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_PATTERNS = ("待确认", "待补齐", "待补充", "待选择")
CORE_BRIEF_LABELS = (
    "项目名称",
    "行业",
    "场景",
    "主要受众",
    "受众更关心",
    "核心目标",
    "期待对方形成的判断",
    "期待对方采取的动作",
    "指定模板",
    "必须固定的品牌元素",
    "源文档",
    "是否允许 AI 生图",
    "页数范围",
    "可讲述 / 可阅读倾向",
)
OPTIONAL_BRIEF_LABELS = (
    "次要受众",
    "历史案例参考",
    "风格偏好",
    "复杂度偏好",
    "历史 PPT",
    "图片 / 截图 / 图表",
    "时间限制",
    "禁用表达",
    "禁用视觉形式",
)
TEMPLATE_DOC_CANDIDATES = [
    "design_spec.md",
    "qa_profile.md",
    "generation_checklist.md",
    "text_prompt_snippets.md",
    "ppt_logic_reference.md",
    "soft_content_qa_framework.md",
    "soft_content_rewrite_strategies.md",
    "advanced_page_patterns.md",
    "complex_graph_semantics.md",
    "complex_case_chain_modeling.md",
    "complex_page_reasoning_template.md",
    "evidence_grading_rules.md",
    "complex_deck_orchestration.md",
    "complex_svg_blueprints.md",
    "sample_grade_content_system.md",
]

CANVAS_SPECS = {
    "ppt169": {"name": "PPT 16:9", "viewbox": "0 0 1280 720", "dimensions": "1280x720"},
    "ppt43": {"name": "PPT 4:3", "viewbox": "0 0 1024 768", "dimensions": "1024x768"},
    "xhs": {"name": "小红书", "viewbox": "0 0 1242 1660", "dimensions": "1242x1660"},
    "story": {"name": "Story 竖版", "viewbox": "0 0 1080 1920", "dimensions": "1080x1920"},
}

TEMPLATE_ID_ALIASES = {
    "security_service": "security_service",
    "长亭安服": "security_service",
    "chaitin": "chaitin",
    "长亭通用墨绿色": "chaitin",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def normalize_template_id(template_name: str) -> str:
    cleaned = re.sub(r"[`*]", "", template_name or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return TEMPLATE_ID_ALIASES.get(cleaned, cleaned)


def load_plan_answers(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "notes" / "plan_answers.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_sources(project_dir: Path) -> list[str]:
    source_dir = project_dir / "sources"
    if not source_dir.exists():
        return []
    return [item.name for item in sorted(source_dir.iterdir()) if item.is_file()]


def extract_recommendation(text: str, label: str) -> str:
    pattern = rf"-\s*{re.escape(label)}：(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else "未提取到"


def extract_recommendation_list(text: str, label: str) -> list[str]:
    value = extract_recommendation(text, label)
    if value == "未提取到":
        return []
    hits = re.findall(r"`([^`]+)`", value)
    if hits:
        return hits
    return [item.strip(" `") for item in value.split(",") if item.strip(" `")]


def find_placeholder_lines(text: str) -> list[str]:
    results: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(token in stripped for token in PLACEHOLDER_PATTERNS):
            results.append(stripped)
    return results


def parse_page_range(value: str) -> tuple[int | None, int | None]:
    text = value.strip()
    if not text or any(token in text for token in PLACEHOLDER_PATTERNS):
        return None, None

    match = re.search(r"(\d+)\s*[-~～至到—]+\s*(\d+)", text)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        return (low, high) if low <= high else (high, low)

    match = re.search(r"不少于\s*(\d+)", text)
    if match:
        low = int(match.group(1))
        return low, None

    match = re.search(r"不超过\s*(\d+)", text)
    if match:
        high = int(match.group(1))
        return None, high

    match = re.search(r"约\s*(\d+)", text) or re.search(r"(\d+)", text)
    if match:
        number = int(match.group(1))
        return number, number

    return None, None


def extract_section(text: str, heading: str, next_heading: str | None = None) -> str:
    if next_heading:
        pattern = rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)^##\s+{re.escape(next_heading)}\s*$"
    else:
        pattern = rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*)$"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def extract_priority_items(brief_text: str) -> list[str]:
    section = extract_section(brief_text, "四、展示重点", "五、品牌与模板要求")
    items: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        if stripped.startswith("- 必须保留的信息："):
            continue
        value = stripped[2:].strip()
        if value and not any(token in value for token in PLACEHOLDER_PATTERNS):
            items.append(value)
    return items


def analyze_brief_placeholders(brief_text: str) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []

    for label in CORE_BRIEF_LABELS:
        value = parse_brief_value(brief_text, label)
        if not value or any(token in value for token in PLACEHOLDER_PATTERNS):
            blockers.append(label)

    if not extract_priority_items(brief_text):
        blockers.append("展示重点")

    for label in OPTIONAL_BRIEF_LABELS:
        value = parse_brief_value(brief_text, label)
        if value and any(token in value for token in PLACEHOLDER_PATTERNS):
            warnings.append(label)

    return blockers, warnings


def parse_outline_entries(text: str) -> list[dict[str, str]]:
    blocks = re.split(r"(?m)^##\s+第\s+\d+\s+页\s*$", text)
    headings = re.findall(r"(?m)^##\s+第\s+(\d+)\s+页\s*$", text)
    entries: list[dict[str, str]] = []
    for page_num, block in zip(headings, blocks[1:]):
        entry: dict[str, str] = {"page_num": page_num}
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            if "：" not in stripped:
                continue
            key, value = stripped[2:].split("：", 1)
            entry[key.strip()] = value.strip()
        entries.append(entry)
    return entries


def infer_complex_mode(entry: dict[str, str]) -> dict[str, str]:
    title_text = " ".join(
        [
            entry.get("页面类型", ""),
            entry.get("页面意图", ""),
            entry.get("核心判断", ""),
        ]
    )
    text = " ".join(
        [
            entry.get("页面类型", ""),
            entry.get("页面意图", ""),
            entry.get("证明目标", ""),
            entry.get("推荐页型", ""),
            entry.get("核心判断", ""),
        ]
    )
    title_lower = title_text.lower()
    lower = text.lower()
    if any(keyword in title_lower for keyword in ["能力总览", "安服价值", "能力价值", "服务价值"]):
        return {
            "mode": "分层体系 / 能力地图",
            "structure": "分层",
            "blueprint": "17_service_overview.svg",
        }
    if any(keyword in lower for keyword in ["运营闭环", "整改复测机制", "闭环", "复测机制"]):
        return {
            "mode": "闭环运营 / 机制页",
            "structure": "闭环",
            "blueprint": "18_domain_capability_map.svg",
        }
    if any(keyword in title_lower for keyword in ["重要成果", "关键结果", "结果总览", "成果总览", "成果摘要"]):
        return {
            "mode": "数据证明 / 关键结果总览",
            "structure": "证据挂载",
            "blueprint": "07_data.svg",
        }
    if any(keyword in title_lower for keyword in ["关键问题拆解", "问题拆解", "根因拆解", "控制薄弱", "治理缺口"]):
        return {
            "mode": "分层根因 / 攻击树",
            "structure": "分层",
            "blueprint": "08_product.svg",
        }
    if any(keyword in lower for keyword in ["攻击链总览", "整体攻击路径分析"]):
        return {
            "mode": "攻击路径总览 / 数据证明页",
            "structure": "证据挂载",
            "blueprint": "07_data.svg",
        }
    if any(keyword in lower for keyword in ["互联网侧攻击路径", "内网侧攻击路径", "社工钓鱼路径", "攻击链展开"]):
        return {
            "mode": "攻击路径双链页 / 多泳道执行链",
            "structure": "链路",
            "blueprint": "09_comparison.svg",
        }
    if any(keyword in lower for keyword in ["攻击结果归因", "结果导向案例", "典型案例摘要", "复杂案例链"]):
        return {
            "mode": "结果导向案例 / 证据挂载案例链",
            "structure": "链路",
            "blueprint": "19_result_leading_case.svg",
        }
    if any(keyword in lower for keyword in ["攻击链", "攻击路径", "突破路径", "横向移动"]):
        return {
            "mode": "攻击链 / 复杂案例链",
            "structure": "链路",
            "blueprint": "09_comparison.svg",
        }
    if any(keyword in lower for keyword in ["关键证据总览", "证据证明", "原始截图", "截图", "日志", "证据页"]):
        return {
            "mode": "证据墙 / 关键证据总览",
            "structure": "证据挂载",
            "blueprint": "12_grid.svg",
        }
    if any(keyword in lower for keyword in ["风险结构", "根因", "归因", "攻击树", "分层结构"]):
        return {
            "mode": "分层根因 / 攻击树",
            "structure": "分层",
            "blueprint": "08_product.svg",
        }
    if any(keyword in lower for keyword in ["治理优先级", "治理看板", "控制矩阵", "域-状态-动作", "整改优先级"]):
        return {
            "mode": "治理矩阵 / 控制看板",
            "structure": "矩阵",
            "blueprint": "16_table.svg",
        }
    if any(keyword in lower for keyword in ["风险暴露面矩阵", "风险总览", "风险域", "控制域", "映射", "矩阵"]):
        return {
            "mode": "风险矩阵 / 风险总览",
            "structure": "矩阵",
            "blueprint": "12_grid.svg",
        }
    if any(keyword in lower for keyword in ["驾驶舱", "kpi", "指标+结论", "数据证明"]):
        return {
            "mode": "数据证明 / 结果证明页",
            "structure": "证据挂载",
            "blueprint": "07_data.svg",
        }
    if any(keyword in lower for keyword in ["客户侧", "长亭侧", "多角色", "协同", "战前战中战后"]):
        return {
            "mode": "多泳道协同页",
            "structure": "泳道",
            "blueprint": "05_case.svg",
        }
    if any(
        keyword in lower
        for keyword in [
            "能力地图",
            "服务体系",
            "平台+服务+结果",
            "平台 + 服务 + 结果",
            "能力域",
            "体系",
            "能力总览",
            "能力价值",
            "安服价值",
        ]
    ):
        return {
            "mode": "分层体系 / 能力地图",
            "structure": "分层",
            "blueprint": "17_service_overview.svg",
        }
    if any(keyword in lower for keyword in ["时间线", "路线图", "里程碑", "演进", "建设路径", "年度变化"]):
        return {
            "mode": "阶段演进 / 路线图",
            "structure": "链路",
            "blueprint": "10_timeline.svg",
        }
    return {
        "mode": "复杂正文页",
        "structure": "混合结构",
        "blueprint": "03_content.svg",
    }


def infer_advanced_pattern(page: dict[str, str]) -> str:
    mode = page.get("mode", "")
    if "结果导向案例" in mode or "证据挂载案例链" in mode:
        return "evidence_attached_case_chain"
    if "攻击路径双链页" in mode or "多泳道执行链" in mode:
        return "multi_lane_execution_chain"
    if "攻击链" in mode:
        return "attack_case_chain"
    if "治理矩阵" in mode:
        return "governance_control_matrix"
    if "风险矩阵" in mode:
        return "matrix_defense_map"
    if "证据墙" in mode:
        return "evidence_wall"
    if "数据证明" in mode:
        return "evidence_cockpit"
    if "分层根因" in mode:
        return "attack_tree_architecture"
    if "分层体系" in mode:
        return "layered_system_map"
    if "闭环" in mode:
        return "operation_loop"
    if "泳道" in mode:
        return "swimlane_collaboration"
    if "路线图" in mode:
        return "timeline_roadmap"
    return "无"


def infer_layout_mode(entry: dict[str, str], preferred_template: str) -> str:
    if preferred_template == "01_cover.svg":
        return "全屏背景图 + 居中标题"
    if preferred_template == "02_toc.svg":
        return "目录列表 + 描述分组"
    if preferred_template == "02_chapter.svg":
        return "大号章节数字 + 章节标题"
    if preferred_template == "04_ending.svg":
        return "收束结语 + 联系信息"
    if preferred_template == "19_result_leading_case.svg":
        return "结果 headline + 主链结构 + 证据侧栏"
    if preferred_template == "09_comparison.svg":
        return "双链对照 + 多阶段执行链 + 底部结果带"
    if preferred_template == "16_table.svg":
        return "优先级带 + 治理矩阵 + 管理判断栏"
    if preferred_template == "17_service_overview.svg":
        return "中心能力底盘 + 分域卡片"
    if preferred_template == "18_domain_capability_map.svg":
        return "分域能力地图 + 结果带"
    if preferred_template == "07_data.svg":
        return "证明 headline + KPI + 主证明区"
    if preferred_template == "12_grid.svg":
        return "分组卡片矩阵 + 底部总结带"
    if preferred_template == "13_highlight.svg":
        return "单一重点指标 + 侧边补充统计"
    if preferred_template == "11_list.svg":
        return "结构化列表 + 简要说明"
    if preferred_template == "05_case.svg":
        return "案例链 / 双栏案例页"
    return entry.get("页面类型", "常规内容布局")


def infer_preferred_template(
    entry: dict[str, str],
    primary_template: str,
    page: dict[str, str] | None = None,
    *,
    page_num: int | None = None,
    total_pages: int | None = None,
) -> str:
    primary_template = normalize_template_id(primary_template)
    fixed_template = infer_fixed_template(entry, page_num=page_num, total_pages=total_pages)
    if fixed_template:
        return fixed_template

    page_type = " ".join(
        [
            entry.get("页面类型", ""),
            entry.get("推荐页型", ""),
        ]
    )
    lower = page_type.lower()
    if page and page.get("blueprint"):
        return page["blueprint"]
    if any(keyword in lower for keyword in ["攻击链总览", "整体攻击路径分析"]):
        return "07_data.svg"
    if any(keyword in lower for keyword in ["互联网侧攻击路径", "内网侧攻击路径", "社工钓鱼路径", "攻击链展开", "突破路径"]):
        return "09_comparison.svg"
    if any(keyword in lower for keyword in ["体系", "总览", "能力地图"]):
        return "17_service_overview.svg" if primary_template == "security_service" else "03_content.svg"
    if any(keyword in lower for keyword in ["时间线", "历程", "阶段"]):
        return "10_timeline.svg"
    if any(keyword in lower for keyword in ["对照", "协同", "泳道"]):
        return "09_comparison.svg"
    if any(keyword in lower for keyword in ["数据证明", "结果总览", "kpi", "指标"]):
        return "07_data.svg"
    if any(keyword in lower for keyword in ["案例"]):
        return "05_case.svg"
    if any(keyword in lower for keyword in ["矩阵", "治理"]):
        return "16_table.svg"
    return "03_content.svg"


def complex_mode_defaults(mode: str) -> dict[str, Any]:
    if "攻击链" in mode:
        return {
            "focus": ["主判断 / 结果 headline", "攻击链主结构", "证据挂载与页尾收束"],
            "nodes": {
                "入口节点": "外部入口 / 弱口令 / 暴露面",
                "动作节点": "命令执行 / 落地 / 横向移动",
                "放大条件": "凭证泄露 / 管理面暴露 / 权限复用",
                "结果节点": "核心资产触达 / 控制结果 / 影响结果",
                "证据节点": "截图 / 日志 / 控制台 / 指标",
                "判断节点 / 控制节点": "管理判断 / 优先治理点",
            },
            "relations": {
                "主链因果": "入口 -> 动作 -> 放大 -> 结果",
                "辅助依赖": "凭证、配置和边界薄弱支撑主链继续推进",
                "放大关系": "弱控制措施使攻击结果可持续扩张",
                "并行 / 汇聚": "多个入口可汇聚到同一结果节点",
                "反馈 / 闭环": "结果回指整改动作与复测要求",
            },
            "compression": {
                "标题句": "用结果导向判断句，避免只写“攻击链分析”",
                "节点文案": "压缩成 对象 + 动作/状态变化",
                "证据说明句": "明确写出该证据证明哪一步已真实发生",
                "页尾收束句": "落到结构性风险与优先整改动作",
            },
            "closure": {
                "管理判断": "当前问题已具备从入口到结果的稳定放大能力。",
                "风险判断": "这不是单点漏洞，而是可重复形成结果的结构性风险。",
                "建议动作": "优先封堵入口、凭证与放大条件，再做复测验证。",
            },
        }
    if "矩阵" in mode or "总览" in mode:
        return {
            "focus": ["优先级判断", "矩阵主体", "管理收束"],
            "nodes": {
                "入口节点": "风险域 / 暴露域 / 攻击阶段",
                "动作节点": "关键控制动作 / 治理动作",
                "放大条件": "高频暴露 / 低控制成熟度 / 跨域叠加",
                "结果节点": "高风险集中区 / 优先治理区",
                "证据节点": "分级数据 / 数量分布 / 关键事实",
                "判断节点 / 控制节点": "P1/P2/P3 治理优先级",
            },
            "relations": {
                "主链因果": "风险域 -> 风险程度 -> 治理优先级",
                "辅助依赖": "当前状态和控制成熟度决定动作顺序",
                "放大关系": "多个薄弱域叠加放大整体风险暴露",
                "并行 / 汇聚": "多风险项汇聚成治理主线",
                "反馈 / 闭环": "动作落地后回到复测与闭环验证",
            },
            "compression": {
                "标题句": "用结论先行句说明风险集中在哪里",
                "节点文案": "优先级 / 现状 / 动作 / 验证 四类短标签",
                "证据说明句": "数据或事实用于解释为何该域优先",
                "页尾收束句": "落到治理排序和资源投入判断",
            },
            "closure": {
                "管理判断": "治理重点应按风险集中度和放大链路优先排序。",
                "风险判断": "风险并非平均分布，关键域需要优先投入治理资源。",
                "建议动作": "先压降高风险域，再推进跨域闭环。",
            },
        }
    if "证据" in mode:
        return {
            "focus": ["证明 headline", "主证明结构", "证据栈与结论"],
            "nodes": {
                "入口节点": "现象 / 问题入口",
                "动作节点": "验证动作 / 取证动作",
                "放大条件": "关键条件 / 规模因素",
                "结果节点": "证明结果 / 影响结果",
                "证据节点": "截图 / KPI / 日志 / 核验结果",
                "判断节点 / 控制节点": "管理结论 / 下一步动作",
            },
            "relations": {
                "主链因果": "现象 -> 验证 -> 结果",
                "辅助依赖": "KPI 与原始证据共同支撑判断",
                "放大关系": "规模或频次强化问题严重程度",
                "并行 / 汇聚": "多类证据汇聚到同一判断",
                "反馈 / 闭环": "结论回指整改验证要求",
            },
            "compression": {
                "标题句": "直接写明“证明了什么”",
                "节点文案": "现象、机制、结果三段式短句",
                "证据说明句": "证据必须回答它证明哪个判断",
                "页尾收束句": "把结论翻译成管理层可执行动作",
            },
            "closure": {
                "管理判断": "关键证据已足以支撑当前判断，不宜再停留在描述层。",
                "风险判断": "若不及时治理，问题会持续扩散或重复出现。",
                "建议动作": "围绕证据指向的关键控制点先行整改并复测。",
            },
        }
    return {
        "focus": ["主判断", "主结构", "证据与收束"],
        "nodes": {
            "入口节点": "",
            "动作节点": "",
            "放大条件": "",
            "结果节点": "",
            "证据节点": "",
            "判断节点 / 控制节点": "",
        },
        "relations": {
            "主链因果": "",
            "辅助依赖": "",
            "放大关系": "",
            "并行 / 汇聚": "",
            "反馈 / 闭环": "",
        },
        "compression": {
            "标题句": "",
            "节点文案": "",
            "证据说明句": "",
            "页尾收束句": "",
        },
        "closure": {
            "管理判断": "",
            "风险判断": "",
            "建议动作": "",
        },
    }


def choose_primary_template(answers: dict[str, Any], recommended_templates: list[str]) -> str:
    answer_template = str(answers.get("template", "")).strip()
    if answer_template:
        return answer_template
    if recommended_templates:
        return recommended_templates[0]
    return ""


def collect_template_docs(template_name: str) -> list[str]:
    if not template_name:
        return []
    template_dir = ROOT / "templates" / "layouts" / template_name
    if not template_dir.exists():
        return []
    docs: list[str] = []
    for name in TEMPLATE_DOC_CANDIDATES:
        if (template_dir / name).exists():
            docs.append(f"templates/layouts/{template_name}/{name}")
    return docs


def collect_domain_docs(domain_name: str) -> list[str]:
    if not domain_name or domain_name == "未提取到":
        return []
    domain_clean = domain_name.strip("`")
    domain_dir = ROOT / "domain_packs" / domain_clean
    if not domain_dir.exists():
        return []
    names = [
        "domain_profile.md",
        "story_patterns.md",
        "page_logic.md",
        "diagram_logic.md",
        "terminology_rules.md",
        "qa_rules.md",
        "rewrite_rules.md",
    ]
    return [f"domain_packs/{domain_clean}/{name}" for name in names if (domain_dir / name).exists()]


def parse_brief_value(text: str, label: str) -> str:
    match = re.search(rf"-\s*{re.escape(label)}：(.+)", text)
    return match.group(1).strip() if match else ""


def analyze_project(project_dir: Path) -> dict[str, Any]:
    brief_path = project_dir / "project_brief.md"
    recommendation_path = project_dir / "notes" / "template_domain_recommendation.md"
    storyline_path = project_dir / "notes" / "storyline.md"
    outline_path = project_dir / "notes" / "page_outline.md"
    answers = load_plan_answers(project_dir)
    sources = collect_sources(project_dir)

    files = {
        "brief": brief_path,
        "recommendation": recommendation_path,
        "storyline": storyline_path,
        "outline": outline_path,
    }
    missing_files = [name for name, path in files.items() if not path.exists()]
    placeholder_map = {
        name: find_placeholder_lines(read_text(path))
        for name, path in files.items()
        if path.exists()
    }

    recommendation_text = read_text(recommendation_path)
    brief_text = read_text(brief_path)
    storyline_text = read_text(storyline_path)
    outline_text = read_text(outline_path)
    outline_entries = parse_outline_entries(outline_text)

    blockers: list[str] = []
    warnings: list[str] = []

    if missing_files:
        blockers.append(f"缺少关键规划文件：{', '.join(missing_files)}")
    if not sources and not answers.get("source_docs"):
        warnings.append("项目 sources/ 下还没有归档源材料，正式生成时需确认是纯对话生成还是仍要补导入。")
    brief_blockers, brief_warnings = analyze_brief_placeholders(brief_text)
    if brief_blockers:
        blockers.append("`project_brief.md` 仍缺少核心字段：" + "、".join(brief_blockers))
    elif placeholder_map.get("brief"):
        warnings.append("`project_brief.md` 仍有非核心待确认项，但不阻塞 `produce`。")
    for label in brief_warnings:
        warnings.append(f"`project_brief.md` 的可选字段“{label}”仍待补齐。")
    if placeholder_map.get("storyline"):
        blockers.append("`notes/storyline.md` 仍存在待补齐的章节目标或复杂页规划。")
    if placeholder_map.get("outline"):
        blockers.append("`notes/page_outline.md` 仍存在待补齐的页面意图/证明目标/页型定义。")
    if not recommendation_text:
        blockers.append("缺少模板与行业建议，无法稳定进入 Strategist。")

    page_range_text = parse_brief_value(brief_text, "页数范围")
    min_pages, max_pages = parse_page_range(page_range_text)
    page_count = len(outline_entries)
    if min_pages is not None and page_count < min_pages:
        blockers.append(f"`notes/page_outline.md` 当前仅 {page_count} 页，低于 brief 要求的最少 {min_pages} 页。")
    if max_pages is not None and page_count > max_pages:
        warnings.append(f"`notes/page_outline.md` 当前 {page_count} 页，已超过 brief 建议上限 {max_pages} 页。")

    recommended_domain = extract_recommendation(recommendation_text, "推荐行业包")
    recommended_templates = extract_recommendation_list(recommendation_text, "推荐模板")
    primary_template = choose_primary_template(answers, recommended_templates)
    normalized_primary_template = normalize_template_id(primary_template)

    complex_pages: list[dict[str, str]] = []
    for entry in outline_entries:
        explicit_complex = entry.get("是否复杂页", "").strip() in {"是", "true", "True", "YES", "yes"}
        inferred = infer_complex_mode(entry)
        inferred_pattern = infer_advanced_pattern(inferred)
        heuristic_complex = (
            normalized_primary_template == "security_service"
            and inferred_pattern not in {"无", "none"}
            and inferred.get("blueprint") not in {"", "03_content.svg"}
        )
        is_complex = explicit_complex or heuristic_complex
        if not is_complex:
            continue
        title = entry.get("页面类型") or entry.get("推荐页型") or f"第 {entry['page_num']} 页复杂页"
        complex_pages.append(
            {
                "page_num": entry["page_num"],
                "title": title,
                "page_role": entry.get("页面角色", ""),
                "page_intent": entry.get("页面意图", ""),
                "proof_goal": entry.get("证明目标", ""),
                "main_judgment": entry.get("核心判断", ""),
                "evidence": entry.get("支撑证据", ""),
                "page_type": entry.get("推荐页型", ""),
                "mode": inferred["mode"],
                "structure": inferred["structure"],
                "blueprint": inferred["blueprint"],
            }
        )

    return {
        "project_dir": str(project_dir),
        "answers": answers,
        "sources": sources,
        "missing_files": missing_files,
        "placeholder_map": placeholder_map,
        "blockers": blockers,
        "warnings": warnings,
        "recommended_domain": recommended_domain,
        "recommended_templates": recommended_templates,
        "primary_template": primary_template,
        "brief_text": brief_text,
        "page_count": len(outline_entries),
        "storyline_sections": len(re.findall(r"^### 章节", storyline_text, flags=re.MULTILINE)),
        "outline_entries": outline_entries,
        "complex_pages": complex_pages,
        "template_docs": collect_template_docs(primary_template),
        "domain_docs": collect_domain_docs(recommended_domain),
    }


def generate_design_spec_scaffold_text(analysis: dict[str, Any]) -> str:
    answers = analysis["answers"]
    brief_text = analysis["brief_text"]
    project_name = str(answers.get("project_name") or parse_brief_value(brief_text, "项目名称") or Path(analysis["project_dir"]).name)
    audience = str(answers.get("audience") or parse_brief_value(brief_text, "主要受众") or "待确认")
    scenario = str(answers.get("scenario") or parse_brief_value(brief_text, "场景") or "待确认")
    goal = str(answers.get("goal") or parse_brief_value(brief_text, "核心目标") or "待确认")
    style = str(answers.get("style") or parse_brief_value(brief_text, "风格偏好") or "待确认")
    language = str(answers.get("language") or parse_brief_value(brief_text, "语言") or "中文")
    format_key = str(answers.get("format") or parse_brief_value(brief_text, "输出格式") or "ppt169")
    priorities = answers.get("priorities") or []
    canvas = CANVAS_SPECS.get(format_key, CANVAS_SPECS["ppt169"])
    domain_clean = str(analysis["recommended_domain"]).strip("`")

    lines = [
        "# Design Specification Scaffold",
        "",
        "> 这是 `produce` 阶段生成的项目级 design_spec 草案骨架。",
        "> Strategist 应在此基础上结合模板、行业包、案例与用户确认结果，补齐并最终保存为项目根目录 `design_spec.md`。",
        "",
        "## I. Project Information",
        f"- Project Name: {project_name}",
        f"- Canvas Format: {format_key} ({canvas['name']})",
        f"- Target Audience: {audience}",
        f"- Scenario: {scenario}",
        f"- Core Goal: {goal}",
        f"- Preferred Template: {analysis['primary_template'] or '待确认'}",
        f"- Domain Pack: {analysis['recommended_domain']}",
        f"- Style Preference: {style}",
        f"- Language: {language}",
        "",
        "## II. Canvas Specification",
        f"- ViewBox: `{canvas['viewbox']}`",
        f"- Dimensions: {canvas['dimensions']}",
        "- Safe Area: 待 Strategist 结合模板骨架确认",
        "",
        "## III. Visual Theme",
        f"- Theme Direction: 以 `{analysis['primary_template'] or '当前模板'}` 的品牌骨架为基础，结合 `{domain_clean or '当前行业包'}` 行业表达。",
        f"- Tone: {style}",
        "- Color Strategy: 待结合模板 design_spec 与品牌规则确认",
        "",
        "## IV. Typography System",
        "- Font Plan: 待结合模板 design_spec 补齐",
        "- Body Baseline: 待结合内容密度确认",
        "",
        "## V. Layout Principles",
        "- Fixed Skeleton: 必须保留模板 Logo、安全区、页脚和装饰条",
        "- Flexible Body: 正文区允许按页型与复杂模式灵活编排",
        "- Density Rule: 复杂页靠结构增密，不靠缩字号增密",
        "",
        "## VI. Icon Usage Specification",
        "- Icon Source: 待 Strategist 根据模板与图标库确认",
        "- Approved Icon Inventory: 待补齐",
        "",
        "## VII. Chart Reference List",
        "- 待按实际数据页补齐",
        "",
        "## VIII. Image Resource List",
        "- 待结合源材料、历史案例与 AI 生图策略补齐",
        "",
        "## IX. Content Outline",
        "",
    ]
    total_pages = len(analysis["outline_entries"])
    for entry in analysis["outline_entries"]:
        page_num = entry.get("page_num", "")
        page_num_int = int(page_num) if str(page_num).isdigit() else None
        page_title = entry.get("页面类型") or entry.get("推荐页型") or f"第 {page_num} 页"
        matched_complex = next((item for item in analysis["complex_pages"] if item["page_num"] == page_num), None)
        preferred_template = infer_preferred_template(
            entry,
            analysis["primary_template"],
            matched_complex,
            page_num=page_num_int,
            total_pages=total_pages,
        )
        advanced_pattern = infer_advanced_pattern(matched_complex) if matched_complex else "无"
        layout_mode = infer_layout_mode(entry, preferred_template)
        lines.extend(
            [
                f"### 第 {page_num} 页 - {page_title}",
                f"- **布局**：{layout_mode}",
                f"- **页面意图**：{entry.get('页面意图', '待补齐')}",
                f"- **证明目标**：{entry.get('证明目标', '待补齐')}",
                f"- **高级正文模式**：{advanced_pattern}",
                f"- **优先页型**：`{preferred_template}`",
            ]
        )
        if preferred_template in {"03_content.svg", "11_list.svg"}:
            lines.append("- **回退原因**：待 Strategist 说明为什么不命中更强页型")
        lines.extend(
            [
                f"- **标题**：{page_title}",
                f"- **图表**：{entry.get('推荐页型', '待确认')}",
                "- **内容**：",
                f"  - 核心判断：{entry.get('核心判断', '待补齐')}",
                f"  - 支撑证据：{entry.get('支撑证据', '待补齐')}",
                f"  - 展示重点：{', '.join(priorities) if priorities else '待补齐'}",
                "",
            ]
        )

    lines.extend(
        [
            "## X. Speaker Notes Requirements",
            "- 命名需与 SVG 页面对应",
            "- 每页备注应包含：过渡语、核心讲法、时间提示",
            "",
            "## XI. Technical Constraints Reminder",
            "- 需遵守模板骨架、SVG 兼容规则与品牌保护区规则",
            "- 命中复杂页前，必须先补齐 `notes/complex_page_models.md`",
            "",
            "## XII. Design Checklist",
            "- 逐页检查文本可读性、边距、安全区、密度与图文协同",
            "- 命中复杂页时，额外检查主判断、结构、证据与收束",
            "",
            "## XIII. Next Steps",
            "- Strategist 根据本草案生成最终 `design_spec.md`",
            "- 若存在复杂页，先同步页面标题，再补齐复杂页建模",
            "- Executor 进入前运行 `check_complex_page_model.py <project_path>`",
        ]
    )
    return "\n".join(lines)


def generate_design_spec_draft_text(analysis: dict[str, Any]) -> str:
    answers = analysis["answers"]
    brief_text = analysis["brief_text"]
    project_name = str(answers.get("project_name") or parse_brief_value(brief_text, "项目名称") or Path(analysis["project_dir"]).name)
    audience = str(answers.get("audience") or parse_brief_value(brief_text, "主要受众") or "待确认")
    scenario = str(answers.get("scenario") or parse_brief_value(brief_text, "场景") or "待确认")
    goal = str(answers.get("goal") or parse_brief_value(brief_text, "核心目标") or "待确认")
    style = str(answers.get("style") or parse_brief_value(brief_text, "风格偏好") or "待确认")
    language = str(answers.get("language") or parse_brief_value(brief_text, "语言") or "中文")
    format_key = str(answers.get("format") or parse_brief_value(brief_text, "输出格式") or "ppt169")
    priorities = answers.get("priorities") or []
    canvas = CANVAS_SPECS.get(format_key, CANVAS_SPECS["ppt169"])
    domain_clean = str(analysis["recommended_domain"]).strip("`")

    lines = [
        f"# {project_name} - Design Specification Draft",
        "",
        "> 这是 `produce` 阶段生成的项目级 design_spec 初稿。",
        "> 它已经把 `/plan`、模板建议、行业包、复杂页候选和页级 outline 拼成一份可继续编辑的草稿；Strategist 需要在此基础上完成八项确认并产出最终 `design_spec.md`。",
        "",
        "## I. Project Information",
        f"- Project Name: {project_name}",
        f"- Canvas Format: {format_key} ({canvas['name']})",
        f"- Target Audience: {audience}",
        f"- Scenario: {scenario}",
        f"- Core Goal: {goal}",
        f"- Preferred Template: {analysis['primary_template'] or '待确认'}",
        f"- Domain Pack: {domain_clean or '待确认'}",
        f"- Style Preference: {style}",
        f"- Language: {language}",
        f"- Priority Messages: {', '.join(priorities) if priorities else '待补齐'}",
        "",
        "## II. Canvas Specification",
        f"- ViewBox: `{canvas['viewbox']}`",
        f"- Dimensions: {canvas['dimensions']}",
        "- Margin Guideline: 待 Strategist 结合模板骨架确认",
        "- Title Area: 待结合模板标题安全区确认",
        "- Content Area: 待结合模板正文安全区确认",
        "- Footer Area: 待结合页脚保护区确认",
        "",
        "## III. Visual Theme",
        f"- Theme Direction: 以 `{analysis['primary_template'] or '当前模板'}` 的品牌骨架为基础，结合 `{domain_clean or '当前行业包'}` 的行业表达逻辑。",
        f"- Tone: {style}",
        "- Primary / Secondary / Accent Colors: 待结合模板 design_spec 与品牌规则确认",
        "- Background Strategy: 固定页沿用模板骨架，正文页以安全区内灵活编排为主",
        "",
        "## IV. Typography System",
        "- Font Plan: 待结合模板 design_spec 补齐",
        "- Body Baseline: 待结合内容密度确认",
        "- Dense Page Override: 复杂页允许结构增密，但不允许靠过度缩字号解决",
        "",
        "## V. Layout Principles",
        "- Fixed Skeleton: 必须保留模板 Logo、安全区、页脚和装饰条",
        "- Flexible Body: 正文区允许按页型与复杂模式灵活编排",
        "- Brand Safety: 标题、正文、图形不得侵入 Logo / 页脚 / 装饰保护区",
        "- Complexity Rule: 只有当文档确实存在链路 / 分层 / 矩阵 / 闭环关系时才命中复杂页",
        "",
        "## VI. Icon Usage Specification",
        "- Icon Source: 待 Strategist 根据模板与图标库确认",
        "- Approved Icon Inventory: 待补齐",
        "",
        "## VII. Chart Reference List",
        "- 待按实际数据页补齐",
        "",
        "## VIII. Image Resource List",
    ]
    if analysis["sources"]:
        lines.extend(f"- Existing Source: {name}" for name in analysis["sources"])
    else:
        lines.append("- 当前未检测到归档源图或源文件，需结合项目材料策略补齐")
    lines.extend(
        [
            "- AI Image Policy: 待结合 brief 中的原图优先 / AI 补图约束确认",
            "",
            "## IX. Content Outline",
            "",
        ]
    )
    total_pages = len(analysis["outline_entries"])
    for entry in analysis["outline_entries"]:
        page_num = entry.get("page_num", "")
        page_num_int = int(page_num) if str(page_num).isdigit() else None
        page_title = entry.get("页面类型") or entry.get("推荐页型") or f"第 {page_num} 页"
        matched_complex = next((item for item in analysis["complex_pages"] if item["page_num"] == page_num), None)
        preferred_template = infer_preferred_template(
            entry,
            analysis["primary_template"],
            matched_complex,
            page_num=page_num_int,
            total_pages=total_pages,
        )
        advanced_pattern = infer_advanced_pattern(matched_complex) if matched_complex else "无"
        layout_mode = infer_layout_mode(entry, preferred_template)
        lines.extend(
            [
                f"### 第 {page_num} 页 - {page_title}",
                f"- **Layout**: {layout_mode}",
                f"- **Page Intent**: {entry.get('页面意图', '待补齐')}",
                f"- **Proof Goal**: {entry.get('证明目标', '待补齐')}",
                f"- **Advanced Pattern**: {advanced_pattern}",
                f"- **Preferred Template**: `{preferred_template}`",
            ]
        )
        if preferred_template in {"03_content.svg", "11_list.svg"}:
            lines.append("- **Fallback Reason**: 待 Strategist 说明为什么不命中更强页型")
        lines.extend(
            [
                f"- **Title**: {page_title}",
                f"- **Core Judgment**: {entry.get('核心判断', '待补齐')}",
                f"- **Supporting Evidence**: {entry.get('支撑证据', '待补齐')}",
                f"- **Recommended Page Type**: {entry.get('推荐页型', '待补齐')}",
                f"- **Complex Page Candidate**: {'Yes' if matched_complex else 'No'}",
                "- **Content Points**:",
                f"  - Audience Focus Alignment: {audience}",
                f"  - Goal Alignment: {goal}",
                f"  - Priority Messages: {', '.join(priorities) if priorities else '待补齐'}",
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

    lines.extend(
        [
            "## X. Speaker Notes Requirements",
            "- 命名需与 SVG 页面对应",
            "- 每页备注应包含：过渡语、核心讲法、时间提示",
            "",
            "## XI. Technical Constraints Reminder",
            "- 需遵守模板骨架、SVG 兼容规则与品牌保护区规则",
            "- 命中复杂页前，必须先补齐 `notes/complex_page_models.md`",
            "- 若使用模板本地图标或品牌资产，需在最终 design_spec 中明确来源与用法",
            "",
            "## XII. Design Checklist",
            "- 逐页检查文本可读性、边距、安全区、密度与图文协同",
            "- 命中复杂页时，额外检查主判断、结构、证据与收束",
            "- 若某页仍无法说明为何必须复杂，应主动回退页型",
            "",
            "## XIII. Next Steps",
            "- Strategist 根据本初稿生成最终 `design_spec.md`",
            "- 若存在复杂页，先同步页面标题，再补齐复杂页建模",
            "- Executor 进入前运行 `check_complex_page_model.py <project_path>`",
        ]
    )
    return "\n".join(lines)


def build_complex_model_scaffold(complex_pages: list[dict[str, str]]) -> str:
    lines = [
        "# 复杂页建模草稿",
        "",
        "> 这是 `produce` 阶段生成的预建模骨架。",
        "> 在 Strategist 输出最终 `design_spec.md` 后，请把这里的页面标题同步为与 design_spec 完全一致，再进入 `check_complex_page_model.py` 校验。",
        "",
    ]
    if not complex_pages:
        lines.extend(["- 当前 `page_outline.md` 未命中复杂页。", ""])
        return "\n".join(lines)

    for page in complex_pages:
        defaults = complex_mode_defaults(page["mode"])
        lines.extend(
            [
                f"#### 第 {page['page_num']} 页 {page['title']}",
                f"- 页面角色：{page['page_role'] or '待补齐'}",
                f"- 页面意图：{page['page_intent'] or '待补齐'}",
                f"- 证明目标：{page['proof_goal'] or '待补齐'}",
                f"- 主判断：{page['main_judgment'] or '待补齐'}",
                "- 分判断：",
                "  1. ",
                "  2. ",
                "  3. ",
                "- 论证主线：",
                "  - 现象 / 入口：",
                "  - 放大机制 / 关键条件：",
                "  - 结果 / 影响：",
                "  - 管理判断 / 动作要求：",
                f"- 主结构类型：{page['structure']}",
                f"- 结构选择理由：优先按 `{page['mode']}` 组织，因为该页在 outline 中已命中复杂结构。",
                "- 为什么不用其他结构：需要结合最终 design_spec 再补齐。",
                "- 关键节点：",
                f"  - 入口节点：{defaults['nodes']['入口节点']}",
                f"  - 动作节点：{defaults['nodes']['动作节点']}",
                f"  - 放大条件：{defaults['nodes']['放大条件']}",
                f"  - 结果节点：{defaults['nodes']['结果节点']}",
                f"  - 证据节点：{defaults['nodes']['证据节点']}",
                f"  - 判断节点 / 控制节点：{defaults['nodes']['判断节点 / 控制节点']}",
                "- 关键关系：",
                f"  - 主链因果：{defaults['relations']['主链因果']}",
                f"  - 辅助依赖：{defaults['relations']['辅助依赖']}",
                f"  - 放大关系：{defaults['relations']['放大关系']}",
                f"  - 并行 / 汇聚：{defaults['relations']['并行 / 汇聚']}",
                f"  - 反馈 / 闭环：{defaults['relations']['反馈 / 闭环']}",
                "- 证据挂载计划：",
                f"  - 现有支撑证据：{page['evidence'] or '待补齐'}",
                "  - 证据 A -> 节点 / 分判断：",
                "  - 证据 B -> 节点 / 分判断：",
                "- 证据分级：",
                "  - 直接证据：",
                "  - 结果证据：",
                "  - 旁证 / 背景证据：",
                "- 文本压缩计划：",
                f"  - 标题句：{defaults['compression']['标题句']}",
                f"  - 节点文案：{defaults['compression']['节点文案']}",
                f"  - 证据说明句：{defaults['compression']['证据说明句']}",
                f"  - 页尾收束句：{defaults['compression']['页尾收束句']}",
                "- 视觉焦点排序：",
                f"  1. {defaults['focus'][0]}",
                f"  2. {defaults['focus'][1]}",
                f"  3. {defaults['focus'][2]}",
                "- 页面收束方式：",
                f"  - 管理判断：{defaults['closure']['管理判断']}",
                f"  - 风险判断：{defaults['closure']['风险判断']}",
                f"  - 建议动作：{defaults['closure']['建议动作']}",
                f"- 推荐重型骨架：`{page['blueprint']}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_outputs(project_dir: Path, analysis: dict[str, Any]) -> dict[str, str]:
    notes_dir = project_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    readiness_path = notes_dir / "production_readiness.md"
    packet_path = notes_dir / "production_packet.md"
    strategist_path = notes_dir / "strategist_packet.md"
    complex_path = notes_dir / "complex_page_models.md"
    design_spec_scaffold_path = notes_dir / "design_spec_scaffold.md"
    design_spec_draft_path = notes_dir / "design_spec_draft.md"

    ready = not analysis["blockers"]

    readiness_lines = [
        "# 生产就绪度",
        "",
        f"- 是否可进入正式生成：{'是' if ready else '否'}",
        f"- 阻塞问题数：{len(analysis['blockers'])}",
        f"- 警告数：{len(analysis['warnings'])}",
        f"- 规划页数：{analysis['page_count']}",
        f"- 章节数：{analysis['storyline_sections']}",
        f"- 复杂页候选数：{len(analysis['complex_pages'])}",
        "",
        "## 阻塞问题",
    ]
    readiness_lines.extend(f"- {item}" for item in analysis["blockers"]) if analysis["blockers"] else readiness_lines.append("- 无")
    readiness_lines.extend(["", "## 警告"])
    readiness_lines.extend(f"- {item}" for item in analysis["warnings"]) if analysis["warnings"] else readiness_lines.append("- 无")
    readiness_lines.extend(["", "## 下一步建议"])
    if ready:
        readiness_lines.extend(
            [
                "- 现在可以进入 Strategist 八项确认与 design_spec 生成",
                "- 先阅读 `strategist_packet.md`，再开始补 design_spec",
                "- 命中复杂页时，先完善 `complex_page_models.md`，再进入 SVG 生成",
            ]
        )
    else:
        readiness_lines.extend(
            [
                "- 先修复阻塞问题，再执行 `ppt_agent.py produce <project_path>` 复检",
                "- 尤其优先补齐 `storyline.md` 与 `page_outline.md` 中的待确认项",
            ]
        )
    readiness_path.write_text("\n".join(readiness_lines) + "\n", encoding="utf-8")

    packet_lines = [
        "# 生产执行包",
        "",
        "## 一、项目摘要",
        f"- 项目路径：`{analysis['project_dir']}`",
        f"- 推荐行业包：{analysis['recommended_domain']}",
        f"- 推荐模板：{', '.join(f'`{item}`' for item in analysis['recommended_templates']) if analysis['recommended_templates'] else '未提取到'}",
        f"- 当前主模板：`{analysis['primary_template']}`" if analysis["primary_template"] else "- 当前主模板：待确认",
        f"- 规划页数：{analysis['page_count']}",
        f"- 章节数：{analysis['storyline_sections']}",
        f"- 复杂页候选数：{len(analysis['complex_pages'])}",
        "",
        "## 二、源材料",
    ]
    packet_lines.extend(f"- {name}" for name in analysis["sources"]) if analysis["sources"] else packet_lines.append("- 当前未检测到归档源文件")
    packet_lines.extend(
        [
            "",
            "## 三、Strategist 必读输入",
            "- `project_brief.md`",
            "- `notes/template_domain_recommendation.md`",
            "- `notes/storyline.md`",
            "- `notes/page_outline.md`",
            "- `notes/strategist_packet.md`",
        ]
    )
    if analysis["domain_docs"]:
        packet_lines.extend(["", "## 四、推荐行业包读取", *[f"- `{item}`" for item in analysis["domain_docs"]]])
    if analysis["template_docs"]:
        packet_lines.extend(["", "## 五、推荐模板文档读取", *[f"- `{item}`" for item in analysis["template_docs"]]])
    packet_lines.extend(
        [
            "",
            "## 六、Executor 进入前检查",
            "- 模板固定骨架、logo、安全区是否已明确",
            "- `notes/page_outline.md` 每页是否已能回答：页面意图 / 证明目标 / 推荐页型 / 是否复杂页",
            "- 命中复杂页时，是否已补齐 `notes/complex_page_models.md`",
            "- 是否已规划 SVG 逐页复核，而不是最后再统一补救",
            "",
            "## 七、当前阻塞与风险",
        ]
    )
    if analysis["blockers"] or analysis["warnings"]:
        packet_lines.extend(f"- {item}" for item in analysis["blockers"])
        packet_lines.extend(f"- {item}" for item in analysis["warnings"])
    else:
        packet_lines.append("- 当前未发现阻塞，可进入正式生成")
    packet_path.write_text("\n".join(packet_lines) + "\n", encoding="utf-8")

    strategist_lines = [
        "# Strategist 执行包",
        "",
        "## 一、启动顺序",
        "1. 先读取 `project_brief.md`、`notes/template_domain_recommendation.md`、`notes/storyline.md`、`notes/page_outline.md`",
        "2. 再读取本文件中的模板文档与行业包文档",
        "3. 完成八项确认后，输出项目级 `design_spec.md`",
        "4. 若存在复杂页候选，同步把页面标题和复杂模式写入 `design_spec.md`，并校正 `notes/complex_page_models.md` 的标题",
        "",
        "## 二、项目重点",
        f"- 行业包：{analysis['recommended_domain']}",
        f"- 主模板：{analysis['primary_template'] or '待确认'}",
        f"- 规划页数：{analysis['page_count']}",
        f"- 复杂页候选：{len(analysis['complex_pages'])}",
        "",
        "## 三、模板与行业包必读",
    ]
    strategist_lines.extend(f"- `{item}`" for item in analysis["template_docs"]) if analysis["template_docs"] else strategist_lines.append("- 当前未定位到模板专属文档")
    if analysis["domain_docs"]:
        strategist_lines.extend(["", "## 四、行业包必读", *[f"- `{item}`" for item in analysis["domain_docs"]]])
    strategist_lines.extend(["", "## 五、复杂页候选"])
    if analysis["complex_pages"]:
        for page in analysis["complex_pages"]:
            strategist_lines.append(
                f"- 第 {page['page_num']} 页《{page['title']}》：角色={page['page_role'] or '待补齐'}；模式={page['mode']}；建议骨架=`{page['blueprint']}`"
            )
    else:
        strategist_lines.append("- 当前未命中复杂页候选")
    strategist_lines.extend(
        [
            "",
            "## 六、design_spec 必补项",
            "- 每页必须明确：页面意图、证明目标、核心判断、支撑证据、推荐页型",
            "- 命中复杂页时，必须明确：高级正文模式、优先页型、后备页型",
            "- 必须把模板固定骨架、品牌元素、保护区写入 design_spec",
            "- 必须把行业包中的术语、图文协同、复杂页规则吸收到 design_spec",
            "",
            "## 七、复杂页同步要求",
            "- `notes/complex_page_models.md` 只是预建模骨架，不是最终校验版",
            "- 在 design_spec 确认复杂页标题后，先同步标题，再继续补齐字段",
            "- 进入复杂页 SVG 生成前，必须运行 `check_complex_page_model.py <project_path>`",
        ]
    )
    strategist_path.write_text("\n".join(strategist_lines) + "\n", encoding="utf-8")

    complex_path.write_text(build_complex_model_scaffold(analysis["complex_pages"]) + "\n", encoding="utf-8")
    design_spec_scaffold_path.write_text(generate_design_spec_scaffold_text(analysis) + "\n", encoding="utf-8")
    design_spec_draft_path.write_text(generate_design_spec_draft_text(analysis) + "\n", encoding="utf-8")

    return {
        "readiness": str(readiness_path),
        "packet": str(packet_path),
        "strategist_packet": str(strategist_path),
        "complex_models": str(complex_path),
        "design_spec_scaffold": str(design_spec_scaffold_path),
        "design_spec_draft": str(design_spec_draft_path),
    }


def build_production_packet(project_path: str | Path) -> tuple[dict[str, Any], dict[str, str]]:
    project_dir = Path(project_path).expanduser().resolve()
    analysis = analyze_project(project_dir)
    outputs = write_outputs(project_dir, analysis)
    return analysis, outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="生成正式进入 Strategist / Executor 前的生产就绪报告与执行包。")
    parser.add_argument("project_path", help="项目路径")
    args = parser.parse_args()

    analysis, outputs = build_production_packet(args.project_path)
    print(f"Production packet built: {args.project_path}")
    for label, path in outputs.items():
        print(f"  - {label}: {path}")
    print(f"  - ready_for_production: {'yes' if not analysis['blockers'] else 'no'}")
    if analysis["blockers"]:
        print("  - blockers:")
        for item in analysis["blockers"]:
            print(f"    * {item}")


if __name__ == "__main__":
    main()
