#!/usr/bin/env python3
"""Build a structured /plan intake packet for a PPT project."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FIELD_SPECS: list[dict[str, Any]] = [
    {
        "id": "project_name",
        "label": "项目名称",
        "group": "基础信息",
        "type": "text",
        "required": False,
        "question": "这份 PPT 的项目名或主题名是什么？",
    },
    {
        "id": "industry",
        "label": "行业",
        "group": "场景与行业",
        "type": "text",
        "required": True,
        "question": "这份 PPT 属于什么行业？是否有固定表达习惯或忌讳？",
    },
    {
        "id": "scenario",
        "label": "场景",
        "group": "场景与行业",
        "type": "text",
        "required": True,
        "question": "这份 PPT 的具体场景是什么，例如售前、汇报、总结、方案、案例证明、培训？",
    },
    {
        "id": "language",
        "label": "语言",
        "group": "基础信息",
        "type": "text",
        "required": False,
        "question": "输出语言是什么？",
        "default": "中文",
    },
    {
        "id": "format",
        "label": "输出格式",
        "group": "基础信息",
        "type": "text",
        "required": False,
        "question": "画布格式是什么，例如 ppt169、ppt43？",
        "default": "ppt169",
    },
    {
        "id": "audience",
        "label": "主要受众",
        "group": "展示对象",
        "type": "text",
        "required": True,
        "question": "这份 PPT 主要给谁看？是管理层、技术团队、客户领导、采购，还是混合受众？",
    },
    {
        "id": "secondary_audience",
        "label": "次要受众",
        "group": "展示对象",
        "type": "text",
        "required": False,
        "question": "有没有次要受众？",
    },
    {
        "id": "audience_focus",
        "label": "受众关注点",
        "group": "展示对象",
        "type": "text",
        "required": False,
        "question": "受众更关心过程、结果、方案、可信度还是 ROI？",
    },
    {
        "id": "goal",
        "label": "核心目标",
        "group": "本次目标",
        "type": "text",
        "required": True,
        "question": "这份 PPT 最终要达成什么目标？",
    },
    {
        "id": "desired_judgment",
        "label": "期待判断",
        "group": "本次目标",
        "type": "text",
        "required": False,
        "question": "看完后，希望对方形成什么判断？",
    },
    {
        "id": "desired_action",
        "label": "期待动作",
        "group": "本次目标",
        "type": "text",
        "required": False,
        "question": "看完后，希望对方采取什么动作？",
    },
    {
        "id": "priorities",
        "label": "展示重点",
        "group": "展示重点",
        "type": "list",
        "required": True,
        "question": "如果只能让对方记住 3 件事，希望是哪 3 件？",
    },
    {
        "id": "must_keep",
        "label": "必须保留的信息",
        "group": "展示重点",
        "type": "list",
        "required": False,
        "question": "哪些内容必须保留，不能被压缩掉？",
    },
    {
        "id": "template",
        "label": "指定模板",
        "group": "品牌与风格要求",
        "type": "text",
        "required": False,
        "question": "是否必须使用某个模板？",
    },
    {
        "id": "reference_cases",
        "label": "历史案例参考",
        "group": "品牌与风格要求",
        "type": "list",
        "required": False,
        "question": "是否有历史案例风格要对齐？",
    },
    {
        "id": "style",
        "label": "风格偏好",
        "group": "品牌与风格要求",
        "type": "text",
        "required": False,
        "question": "更偏稳妥清晰，还是高信息密度、专业感强？",
    },
    {
        "id": "complexity_preference",
        "label": "复杂度偏好",
        "group": "品牌与风格要求",
        "type": "text",
        "required": False,
        "question": "是否希望适度复杂页，还是尽量简洁？",
    },
    {
        "id": "brand_mandatories",
        "label": "必须固定的品牌元素",
        "group": "品牌与风格要求",
        "type": "list",
        "required": False,
        "question": "是否有必须沿用的 logo、背景、品牌素材或保护区规则？",
    },
    {
        "id": "source_docs",
        "label": "源文档",
        "group": "材料情况",
        "type": "list",
        "required": False,
        "question": "当前有哪些源文档，例如 docx、pdf、markdown？",
    },
    {
        "id": "source_ppts",
        "label": "历史 PPT",
        "group": "材料情况",
        "type": "list",
        "required": False,
        "question": "是否提供历史 PPT 作为参考？",
    },
    {
        "id": "source_assets",
        "label": "图片与图表素材",
        "group": "材料情况",
        "type": "list",
        "required": False,
        "question": "是否有图片、截图、图表或其他素材？",
    },
    {
        "id": "allow_ai_images",
        "label": "是否允许 AI 生图",
        "group": "材料情况",
        "type": "text",
        "required": False,
        "question": "是否允许 AI 生图？是否优先使用文档原图？",
    },
    {
        "id": "page_range",
        "label": "页数范围",
        "group": "交付约束",
        "type": "text",
        "required": False,
        "question": "预计页数范围是多少？",
    },
    {
        "id": "time_limit",
        "label": "时间限制",
        "group": "交付约束",
        "type": "text",
        "required": False,
        "question": "有无时间限制、汇报时长限制？",
    },
    {
        "id": "reading_mode",
        "label": "阅读方式",
        "group": "交付约束",
        "type": "text",
        "required": False,
        "question": "这份 PPT 更偏可讲述，还是偏可阅读？",
    },
    {
        "id": "forbidden_terms",
        "label": "禁用表达",
        "group": "交付约束",
        "type": "list",
        "required": False,
        "question": "有哪些表达、术语或措辞必须避免？",
    },
    {
        "id": "forbidden_visuals",
        "label": "禁用视觉形式",
        "group": "交付约束",
        "type": "list",
        "required": False,
        "question": "有哪些视觉形式必须避免？",
    },
]


FIELD_HINTS: dict[str, dict[str, Any]] = {
    "project_name": {
        "phase": 1,
        "why_needed": "便于后续项目归档与 brief 命名。",
    },
    "industry": {
        "phase": 1,
        "blocking_weak": True,
        "why_needed": "行业会直接影响术语体系、案例抽象方式和专业表达边界。",
        "suggestions": ["安服 / 攻防演练", "售前方案 / 解决方案", "经营汇报 / 内部复盘"],
    },
    "scenario": {
        "phase": 1,
        "blocking_weak": True,
        "why_needed": "场景决定这套 PPT 是要证明能力、解释方案还是推动决策。",
        "suggestions": ["客户汇报", "项目总结", "售前方案", "案例证明", "培训讲解"],
    },
    "audience": {
        "phase": 1,
        "blocking_weak": True,
        "why_needed": "受众不同，信息层级、术语密度和页面节奏都会明显不同。",
        "suggestions": ["客户管理层", "客户技术团队", "混合受众", "内部管理层", "内部执行团队"],
    },
    "goal": {
        "phase": 1,
        "blocking_weak": True,
        "why_needed": "目标不清，会导致后面故事线和复杂页都失焦。",
        "suggestions": ["证明能力", "展示成果", "推动采购/立项", "解释方案", "沉淀复盘"],
    },
    "priorities": {
        "phase": 2,
        "blocking_weak": True,
        "min_items": 3,
        "why_needed": "这会直接决定目录和正文重点，少于 3 个重点很难稳定收敛。",
        "suggestions": ["成果与结论", "攻击链路与证据", "问题与整改建议", "能力体系与方法论"],
    },
    "must_keep": {
        "phase": 2,
        "why_needed": "帮助后续压缩文案时保留关键信息。",
    },
    "template": {
        "phase": 2,
        "why_needed": "模板会决定品牌骨架、Logo、安全区与固定页结构。",
        "suggestions": ["长亭通用墨绿色", "长亭安服", "其他指定模板"],
    },
    "reference_cases": {
        "phase": 2,
        "why_needed": "可帮助 Agent 对齐历史案例的结构与复杂页打法。",
    },
    "style": {
        "phase": 2,
        "why_needed": "用于平衡稳妥清晰和高信息密度的取舍。",
        "suggestions": ["稳妥清晰", "专业克制", "高信息密度", "复杂页适中"],
    },
    "complexity_preference": {
        "phase": 2,
        "why_needed": "决定复杂页的比例和复杂结构是否要主动命中。",
        "suggestions": ["尽量简洁", "少量复杂页", "复杂页偏多但服务内容"],
    },
    "brand_mandatories": {
        "phase": 2,
        "why_needed": "避免正式生成时遗漏 Logo、背景、保护区等品牌硬约束。",
    },
    "source_docs": {
        "phase": 3,
        "why_needed": "决定正文提炼的主输入来源。",
    },
    "source_ppts": {
        "phase": 3,
        "why_needed": "有助于吸收既有页型与表达方式。",
    },
    "source_assets": {
        "phase": 3,
        "why_needed": "决定是否优先使用原图、截图和现成证据素材。",
    },
    "allow_ai_images": {
        "phase": 3,
        "why_needed": "会影响图片获取方式与风格控制。",
        "suggestions": ["优先原图，不够再 AI 生图", "允许 AI 生图", "禁止 AI 生图"],
    },
    "page_range": {
        "phase": 3,
        "why_needed": "页数约束会直接影响文案压缩和复杂页分配。",
    },
    "time_limit": {
        "phase": 3,
        "why_needed": "决定内容展开深度和是否偏演讲稿式表达。",
    },
    "reading_mode": {
        "phase": 3,
        "why_needed": "决定页面是偏演示讲述还是偏阅读浏览。",
        "suggestions": ["偏可讲述", "偏可阅读", "两者兼顾"],
    },
    "forbidden_terms": {
        "phase": 3,
        "why_needed": "避免出现客户敏感或内部禁用表达。",
    },
    "forbidden_visuals": {
        "phase": 3,
        "why_needed": "帮助避开用户明确不接受的视觉形式。",
    },
}


WEAK_TEXT_PATTERNS = [
    r"^都可以$",
    r"^都行$",
    r"^随意$",
    r"^不限$",
    r"^看着办$",
    r"^先做一版$",
    r"^你定$",
    r"^按你来$",
    r"^自行判断$",
    r"^暂无$",
    r"^没有要求$",
    r"^没有限制$",
    r"^普通汇报$",
    r"^高级一点$",
    r"^专业一点$",
]


SECURITY_SERVICE_KEYWORDS = [
    "安服",
    "hw",
    "攻防",
    "攻防演练",
    "红队",
    "蓝队",
    "安全运营",
    "漏洞",
    "复测",
    "整改",
    "攻击队",
    "演练复盘",
]

CHAITIN_KEYWORDS = [
    "长亭",
    "chaitin",
]


def unique_list(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = normalize_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def get_field_hint(spec_id: str) -> dict[str, Any]:
    return FIELD_HINTS.get(spec_id, {})


def get_spec_map() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in FIELD_SPECS}


def split_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = value.split(",")
    return [str(item).strip() for item in items if str(item).strip()]


def normalize_value(spec: dict[str, Any], value: Any) -> Any:
    if spec["type"] == "list":
        return split_list(value)
    if value is None:
        return str(spec.get("default", "")).strip()
    return str(value).strip()


def create_empty_answers() -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for spec in FIELD_SPECS:
        answers[spec["id"]] = normalize_value(spec, spec.get("default"))
    return answers


def merge_answers(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    spec_map = get_spec_map()
    for key, value in override.items():
        if key not in spec_map:
            continue
        normalized = normalize_value(spec_map[key], value)
        if spec_map[key]["type"] == "list":
            if normalized:
                merged[key] = normalized
        elif normalized:
            merged[key] = normalized
    return merged


def load_answers_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_known_answers(answers: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for spec in FIELD_SPECS:
        value = answers.get(spec["id"])
        if spec["type"] == "list":
            if value:
                lines.append(f"- {spec['label']}：{', '.join(value)}")
        elif value:
                lines.append(f"- {spec['label']}：{value}")
    return lines


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def is_weak_text(value: str) -> bool:
    text = normalize_text(value)
    if not text:
        return False
    compact = re.sub(r"\s+", "", text)
    if len(compact) <= 1:
        return True
    return any(re.search(pattern, compact, flags=re.IGNORECASE) for pattern in WEAK_TEXT_PATTERNS)


def infer_domain_context(answers: dict[str, Any]) -> dict[str, str]:
    text_parts: list[str] = []
    for key in (
        "industry",
        "scenario",
        "goal",
        "template",
        "style",
        "complexity_preference",
        "desired_judgment",
    ):
        text_parts.append(normalize_text(answers.get(key)))
    for key in ("priorities", "must_keep", "reference_cases", "brand_mandatories", "source_docs", "source_ppts"):
        text_parts.extend(answers.get(key) or [])

    combined = " ".join(text_parts)
    lower = combined.lower()
    template_text = normalize_text(answers.get("template"))
    template_lower = template_text.lower()

    security_hit = any(keyword in lower for keyword in SECURITY_SERVICE_KEYWORDS)
    chaitin_hit = any(keyword in lower for keyword in CHAITIN_KEYWORDS)

    if "security_service" in template_lower or "长亭安服" in template_text:
        domain_id = "security_service"
        domain_label = "安服 / 长亭安服"
        template_hint = "长亭安服"
        reason = "当前信息已明显命中安服 / 攻防复盘 / 能力证明类场景。"
    elif "chaitin" in template_lower or "长亭通用墨绿色" in template_text:
        domain_id = "chaitin_brand"
        domain_label = "长亭品牌通用"
        template_hint = "长亭通用墨绿色"
        reason = "当前模板已明确为长亭品牌通用表达。"
    elif security_hit:
        domain_id = "security_service"
        domain_label = "安服 / 长亭安服"
        template_hint = "长亭安服"
        reason = "行业与场景更像安服方案、攻防演练、能力证明或安全运营类胶片。"
    elif chaitin_hit:
        domain_id = "chaitin_brand"
        domain_label = "长亭品牌通用"
        template_hint = "长亭通用墨绿色"
        reason = "当前信息命中了长亭品牌语境，但还未明确是通用品牌表达还是安服专项表达。"
    else:
        domain_id = "general"
        domain_label = "通用场景"
        template_hint = ""
        reason = "当前信息未明显命中特定行业包或长亭品牌模板。"

    return {
        "domain_id": domain_id,
        "domain_label": domain_label,
        "template_hint": template_hint,
        "reason": reason,
    }


def build_item_for_field(field_id: str, *, status: str = "domain_followup", blocking: bool = False) -> dict[str, Any]:
    spec = get_spec_map()[field_id]
    hint = get_field_hint(field_id)
    return {
        "id": field_id,
        "label": spec["label"],
        "question": spec["question"],
        "group": spec["group"],
        "status": status,
        "phase": int(hint.get("phase", 3)),
        "why_needed": str(hint.get("why_needed") or ""),
        "reason": str(hint.get("why_needed") or ""),
        "suggestions": list(hint.get("suggestions") or []),
        "blocking": blocking,
        "priority": 0,
    }


def upsert_item(target: list[dict[str, Any]], item: dict[str, Any]) -> None:
    for index, current in enumerate(target):
        if current["id"] == item["id"]:
            merged = dict(current)
            merged.update(item)
            merged["suggestions"] = unique_list(list(current.get("suggestions") or []) + list(item.get("suggestions") or []))
            target[index] = merged
            return
    target.append(item)


def apply_domain_enrichment(
    answers: dict[str, Any],
    missing_optional: list[dict[str, Any]],
    weak_optional: list[dict[str, Any]],
    weak_blocking: list[dict[str, Any]],
    context: dict[str, str],
) -> None:
    domain_id = context["domain_id"]
    audience_text = normalize_text(answers.get("audience"))
    audience_lower = audience_text.lower()
    mixed_audience = any(token in audience_text for token in ["管理层", "领导"]) and any(
        token in audience_text for token in ["技术", "专家", "团队"]
    )

    def patch_optional(field_id: str, **updates: Any) -> None:
        for bucket in (missing_optional, weak_optional):
            for item in bucket:
                if item["id"] == field_id:
                    item.update(updates)
                    item["suggestions"] = unique_list(list(item.get("suggestions") or []))
                    return

    def add_optional(field_id: str, **updates: Any) -> None:
        item = build_item_for_field(field_id)
        item.update(updates)
        item["suggestions"] = unique_list(list(item.get("suggestions") or []))
        upsert_item(weak_optional, item)

    if domain_id == "security_service":
        patch_optional(
            "template",
            question="这次如果走长亭体系，建议明确用 `长亭安服` 还是 `长亭通用墨绿色`。如果是安服方案 / 攻防复盘 / 能力证明，通常优先 `长亭安服`。这次准备按哪套？",
            reason="安服场景里，模板不只是视觉皮肤，还会影响正文证明链、复杂页打法和品牌骨架。",
            suggestions=["长亭安服", "长亭通用墨绿色"],
            phase=2,
            priority=100,
        )
        patch_optional(
            "desired_judgment",
            question="这份安服 PPT 最希望对方最终形成哪类判断：能力成立、结果成立、可信度成立，还是整改建议成立？",
            reason="安服胶片更强调“要证明什么”，没有期待判断，正文很容易只有材料没有结论。",
            suggestions=["能力成立", "结果成立", "可信度成立", "整改建议成立"],
            phase=1,
            priority=96,
        )
        patch_optional(
            "complexity_preference",
            question="这次哪些页值得做复杂页：攻击链、证据链、治理闭环、能力地图，还是尽量少做？",
            reason="安服类 PPT 的复杂页应服务于证明链，而不是单纯为了显得高级。",
            suggestions=["攻击链 / 证据链页", "治理闭环 / 整改页", "能力地图 / 体系页", "尽量少做复杂页"],
            phase=2,
            priority=92,
        )
        patch_optional(
            "style",
            question="这次更偏历史胶片式的证明型表达，还是偏常规项目总结表达？",
            reason="安服场景里，“证明型表达”和“常规总结表达”会直接影响标题写法和图文组织方式。",
            suggestions=["证明型胶片表达", "常规项目总结表达", "两者结合但以证明为主"],
            phase=2,
            priority=88,
        )
        patch_optional(
            "source_assets",
            question="文档里的截图、证据图、攻击路径素材，是否允许直接作为案例证据页素材？",
            reason="安服页往往需要原始证据截图、链路图或现场素材，素材策略会影响案例页可信度。",
            suggestions=["优先使用文档原图/截图", "原图和 AI 示意结合", "只用 AI 示意，不直接用原图"],
            phase=3,
            priority=85,
        )
        patch_optional(
            "reference_cases",
            question="是否有历史安服胶片需要对齐？如果有，优先说明你最认可的是节奏、复杂页还是行文逻辑。",
            reason="安服类模板对历史胶片节奏和复杂页表达更敏感，案例偏好越清楚，后续越稳定。",
            phase=2,
            priority=82,
        )
        patch_optional(
            "brand_mandatories",
            question="长亭相关品牌元素这次要固定到什么程度？例如右上角 Logo、页脚、章节背景、保护区。",
            reason="长亭安服模板对品牌骨架和安全区要求更严格，最好在 /plan 先锁定。",
            suggestions=["固定完整品牌骨架", "固定 Logo 与页脚，正文灵活", "按模板默认即可"],
            phase=2,
            priority=80,
        )
        if mixed_audience:
            add_optional(
                "audience_focus",
                question="这套安服胶片更偏管理判断还是技术证据？如果是混合受众，建议明确主副线。",
                reason="混合受众下，如果不先定主副线，正文很容易又想讲管理结论、又想塞满技术细节。",
                suggestions=["管理判断为主，技术证据辅助", "技术证据为主，管理结论收束", "双线并行但主次分明"],
                phase=1,
                priority=94,
            )
        if normalize_text(answers.get("forbidden_terms")) == "":
            add_optional(
                "forbidden_terms",
                question="这次安服场景有没有明确要避开的措辞？例如过虚、过满、像 AI 自造的表达。",
                reason="安服正文很容易出现听起来高级但不合逻辑的术语，提前锁定禁用表达更稳。",
                suggestions=["避免 AI 自造术语", "避免过度营销腔", "沿用客户习惯说法"],
                phase=3,
                priority=40,
            )

    elif domain_id == "chaitin_brand":
        patch_optional(
            "template",
            question="这次更适合 `长亭通用墨绿色` 还是 `长亭安服`？如果是品牌表达、产品介绍、培训分享，通常优先 `长亭通用墨绿色`。",
            reason="长亭相关任务最好在 /plan 明确模板，不然后续品牌骨架和正文逻辑容易混用。",
            suggestions=["长亭通用墨绿色", "长亭安服"],
            phase=2,
            priority=100,
        )
        patch_optional(
            "brand_mandatories",
            question="长亭品牌元素这次要固定到什么程度？例如右上角 Logo、章节背景、页脚、保护区。",
            reason="长亭模板的 Logo、背景、页脚和保护区属于硬约束，最好在 /plan 先锁定。",
            suggestions=["固定完整品牌骨架", "固定 Logo 和背景", "按模板默认即可"],
            phase=2,
            priority=92,
        )
        patch_optional(
            "style",
            question="正文更偏稳妥品牌表达，还是在骨架固定前提下做更丰富、更专业的正文页？",
            reason="长亭通用模板强调品牌统一，但正文丰富度仍可调，最好提前确定边界。",
            suggestions=["稳妥品牌表达", "品牌骨架固定下正文更丰富", "偏培训分享 / 偏方案表达"],
            phase=2,
            priority=88,
        )
        patch_optional(
            "complexity_preference",
            question="在不破坏品牌骨架前提下，正文复杂度希望到什么程度？",
            reason="这会影响正文是以稳妥卡片页为主，还是引入更多图文协同页面。",
            suggestions=["尽量简洁", "少量复杂页", "正文适度丰富"],
            phase=2,
            priority=84,
        )


def build_followup_question(spec: dict[str, Any], issue_type: str) -> str:
    label = spec["label"]
    base = spec["question"]
    if issue_type == "weak":
        return f"{label} 目前还比较泛。{base}"
    return base


def build_issue_reason(spec: dict[str, Any], issue_type: str, value: Any) -> str:
    hint = get_field_hint(spec["id"])
    if issue_type == "missing":
        return str(hint.get("why_needed") or f"{spec['label']} 会直接影响后续 brief 与页面规划。")
    if spec["type"] == "list":
        min_items = int(hint.get("min_items", 1))
        if len(value or []) < min_items:
            return f"{spec['label']} 当前少于 {min_items} 项，后续目录和重点页容易失焦。"
        return f"{spec['label']} 仍偏泛，后续很难稳定转成明确页纲。"
    return f"{spec['label']} 当前表述偏泛，仍不足以稳定驱动 brief 与故事线。"


def analyze_field_issue(spec: dict[str, Any], value: Any) -> tuple[str | None, dict[str, Any] | None]:
    hint = get_field_hint(spec["id"])
    if spec["type"] == "list":
        items = value or []
        if not items:
            status = "missing"
        else:
            min_items = int(hint.get("min_items", 1))
            if len(items) < min_items or any(is_weak_text(item) for item in items):
                status = "weak"
            else:
                status = None
    else:
        text = normalize_text(value)
        if not text:
            status = "missing"
        elif is_weak_text(text):
            status = "weak"
        else:
            status = None

    if status is None:
        return None, None

    item = {
        "id": spec["id"],
        "label": spec["label"],
        "question": build_followup_question(spec, status),
        "group": spec["group"],
        "status": status,
        "phase": int(hint.get("phase", 3)),
        "why_needed": str(hint.get("why_needed") or ""),
        "reason": build_issue_reason(spec, status, value),
        "suggestions": list(hint.get("suggestions") or []),
        "blocking": bool(spec.get("required")) if status == "missing" else bool(hint.get("blocking_weak", False)),
    }
    return status, item


def build_conversation_stage(blocking_items: list[dict[str, Any]]) -> tuple[int, str, str]:
    if not blocking_items:
        return 4, "可进入 brief", "核心信息已齐备，可转入 brief、模板推荐与故事线规划。"

    phase = min(int(item.get("phase", 3)) for item in blocking_items)
    if phase <= 1:
        return 1, "锁定项目基础", "先锁定行业、场景、受众、目标，避免后续故事线方向跑偏。"
    if phase == 2:
        return 2, "锁定表达重点", "先明确展示重点、模板与复杂度取向，避免目录和高级页误判。"
    return 3, "锁定执行约束", "先补齐材料来源、页数和交付约束，方便进入稳定生产。"


def build_next_questions(
    blocking_items: list[dict[str, Any]],
    optional_items: list[dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, Any]]:
    ranked_blocking = sorted(
        blocking_items,
        key=lambda item: (
            int(item.get("phase", 3)),
            -int(item.get("priority", 0)),
            0 if item.get("status") == "missing" else 1,
            item["label"],
        ),
    )
    ranked_optional = sorted(
        optional_items,
        key=lambda item: (int(item.get("phase", 3)), -int(item.get("priority", 0)), item["label"]),
    )
    if ranked_blocking:
        return ranked_blocking[:limit]
    return ranked_optional[:limit]


def build_readiness(answers: dict[str, Any]) -> dict[str, Any]:
    missing_required: list[dict[str, str]] = []
    weak_blocking: list[dict[str, Any]] = []
    missing_optional: list[dict[str, str]] = []
    weak_optional: list[dict[str, Any]] = []

    for spec in FIELD_SPECS:
        value = answers.get(spec["id"])
        status, item = analyze_field_issue(spec, value)
        if item is None:
            continue
        if status == "missing" and spec.get("required"):
            missing_required.append(item)
        elif status == "missing":
            missing_optional.append(item)
        elif item["blocking"]:
            weak_blocking.append(item)
        else:
            weak_optional.append(item)

    domain_context = infer_domain_context(answers)
    apply_domain_enrichment(answers, missing_optional, weak_optional, weak_blocking, domain_context)

    blocking_items = [*missing_required, *weak_blocking]
    optional_items = [*missing_optional, *weak_optional]
    next_questions = build_next_questions(blocking_items, [], limit=3)
    suggested_optional_questions = build_next_questions([], optional_items, limit=3)
    stage_number, stage_label, round_objective = build_conversation_stage(blocking_items)
    ready_for_brief = len(missing_required) == 0 and len(weak_blocking) == 0
    return {
        "ready_for_brief": ready_for_brief,
        "missing_required": missing_required,
        "weak_blocking": weak_blocking,
        "missing_optional": missing_optional,
        "weak_optional": weak_optional,
        "blocking_items": blocking_items,
        "optional_items": optional_items,
        "next_questions": next_questions,
        "suggested_optional_questions": suggested_optional_questions,
        "conversation_stage": stage_label,
        "conversation_stage_number": stage_number,
        "round_objective": round_objective,
        "domain_context": domain_context,
    }


def load_round_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def diff_answers(previous: dict[str, Any], current: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for spec in FIELD_SPECS:
        key = spec["id"]
        before = previous.get(key)
        after = current.get(key)
        if spec["type"] == "list":
            before_list = before or []
            after_list = after or []
            if before_list != after_list:
                changes.append(
                    {
                        "id": key,
                        "label": spec["label"],
                        "before": before_list,
                        "after": after_list,
                    }
                )
        else:
            before_text = normalize_text(before)
            after_text = normalize_text(after)
            if before_text != after_text:
                changes.append(
                    {
                        "id": key,
                        "label": spec["label"],
                        "before": before_text,
                        "after": after_text,
                    }
                )
    return changes


def append_plan_round(
    notes_dir: Path,
    answers: dict[str, Any],
    readiness: dict[str, Any],
    next_turn_path: Path,
) -> tuple[Path, Path, Path]:
    rounds_path = notes_dir / "plan_rounds.json"
    dialogue_path = notes_dir / "plan_dialogue.md"
    session_status_path = notes_dir / "plan_session_status.md"
    history = load_round_history(rounds_path)

    previous_answers = history[-1].get("answers_snapshot", {}) if history else {}
    changes = diff_answers(previous_answers, answers)
    previous_stage = str(history[-1].get("conversation_stage", "")) if history else ""
    previous_ready = bool(history[-1].get("ready_for_brief", False)) if history else False
    should_append = not history or bool(changes) or previous_stage != readiness["conversation_stage"] or previous_ready != readiness["ready_for_brief"]

    if should_append:
        round_entry = {
            "round": len(history) + 1,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "conversation_stage": readiness["conversation_stage"],
            "round_objective": readiness["round_objective"],
            "ready_for_brief": readiness["ready_for_brief"],
            "domain_context": readiness["domain_context"],
            "changed_fields": changes,
            "blocking_items": readiness["blocking_items"],
            "next_questions": readiness["next_questions"],
            "suggested_optional_questions": readiness["suggested_optional_questions"],
            "next_turn_path": str(next_turn_path),
            "answers_snapshot": answers,
        }
        history.append(round_entry)
        rounds_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dialogue_lines = [
        "# /plan 对话轮次记录",
        "",
        f"- 累计轮次：{len(history)}",
        "",
    ]
    if not history:
        dialogue_lines.append("- 暂无轮次记录")
    else:
        for item in history:
            dialogue_lines.extend(
                [
                    f"## Round {item['round']}",
                    f"- 时间：{item['timestamp']}",
                    f"- 阶段：{item.get('conversation_stage') or '待确认'}",
                    f"- 本轮目标：{item.get('round_objective') or '待确认'}",
                    f"- 识别领域：{(item.get('domain_context') or {}).get('domain_label', '待确认')}",
                    f"- 模板倾向建议：{(item.get('domain_context') or {}).get('template_hint', '待确认') or '待确认'}",
                    f"- 是否可直接生成 brief：{'是' if item.get('ready_for_brief') else '否'}",
                    "",
                    "### 本轮新增 / 修改信息",
                ]
            )
            changed_fields = item.get("changed_fields") or []
            if changed_fields:
                for changed in changed_fields:
                    before = changed.get("before")
                    after = changed.get("after")
                    if isinstance(before, list):
                        before_text = "、".join(before) if before else "空"
                    else:
                        before_text = str(before or "空")
                    if isinstance(after, list):
                        after_text = "、".join(after) if after else "空"
                    else:
                        after_text = str(after or "空")
                    dialogue_lines.append(f"- {changed['label']}：{before_text} -> {after_text}")
            else:
                dialogue_lines.append("- 本轮未新增有效字段，主要是状态刷新或重复执行。")

            dialogue_lines.extend(["", "### 本轮建议继续追问", ""])
            next_questions = item.get("next_questions") or []
            optional_questions = item.get("suggested_optional_questions") or []
            if next_questions:
                for idx, question in enumerate(next_questions, start=1):
                    dialogue_lines.append(f"{idx}. {question['question']}")
            elif optional_questions:
                for idx, question in enumerate(optional_questions, start=1):
                    dialogue_lines.append(f"{idx}. {question['question']}")
            else:
                dialogue_lines.append("1. 当前已可进入 brief / storyline 阶段。")
            dialogue_lines.append("")
    dialogue_path.write_text("\n".join(dialogue_lines) + "\n", encoding="utf-8")

    latest = history[-1] if history else {}
    session_lines = [
        "# /plan 会话状态",
        "",
        f"- 最新轮次：{latest.get('round', 0)}",
        f"- 当前阶段：{readiness['conversation_stage']}",
        f"- 本轮目标：{readiness['round_objective']}",
        f"- 识别领域：{readiness['domain_context']['domain_label']}",
        f"- 模板倾向建议：{readiness['domain_context']['template_hint'] or '待确认'}",
        f"- 是否可直接生成 brief：{'是' if readiness['ready_for_brief'] else '否'}",
        f"- 下一轮话术：`{next_turn_path}`",
        f"- 轮次记录：`{dialogue_path}`",
    ]
    if readiness["next_questions"]:
        session_lines.extend(["", "## 当前必须优先补的 1-3 个问题"])
        for idx, item in enumerate(readiness["next_questions"], start=1):
            session_lines.append(f"{idx}. {item['question']}")
    elif readiness["suggested_optional_questions"]:
        session_lines.extend(["", "## 当前建议补强的问题（非阻塞）"])
        for idx, item in enumerate(readiness["suggested_optional_questions"], start=1):
            session_lines.append(f"{idx}. {item['question']}")
    else:
        session_lines.extend(["", "## 当前状态", "- 可直接进入 brief / storyline 阶段。"])
    session_status_path.write_text("\n".join(session_lines) + "\n", encoding="utf-8")

    return rounds_path, dialogue_path, session_status_path


def write_plan_packet(project_dir: Path, answers: dict[str, Any], readiness: dict[str, Any]) -> dict[str, str]:
    notes_dir = project_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)

    answers_path = notes_dir / "plan_answers.json"
    questions_path = notes_dir / "plan_questions.md"
    readiness_path = notes_dir / "plan_readiness.md"
    agent_state_path = notes_dir / "plan_agent_state.json"
    next_turn_path = notes_dir / "plan_next_turn.md"

    answers_path.write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    agent_state = {
        "ready_for_brief": readiness["ready_for_brief"],
        "conversation_stage": readiness["conversation_stage"],
        "conversation_stage_number": readiness["conversation_stage_number"],
        "round_objective": readiness["round_objective"],
        "domain_context": readiness["domain_context"],
        "blocking_items": readiness["blocking_items"],
        "optional_items": readiness["optional_items"],
        "next_questions": readiness["next_questions"],
        "suggested_optional_questions": readiness["suggested_optional_questions"],
    }
    agent_state_path.write_text(json.dumps(agent_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    question_lines = [
        "# /plan 追问清单",
        "",
        "## 当前已知信息",
    ]
    known_lines = summarize_known_answers(answers)
    if known_lines:
        question_lines.extend(known_lines)
    else:
        question_lines.append("- 暂无")

    question_lines.extend(
        [
            "",
            "## 当前 Agent 轮次状态",
            f"- 当前阶段：{readiness['conversation_stage']}",
            f"- 本轮目标：{readiness['round_objective']}",
            f"- 是否可直接生成 brief：{'是' if readiness['ready_for_brief'] else '否'}",
            f"- 识别领域：{readiness['domain_context']['domain_label']}",
            f"- 模板倾向建议：{readiness['domain_context']['template_hint'] or '待用户确认 / 系统后续推荐'}",
            f"- 识别依据：{readiness['domain_context']['reason']}",
            "",
            "## 本轮优先追问（建议最多 3 个）",
            "",
        ]
    )
    if readiness["next_questions"]:
        for index, item in enumerate(readiness["next_questions"], start=1):
            question_lines.append(f"{index}. [{item['group']}] {item['question']}")
            question_lines.append(f"   - 原因：{item['reason']}")
            if item.get("suggestions"):
                question_lines.append(f"   - 可给用户的建议方向：{' / '.join(item['suggestions'])}")
    else:
        question_lines.append("1. 当前关键信息已齐备，可进入 brief / storyline 阶段。")

    if readiness["blocking_items"]:
        question_lines.extend(["", "## 当前阻塞项", ""])
        for item in readiness["blocking_items"]:
            question_lines.append(f"- [{item['group']}] {item['label']}（{item['status']}）：{item['reason']}")
    elif readiness["suggested_optional_questions"]:
        question_lines.extend(["", "## 可选补强问题（非阻塞）", ""])
        for item in readiness["suggested_optional_questions"]:
            question_lines.append(f"- [{item['group']}] {item['label']}：{item['reason']}")

    question_lines.extend(
        [
            "",
            "## Agent 使用提示",
            "- 每轮优先只问 1-3 个高价值问题，不要一次性把整张问卷全抛给用户",
            "- 优先追问阻塞项，不重复询问已明确的信息",
            "- 若用户回答模糊，应给出建议选项帮助收敛，再继续下一轮",
            f"- 结构化答案文件：`{answers_path}`",
            f"- Agent 状态文件：`{agent_state_path}`",
        ]
    )
    questions_path.write_text("\n".join(question_lines) + "\n", encoding="utf-8")

    readiness_lines = [
        "# /plan 就绪度",
        "",
        f"- 是否可直接生成 brief：{'是' if readiness['ready_for_brief'] else '否'}",
        f"- 当前阶段：{readiness['conversation_stage']}",
        f"- 本轮目标：{readiness['round_objective']}",
        f"- 识别领域：{readiness['domain_context']['domain_label']}",
        f"- 模板倾向建议：{readiness['domain_context']['template_hint'] or '待用户确认 / 系统后续推荐'}",
        f"- 缺失的核心字段数量：{len(readiness['missing_required'])}",
        f"- 表述仍模糊的关键字段数量：{len(readiness['weak_blocking'])}",
        f"- 缺失的补充字段数量：{len(readiness['missing_optional'])}",
        f"- 表述仍模糊的补充字段数量：{len(readiness['weak_optional'])}",
        "",
        "## 缺失的核心字段",
    ]
    if readiness["missing_required"]:
        readiness_lines.extend(f"- {item['label']}：{item['question']}" for item in readiness["missing_required"])
    else:
        readiness_lines.append("- 无")
    readiness_lines.extend(["", "## 模糊但仍阻塞的关键字段"])
    if readiness["weak_blocking"]:
        readiness_lines.extend(f"- {item['label']}：{item['reason']}" for item in readiness["weak_blocking"])
    else:
        readiness_lines.append("- 无")
    readiness_lines.extend(["", "## 下一步建议"])
    if readiness["ready_for_brief"]:
        readiness_lines.extend(
            [
                "- 当前已具备进入 `build_project_brief.py` 的最低条件",
                "- 可以继续执行模板推荐与 storyline 生成",
            ]
        )
    else:
        readiness_lines.extend(
            [
                "- 先按 `plan_next_turn.md` 完成当前这一轮追问，再进入下一轮",
                "- 只有当核心字段齐备、且关键字段不再模糊时，再进入 `build_project_brief.py`",
                "- 如果用户信息不足，优先围绕目标、受众、重点给出建议选项帮助收敛",
            ]
        )
    readiness_path.write_text("\n".join(readiness_lines) + "\n", encoding="utf-8")

    next_turn_lines = [
        "# /plan 下一轮建议话术",
        "",
        f"- 当前阶段：{readiness['conversation_stage']}",
        f"- 本轮目标：{readiness['round_objective']}",
        f"- 识别领域：{readiness['domain_context']['domain_label']}",
        f"- 模板倾向建议：{readiness['domain_context']['template_hint'] or '待用户确认 / 系统后续推荐'}",
        "",
        "## 建议直接这样问用户",
        "",
    ]
    if readiness["next_questions"]:
        intro = "为了让这份 PPT 后面的故事线、模板和复杂页判断不跑偏，我先补这 3 个关键点："
        next_turn_lines.append(intro)
        next_turn_lines.append("")
        for index, item in enumerate(readiness["next_questions"], start=1):
            next_turn_lines.append(f"{index}. {item['question']}")
            if item.get("suggestions"):
                next_turn_lines.append(f"   - 如果用户没想清楚，可给出方向：{' / '.join(item['suggestions'])}")
    elif readiness["suggested_optional_questions"]:
        next_turn_lines.append("当前已可直接进入 brief / storyline。")
        next_turn_lines.append("")
        next_turn_lines.append("如果还想把规划做得更稳，可以再补这 1-3 个非阻塞问题：")
        next_turn_lines.append("")
        for index, item in enumerate(readiness["suggested_optional_questions"], start=1):
            next_turn_lines.append(f"{index}. {item['question']}")
            if item.get("suggestions"):
                next_turn_lines.append(f"   - 如果用户没想清楚，可给出方向：{' / '.join(item['suggestions'])}")
    else:
        next_turn_lines.append("当前关键信息已齐备，可以进入 brief / storyline 阶段。")
    next_turn_lines.extend(
        [
            "",
            "## 本轮沟通原则",
            "- 一次最多问 3 个问题",
            "- 不重复追问用户已经明确说过的内容",
            "- 如果某个答案仍然很泛，优先给建议选项，而不是继续抽象追问",
        ]
    )
    next_turn_path.write_text("\n".join(next_turn_lines) + "\n", encoding="utf-8")

    rounds_path, dialogue_path, session_status_path = append_plan_round(
        notes_dir,
        answers,
        readiness,
        next_turn_path,
    )

    return {
        "answers": str(answers_path),
        "questions": str(questions_path),
        "readiness": str(readiness_path),
        "agent_state": str(agent_state_path),
        "next_turn": str(next_turn_path),
        "rounds": str(rounds_path),
        "dialogue": str(dialogue_path),
        "session_status": str(session_status_path),
    }


def build_cli_answers(args: argparse.Namespace) -> dict[str, Any]:
    cli_answers: dict[str, Any] = {}
    for spec in FIELD_SPECS:
        value = getattr(args, spec["id"], None)
        if value is not None:
            cli_answers[spec["id"]] = value
    return cli_answers


def prepare_plan_packet(project_path: str | Path, cli_answers: dict[str, Any], answers_json: str | Path | None = None) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    project_dir = Path(project_path).expanduser().resolve()
    base_answers = create_empty_answers()
    json_answers = load_answers_json(Path(answers_json).expanduser().resolve() if answers_json else None)
    merged = merge_answers(base_answers, json_answers)
    merged = merge_answers(merged, cli_answers)
    readiness = build_readiness(merged)
    paths = write_plan_packet(project_dir, merged, readiness)
    return merged, readiness, paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="为项目生成结构化 /plan 问卷、答案文件与就绪度报告。")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("--answers-json", help="已有的答案 JSON，可作为输入基础")
    for spec in FIELD_SPECS:
        if spec["type"] == "list":
            parser.add_argument(f"--{spec['id'].replace('_', '-')}", dest=spec["id"], help=f"{spec['label']}，逗号分隔")
        else:
            parser.add_argument(f"--{spec['id'].replace('_', '-')}", dest=spec["id"], help=spec["label"])
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cli_answers = build_cli_answers(args)
    _, readiness, paths = prepare_plan_packet(args.project_path, cli_answers, answers_json=args.answers_json)

    print(f"Plan packet prepared: {args.project_path}")
    for label, path in paths.items():
        print(f"  - {label}: {path}")
    print(f"  - ready_for_brief: {'yes' if readiness['ready_for_brief'] else 'no'}")
    print(f"  - conversation_stage: {readiness['conversation_stage']}")
    print(f"  - round_objective: {readiness['round_objective']}")
    print(f"  - domain: {readiness['domain_context']['domain_label']}")
    if readiness["domain_context"]["template_hint"]:
        print(f"  - template_hint: {readiness['domain_context']['template_hint']}")
    if readiness["next_questions"]:
        print("  - next_questions:")
        for item in readiness["next_questions"]:
            print(f"    * [{item['group']}] {item['question']}")


if __name__ == "__main__":
    main()
