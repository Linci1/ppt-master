#!/usr/bin/env python3
"""
PPT Master - Complex Page Model Checker

Validates complex-page reasoning outputs for templates such as security_service.

Usage:
    python3 scripts/check_complex_page_model.py <project_path>
    python3 scripts/check_complex_page_model.py <complex_page_models.md>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

try:
    from template_semantics import fixed_template_matches_entry
except ImportError:
    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from template_semantics import fixed_template_matches_entry  # type: ignore


SECURITY_SERVICE_FIXED_TEMPLATES = {
    '01_cover.svg',
    '02_toc.svg',
    '02_chapter.svg',
    '04_ending.svg',
}

MODEL_FIELD_LABELS: Dict[str, Sequence[str]] = {
    'page_role': ('页面角色', 'Page Role'),
    'page_intent': ('页面意图', 'Page Intent'),
    'proof_goal': ('证明目标', 'Proof Goal'),
    'main_judgment': ('主判断', 'Main Judgment'),
    'sub_judgment': ('分判断', 'Sub Judgment', 'Sub Judgments'),
    'argument_spine': ('论证主线', 'Argument Spine'),
    'structure_type': ('主结构类型', 'Structure Type'),
    'structure_reason': ('结构选择理由', 'Structure Reason'),
    'structure_reject': ('为什么不用其他结构', 'Why Not Other Structure', 'Why Not Other Structures'),
    'key_nodes': ('关键节点', 'Key Nodes'),
    'key_relations': ('关键关系', 'Key Relations'),
    'evidence_plan': ('证据挂载计划', 'Evidence Attachment Plan'),
    'evidence_grading': ('证据分级', 'Evidence Grading'),
    'compression_plan': ('文本压缩计划', 'Compression Plan'),
    'visual_focus': ('视觉焦点排序', 'Visual Focus Order'),
    'closure': ('页面收束方式', 'Closure Strategy'),
}
FIELD_ORDER = list(MODEL_FIELD_LABELS.keys())
JUDGMENT_MARKERS = (
    "已",
    "仍",
    "存在",
    "形成",
    "使",
    "会",
    "让",
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

PAGE_HEADING_RE = re.compile(r'(?im)^####\s+(.+)$')


def _compile_field_pattern(labels: Sequence[str]) -> re.Pattern[str]:
    escaped = '|'.join(re.escape(label) for label in labels)
    return re.compile(
        rf'(?im)^\s*(?:-\s*)?(?:\*\*)?(?:{escaped})(?:\*\*)?\s*[:：]'
    )


FIELD_PATTERNS = {
    field_name: _compile_field_pattern(labels)
    for field_name, labels in MODEL_FIELD_LABELS.items()
}
LIST_FIELDS = {
    'sub_judgment',
    'argument_spine',
    'key_nodes',
    'key_relations',
    'evidence_plan',
    'evidence_grading',
    'compression_plan',
    'visual_focus',
    'closure',
}


def _extract_design_spec_complex_pages(content: str) -> List[str]:
    blocks = []
    matches = list(PAGE_HEADING_RE.finditer(content))
    total_pages = len(matches)
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        title = match.group(1).strip()
        block = content[start:end]
        title_match = re.match(r'^第\s*(\d+)\s*页\s*(.+)$', title)
        page_num = int(title_match.group(1)) if title_match else None
        page_title = title_match.group(2).strip() if title_match else title
        preferred_match = re.search(
            r'(?im)^\s*-\s*\*\*(?:优先页型|Preferred Template)\*\*\s*[:：]\s*(.+)$',
            block,
        )
        preferred_template = None
        if preferred_match:
            preferred_template_match = re.search(
                r'([0-9]{2}_[A-Za-z0-9_]+\.svg)', preferred_match.group(1)
            )
            preferred_template = (
                preferred_template_match.group(1)
                if preferred_template_match
                else preferred_match.group(1).strip()
            )
        advanced_match = re.search(
            r'(?im)^\s*-\s*\*\*(?:高级正文模式|Advanced Pattern)\*\*\s*[:：]\s*(.+)$',
            block,
        )
        if not advanced_match:
            continue
        advanced = re.sub(r'[`*_]', '', advanced_match.group(1)).strip().lower()
        if '无' in advanced or re.search(r'\bnone\b', advanced):
            continue
        recommended_match = re.search(
            r'(?im)^\s*-\s*\*\*(?:Recommended Page Type|推荐页型)\*\*\s*[:：]\s*(.+)$',
            block,
        )
        recommended_page_type = recommended_match.group(1).strip() if recommended_match else ''
        if preferred_template in SECURITY_SERVICE_FIXED_TEMPLATES and fixed_template_matches_entry(
            preferred_template,
            {
                'page_num': str(page_num or ''),
                '页面类型': page_title,
                '推荐页型': recommended_page_type,
            },
            page_num=page_num,
            total_pages=total_pages,
        ):
            continue
        blocks.append(title)
    return blocks


def _extract_model_blocks(content: str) -> Dict[str, str]:
    blocks: Dict[str, str] = {}
    matches = list(PAGE_HEADING_RE.finditer(content))
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        title = match.group(1).strip()
        blocks[title] = content[start:end]
    return blocks


def _extract_field_section(block: str, field_name: str) -> str:
    pattern = FIELD_PATTERNS[field_name]
    start_match = pattern.search(block)
    if not start_match:
        return ''

    start = start_match.end()
    next_positions: List[int] = []
    for candidate in FIELD_ORDER:
        if candidate == field_name:
            continue
        candidate_match = FIELD_PATTERNS[candidate].search(block, start)
        if candidate_match:
            next_positions.append(candidate_match.start())
    end = min(next_positions) if next_positions else len(block)
    return block[start:end].strip()


def _count_list_items(section: str) -> int:
    return len(re.findall(r'(?im)^\s*(?:\d+\.|[-*])\s+.+$', section))


def _normalize_sentence(value: str) -> str:
    text = re.sub(r"[`*_]+", "", value or "")
    return re.sub(r"\s+", "", text).strip()


def _normalize_text(value: str) -> str:
    text = re.sub(r"[`*_]+", "", value or "")
    return re.sub(r"\s+", " ", text).strip()


def _looks_like_judgment_sentence(value: str) -> bool:
    normalized = _normalize_sentence(value)
    if len(normalized) < 6:
        return False
    if normalized in GENERIC_JUDGMENT_PHRASES:
        return False
    return any(marker in normalized for marker in JUDGMENT_MARKERS)


def _parse_heading(title: str) -> Tuple[int | None, str]:
    match = re.match(r'^第\s*(\d+)\s*页\s*(.+)$', title.strip())
    if not match:
        return None, title.strip()
    return int(match.group(1)), match.group(2).strip()


def _split_section_items(section: str) -> List[str]:
    items: List[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        stripped = re.sub(r'^(?:\d+\.\s*|[-*]\s*)', '', stripped)
        stripped = _normalize_text(stripped)
        if not stripped:
            continue
        items.append(stripped)
    if not items and _normalize_text(section):
        items.append(_normalize_text(section))
    return items


def extract_model_blocks(content: str) -> Dict[str, str]:
    return _extract_model_blocks(content)


def extract_field_section(block: str, field_name: str) -> str:
    return _extract_field_section(block, field_name)


def count_list_items(section: str) -> int:
    return _count_list_items(section)


def looks_like_judgment_sentence(value: str) -> bool:
    return _looks_like_judgment_sentence(value)


def parse_model_block(title: str, block: str) -> Dict[str, Any]:
    page_num, page_title = _parse_heading(title)
    parsed: Dict[str, Any] = {
        'heading': title.strip(),
        'page_num': page_num,
        'page_title': page_title,
    }
    for field_name in FIELD_ORDER:
        section = _extract_field_section(block, field_name)
        parsed[field_name] = _normalize_text(section)
        if field_name in LIST_FIELDS:
            parsed[f'{field_name}_items'] = _split_section_items(section)
    return parsed


def validate_model_block(title: str, block: str) -> Tuple[List[str], List[str]]:
    return _validate_model_block(title, block)


def _validate_argument_spine(title: str, section: str, warnings: List[str]) -> None:
    required_keywords = ['现象', '入口', '机制', '条件', '结果', '影响', '管理', '动作']
    hits = sum(1 for keyword in required_keywords if keyword in section)
    if hits < 4:
        warnings.append(f'复杂页“{title}”的 `论证主线` 信息偏弱，可能不足以形成完整推演')


def _validate_field_quality(title: str, block: str, warnings: List[str]) -> None:
    main_judgment = _extract_field_section(block, 'main_judgment')
    if main_judgment and not _looks_like_judgment_sentence(main_judgment):
        warnings.append(f'复杂页“{title}”的 `主判断` 仍像栏目名或摘录句，不够像判断句')

    sub_judgment = _extract_field_section(block, 'sub_judgment')
    sub_judgment_count = _count_list_items(sub_judgment)
    if sub_judgment and sub_judgment_count < 2:
        warnings.append(f'复杂页“{title}”的 `分判断` 少于 2 条，可能不足以支撑主判断')
    if sub_judgment_count > 3:
        warnings.append(f'复杂页“{title}”的 `分判断` 多于 3 条，页面容易失去单一主判断焦点')

    key_nodes = _extract_field_section(block, 'key_nodes')
    if key_nodes and _count_list_items(key_nodes) < 3:
        warnings.append(f'复杂页“{title}”的 `关键节点` 少于 3 项，可能不足以支撑复杂图结构')

    key_relations = _extract_field_section(block, 'key_relations')
    if key_relations and _count_list_items(key_relations) < 2:
        warnings.append(f'复杂页“{title}”的 `关键关系` 少于 2 项，可能不足以支撑链路或层级表达')

    evidence_plan = _extract_field_section(block, 'evidence_plan')
    if evidence_plan and _count_list_items(evidence_plan) < 2:
        warnings.append(f'复杂页“{title}”的 `证据挂载计划` 少于 2 条，证据容易悬空')

    visual_focus = _extract_field_section(block, 'visual_focus')
    if visual_focus and _count_list_items(visual_focus) < 3:
        warnings.append(f'复杂页“{title}”的 `视觉焦点排序` 少于 3 项，可能不足以指导复杂页阅读顺序')

    evidence_grading = _extract_field_section(block, 'evidence_grading')
    if evidence_grading and _count_list_items(evidence_grading) < 2:
        warnings.append(f'复杂页“{title}”的 `证据分级` 过弱，建议至少区分主证据与辅助证据')

    compression_plan = _extract_field_section(block, 'compression_plan')
    if compression_plan and _count_list_items(compression_plan) < 3:
        warnings.append(f'复杂页“{title}”的 `文本压缩计划` 过弱，可能不足以指导案例级文案压缩')

    argument_spine = _extract_field_section(block, 'argument_spine')
    if argument_spine:
        _validate_argument_spine(title, argument_spine, warnings)


def _validate_model_block(title: str, block: str) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    for field_name, pattern in FIELD_PATTERNS.items():
        if not pattern.search(block):
            errors.append(f'复杂页“{title}”缺少字段: {field_name}')

    if not errors:
        main_judgment = _extract_field_section(block, 'main_judgment')
        if not _looks_like_judgment_sentence(main_judgment):
            errors.append(f'复杂页“{title}”的 `主判断` 不是清晰判断句，仍像栏目名或摘录语')

        sub_judgment = _extract_field_section(block, 'sub_judgment')
        if _count_list_items(sub_judgment) < 2:
            errors.append(f'复杂页“{title}”的 `分判断` 少于 2 条，当前不允许进入复杂页绘制')

        key_nodes = _extract_field_section(block, 'key_nodes')
        if _count_list_items(key_nodes) < 3:
            errors.append(f'复杂页“{title}”的 `关键节点` 少于 3 项，当前不允许进入复杂页绘制')

        key_relations = _extract_field_section(block, 'key_relations')
        if _count_list_items(key_relations) < 2:
            errors.append(f'复杂页“{title}”的 `关键关系` 少于 2 项，当前不允许进入复杂页绘制')

        evidence_plan = _extract_field_section(block, 'evidence_plan')
        if _count_list_items(evidence_plan) < 2:
            errors.append(f'复杂页“{title}”的 `证据挂载计划` 少于 2 条，当前不允许进入复杂页绘制')

        visual_focus = _extract_field_section(block, 'visual_focus')
        if _count_list_items(visual_focus) < 3:
            errors.append(f'复杂页“{title}”的 `视觉焦点排序` 少于 3 项，当前不允许进入复杂页绘制')

        _validate_field_quality(title, block, warnings)

    return errors, warnings


def validate(project_or_file: Path) -> Tuple[bool, List[str], List[str], Dict[str, object]]:
    errors: List[str] = []
    warnings: List[str] = []

    if project_or_file.is_dir():
        project_path = project_or_file
        design_spec_path = project_path / 'design_spec.md'
        model_path = project_path / 'notes' / 'complex_page_models.md'
    else:
        model_path = project_or_file
        project_path = model_path.parent.parent if model_path.parent.name == 'notes' else model_path.parent
        design_spec_path = project_path / 'design_spec.md'

    if not design_spec_path.exists():
        return False, [f'design_spec.md not found: {design_spec_path}'], warnings, {}

    design_content = design_spec_path.read_text(encoding='utf-8')
    complex_pages = _extract_design_spec_complex_pages(design_content)
    summary: Dict[str, object] = {
        'design_spec_path': str(design_spec_path),
        'complex_pages_expected': complex_pages,
        'complex_page_count': len(complex_pages),
        'model_path': str(model_path),
    }

    if not complex_pages:
        warnings.append('design_spec.md 中未检测到需要复杂页建模的页面')
        summary['ok'] = True
        return True, errors, warnings, summary

    if not model_path.exists():
        errors.append(f'缺少复杂页建模文件: {model_path}')
        summary['ok'] = False
        return False, errors, warnings, summary

    model_content = model_path.read_text(encoding='utf-8')
    model_blocks = _extract_model_blocks(model_content)
    summary['model_page_count'] = len(model_blocks)

    missing_pages = [title for title in complex_pages if title not in model_blocks]
    if missing_pages:
        errors.append(f'复杂页建模文件缺少以下页面: {", ".join(missing_pages)}')

    extra_pages = [title for title in model_blocks if title not in complex_pages]
    if extra_pages:
        warnings.append(f'复杂页建模文件包含 design_spec 未声明的页面: {", ".join(extra_pages)}')

    for title in complex_pages:
        block = model_blocks.get(title)
        if not block:
            continue
        block_errors, block_warnings = _validate_model_block(title, block)
        errors.extend(block_errors)
        warnings.extend(block_warnings)

    summary['ok'] = not errors
    return not errors, errors, warnings, summary


def main() -> int:
    if len(sys.argv) < 2:
        print('PPT Master - Complex Page Model Checker\n')
        print('Usage:')
        print('  python3 scripts/check_complex_page_model.py <project_path>')
        print('  python3 scripts/check_complex_page_model.py <complex_page_models.md>')
        return 0

    target = Path(sys.argv[1]).resolve()
    ok, errors, warnings, summary = validate(target)

    print(f'\n[CHECK] {target}\n')
    if summary:
        if summary.get('complex_page_count') is not None:
            print(f"[INFO] Expected complex pages: {summary.get('complex_page_count')}")
        if summary.get('model_page_count') is not None:
            print(f"[INFO] Model pages found: {summary.get('model_page_count')}")

    if ok and not warnings:
        print('[OK] Complex page models are valid')
        return 0

    if ok:
        print('[WARN] Complex page models are valid with warnings:')
        for warning in warnings:
            print(f'   {warning}')
        return 0

    print('[ERROR] Complex page models have errors:')
    for error in errors:
        print(f'   {error}')
    if warnings:
        print('\nWarnings:')
        for warning in warnings:
            print(f'   {warning}')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
