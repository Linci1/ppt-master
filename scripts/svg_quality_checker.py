#!/usr/bin/env python3
"""
PPT Master - SVG Quality Check Tool

Checks whether SVG files comply with project technical specifications.

Usage:
    python3 scripts/svg_quality_checker.py <svg_file>
    python3 scripts/svg_quality_checker.py <directory>
    python3 scripts/svg_quality_checker.py --all examples
"""

import json
import sys
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

SCRIPT_DIR = Path(__file__).resolve().parent

try:
    from project_utils import CANVAS_FORMATS
    from error_helper import ErrorHelper
    from template_semantics import fixed_template_matches_entry, is_slug_like
except ImportError:
    print("Warning: Unable to import dependency modules")
    CANVAS_FORMATS = {}
    ErrorHelper = None
    try:
        if str(SCRIPT_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPT_DIR))
        from template_semantics import fixed_template_matches_entry, is_slug_like  # type: ignore
    except Exception:
        fixed_template_matches_entry = None  # type: ignore
        is_slug_like = None  # type: ignore

LAYOUT_INDEX_PATH = SCRIPT_DIR.parent / 'templates' / 'layouts' / 'layouts_index.json'


class SVGQualityChecker:
    """SVG quality checker"""

    FOOTER_PROTECTED_TOP = 648
    CANVAS_EDGE_WARNING_GAP = 28
    CARD_MIN_PADDING = 16
    CARD_COMFORT_PADDING = 22
    MAX_CJK_LINE_CHARS = 32
    MAX_CJK_SINGLE_LINE_CHARS = 36
    TAKEAWAY_MIN_WIDTH_RATIO = 0.72
    TAKEAWAY_MIN_HEIGHT = 40
    TAKEAWAY_MAX_HEIGHT = 110
    TAKEAWAY_MIN_TOP = 140
    TAKEAWAY_MAX_TOP = 240
    TAKEAWAY_BODY_MIN_GAP = 18
    DENSITY_MAX_MAJOR_BLOCKS = 14
    DENSITY_MAX_TOTAL_LINES = 24
    DENSITY_MAX_TOTAL_CHARS = 320
    BRAND_BLOCKING_WARNING_CODES = {
        'brand_presence',
        'brand_asset_misuse',
        'logo_safe_zone',
        'template_safe_area',
    }
    TEMPLATE_BLOCKING_WARNING_CODES = {
        'chinese_readability',
        'line_break_punctuation',
        'edge_pressure_canvas',
        'edge_pressure_card',
        'card_overflow',
        'takeaway_separation',
        'dense_content',
        'toc_consistency',
        'logo_safe_zone',
        'template_safe_area',
        'top_stack_collision',
        'headline_bundle_collision',
        'chapter_safe_zone',
        'chapter_subtitle_semantics',
    }
    ADVANCED_PATTERN_WARNING_ONLY_CODES = {
        'edge_pressure_card',
        'card_overflow',
        'dense_content',
    }
    ADVANCED_PATTERN_BLOCKING_WARNING_CODES = {
        'complex_page_headline',
        'complex_page_closure',
        'complex_page_argument_cohesion',
        'adjacent_complex_progression',
    }
    COMPLEX_MODEL_FIELD_ALIASES = {
        'page_role': ('页面角色', 'Page Role'),
        'page_intent': ('页面意图', 'Page Intent'),
        'proof_goal': ('证明目标', 'Proof Goal'),
        'main_judgment': ('主判断', 'Main Judgment'),
        'sub_judgment': ('分判断', 'Sub Judgment', 'Sub Judgments'),
        'structure_type': ('主结构类型', 'Structure Type'),
        'structure_reason': ('结构选择理由', 'Structure Reason'),
        'structure_reject': ('为什么不用其他结构', 'Why Not Other Structure', 'Why Not Other Structures'),
        'key_nodes': ('关键节点', 'Key Nodes'),
        'key_relations': ('关键关系', 'Key Relations'),
        'evidence_plan': ('证据挂载计划', 'Evidence Attachment Plan'),
        'visual_focus': ('视觉焦点排序', 'Visual Focus Order'),
        'closure': ('页面收束方式', 'Closure Strategy'),
    }
    PLANNING_TONE_PHRASES = {
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
        "传递到下一页",
    }
    SOFT_TERM_BLACKLIST = {
        "证据驾驶舱",
        "证据挂载",
        "挂载型案例页",
        "高级洞察",
        "一体化协同提效",
        "能力沉淀闭环体系",
        "安全水位拉齐",
        "攻击赋能",
        "关键证据证明",
        "攻击链证据页",
        "矩阵证据墙",
        "协同案例链",
        "结果证明总览",
        "纵深突破证明页",
        "证据链已闭合",
    }
    GENERIC_CHAPTER_DESCS = {
        "章节概览",
        "章节重点概览",
        "章节摘要",
        "本章概览",
    }
    GENERIC_MODULE_TITLES = {
        "问题现状",
        "关键证据",
        "整改推进",
        "管理动作",
        "结果证明",
        "直接证据",
        "治理优先级",
        "闭环要求",
        "管理判断",
        "结果判断",
        "案例切面",
        "核心现状",
        "关键判断",
        "场景输入 / 关键约束",
        "核心能力结构",
        "问题输入",
        "方法论补充",
    }
    MODULE_SCAFFOLD_TITLES = {
        "场景输入 / 关键约束",
        "核心能力结构",
        "问题输入",
        "结果输出",
        "结构判断",
        "管理判断",
        "方法论补充",
        "能力",
        "闭环",
        "输出",
    }
    CHAPTER_SUBTITLE_VALUE_MARKERS = (
        "回顾",
        "聚焦",
        "拆解",
        "展开",
        "识别",
        "归因",
        "判断",
        "推进",
        "收束",
        "进入",
        "映射",
        "呈现",
        "量化",
        "验证",
        "评估",
        "治理",
        "整改",
        "闭环",
        "优先级",
    )
    SEMANTIC_KEYWORD_STOPWORDS = {
        "问题",
        "结果",
        "风险",
        "安全",
        "攻击",
        "页面",
        "结构",
        "模块",
        "动作",
        "结论",
        "判断",
        "能力",
        "机制",
        "内容",
        "分析",
        "总览",
        "概览",
        "概述",
        "摘要",
        "案例",
        "路径",
        "链路",
        "矩阵",
        "证明",
        "证据",
        "整改",
        "治理",
        "闭环",
    }
    GENERIC_RELATION_PATTERNS = {
        "承接上一页",
        "承接前页",
        "延续上一页",
        "继续下一页",
        "进入下一页",
        "引出下一页",
        "转入下一页",
        "承上启下",
        "进入正文",
        "从章节页进入正文",
    }
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
    COMPLEX_STRUCTURE_ALIASES = {
        '链路': 'chain',
        '时间线': 'chain',
        'timeline': 'chain',
        'roadmap': 'chain',
        '分层': 'layered',
        'layered': 'layered',
        '体系': 'layered',
        '矩阵': 'matrix',
        'matrix': 'matrix',
        '闭环': 'loop',
        'loop': 'loop',
        '泳道': 'swimlane',
        'swimlane': 'swimlane',
        '证据挂载': 'evidence',
        'evidence': 'evidence',
        '证据墙': 'evidence',
        '混合结构': 'hybrid',
        'hybrid': 'hybrid',
    }
    ADVANCED_PATTERN_QA_POLICIES = {
        'attack_tree_architecture': {
            'card_min_padding': 10,
            'card_vertical_padding': 8,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': 18,
            'card_width_warn_ratio': 1.08,
            'card_width_error_ratio': 1.24,
            'card_height_warn_ratio': 1.10,
            'card_height_error_ratio': 1.28,
            'density_warn_major_blocks': 34,
            'density_error_major_blocks': 46,
            'density_warn_total_lines': 38,
            'density_error_total_lines': 52,
            'density_warn_total_chars': 320,
            'density_error_total_chars': 440,
        },
        'multi_lane_execution_chain': {
            'card_min_padding': 10,
            'card_vertical_padding': 8,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': 16,
            'card_width_warn_ratio': 1.08,
            'card_width_error_ratio': 1.22,
            'card_height_warn_ratio': 1.10,
            'card_height_error_ratio': 1.26,
            'density_warn_major_blocks': 32,
            'density_error_major_blocks': 44,
            'density_warn_total_lines': 38,
            'density_error_total_lines': 52,
            'density_warn_total_chars': 300,
            'density_error_total_chars': 420,
        },
        'evidence_attached_case_chain': {
            'card_min_padding': 10,
            'card_vertical_padding': 8,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': 16,
            'card_width_warn_ratio': 1.08,
            'card_width_error_ratio': 1.22,
            'card_height_warn_ratio': 1.10,
            'card_height_error_ratio': 1.26,
            'density_warn_major_blocks': 26,
            'density_error_major_blocks': 36,
            'density_warn_total_lines': 34,
            'density_error_total_lines': 46,
            'density_warn_total_chars': 280,
            'density_error_total_chars': 380,
        },
        'evidence_cockpit': {
            'card_min_padding': 10,
            'card_vertical_padding': 8,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': 16,
            'card_width_warn_ratio': 1.08,
            'card_width_error_ratio': 1.20,
            'card_height_warn_ratio': 1.10,
            'card_height_error_ratio': 1.24,
            'density_warn_major_blocks': 20,
            'density_error_major_blocks': 28,
            'density_warn_total_lines': 28,
            'density_error_total_lines': 38,
            'density_warn_total_chars': 220,
            'density_error_total_chars': 260,
        },
        'governance_control_matrix': {
            'card_min_padding': 10,
            'card_vertical_padding': 8,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': 14,
            'card_width_warn_ratio': 1.12,
            'card_width_error_ratio': 1.28,
            'card_height_warn_ratio': 1.14,
            'card_height_error_ratio': 1.30,
            'density_warn_major_blocks': 46,
            'density_error_major_blocks': 62,
            'density_warn_total_lines': 58,
            'density_error_total_lines': 76,
            'density_warn_total_chars': 400,
            'density_error_total_chars': 540,
        },
        'matrix_defense_map': {
            'card_min_padding': 10,
            'card_vertical_padding': 8,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': 14,
            'card_width_warn_ratio': 1.10,
            'card_width_error_ratio': 1.26,
            'card_height_warn_ratio': 1.12,
            'card_height_error_ratio': 1.28,
            'density_warn_major_blocks': 34,
            'density_error_major_blocks': 48,
            'density_warn_total_lines': 42,
            'density_error_total_lines': 58,
            'density_warn_total_chars': 350,
            'density_error_total_chars': 460,
        },
        'operation_loop': {
            'card_min_padding': 10,
            'card_vertical_padding': 8,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': 16,
            'card_width_warn_ratio': 1.08,
            'card_width_error_ratio': 1.22,
            'card_height_warn_ratio': 1.10,
            'card_height_error_ratio': 1.26,
            'density_warn_major_blocks': 34,
            'density_error_major_blocks': 46,
            'density_warn_total_lines': 40,
            'density_error_total_lines': 54,
            'density_warn_total_chars': 320,
            'density_error_total_chars': 440,
        },
    }

    def __init__(self, design_spec_path: Optional[str] = None):
        self.results = []
        self.summary = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0,
            'blocking': 0,
        }
        self.issue_types = defaultdict(int)
        self.layouts_index = self._load_layout_index()
        self.design_spec_path = Path(design_spec_path).resolve() if design_spec_path else None
        self.page_specs = self._load_design_spec(self.design_spec_path)
        self.page_specs_by_title = self._index_page_specs_by_title(self.page_specs)
        self.storyline_sections = self._load_storyline_sections(self.design_spec_path.parent / 'notes' / 'storyline.md' if self.design_spec_path else None)
        self.complex_page_models = self._load_complex_page_models(self.design_spec_path.parent / 'notes' / 'complex_page_models.md' if self.design_spec_path else None)

    def check_file(self, svg_file: str, expected_format: str = None) -> Dict:
        """
        Check a single SVG file

        Args:
            svg_file: SVG file path
            expected_format: Expected canvas format (e.g., 'ppt169')

        Returns:
            Check result dictionary
        """
        svg_path = Path(svg_file)

        if not svg_path.exists():
            return {
                'file': str(svg_file),
                'exists': False,
                'errors': ['File does not exist'],
                'warnings': [],
                'issues': [{
                    'severity': 'error',
                    'code': 'file_missing',
                    'message': 'File does not exist',
                    'blocking': True,
                }],
                'blocking_issue_count': 1,
                'passed': False
            }

        result = {
            'file': svg_path.name,
            'path': str(svg_path),
            'exists': True,
            'errors': [],
            'warnings': [],
            'issues': [],
            'info': {},
            'blocking_issue_count': 0,
            'passed': True
        }

        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()

            hints = self._extract_svg_hints(content)
            result['template_context'] = self._resolve_template_context(hints)
            page_spec = self._resolve_page_spec(svg_path.name)
            if page_spec:
                result['page_spec'] = page_spec
                advanced_pattern = page_spec.get('advanced_pattern')
                if advanced_pattern:
                    result['template_context']['advanced_pattern'] = advanced_pattern
                    result['info']['advanced_pattern'] = advanced_pattern
                preferred_template = page_spec.get('preferred_template')
                if preferred_template:
                    result['info']['preferred_template'] = preferred_template
            complex_model = self._resolve_complex_page_model(svg_path.name, page_spec)
            if complex_model:
                result['complex_page_model'] = complex_model
                result['info']['complex_model_title'] = complex_model.get('title')
                structure_type = complex_model.get('structure_type')
                if structure_type:
                    result['info']['complex_structure_type'] = structure_type
            if result['template_context'].get('template_id'):
                result['info']['template'] = result['template_context']['template_id']
            if result['template_context'].get('page_family'):
                result['info']['page_family'] = result['template_context']['page_family']

            # 1. Check viewBox
            self._check_viewbox(content, result, expected_format)

            # 2. Check forbidden elements
            self._check_forbidden_elements(content, result)

            # 3. Check fonts
            self._check_fonts(content, result)

            # 4. Check width/height consistency with viewBox
            self._check_dimensions(content, result)

            # 5. Check text wrapping methods
            self._check_text_elements(content, result)

            # 6. Check footer zone protection using actual occupied bottom edge
            self._check_footer_zone(content, result)

            # 7. Check brand usage for brand-locked templates
            self._check_brand_consistency(content, result)

            # 8. Check complex-page structure consistency when applicable
            self._check_complex_page_consistency(content, result)

            # 9. Check higher-level visual hierarchy collisions that often slip through
            # basic overflow checks but still look obviously wrong in the final PPT.
            self._check_visual_hierarchy_collisions(content, result)

            # 10. Check semantic completion so technically clean SVGs do not pass
            # when they still contain planning scaffolds or misuse fixed templates.
            self._check_semantic_completion(content, result)

            # Determine pass/fail
            self._synthesize_issue_details(result)
            result['passed'] = len(result['errors']) == 0 and result['blocking_issue_count'] == 0

        except Exception as e:
            result['errors'].append(f"Failed to read file: {e}")
            self._synthesize_issue_details(result)
            result['passed'] = False

        # Update statistics
        self.summary['total'] += 1
        if result['passed']:
            if result['warnings']:
                self.summary['warnings'] += 1
            else:
                self.summary['passed'] += 1
        else:
            self.summary['errors'] += 1
        if result['blocking_issue_count'] > 0:
            self.summary['blocking'] += 1

        # Categorize issue types
        for issue in result['issues']:
            self.issue_types[issue['code']] += 1

        self.results.append(result)
        return result

    def _check_viewbox(self, content: str, result: Dict, expected_format: str = None):
        """Check viewBox attribute"""
        viewbox_match = re.search(r'viewBox="([^"]+)"', content)

        if not viewbox_match:
            result['errors'].append("Missing viewBox attribute")
            return

        viewbox = viewbox_match.group(1)
        result['info']['viewbox'] = viewbox

        # Check format
        if not re.match(r'0 0 \d+ \d+', viewbox):
            result['warnings'].append(f"Unusual viewBox format: {viewbox}")

        # Check if it matches expected format
        if expected_format and expected_format in CANVAS_FORMATS:
            expected_viewbox = CANVAS_FORMATS[expected_format]['viewbox']
            if viewbox != expected_viewbox:
                result['errors'].append(
                    f"viewBox mismatch: expected '{expected_viewbox}', got '{viewbox}'"
                )

    def _check_forbidden_elements(self, content: str, result: Dict):
        """Check forbidden elements (blocklist)"""
        content_lower = content.lower()

        # ============================================================
        # Forbidden elements blocklist - PPT incompatible
        # ============================================================

        # Clipping / masking
        if '<clippath' in content_lower:
            result['errors'].append("Detected forbidden <clipPath> element (PPT does not support SVG clip paths)")
        if '<mask' in content_lower:
            result['errors'].append("Detected forbidden <mask> element (PPT does not support SVG masks)")

        # Style system
        if '<style' in content_lower:
            result['errors'].append("Detected forbidden <style> element (use inline attributes instead)")
        if re.search(r'\bclass\s*=', content):
            result['errors'].append("Detected forbidden class attribute (use inline styles instead)")
        # id attribute: only report error when <style> also exists (id is harmful only with CSS selectors)
        # id inside <defs> for linearGradient/filter etc. is required, Inkscape also auto-adds id to elements,
        # standalone id attributes have no impact on PPT export
        if '<style' in content_lower and re.search(r'\bid\s*=', content):
            result['errors'].append(
                "Detected id attribute used with <style> (CSS selectors forbidden, use inline styles instead)"
            )
        if re.search(r'<\?xml-stylesheet\b', content_lower):
            result['errors'].append("Detected forbidden xml-stylesheet (external CSS references forbidden)")
        if re.search(r'<link[^>]*rel\s*=\s*["\']stylesheet["\']', content_lower):
            result['errors'].append("Detected forbidden <link rel=\"stylesheet\"> (external CSS references forbidden)")
        if re.search(r'@import\s+', content_lower):
            result['errors'].append("Detected forbidden @import (external CSS references forbidden)")

        # Structure / nesting
        if '<foreignobject' in content_lower:
            result['errors'].append(
                "Detected forbidden <foreignObject> element (use <tspan> for manual line breaks)")
        has_symbol = '<symbol' in content_lower
        has_use = re.search(r'<use\b', content_lower) is not None
        if has_symbol and has_use:
            result['errors'].append("Detected forbidden <symbol> + <use> complex usage (use basic shapes or simple <use> instead)")
        if '<marker' in content_lower:
            result['errors'].append("Detected forbidden <marker> element (PPT does not support SVG markers)")
        if re.search(r'\bmarker-end\s*=', content_lower):
            result['errors'].append("Detected forbidden marker-end attribute (use line + polygon instead)")

        # Text / fonts
        if '<textpath' in content_lower:
            result['errors'].append("Detected forbidden <textPath> element (path text is incompatible with PPT)")
        if '@font-face' in content_lower:
            result['errors'].append("Detected forbidden @font-face (use system font stack)")

        # Animation / interaction
        if re.search(r'<animate', content_lower):
            result['errors'].append("Detected forbidden SMIL animation element <animate*> (SVG animations are not exported)")
        if re.search(r'<set\b', content_lower):
            result['errors'].append("Detected forbidden SMIL animation element <set> (SVG animations are not exported)")
        if '<script' in content_lower:
            result['errors'].append("Detected forbidden <script> element (scripts and event handlers forbidden)")
        if re.search(r'\bon\w+\s*=', content):  # onclick, onload etc.
            result['errors'].append("Detected forbidden event attributes (e.g., onclick, onload)")

        # Other discouraged elements
        if '<iframe' in content_lower:
            result['errors'].append("Detected <iframe> element (should not appear in SVG)")
        if re.search(r'rgba\s*\(', content_lower):
            result['errors'].append("Detected forbidden rgba() color (use fill-opacity/stroke-opacity instead)")
        if re.search(r'<g[^>]*\sopacity\s*=', content_lower):
            result['errors'].append("Detected forbidden <g opacity> (set opacity on each child element individually)")
        if re.search(r'<image[^>]*\sopacity\s*=', content_lower):
            result['errors'].append("Detected forbidden <image opacity> (use overlay mask approach)")

    def _check_fonts(self, content: str, result: Dict):
        """Check font usage"""
        # Find font-family declarations
        font_matches = re.findall(
            r'font-family[:\s]*["\']([^"\']+)["\']', content, re.IGNORECASE)

        if font_matches:
            result['info']['fonts'] = list(set(font_matches))

            # Check if system UI font stack is used
            recommended_fonts = [
                'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI']

            for font_family in font_matches:
                has_recommended = any(
                    rec in font_family for rec in recommended_fonts)

                if not has_recommended:
                    result['warnings'].append(
                        f"Recommend using system UI font stack, current: {font_family}"
                    )
                    break  # Only warn once

    def _check_dimensions(self, content: str, result: Dict):
        """Check width/height consistency with viewBox"""
        width_match = re.search(r'width="(\d+)"', content)
        height_match = re.search(r'height="(\d+)"', content)

        if width_match and height_match:
            width = width_match.group(1)
            height = height_match.group(1)
            result['info']['dimensions'] = f"{width}x{height}"

            # Check consistency with viewBox
            if 'viewbox' in result['info']:
                viewbox_parts = result['info']['viewbox'].split()
                if len(viewbox_parts) == 4:
                    vb_width, vb_height = viewbox_parts[2], viewbox_parts[3]
                    if width != vb_width or height != vb_height:
                        result['warnings'].append(
                            f"width/height ({width}x{height}) does not match viewBox "
                            f"({vb_width}x{vb_height})"
                        )

    def _check_text_elements(self, content: str, result: Dict):
        """Check text elements and wrapping methods"""
        # Count text and tspan elements
        text_count = content.count('<text')
        tspan_count = content.count('<tspan')

        result['info']['text_elements'] = text_count
        result['info']['tspan_elements'] = tspan_count

        # Check for overly long single-line text (may need wrapping)
        text_matches = re.findall(r'<text[^>]*>([^<]{100,})</text>', content)
        if text_matches:
            result['warnings'].append(
                f"Detected {len(text_matches)} potentially overly long single-line text(s) (consider using tspan for wrapping)"
            )

        text_blocks = self._extract_text_blocks(content)
        canvas_width, canvas_height = self._get_canvas_size(content)
        content_scope = self._extract_content_area(content) or content
        content_text_blocks = self._extract_text_blocks(content_scope)
        rects = self._collect_rect_containers(content_scope)
        hints = self._extract_svg_hints(content)
        qa_policy = self._build_page_qa_policy(result)

        # Check for text without tspan but with long content
        self._check_text_overflow(text_blocks, result)
        self._check_chinese_readability(text_blocks, result)
        self._check_edge_pressure(text_blocks, rects, canvas_width, canvas_height, result, qa_policy)
        self._check_card_text_fit(text_blocks, rects, result, qa_policy)
        self._check_takeaway_body_separation(rects, canvas_width, result)
        self._check_information_density(text_blocks, result, qa_policy)
        self._check_toc_consistency(result['file'], text_blocks, rects, result)
        self._check_template_protected_zones(content_text_blocks, rects, hints, result)

    def _check_text_overflow(self, text_blocks: List[Dict], result: Dict):
        """Check if text content might overflow its container based on estimated width."""
        overflow_count = 0
        for block in text_blocks:
            if block['estimated_width'] > 620 and block['x'] > 400:
                overflow_count += 1

        if overflow_count > 0:
            result['warnings'].append(
                f"Detected {overflow_count} text element(s) with potential overflow (estimated line width is too large)"
            )

    def _check_chinese_readability(self, text_blocks: List[Dict], result: Dict):
        """Heuristic checks for Chinese line breaking and scan readability."""
        long_lines = 0
        awkward_breaks = 0
        dense_single_lines = 0
        long_line_examples = []
        awkward_examples = []
        dense_examples = []

        for block in text_blocks:
            if not block['has_cjk']:
                continue

            if (not block['has_tspan']
                    and block['font_size'] <= 18
                    and block['cjk_chars'] >= self.MAX_CJK_SINGLE_LINE_CHARS):
                dense_single_lines += 1
                if len(dense_examples) < 2:
                    dense_examples.append(self._clip_text(block['text']))

            for line in block['lines']:
                stripped = line.strip()
                if not stripped:
                    continue
                cjk_len = self._count_cjk_chars(stripped)
                if cjk_len >= self.MAX_CJK_LINE_CHARS and block['font_size'] <= 18:
                    long_lines += 1
                    if len(long_line_examples) < 2:
                        long_line_examples.append(self._clip_text(stripped))
                if re.match(r'^[，。；：！？、）》】」』]', stripped):
                    awkward_breaks += 1
                    if len(awkward_examples) < 2:
                        awkward_examples.append(self._clip_text(stripped))
                if re.search(r'[（《【「『]$', stripped):
                    awkward_breaks += 1
                    if len(awkward_examples) < 2:
                        awkward_examples.append(self._clip_text(stripped))

        if long_lines > 0:
            result['warnings'].append(
                f"Chinese readability risk: detected {long_lines} line(s) that are likely too long for glance reading"
                f"{self._format_examples(long_line_examples)}"
            )
        if dense_single_lines > 0:
            result['warnings'].append(
                f"Chinese readability risk: detected {dense_single_lines} dense single-line Chinese text block(s) without line breaks"
                f"{self._format_examples(dense_examples)}"
            )
        if awkward_breaks > 0:
            result['warnings'].append(
                f"Chinese line-break risk: detected {awkward_breaks} line(s) starting/ending with awkward punctuation"
                f"{self._format_examples(awkward_examples)}"
            )

    def _check_edge_pressure(
        self,
        text_blocks: List[Dict],
        rects: List[Dict],
        canvas_width: float,
        canvas_height: float,
        result: Dict,
        qa_policy: Dict[str, object]
    ):
        """Check whether text sits too close to card edges or canvas boundaries."""
        canvas_hits = 0
        card_hits = 0
        card_hard_hits = 0
        canvas_examples = []
        card_examples = []
        card_hard_examples = []
        soft_pad = float(qa_policy.get('card_min_padding', self.CARD_MIN_PADDING))
        hard_pad = float(qa_policy.get('card_hard_padding', -2))
        soft_vertical = float(qa_policy.get('card_vertical_padding', 10))
        hard_vertical = float(qa_policy.get('card_hard_vertical_padding', -4))

        for block in text_blocks:
            if self._is_minor_label(block):
                continue
            if (block['left'] < self.CANVAS_EDGE_WARNING_GAP
                    or block['right'] > canvas_width - self.CANVAS_EDGE_WARNING_GAP
                    or block['top'] < self.CANVAS_EDGE_WARNING_GAP):
                canvas_hits += 1
                if len(canvas_examples) < 2:
                    canvas_examples.append(self._clip_text(block['text']))

            container = self._find_containing_rect(block, rects)
            if not container:
                continue

            # Ignore short chip/header labels inside very shallow pills or header bands.
            if container['height'] <= 30 and block['font_size'] <= 14:
                continue
            if container['height'] <= 40 and block['font_size'] <= 12.5 and len(re.sub(r'\s+', '', block['text'])) <= 14:
                continue

            left_pad = block['left'] - container['x']
            right_pad = container['right'] - block['right']
            top_pad = block['top'] - container['y']
            bottom_pad = container['bottom'] - block['bottom']
            line_count = len(block.get('lines', []))

            # Small title ribbons and chip-style headers often run tight by design.
            if container['height'] <= 40 and block['font_size'] <= 16 and len(re.sub(r'\s+', '', block['text'])) <= 18:
                continue

            # Wide summary / closure bands tolerate slightly tighter padding as long as
            # text-fit checks already show the copy remains comfortably inside the strip.
            if (
                container['width'] >= 240
                and container['height'] <= 80
                and block['font_size'] <= 12.5
                and line_count <= 2
                and block['estimated_height'] <= container['height'] - 8
            ):
                continue

            if min(left_pad, right_pad) < hard_pad or min(top_pad, bottom_pad) < hard_vertical:
                card_hard_hits += 1
                if len(card_hard_examples) < 3:
                    card_hard_examples.append(self._clip_text(block['text']))
            elif min(left_pad, right_pad) < soft_pad or min(top_pad, bottom_pad) < soft_vertical:
                card_hits += 1
                if len(card_examples) < 3:
                    card_examples.append(self._clip_text(block['text']))

        if canvas_hits > 0:
            result['warnings'].append(
                f"Edge pressure risk: detected {canvas_hits} text block(s) too close to canvas edges"
                f"{self._format_examples(canvas_examples)}"
            )
        if card_hard_hits > 0:
            result['errors'].append(
                f"Edge pressure violation: detected {card_hard_hits} text block(s) with critically low card padding"
                f"{self._format_examples(card_hard_examples)}"
            )
        if card_hits > 0:
            result['warnings'].append(
                f"Edge pressure risk: detected {card_hits} text block(s) with insufficient card padding"
                f"{self._format_examples(card_examples)}"
            )

    def _check_card_text_fit(
        self,
        text_blocks: List[Dict],
        rects: List[Dict],
        result: Dict,
        qa_policy: Dict[str, object]
    ):
        """Estimate whether text is visually cramped inside its card container."""
        width_hits = 0
        height_hits = 0
        width_hard_hits = 0
        height_hard_hits = 0
        width_examples = []
        height_examples = []
        width_hard_examples = []
        height_hard_examples = []
        comfort_padding = float(qa_policy.get('card_comfort_padding', self.CARD_COMFORT_PADDING))
        min_padding = float(qa_policy.get('card_min_padding', self.CARD_MIN_PADDING))
        width_warn_ratio = float(qa_policy.get('card_width_warn_ratio', 1.0))
        width_error_ratio = float(qa_policy.get('card_width_error_ratio', 1.18))
        height_warn_ratio = float(qa_policy.get('card_height_warn_ratio', 1.0))
        height_error_ratio = float(qa_policy.get('card_height_error_ratio', 1.18))

        for block in text_blocks:
            if self._is_minor_label(block):
                continue
            container = self._find_containing_rect(block, rects)
            if not container:
                continue

            adaptive_width_padding = min(
                comfort_padding,
                max(6.0, container['width'] * 0.08),
            )
            adaptive_height_padding = min(
                min_padding,
                max(4.0, container['height'] * 0.18),
            )
            usable_width = container['width'] - adaptive_width_padding * 2
            usable_height = container['height'] - adaptive_height_padding * 2
            if usable_width <= 0 or usable_height <= 0:
                continue

            if block['estimated_width'] > usable_width * width_error_ratio:
                width_hard_hits += 1
                if len(width_hard_examples) < 2:
                    width_hard_examples.append(self._clip_text(block['text']))
            elif block['estimated_width'] > usable_width * width_warn_ratio:
                width_hits += 1
                if len(width_examples) < 2:
                    width_examples.append(self._clip_text(block['text']))
            if block['estimated_height'] > usable_height * height_error_ratio:
                height_hard_hits += 1
                if len(height_hard_examples) < 2:
                    height_hard_examples.append(self._clip_text(block['text']))
            elif block['estimated_height'] > usable_height * height_warn_ratio:
                height_hits += 1
                if len(height_examples) < 2:
                    height_examples.append(self._clip_text(block['text']))

        if width_hard_hits > 0 or height_hard_hits > 0:
            parts = []
            if width_hard_hits > 0:
                parts.append(
                    f"{width_hard_hits} block(s) exceed card width budget by a critical margin"
                    f"{self._format_examples(width_hard_examples)}"
                )
            if height_hard_hits > 0:
                parts.append(
                    f"{height_hard_hits} block(s) exceed card height budget by a critical margin"
                    f"{self._format_examples(height_hard_examples)}"
                )
            result['errors'].append("Card overflow violation: " + ", ".join(parts))
        if width_hits > 0 or height_hits > 0:
            parts = []
            if width_hits > 0:
                parts.append(
                    f"{width_hits} block(s) exceed card width budget{self._format_examples(width_examples)}"
                )
            if height_hits > 0:
                parts.append(
                    f"{height_hits} block(s) exceed card height budget{self._format_examples(height_examples)}"
                )
            result['warnings'].append(
                "Card overflow risk: " + ", ".join(parts)
            )

    def _check_takeaway_body_separation(self, rects: List[Dict], canvas_width: float, result: Dict):
        """Detect the common case where a takeaway strip sits too close to the body modules below."""
        takeaway_candidates = [
            rect for rect in rects
            if rect['width'] >= canvas_width * self.TAKEAWAY_MIN_WIDTH_RATIO
            and self.TAKEAWAY_MIN_HEIGHT <= rect['height'] <= self.TAKEAWAY_MAX_HEIGHT
            and self.TAKEAWAY_MIN_TOP <= rect['y'] <= self.TAKEAWAY_MAX_TOP
        ]
        if not takeaway_candidates:
            return

        takeaway = min(takeaway_candidates, key=lambda rect: rect['y'])
        body_candidates = [
            rect for rect in rects
            if rect['y'] >= takeaway['y']
            and rect['height'] >= 120
            and rect['width'] >= 240
            and rect['area'] < takeaway['area'] * 0.95
            and self._horizontal_overlap(rect, takeaway) >= min(rect['width'], takeaway['width']) * 0.2
        ]
        if not body_candidates:
            return

        first_body = min(body_candidates, key=lambda rect: rect['y'])
        gap = first_body['y'] - takeaway['bottom']

        if gap < 0:
            result['errors'].append(
                "Layer separation violation: body module overlaps takeaway band "
                f"(gap {gap:.1f}px, takeaway bottom={takeaway['bottom']:.1f}, body top={first_body['y']:.1f})"
            )
        elif gap < self.TAKEAWAY_BODY_MIN_GAP:
            result['warnings'].append(
                "Takeaway/body separation risk: body module starts too close to takeaway band "
                f"(gap {gap:.1f}px; recommended >= {self.TAKEAWAY_BODY_MIN_GAP}px)"
            )

    def _check_information_density(
        self,
        text_blocks: List[Dict],
        result: Dict,
        qa_policy: Dict[str, object]
    ):
        """Warn when a page is likely too dense for presentation-style reading."""
        major_blocks = [block for block in text_blocks if not self._is_minor_label(block)]
        total_lines = sum(len(block['lines']) for block in major_blocks)
        total_chars = sum(len(re.sub(r'\s+', '', block['text'])) for block in major_blocks)

        warn_major = int(qa_policy.get('density_warn_major_blocks', self.DENSITY_MAX_MAJOR_BLOCKS))
        warn_lines = int(qa_policy.get('density_warn_total_lines', self.DENSITY_MAX_TOTAL_LINES))
        warn_chars = int(qa_policy.get('density_warn_total_chars', self.DENSITY_MAX_TOTAL_CHARS))
        error_major = int(qa_policy.get('density_error_major_blocks', warn_major + 8))
        error_lines = int(qa_policy.get('density_error_total_lines', warn_lines + 12))
        error_chars = int(qa_policy.get('density_error_total_chars', warn_chars + 120))

        if (len(major_blocks) > error_major
                or total_lines > error_lines
                or total_chars > error_chars):
            result['errors'].append(
                "Information density overload: page exceeds the allowed content budget even for its current layout "
                f"(major_blocks={len(major_blocks)}, lines={total_lines}, chars={total_chars})"
            )
        elif (len(major_blocks) > warn_major
                or total_lines > warn_lines
                or total_chars > warn_chars):
            result['warnings'].append(
                "Information density risk: page may be too dense for glance reading "
                f"(major_blocks={len(major_blocks)}, lines={total_lines}, chars={total_chars})"
            )

    def _check_toc_consistency(
        self,
        filename: str,
        text_blocks: List[Dict],
        rects: List[Dict],
        result: Dict
    ):
        """Catch TOC cards that use inconsistent text structures within the same page."""
        if not self._looks_like_toc(filename):
            return

        toc_cards = [
            rect for rect in rects
            if 140 <= rect['width'] <= 620
            and 70 <= rect['height'] <= 220
            and 140 <= rect['y'] <= 620
        ]
        if len(toc_cards) < 4:
            return

        structure_counts = []
        for card in toc_cards:
            line_count = 0
            for block in text_blocks:
                if self._is_minor_label(block):
                    continue
                container = self._find_containing_rect(block, [card])
                if container:
                    line_count += max(1, len(block['lines']))
            if line_count > 0:
                structure_counts.append(line_count)

        if len(structure_counts) >= 4 and len(set(structure_counts)) > 1:
            result['warnings'].append(
                "TOC consistency risk: directory cards contain inconsistent text structures "
                "(for example, some cards include subtitle lines while others do not)"
            )

    def _check_template_protected_zones(
        self,
        text_blocks: List[Dict],
        rects: List[Dict],
        hints: Dict[str, object],
        result: Dict
    ):
        """Honor template-declared protected zones without constraining content creativity."""
        content_max_bottom = hints.get('content_max_bottom')
        if isinstance(content_max_bottom, (int, float)):
            block_hits = []
            rect_hits = []

            for block in text_blocks:
                if self._is_minor_label(block):
                    continue
                if block['bottom'] > content_max_bottom:
                    if len(block_hits) < 3:
                        block_hits.append(self._clip_text(block['text']))

            for rect in rects:
                if rect['width'] >= 1200 and rect['height'] >= 680:
                    continue
                if rect['bottom'] > content_max_bottom and rect['height'] >= 70 and rect['width'] >= 160:
                    if len(rect_hits) < 2:
                        rect_hits.append(
                            f"rect({int(rect['x'])},{int(rect['y'])},{int(rect['width'])},{int(rect['height'])})"
                        )

            if block_hits or rect_hits:
                examples = block_hits + rect_hits
                result['warnings'].append(
                    "Template safe-area risk: content extends below the template's recommended body baseline "
                    f"(bottom > {content_max_bottom}){self._format_examples(examples)}"
                )

        logo_zone = hints.get('logo_safe_zone')
        if isinstance(logo_zone, tuple):
            zx, zy, zw, zh = logo_zone
            zone = {
                'x': zx,
                'y': zy,
                'right': zx + zw,
                'bottom': zy + zh,
            }
            hits = []

            for block in text_blocks:
                if self._is_minor_label(block):
                    continue
                if self._boxes_intersect(block, zone):
                    if len(hits) < 3:
                        hits.append(self._clip_text(block['text']))

            for rect in rects:
                if rect['width'] >= 1200 and rect['height'] >= 680:
                    continue
                if rect['height'] < 50 or rect['width'] < 120:
                    continue
                if self._boxes_intersect(rect, zone):
                    if len(hits) < 4:
                        hits.append(
                            f"rect({int(rect['x'])},{int(rect['y'])},{int(rect['width'])},{int(rect['height'])})"
                        )

            if hits:
                result['warnings'].append(
                    "Logo safe-zone risk: body content enters the template-declared logo/footer breathing room "
                    f"{self._format_examples(hits)}"
                )

    def _check_footer_zone(self, content: str, result: Dict):
        """Check if content elements extend into the footer zone.

        The original implementation only looked at an element's starting y position,
        which misses wide takeaway bars whose top edge is above the footer line but
        whose actual visual bottom still pushes into the footer breathing zone.
        This version checks the occupied bottom edge of content elements instead.
        """
        content_scope = self._extract_content_area(content) or content
        hints = self._extract_svg_hints(content)
        footer_protected_top = hints.get('footer_protected_top', self.FOOTER_PROTECTED_TOP)
        footer_violations = []

        for element in self._collect_footer_candidates(content_scope):
            if self._is_allowed_footer_element(element):
                continue

            occupied_bottom = element['bottom']
            if occupied_bottom > footer_protected_top:
                footer_violations.append(
                    f"{element['type']} bottom={element['bottom']:.1f} (y={element['y']:.1f})"
                )

        if footer_violations:
            unique_violations = list(dict.fromkeys(footer_violations))
            result['errors'].append(
                "Footer zone violation: "
                f"{len(unique_violations)} content element(s) cross the protected footer area "
                f"(bottom > {footer_protected_top}). Elements: "
                f"{', '.join(unique_violations[:3])}"
                f"{'...' if len(unique_violations) > 3 else ''}"
            )

    def _extract_content_area(self, content: str) -> Optional[str]:
        """Return the markup inside <g id="content-area"> when present."""
        start_match = re.search(r'<g[^>]*id=["\']content-area["\'][^>]*>', content)
        if not start_match:
            return None

        idx = start_match.end()
        depth = 1

        while idx < len(content):
            next_open = content.find('<g', idx)
            next_close = content.find('</g>', idx)

            if next_close == -1:
                return None

            if next_open != -1 and next_open < next_close:
                depth += 1
                idx = next_open + 2
                continue

            depth -= 1
            if depth == 0:
                return content[start_match.end():next_close]
            idx = next_close + 4

        return None

    def _collect_footer_candidates(self, content: str) -> List[Dict]:
        """Collect positioned elements that can visually enter the footer safe area."""
        elements = []

        for match in re.finditer(r'<rect\b[^>]*>', content):
            attrs = self._parse_attrs(match.group(0))
            y = self._to_float(attrs.get('y'))
            height = self._to_float(attrs.get('height'))
            if y is None or height is None:
                continue
            elements.append({
                'type': 'rect',
                'raw': match.group(0),
                'x': self._to_float(attrs.get('x')),
                'y': y,
                'bottom': y + height,
            })

        for match in re.finditer(r'<image\b[^>]*>', content):
            attrs = self._parse_attrs(match.group(0))
            y = self._to_float(attrs.get('y'))
            height = self._to_float(attrs.get('height'))
            if y is None or height is None:
                continue
            elements.append({
                'type': 'image',
                'raw': match.group(0),
                'x': self._to_float(attrs.get('x')),
                'y': y,
                'bottom': y + height,
            })

        for match in re.finditer(r'<text\b[^>]*>.*?</text>', content, re.DOTALL):
            raw = match.group(0)
            open_tag_match = re.match(r'<text\b[^>]*>', raw)
            if not open_tag_match:
                continue
            attrs = self._parse_attrs(open_tag_match.group(0))
            y = self._to_float(attrs.get('y'))
            font_size = self._to_float(attrs.get('font-size'))
            if y is None:
                continue

            bottom = y + (font_size or 14) * 0.9
            dy_values = [
                self._to_float(val)
                for val in re.findall(r'<tspan\b[^>]*\bdy=["\'](-?\d+(?:\.\d+)?)["\']', raw)
            ]
            dy_total = 0.0
            for dy in dy_values:
                if dy is not None and dy > 0:
                    dy_total += dy
            if dy_total:
                bottom = y + dy_total + (font_size or 14) * 0.9

            elements.append({
                'type': 'text',
                'raw': raw,
                'x': self._to_float(attrs.get('x')),
                'y': y,
                'bottom': bottom,
            })

        return elements

    def _collect_rect_containers(self, content: str) -> List[Dict]:
        """Collect likely card/background rects for text-fit and padding estimation."""
        rects = []
        for match in re.finditer(r'<rect\b[^>]*>', content):
            attrs = self._parse_attrs(match.group(0))
            x = self._to_float(attrs.get('x'))
            y = self._to_float(attrs.get('y'))
            width = self._to_float(attrs.get('width'))
            height = self._to_float(attrs.get('height'))
            if None in (x, y, width, height):
                continue
            if width < 80 or height < 20:
                continue
            rects.append({
                'raw': match.group(0),
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'right': x + width,
                'bottom': y + height,
                'area': width * height,
            })
        rects.sort(key=lambda item: item['area'])
        return rects

    def _collect_separator_elements(self, content: str) -> List[Dict]:
        """Collect thin horizontal separators that can cut through compact headline text."""
        separators: List[Dict] = []

        for match in re.finditer(r'<line\b[^>]*>', content):
            attrs = self._parse_attrs(match.group(0))
            x1 = self._to_float(attrs.get('x1'))
            y1 = self._to_float(attrs.get('y1'))
            x2 = self._to_float(attrs.get('x2'))
            y2 = self._to_float(attrs.get('y2'))
            stroke_width = self._to_float(attrs.get('stroke-width')) or 1.0
            if None in (x1, y1, x2, y2):
                continue
            if abs(y1 - y2) > max(2.0, stroke_width):
                continue
            width = abs(x2 - x1)
            if width < 80:
                continue
            top = min(y1, y2) - stroke_width / 2
            bottom = max(y1, y2) + stroke_width / 2
            separators.append({
                'type': 'line',
                'x': min(x1, x2),
                'y': top,
                'width': width,
                'height': max(stroke_width, bottom - top),
                'right': max(x1, x2),
                'bottom': bottom,
            })

        for match in re.finditer(r'<rect\b[^>]*>', content):
            attrs = self._parse_attrs(match.group(0))
            x = self._to_float(attrs.get('x'))
            y = self._to_float(attrs.get('y'))
            width = self._to_float(attrs.get('width'))
            height = self._to_float(attrs.get('height'))
            if None in (x, y, width, height):
                continue
            if width < 80 or height <= 0 or height > 8:
                continue
            separators.append({
                'type': 'rect',
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'right': x + width,
                'bottom': y + height,
            })

        return separators

    def _extract_text_blocks(self, content: str) -> List[Dict]:
        """Parse text blocks and estimate their visual footprint."""
        blocks = []
        for match in re.finditer(r'<text\b[^>]*>.*?</text>', content, re.DOTALL):
            raw = match.group(0)
            open_tag_match = re.match(r'<text\b[^>]*>', raw)
            if not open_tag_match:
                continue

            open_tag = open_tag_match.group(0)
            attrs = self._parse_attrs(open_tag)
            x = self._to_float(attrs.get('x'))
            y = self._to_float(attrs.get('y'))
            font_size = self._to_float(attrs.get('font-size')) or 14.0
            text_anchor = attrs.get('text-anchor', 'start')
            if x is None or y is None:
                continue

            lines = []
            positive_dy_sum = 0.0
            tspan_matches = list(re.finditer(r'<tspan\b([^>]*)>(.*?)</tspan>', raw, re.DOTALL))
            if tspan_matches:
                for tspan_match in tspan_matches:
                    tspan_attrs = self._parse_attrs(f"<tspan{tspan_match.group(1)}>")
                    dy = self._to_float(tspan_attrs.get('dy')) or 0.0
                    if dy > 0:
                        positive_dy_sum += dy
                    line_text = self._strip_tags(tspan_match.group(2)).strip()
                    if line_text:
                        lines.append(line_text)
            else:
                inner = re.sub(r'^<text\b[^>]*>|</text>$', '', raw, flags=re.DOTALL)
                line_text = self._strip_tags(inner).strip()
                if line_text:
                    lines.append(line_text)

            if not lines:
                continue

            estimated_width = max(self._estimate_text_width(line, font_size) for line in lines)
            # Use a lighter descent estimate so small title bands / label pills
            # are not over-penalized while still catching obvious overflow.
            estimated_height = positive_dy_sum + font_size * 0.55
            left, right = self._resolve_horizontal_bounds(x, estimated_width, text_anchor)
            top = y - font_size * 0.8
            bottom = y + estimated_height
            full_text = " ".join(lines)

            blocks.append({
                'raw': raw,
                'x': x,
                'y': y,
                'font_size': font_size,
                'text_anchor': text_anchor,
                'lines': lines,
                'has_tspan': bool(tspan_matches),
                'estimated_width': estimated_width,
                'estimated_height': estimated_height,
                'left': left,
                'right': right,
                'top': top,
                'bottom': bottom,
                'text': full_text,
                'has_cjk': self._count_cjk_chars(full_text) > 0,
                'cjk_chars': self._count_cjk_chars(full_text),
            })

        return blocks

    def _find_containing_rect(self, text_block: Dict, rects: List[Dict]) -> Optional[Dict]:
        """Find the smallest rect that contains the estimated text footprint."""
        for rect in rects:
            if (text_block['left'] >= rect['x'] - 2
                    and text_block['right'] <= rect['right'] + 2
                    and text_block['top'] >= rect['y'] - 6
                    and text_block['bottom'] <= rect['bottom'] + 6):
                return rect
        return None

    def _get_canvas_size(self, content: str) -> Tuple[float, float]:
        """Read canvas width/height from viewBox when available."""
        viewbox_match = re.search(r'viewBox=["\']0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)["\']', content)
        if viewbox_match:
            return float(viewbox_match.group(1)), float(viewbox_match.group(2))
        width_match = re.search(r'width=["\'](\d+(?:\.\d+)?)["\']', content)
        height_match = re.search(r'height=["\'](\d+(?:\.\d+)?)["\']', content)
        return (
            float(width_match.group(1)) if width_match else 1280.0,
            float(height_match.group(1)) if height_match else 720.0,
        )

    def _extract_svg_hints(self, content: str) -> Dict[str, object]:
        """Read optional template hints from <svg> and content-area attributes."""
        hints: Dict[str, object] = {}

        svg_tag_match = re.search(r'<svg\b[^>]*>', content)
        if svg_tag_match:
            attrs = self._parse_attrs(svg_tag_match.group(0))
            hints['template_id'] = attrs.get('data-template')
            hints['page_family'] = attrs.get('data-page-family')
            hints['brand_required_attr'] = attrs.get('data-brand-required')
            brand_assets = attrs.get('data-brand-assets')
            if brand_assets:
                hints['brand_assets'] = [
                    asset.strip() for asset in brand_assets.split(',') if asset.strip()
                ]
            footer_top = self._to_float(attrs.get('data-footer-protected-top'))
            if footer_top is not None:
                hints['footer_protected_top'] = footer_top
            logo_zone = self._parse_zone(attrs.get('data-logo-safe-zone'))
            if logo_zone:
                hints['logo_safe_zone'] = logo_zone

        content_area_match = re.search(r'<g\b[^>]*id=["\']content-area["\'][^>]*>', content)
        if content_area_match:
            attrs = self._parse_attrs(content_area_match.group(0))
            content_max_bottom = self._to_float(attrs.get('data-content-max-bottom'))
            if content_max_bottom is not None:
                hints['content_max_bottom'] = content_max_bottom

        return hints

    def _load_layout_index(self) -> Dict[str, object]:
        """Load template metadata for template-aware QA rules."""
        if not LAYOUT_INDEX_PATH.exists():
            return {}
        try:
            return json.loads(LAYOUT_INDEX_PATH.read_text(encoding='utf-8'))
        except Exception:
            return {}

    def _resolve_template_context(self, hints: Dict[str, object]) -> Dict[str, object]:
        """Combine inline SVG metadata with layouts_index.json brand policy."""
        template_id = hints.get('template_id')
        page_family = hints.get('page_family')
        layouts = self.layouts_index.get('layouts', {}) if isinstance(self.layouts_index, dict) else {}
        layout_meta = layouts.get(template_id, {}) if template_id else {}
        stability_profile = layout_meta.get('stabilityProfile', {}) if isinstance(layout_meta, dict) else {}
        brand_policy = layout_meta.get('brandPolicy', {}) if isinstance(layout_meta, dict) else {}

        required_families = brand_policy.get('requiredFamilies', []) if isinstance(brand_policy, dict) else []
        approved_assets = hints.get('brand_assets') or brand_policy.get('approvedAssets', [])
        brand_required_attr = str(hints.get('brand_required_attr', '')).lower()

        context = {
            'template_id': template_id,
            'page_family': page_family,
            'fixed_skeleton': bool(stability_profile.get('fixedSkeleton')),
            'approved_brand_assets': approved_assets if isinstance(approved_assets, list) else [],
            'required_brand_families': required_families if isinstance(required_families, list) else [],
            'brand_required': False,
            'logo_safe_zone': hints.get('logo_safe_zone'),
        }

        if brand_required_attr in {'1', 'true', 'yes'}:
            context['brand_required'] = True
        elif page_family and page_family in context['required_brand_families']:
            context['brand_required'] = True
        elif bool(brand_policy.get('required')) and template_id:
            context['brand_required'] = True

        return context

    def _contains_planning_tone(self, text: str) -> bool:
        normalized = re.sub(r'\s+', '', text or '')
        return any(phrase in normalized for phrase in self.PLANNING_TONE_PHRASES)

    def _resolve_asset_path(self, svg_path: str, asset: str) -> Optional[Path]:
        if not asset or asset.startswith('data:') or re.match(r'https?://', asset):
            return None
        candidate = Path(asset)
        if candidate.is_absolute():
            return candidate
        return (Path(svg_path).resolve().parent / asset).resolve()

    def _read_image_size(self, asset_path: Path) -> Tuple[Optional[int], Optional[int]]:
        """Read image dimensions even when Pillow is unavailable."""
        try:
            data = asset_path.read_bytes()
        except Exception:
            return None, None

        if len(data) >= 24 and data[:8] == b'\x89PNG\r\n\x1a\n':
            return (
                int.from_bytes(data[16:20], 'big'),
                int.from_bytes(data[20:24], 'big'),
            )

        if len(data) >= 10 and data[:6] in {b'GIF87a', b'GIF89a'}:
            return (
                int.from_bytes(data[6:8], 'little'),
                int.from_bytes(data[8:10], 'little'),
            )

        if len(data) >= 4 and data[:2] == b'\xff\xd8':
            index = 2
            while index + 9 < len(data):
                if data[index] != 0xFF:
                    index += 1
                    continue
                marker = data[index + 1]
                index += 2
                if marker in {0xD8, 0xD9}:
                    continue
                if index + 2 > len(data):
                    break
                segment_len = int.from_bytes(data[index:index + 2], 'big')
                if segment_len < 2 or index + segment_len > len(data):
                    break
                if 0xC0 <= marker <= 0xCF and marker not in {0xC4, 0xC8, 0xCC}:
                    if index + 7 <= len(data):
                        return (
                            int.from_bytes(data[index + 5:index + 7], 'big'),
                            int.from_bytes(data[index + 3:index + 5], 'big'),
                        )
                    break
                index += segment_len

        return None, None

    def _inspect_logo_asset(self, asset_path: Path) -> Dict[str, float]:
        if not asset_path.exists():
            return {}
        width, height = self._read_image_size(asset_path)
        info: Dict[str, float] = {}
        if width and height:
            info['aspect_ratio'] = width / max(height, 1)
        info['file_size_kb'] = asset_path.stat().st_size / 1024.0
        if Image is None:
            return info
        try:
            image = Image.open(asset_path).convert('RGBA')
            sample = image.copy()
            sample.thumbnail((240, 240))
            width, height = sample.size
            pixels = list(sample.getdata())
        except Exception:
            return info

        if not pixels or width <= 0 or height <= 0:
            return info

        opaque_pixels = [pixel for pixel in pixels if pixel[3] > 20]
        if not opaque_pixels:
            info.update({
                'opaque_ratio': 0.0,
                'green_ratio': 0.0,
                'dark_ratio': 0.0,
                'non_white_ratio': 0.0,
            })
            return info

        def is_green(pixel: tuple[int, int, int, int]) -> bool:
            r, g, b, _ = pixel
            return g >= 110 and g > r + 12 and g > b + 12

        def is_dark(pixel: tuple[int, int, int, int]) -> bool:
            r, g, b, _ = pixel
            return max(r, g, b) <= 110

        def is_non_white(pixel: tuple[int, int, int, int]) -> bool:
            r, g, b, _ = pixel
            return min(r, g, b) < 245

        green_ratio = sum(1 for pixel in opaque_pixels if is_green(pixel)) / len(opaque_pixels)
        dark_ratio = sum(1 for pixel in opaque_pixels if is_dark(pixel)) / len(opaque_pixels)
        non_white_ratio = sum(1 for pixel in opaque_pixels if is_non_white(pixel)) / len(opaque_pixels)

        info.update({
            'opaque_ratio': len(opaque_pixels) / len(pixels),
            'green_ratio': green_ratio,
            'dark_ratio': dark_ratio,
            'non_white_ratio': non_white_ratio,
        })
        return info

    def _load_design_spec(self, design_spec_path: Optional[Path]) -> Dict[int, Dict[str, str]]:
        """Parse project design_spec.md for per-slide advanced-page metadata."""
        if not design_spec_path or not design_spec_path.exists():
            return {}
        try:
            content = design_spec_path.read_text(encoding='utf-8')
        except Exception:
            return {}

        slide_specs: Dict[int, Dict[str, str]] = {}
        sections = self._extract_markdown_blocks(content)
        for heading, section in sections:
            slide_num, title = self._parse_section_heading(heading)
            if slide_num is None:
                continue
            slide_specs[slide_num] = {
                'title': title,
                'layout': self._extract_spec_value(section, 'Layout'),
                'page_intent': self._extract_spec_value(section, '页面意图'),
                'proof_goal': self._extract_spec_value(section, '证明目标'),
                'core_judgment': self._extract_spec_value(section, 'Core Judgment'),
                'supporting_evidence': self._extract_spec_value(section, 'Supporting Evidence'),
                'recommended_page_type': self._extract_spec_value(section, 'Recommended Page Type'),
                'advanced_pattern': self._extract_spec_value(section, '高级正文模式'),
                'preferred_template': self._extract_spec_value(section, '优先页型'),
                'page_role': self._extract_spec_value(section, '页面角色'),
                'previous_relation': self._extract_spec_value(section, '与上一页关系'),
                'next_relation': self._extract_spec_value(section, '与下一页关系'),
            }
        return slide_specs

    def _load_storyline_sections(self, storyline_path: Optional[Path]) -> List[str]:
        """Load expected storyline section titles for TOC completeness checks."""
        if not storyline_path or not storyline_path.exists():
            return []
        try:
            content = storyline_path.read_text(encoding='utf-8')
        except Exception:
            return []

        sections: List[str] = []
        for match in re.finditer(r'(?m)^###\s+章节\s+\d+\s*[：:]\s*(.+)$', content):
            title = match.group(1).strip()
            title = re.sub(r'\s*[（(]第\s*\d+\s*[-–—]\s*\d+\s*页[）)]\s*$', '', title)
            if title:
                sections.append(title)
        return sections

    def _index_page_specs_by_title(self, page_specs: Dict[int, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """Build a normalized title index for matching complex-page models."""
        indexed: Dict[str, Dict[str, str]] = {}
        for page_spec in page_specs.values():
            title = page_spec.get('title', '').strip()
            if not title:
                continue
            indexed[self._normalize_title_key(title)] = page_spec
        return indexed

    def _load_complex_page_models(self, model_path: Optional[Path]) -> Dict[str, Dict]:
        """Load `<project>/notes/complex_page_models.md` for structure-aware QA."""
        model_index: Dict[str, Dict] = {
            'by_slide': {},
            'by_title': {},
            'path': str(model_path) if model_path else '',
        }
        if not model_path or not model_path.exists():
            return model_index

        try:
            content = model_path.read_text(encoding='utf-8')
        except Exception:
            return model_index

        for heading, block in self._extract_markdown_blocks(content):
            slide_num, title = self._parse_section_heading(heading)
            model = {
                'heading': heading.strip(),
                'title': title,
            }
            for field_name, aliases in self.COMPLEX_MODEL_FIELD_ALIASES.items():
                model[field_name] = self._extract_labeled_value(block, aliases)
            if slide_num is not None:
                model['slide_num'] = slide_num
                model_index['by_slide'][slide_num] = model
            normalized_title = self._normalize_title_key(title)
            if normalized_title:
                model_index['by_title'][normalized_title] = model
        return model_index

    def _extract_markdown_blocks(self, content: str) -> List[Tuple[str, str]]:
        """Split markdown content into `####` blocks."""
        heading_re = re.compile(r'(?im)^####\s+(.+)$')
        matches = list(heading_re.finditer(content))
        blocks: List[Tuple[str, str]] = []
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            blocks.append((match.group(1).strip(), content[start:end]))
        return blocks

    def _parse_section_heading(self, heading: str) -> Tuple[Optional[int], str]:
        """Parse markdown `####` headings like `Slide 03 - Title` or `03 Title`."""
        match = re.match(r'(?i)^slide\s+(\d+)\s*[-:：]\s*(.+)$', heading.strip())
        if match:
            return int(match.group(1)), match.group(2).strip()

        match = re.match(r'^第\s*(\d+)\s*页\s*(.+)$', heading.strip())
        if match:
            return int(match.group(1)), match.group(2).strip()

        match = re.match(r'^(\d+)\s*[-_.:：]?\s*(.+)$', heading.strip())
        if match:
            return int(match.group(1)), match.group(2).strip()

        return None, heading.strip()

    def _extract_labeled_value(self, block: str, labels: Tuple[str, ...]) -> str:
        """Extract a markdown bullet/block field from a complex page model block."""
        lines = block.splitlines()
        start_idx = -1
        first_value = ''

        for idx, line in enumerate(lines):
            stripped = line.strip()
            for label in labels:
                match = re.match(
                    rf'^(?:-\s*)?(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*[:：]\s*(.*)$',
                    stripped,
                )
                if match:
                    start_idx = idx
                    first_value = match.group(1).strip()
                    break
            if start_idx != -1:
                break

        if start_idx == -1:
            return ''

        collected: List[str] = []
        if first_value:
            collected.append(first_value)

        known_labels = {
            alias
            for alias_group in self.COMPLEX_MODEL_FIELD_ALIASES.values()
            for alias in alias_group
        }
        for line in lines[start_idx + 1:]:
            stripped = line.strip()
            if not stripped:
                if collected:
                    collected.append('')
                continue
            is_next_field = False
            for label in known_labels:
                if re.match(
                    rf'^(?:-\s*)?(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*[:：]\s*(.*)$',
                    stripped,
                ):
                    is_next_field = True
                    break
            if is_next_field:
                break
            collected.append(stripped)

        value = "\n".join(part for part in collected).strip()
        value = re.sub(r'`([^`]+)`', r'\1', value)
        return value.strip()

    def _extract_spec_value(self, section: str, label: str) -> str:
        """Extract a markdown bullet value from design_spec.md and normalize code spans."""
        pattern = rf'- \*\*{re.escape(label)}\*\*:\s*(.+)'
        match = re.search(pattern, section)
        if not match:
            return ''
        value = match.group(1).strip()
        value = re.sub(r'`([^`]+)`', r'\1', value)
        return value.strip()

    def _resolve_page_spec(self, filename: str) -> Dict[str, str]:
        """Match an SVG filename back to the slide entry in design_spec.md."""
        if not self.page_specs:
            return {}
        slide_num = self._extract_slide_number(filename)
        if slide_num is None:
            return {}
        return self.page_specs.get(slide_num, {})

    def _resolve_complex_page_model(self, filename: str, page_spec: Dict[str, str]) -> Dict[str, str]:
        """Match the current SVG back to its complex-page reasoning block when available."""
        model_index = self.complex_page_models or {}
        slide_num = self._extract_slide_number(filename)
        if slide_num is not None:
            slide_model = model_index.get('by_slide', {}).get(slide_num)
            if slide_model:
                return slide_model

        title = page_spec.get('title', '').strip()
        if title:
            title_model = model_index.get('by_title', {}).get(self._normalize_title_key(title))
            if title_model:
                return title_model
        return {}

    def _extract_slide_number(self, filename: str) -> Optional[int]:
        """Read the leading numeric page index from an SVG filename."""
        match = re.match(r'(\d+)', filename)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _normalize_title_key(self, value: str) -> str:
        """Normalize titles for tolerant cross-file matching."""
        value = value.strip().lower()
        value = re.sub(r'(?i)^slide\s+\d+\s*[-:：]\s*', '', value)
        value = re.sub(r'^\d+\s*[-_.:：]?\s*', '', value)
        value = re.sub(r'\s+', '', value)
        return value

    def _normalize_advanced_pattern(self, raw_value: str) -> str:
        """Normalize advanced-pattern values from design spec or SVG metadata."""
        cleaned = re.sub(r'[`*\s]+', '', raw_value or '').lower()
        if not cleaned or '无' in cleaned or cleaned == 'none':
            return ''
        return cleaned

    def _normalize_structure_type(self, raw_value: str, advanced_pattern: str = '') -> str:
        """Map free-form structure descriptions to a small normalized set."""
        raw = re.sub(r'[`*_]', '', raw_value or '').strip().lower()
        for key, value in self.COMPLEX_STRUCTURE_ALIASES.items():
            if key.lower() in raw:
                return value

        pattern = self._normalize_advanced_pattern(advanced_pattern)
        if pattern in {'attack_case_chain', 'timeline_roadmap'}:
            return 'chain'
        if pattern in {'layered_system_map', 'attack_tree_architecture', 'maturity_model'}:
            return 'layered'
        if pattern in {'matrix_defense_map', 'governance_control_matrix'}:
            return 'matrix'
        if pattern in {'operation_loop'}:
            return 'loop'
        if pattern in {'swimlane_collaboration', 'multi_lane_execution_chain'}:
            return 'swimlane'
        if pattern in {'evidence_wall', 'evidence_attached_case_chain', 'evidence_cockpit'}:
            return 'evidence'
        return ''

    def _normalize_page_role(self, raw_value: str) -> str:
        """Normalize page-role labels."""
        raw = re.sub(r'[`*_]', '', raw_value or '').strip().lower()
        if not raw:
            return ''
        if '概览' in raw or 'overview' in raw:
            return 'overview'
        if '推进' in raw or 'advance' in raw:
            return 'advance'
        if '证明' in raw or 'evidence' in raw or 'proof' in raw:
            return 'evidence'
        if '收束' in raw or 'closure' in raw:
            return 'closure'
        return raw

    def _normalize_semantic_text(self, value: str) -> str:
        text = re.sub(r'[`*_]+', '', value or '')
        text = re.sub(r'\s+', '', text)
        return text.strip()

    def _looks_like_judgment_sentence(self, value: str) -> bool:
        normalized = self._normalize_semantic_text(value)
        if len(normalized) < 6:
            return False
        if normalized in self.GENERIC_JUDGMENT_PHRASES:
            return False
        return any(marker in normalized for marker in self.JUDGMENT_MARKERS)

    def _semantic_keywords(self, value: str) -> List[str]:
        text = self._normalize_semantic_text(value)
        if not text:
            return []
        text = re.sub(r'第\d+页', '', text)
        parts = re.split(r'[，。；：、“”‘’（）()【】/\-|]+', text)
        keywords: List[str] = []
        for part in parts:
            cleaned = part.strip()
            if len(cleaned) < 2:
                continue
            if cleaned in keywords:
                continue
            keywords.append(cleaned)
        if not keywords and text:
            keywords.append(text)
        return keywords[:8]

    def _headline_matches_judgment(self, headline: str, judgment: str) -> bool:
        normalized_headline = self._normalize_semantic_text(headline)
        normalized_judgment = self._normalize_semantic_text(judgment)
        if not normalized_headline or not normalized_judgment:
            return False
        if normalized_headline in normalized_judgment or normalized_judgment in normalized_headline:
            return True
        collapsed_headline = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized_headline)
        collapsed_judgment = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized_judgment)
        if collapsed_headline and collapsed_judgment and (
            collapsed_headline in collapsed_judgment or collapsed_judgment in collapsed_headline
        ):
            return True
        headline_keywords = set(self._semantic_keywords(headline))
        judgment_keywords = set(self._semantic_keywords(judgment))
        if not headline_keywords or not judgment_keywords:
            return self._semantic_texts_overlap(headline, judgment)
        if len(headline_keywords & judgment_keywords) >= 2:
            return True
        return self._semantic_texts_overlap(headline, judgment)

    def _semantic_keyword_set(self, value: str) -> Set[str]:
        """Extract more stable keywords by dropping page-type filler words."""
        keywords: Set[str] = set()
        def add_keyword_variants(raw_value: str) -> None:
            raw_value = raw_value.strip()
            if len(raw_value) < 2:
                return
            variants = {raw_value}
            prefix_stripped = re.sub(
                r'^(整体|总体|核心|关键|主要|本次|当前|后续|进一步|继续|先|再|最后|优先|应|需|需要|必须|收口|切断|封堵|阻断|补强|治理|整改|复测|验证|安排|补齐|压降|确认|判断|证明|说明|聚焦|围绕|按)',
                '',
                raw_value,
            )
            if prefix_stripped and prefix_stripped != raw_value:
                variants.add(prefix_stripped)
            suffix_stripped = re.sub(
                r'(总览|概览|概述|摘要|分析|拆解|矩阵|路径|链路|案例|结构|页面|模块|动作|结果|问题|治理|整改|闭环|风险|判断|证明)$',
                '',
                raw_value,
            )
            if suffix_stripped and suffix_stripped != raw_value:
                variants.add(suffix_stripped)
            combined = re.sub(
                r'(总览|概览|概述|摘要|分析|拆解|矩阵|路径|链路|案例|结构|页面|模块|动作|结果|问题|治理|整改|闭环|风险|判断|证明)$',
                '',
                prefix_stripped,
            )
            if combined and combined != raw_value:
                variants.add(combined)
            if raw_value.startswith('非') and len(raw_value) >= 3:
                variants.add(raw_value[1:])
            if '后的' in raw_value:
                before, after = raw_value.split('后的', 1)
                if before:
                    variants.add(before)
                if after:
                    variants.add(after)
            for candidate in variants:
                candidate = candidate.strip()
                if len(candidate) < 2 or candidate in self.SEMANTIC_KEYWORD_STOPWORDS:
                    continue
                keywords.add(candidate)

        for item in self._semantic_keywords(value):
            fragments = [
                part.strip()
                for part in re.split(
                    r'(?:与|和|及|并|共同|导致|形成|放大|推进|整改|复测|验证|切断|封堵|收口|治理|补齐|安排|并非|而是|使|缺少|滞后|存在)',
                    item,
                )
                if part.strip()
            ]
            if not fragments:
                fragments = [item.strip()]
            for fragment in fragments:
                add_keyword_variants(fragment)
        return keywords

    def _has_semantic_value_marker(self, value: str) -> bool:
        normalized = self._normalize_semantic_text(value)
        if not normalized:
            return False
        return any(marker in normalized for marker in self.CHAPTER_SUBTITLE_VALUE_MARKERS)

    def _looks_generic_module_title(self, value: str) -> bool:
        normalized = self._normalize_semantic_text(value)
        if not normalized:
            return False
        normalized_generic_titles = {
            self._normalize_semantic_text(item) for item in self.GENERIC_MODULE_TITLES
        }
        if normalized in normalized_generic_titles:
            return True
        if len(normalized) <= 8 and any(token in normalized for token in ("总览", "概览", "摘要")):
            return True
        if re.match(
            r'^(?:关键|核心|主要|直接)?(?:问题|证据|结果|动作|判断|结论|治理|案例)(?:现状|总览|概览|摘要|拆解|矩阵|链路|路径)?$',
            normalized,
        ):
            return True
        return False

    def _module_title_matches_references(self, title: str, references: List[str]) -> bool:
        title_norm = self._normalize_semantic_text(title)
        if not title_norm:
            return False
        title_keywords = self._semantic_keyword_set(title)
        for reference in references:
            ref_norm = self._normalize_semantic_text(reference)
            if not ref_norm:
                continue
            if len(title_norm) >= 4 and title_norm in ref_norm:
                return True
            for keyword in title_keywords:
                if keyword in ref_norm:
                    return True
            ref_keywords = self._semantic_keyword_set(reference)
            if title_keywords and ref_keywords and title_keywords & ref_keywords:
                return True
            if title_keywords and ref_keywords:
                for title_keyword in title_keywords:
                    for ref_keyword in ref_keywords:
                        if len(title_keyword) < 2 or len(ref_keyword) < 2:
                            continue
                        if title_keyword in ref_keyword or ref_keyword in title_keyword:
                            return True
            if self._semantic_texts_overlap(title, reference):
                return True
        return False

    def _semantic_texts_overlap(self, left: str, right: str) -> bool:
        left_norm = self._normalize_semantic_text(left)
        right_norm = self._normalize_semantic_text(right)
        if not left_norm or not right_norm:
            return False
        if min(len(left_norm), len(right_norm)) >= 4 and (
            left_norm in right_norm or right_norm in left_norm
        ):
            return True
        left_keywords = self._semantic_keyword_set(left)
        right_keywords = self._semantic_keyword_set(right)
        if left_keywords and right_keywords and left_keywords & right_keywords:
            return True
        if left_keywords and right_keywords:
            for left_keyword in left_keywords:
                for right_keyword in right_keywords:
                    if len(left_keyword) < 2 or len(right_keyword) < 2:
                        continue
                    if left_keyword in right_keyword or right_keyword in left_keyword:
                        return True
        return False

    def _normalize_progression_title_key(self, value: str) -> str:
        normalized = self._normalize_title_key(value or '')
        normalized = re.sub(r'[（(]第?[一二三四五六七八九十\d]+组[）)]', '', normalized)
        normalized = re.sub(r'第?[一二三四五六七八九十\d]+组', '', normalized)
        normalized = re.sub(r'(总览|概览|概述|摘要|分析)$', '', normalized)
        return normalized.strip()

    def _relation_text_is_generic(self, value: str) -> bool:
        normalized = self._normalize_semantic_text(value)
        if not normalized:
            return True
        if normalized in self.GENERIC_RELATION_PATTERNS:
            return True
        if len(normalized) <= 10 and any(token in normalized for token in ("上一页", "下一页", "章节页")):
            return True
        return False

    def _looks_like_closure_sentence(self, value: str) -> bool:
        normalized = self._normalize_semantic_text(value)
        if len(normalized) < 4:
            return False
        if any(pattern in normalized for pattern in self.GENERIC_CLOSURE_PATTERNS):
            return False
        return any(marker in normalized for marker in self.CLOSURE_ACTION_MARKERS)

    def _build_page_qa_policy(self, result: Dict) -> Dict[str, object]:
        """Compute layout-aware QA thresholds so advanced pages are checked fairly."""
        policy: Dict[str, object] = {
            'card_min_padding': self.CARD_MIN_PADDING,
            'card_vertical_padding': 10,
            'card_hard_padding': -2,
            'card_hard_vertical_padding': -4,
            'card_comfort_padding': self.CARD_COMFORT_PADDING,
            'card_width_warn_ratio': 1.0,
            'card_width_error_ratio': 1.18,
            'card_height_warn_ratio': 1.0,
            'card_height_error_ratio': 1.18,
            'density_warn_major_blocks': self.DENSITY_MAX_MAJOR_BLOCKS,
            'density_warn_total_lines': self.DENSITY_MAX_TOTAL_LINES,
            'density_warn_total_chars': self.DENSITY_MAX_TOTAL_CHARS,
            'density_error_major_blocks': self.DENSITY_MAX_MAJOR_BLOCKS + 10,
            'density_error_total_lines': self.DENSITY_MAX_TOTAL_LINES + 12,
            'density_error_total_chars': self.DENSITY_MAX_TOTAL_CHARS + 120,
            'warning_only_codes': set(),
        }

        context = result.get('template_context', {})
        advanced_pattern = context.get('advanced_pattern')
        if advanced_pattern and advanced_pattern in self.ADVANCED_PATTERN_QA_POLICIES:
            policy.update(self.ADVANCED_PATTERN_QA_POLICIES[advanced_pattern])
            policy['warning_only_codes'] = set(self.ADVANCED_PATTERN_WARNING_ONLY_CODES)

        return policy

    def _check_complex_page_consistency(self, content: str, result: Dict):
        """Check whether complex-page SVG structure matches the modeled page logic."""
        page_spec = result.get('page_spec', {})
        model = result.get('complex_page_model', {})
        context = result.get('template_context', {})

        advanced_pattern = self._normalize_advanced_pattern(
            page_spec.get('advanced_pattern') or str(context.get('advanced_pattern', ''))
        )
        if not advanced_pattern and not model:
            return

        structure_type = self._normalize_structure_type(
            model.get('structure_type', ''),
            advanced_pattern=advanced_pattern,
        )
        page_role = self._normalize_page_role(
            model.get('page_role', '') or page_spec.get('page_role', '')
        )

        text_blocks = self._extract_text_blocks(content)
        content_scope = self._extract_content_area(content) or content
        content_text_blocks = self._extract_text_blocks(content_scope)
        rects = self._collect_rect_containers(content_scope)
        canvas_width, canvas_height = self._get_canvas_size(content)
        metrics = self._collect_complex_layout_metrics(
            content_scope,
            text_blocks,
            content_text_blocks,
            rects,
            canvas_width,
            canvas_height,
        )
        metrics['advanced_pattern'] = advanced_pattern
        metrics['structure_type'] = structure_type
        metrics['page_role'] = page_role
        result['info']['complex_metrics'] = {
            'major_nodes': metrics['major_nodes'],
            'connector_count': metrics['connector_count'],
            'row_groups': metrics['row_groups'],
            'col_groups': metrics['col_groups'],
            'lane_count': metrics['lane_count'],
            'hub_count': metrics['hub_count'],
            'summary_rect_count': metrics['summary_rect_count'],
            'side_summary_count': metrics['side_summary_count'],
            'evidence_count': metrics['evidence_count'],
            'headline_count': metrics['headline_count'],
            'headline_judgment_count': metrics['headline_judgment_count'],
            'headline_texts': metrics['headline_texts'],
            'module_title_count': metrics['module_title_count'],
            'module_title_texts': metrics['module_title_texts'],
            'closure_count': metrics['closure_count'],
            'closure_band_count': metrics['closure_band_count'],
            'closure_action_count': metrics['closure_action_count'],
            'closure_texts': metrics['closure_texts'],
        }

        self._check_complex_page_baseline(metrics, result)
        self._check_complex_structure_by_type(structure_type, advanced_pattern, metrics, result)
        self._check_complex_role_expectation(page_role, model, metrics, result)
        self._check_complex_headline_semantics(page_spec, model, metrics, result)
        self._check_complex_argument_cohesion(page_spec, model, metrics, result)
        self._check_complex_closure_semantics(model, metrics, result)
        self._check_adjacent_complex_progression(page_spec, model, metrics, result)
        self._check_security_service_pattern_detail(advanced_pattern, metrics, model, result)

    def _check_visual_hierarchy_collisions(self, content: str, result: Dict):
        """Catch module-to-module collisions that are visually obvious in exported PPTs."""
        text_blocks = self._extract_text_blocks(content)
        rects = self._collect_rect_containers(content)
        separators = self._collect_separator_elements(content)
        filename = result.get('file', '')
        context = result.get('template_context', {})

        self._check_top_stack_collision(rects, result)
        self._check_headline_bundle_collision(text_blocks, rects, result)
        self._check_headline_separator_collision(text_blocks, separators, result)
        self._check_chapter_safe_zone_collision(text_blocks, filename, context, result)

    def _check_semantic_completion(self, content: str, result: Dict):
        """Block outputs that are layout-clean but semantically still unfinished."""
        text_blocks = self._extract_text_blocks(content)
        page_spec = result.get('page_spec', {})
        self._check_planning_scaffold_leakage(text_blocks, result)
        self._check_planning_tone_leakage(text_blocks, result)
        self._check_soft_term_blacklist(text_blocks, result)
        self._check_visible_ellipsis(text_blocks, result)
        self._check_fixed_template_semantics(page_spec, result)
        self._check_chapter_desc_semantics(text_blocks, page_spec, result)
        self._check_chapter_number_semantics(text_blocks, page_spec, result)
        self._check_cover_title_semantics(text_blocks, page_spec, result)
        self._check_toc_section_coverage(text_blocks, page_spec, result)

    def _check_planning_scaffold_leakage(self, text_blocks: List[Dict], result: Dict):
        """Final SVG must not leak planning-card labels into customer-facing pages."""
        leaked = []
        forbidden_labels = {"页面意图", "证明目标", "支撑证据", "讲述推进"}
        for block in text_blocks:
            text = re.sub(r'\s+', '', block.get('text', ''))
            if text in forbidden_labels:
                leaked.append(text)
        if leaked:
            result['errors'].append(
                "Planning scaffold leakage: final SVG still exposes planning labels instead of finished client-facing content "
                f"{self._format_examples(sorted(set(leaked))[:3])}"
            )

    def _check_planning_tone_leakage(self, text_blocks: List[Dict], result: Dict):
        page_family = str(result.get('template_context', {}).get('page_family') or '')
        if page_family not in {'toc', 'chapter', 'section'}:
            return
        leaked = []
        for block in text_blocks:
            text = block.get('text', '')
            if self._contains_planning_tone(text):
                leaked.append(self._clip_text(text, 28))
        if leaked:
            result['errors'].append(
                "Planning tone leakage: fixed pages still show internal transition language instead of client-facing chapter copy "
                f"{self._format_examples(sorted(set(leaked))[:3])}"
            )

    def _check_soft_term_blacklist(self, text_blocks: List[Dict], result: Dict):
        hits = []
        for block in text_blocks:
            text = re.sub(r'\s+', '', block.get('text', ''))
            for term in self.SOFT_TERM_BLACKLIST:
                if term in text:
                    hits.append(term)
        if hits:
            result['errors'].append(
                "Soft content blacklist violation: final SVG still uses banned consultant-like filler terms "
                f"{self._format_examples(sorted(set(hits))[:4])}"
            )

    def _check_visible_ellipsis(self, text_blocks: List[Dict], result: Dict):
        """Customer-facing final SVG must not expose truncation markers like `…`."""
        hits = []
        for block in text_blocks:
            text = re.sub(r'\s+', '', block.get('text', ''))
            if not text:
                continue
            if len(text) <= 2:
                continue
            if '…' not in text and '...' not in text:
                continue
            hits.append(self._clip_text(text, 24))
        if hits:
            result['errors'].append(
                "Visible ellipsis violation: final SVG still contains truncated customer-facing copy "
                f"{self._format_examples(sorted(set(hits))[:4])}"
            )

    def _check_chapter_desc_semantics(self, text_blocks: List[Dict], page_spec: Dict[str, str], result: Dict):
        """Chapter divider subtitle must add real information instead of repeating the chapter title."""
        preferred_template = str(page_spec.get('preferred_template') or '').strip()
        page_family = str(result.get('template_context', {}).get('page_family') or '').lower()
        if preferred_template != '02_chapter.svg' and page_family not in {'chapter', 'section'}:
            return

        title = re.sub(r'^(章节页|分节页)\s*[/／]\s*', '', page_spec.get('title', '').strip())
        if not title:
            return

        candidates = []
        for block in text_blocks:
            text = block.get('text', '').strip()
            if not text:
                continue
            compact = re.sub(r'\s+', '', text)
            if len(compact) < 4:
                continue
            if block.get('font_size', 0) < 14 or block.get('font_size', 0) > 24:
                continue
            if block.get('y', 0) < 395 or block.get('y', 0) > 470:
                continue
            candidates.append(text)

        if not candidates:
            result['errors'].append(
                "Chapter subtitle semantic violation: divider page is missing a readable chapter subtitle / description"
            )
            return

        subtitle = max(candidates, key=lambda item: len(re.sub(r'\s+', '', item)))
        normalized_title = self._normalize_title_key(title)
        normalized_subtitle = self._normalize_title_key(subtitle)
        if (
            normalized_subtitle in self.GENERIC_CHAPTER_DESCS
            or normalized_subtitle == normalized_title
            or normalized_subtitle in normalized_title
            or normalized_title in normalized_subtitle
        ):
            result['errors'].append(
                "Chapter subtitle semantic violation: divider subtitle is still generic or repeats the chapter title "
                f"{self._format_examples([subtitle])}"
            )
            return

        title_overlap = self._semantic_texts_overlap(subtitle, title)
        reduced_subtitle = normalized_subtitle
        if normalized_title and normalized_title in reduced_subtitle:
            reduced_subtitle = reduced_subtitle.replace(normalized_title, '', 1)
        reduced_subtitle = re.sub(
            r'^(本章|章节|本节|分节|关于|围绕)',
            '',
            reduced_subtitle,
        )
        reduced_subtitle = re.sub(
            r'(总览|概览|概述|摘要|分析|说明|部分|内容|章节|本章)$',
            '',
            reduced_subtitle,
        )
        if title_overlap and not self._has_semantic_value_marker(subtitle) and len(reduced_subtitle) < 2:
            result['errors'].append(
                "Chapter subtitle semantic violation: divider subtitle is only a weak restatement of the chapter title and does not add scope / action / management focus "
                f"{self._format_examples([subtitle])}"
            )

    def _derive_storyline_section_index(self, page_spec: Dict[str, str], result: Dict) -> Optional[int]:
        """Map the current chapter/section page to the expected storyline index."""
        if not self.storyline_sections:
            return None

        candidates: List[str] = []
        title = page_spec.get('title', '').strip()
        if title:
            cleaned = re.sub(r'^(章节页|分节页|目录页|封面页|结束页)\s*[/／]\s*', '', title)
            cleaned = re.sub(r'^\d+\s*[-_.:：]?\s*', '', cleaned)
            candidates.append(cleaned)
        filename = result.get('file', '')
        if filename:
            stem = Path(filename).stem
            stem = re.sub(r'^\d+\s*[_-]?\s*', '', stem)
            stem = re.sub(r'^(章节页|分节页|目录页|封面页|结束页)\s*[_-]?\s*', '', stem)
            candidates.append(stem.replace('_', ' '))

        normalized_candidates = []
        for candidate in candidates:
            normalized = self._normalize_title_key(candidate)
            if normalized and normalized not in normalized_candidates:
                normalized_candidates.append(normalized)

        if not normalized_candidates:
            return None

        for idx, section in enumerate(self.storyline_sections, start=1):
            normalized_section = self._normalize_title_key(section)
            if not normalized_section:
                continue
            for candidate in normalized_candidates:
                if (
                    candidate == normalized_section
                    or candidate in normalized_section
                    or normalized_section in candidate
                ):
                    return idx
        return None

    def _check_chapter_number_semantics(self, text_blocks: List[Dict], page_spec: Dict[str, str], result: Dict):
        """Chapter/section divider pages must use storyline numbering, not slide numbers."""
        preferred_template = str(page_spec.get('preferred_template') or '')
        page_family = str(result.get('template_context', {}).get('page_family') or '').lower()
        if page_family not in {'chapter', 'section'} and preferred_template not in {'02_chapter.svg', '15_section.svg'}:
            return

        if any(
            token in block.get('raw', '')
            for block in text_blocks
            for token in ('CHAPTER_NUM', 'SECTION_NUM')
        ):
            return

        large_numbers = []
        for block in text_blocks:
            text = re.sub(r'\s+', '', block.get('text', ''))
            if re.fullmatch(r'\d{1,2}', text) and block.get('font_size', 0) >= 48:
                large_numbers.append((int(text), block))

        if not large_numbers:
            result['warnings'].append(
                "Chapter numbering risk: chapter divider page is missing a visible chapter index"
            )
            return

        actual_number, number_block = max(
            large_numbers,
            key=lambda item: (item[1].get('font_size', 0), item[1].get('estimated_width', 0)),
        )
        expected_index = self._derive_storyline_section_index(page_spec, result)
        slide_num = self._extract_slide_number(result.get('file', ''))

        if expected_index is not None and actual_number != expected_index:
            if slide_num is not None and actual_number == slide_num:
                result['errors'].append(
                    "Chapter number semantic violation: divider page is using the slide index instead of the storyline chapter index "
                    f"(expected {expected_index:02d}, found {actual_number:02d})"
                )
            else:
                result['errors'].append(
                    "Chapter number semantic violation: divider page chapter index does not match the storyline section ordering "
                    f"(expected {expected_index:02d}, found {actual_number:02d})"
                )
            return

        if expected_index is None and slide_num is not None and actual_number == slide_num and len(self.storyline_sections) > 0:
            if slide_num > len(self.storyline_sections):
                result['errors'].append(
                    "Chapter number semantic violation: divider page appears to expose the slide index as chapter numbering "
                    f"{self._format_examples([number_block.get('text', '')])}"
                )

    def _check_fixed_template_semantics(self, page_spec: Dict[str, str], result: Dict):
        """Fixed templates must only be used on truly matching pages."""
        preferred_template = str(page_spec.get('preferred_template') or '').strip()
        if not preferred_template or fixed_template_matches_entry is None:
            return

        slide_num = self._extract_slide_number(result.get('file', ''))
        if not fixed_template_matches_entry(
            preferred_template,
            {
                'page_num': str(slide_num or ''),
                '页面类型': page_spec.get('title', ''),
                '推荐页型': page_spec.get('recommended_page_type', ''),
            },
            page_num=slide_num,
            total_pages=len(self.page_specs),
        ):
            result['errors'].append(
                f"Fixed template mismatch: `{preferred_template}` does not match the page semantics declared in design_spec"
            )

    def _check_cover_title_semantics(self, text_blocks: List[Dict], page_spec: Dict[str, str], result: Dict):
        """Cover page should not expose internal slugs as the presentation title."""
        preferred_template = str(page_spec.get('preferred_template') or '')
        page_family = str(result.get('template_context', {}).get('page_family') or '').lower()
        is_cover = preferred_template == '01_cover.svg' or page_family == 'cover'
        if not is_cover:
            return
        suspects = []
        for block in text_blocks:
            text = block.get('text', '').strip()
            if block.get('font_size', 0) < 22:
                continue
            if is_slug_like and is_slug_like(text):
                suspects.append(self._clip_text(text))
        if suspects:
            result['errors'].append(
                "Cover title semantic violation: cover still shows an internal project token instead of a customer-facing title "
                f"{self._format_examples(suspects[:2])}"
            )

    def _check_toc_section_coverage(self, text_blocks: List[Dict], page_spec: Dict[str, str], result: Dict):
        """TOC must cover the expected storyline chapters, not only fit the layout."""
        preferred_template = str(page_spec.get('preferred_template') or '')
        if preferred_template != '02_toc.svg' and not self._looks_like_toc(result.get('file', '')):
            return
        if not self.storyline_sections:
            return

        toc_text = ''.join(re.sub(r'\s+', '', block.get('text', '')) for block in text_blocks)
        missing = []
        for section in self.storyline_sections:
            compact = re.sub(r'\s+', '', section)
            parts = [part for part in re.split(r'[／/、，,；;与及和-]+', compact) if len(part) >= 2]
            candidates = [compact] + parts
            if not any(candidate and candidate in toc_text for candidate in candidates):
                missing.append(section)

        if missing:
            result['errors'].append(
                "TOC completeness violation: directory page is missing expected storyline sections "
                f"{self._format_examples(missing[:3])}"
            )

    def _check_top_stack_collision(self, rects: List[Dict], result: Dict):
        """Detect a top chip/tag colliding with the first header/module row."""
        label_rects = [
            rect for rect in rects
            if rect['y'] <= 170
            and 110 <= rect['width'] <= 320
            and 24 <= rect['height'] <= 42
        ]
        header_rects = [
            rect for rect in rects
            if rect['y'] <= 240
            and 160 <= rect['width'] <= 360
            and 44 <= rect['height'] <= 88
        ]

        examples: List[str] = []
        for label in label_rects:
            for header in header_rects:
                if header is label or header['y'] <= label['y']:
                    continue
                overlap = self._horizontal_overlap(label, header)
                if overlap < min(label['width'], header['width']) * 0.42:
                    continue
                gap = header['y'] - label['bottom']
                if gap < 12:
                    examples.append(
                        f"label y={label['y']:.0f}-{label['bottom']:.0f} vs header y={header['y']:.0f}-{header['bottom']:.0f}"
                    )
                    if len(examples) >= 2:
                        break
            if len(examples) >= 2:
                break

        if examples:
            result['warnings'].append(
                "Top stack collision risk: top label/tag strip sits too close to the first structural header row"
                f"{self._format_examples(examples)}"
            )

    def _check_headline_bundle_collision(self, text_blocks: List[Dict], rects: List[Dict], result: Dict):
        """Detect overly tight title/subtitle/judgment stacks in the upper page band."""
        headline_containers = [
            rect for rect in rects
            if rect['y'] <= 240
            and rect['width'] >= 460
            and 56 <= rect['height'] <= 180
        ]
        examples: List[str] = []

        for container in headline_containers:
            blocks = [
                block for block in text_blocks
                if not self._is_minor_label(block)
                and block['top'] >= container['y'] - 6
                and block['bottom'] <= container['bottom'] + 6
                and block['left'] >= container['x'] - 6
                and block['right'] <= container['right'] + 6
            ]
            blocks.sort(key=lambda item: (item['top'], item['left']))
            for idx in range(len(blocks) - 1):
                first = blocks[idx]
                second = blocks[idx + 1]
                if (
                    abs(first['font_size'] - second['font_size']) < 0.6
                    and abs(first['x'] - second['x']) < 2.0
                    and first.get('text_anchor') == second.get('text_anchor')
                    and (second['top'] - first['bottom']) <= first['font_size'] * 1.2
                ):
                    # Treat tightly stacked same-style lines as one multiline title block.
                    continue
                horizontal_overlap = max(0.0, min(first['right'], second['right']) - max(first['left'], second['left']))
                vertical_gap = second['top'] - first['bottom']
                if horizontal_overlap >= 120 and vertical_gap < 8:
                    examples.append(
                        f"{self._clip_text(first['text'])} -> {self._clip_text(second['text'])}"
                    )
                    break
            if examples:
                break

        if examples:
            result['warnings'].append(
                "Headline bundle collision risk: title / subtitle / judgment group is too tight and may overlap after PPT export"
                f"{self._format_examples(examples)}"
            )

    def _check_headline_separator_collision(self, text_blocks: List[Dict], separators: List[Dict], result: Dict):
        """Detect divider lines or accent bars crossing compacted headline text."""
        if not separators:
            return

        headline_blocks = [
            block for block in text_blocks
            if not self._is_minor_label(block)
            and block['top'] <= 280
            and block['bottom'] >= 170
        ]
        examples: List[str] = []

        for separator in separators:
            if separator['y'] > 280 or separator['height'] > 10:
                continue
            for block in headline_blocks:
                overlap = max(0.0, min(block['right'], separator['right']) - max(block['left'], separator['x']))
                if overlap < min(block['right'] - block['left'], separator['width']) * 0.22:
                    continue
                if not self._boxes_intersect(block, separator, pad=0.0):
                    continue
                examples.append(
                    f"{self._clip_text(block['text'])} @ y={block['top']:.0f}-{block['bottom']:.0f} vs separator y={separator['y']:.0f}-{separator['bottom']:.0f}"
                )
                if len(examples) >= 2:
                    break
            if len(examples) >= 2:
                break

        if examples:
            result['warnings'].append(
                "Headline bundle collision risk: separator line or accent bar crosses headline text"
                f"{self._format_examples(examples)}"
            )

    def _check_chapter_safe_zone_collision(
        self,
        text_blocks: List[Dict],
        filename: str,
        context: Dict[str, object],
        result: Dict,
    ):
        """Protect chapter-page decorative numerals from being crossed by descriptions."""
        page_family = str(context.get('page_family') or '').lower()
        is_chapter = '章节页' in filename or page_family in {'chapter', 'section'}
        if not is_chapter:
            return

        numeral_blocks = [
            block for block in text_blocks
            if block['font_size'] >= 150
            and block['x'] <= 260
            and re.fullmatch(r'\d{1,3}', re.sub(r'\s+', '', block['text']))
        ]
        desc_blocks = [
            block for block in text_blocks
            if 14 <= block['font_size'] <= 26
            and block['y'] >= 380
            and self._count_cjk_chars(block['text']) >= 6
        ]

        for numeral in numeral_blocks:
            for desc in desc_blocks:
                if desc['left'] < numeral['right'] + 24 and desc['top'] < numeral['bottom'] - 20:
                    result['warnings'].append(
                        "Chapter safe-zone risk: chapter description intrudes into the decorative numeral area"
                        f"{self._format_examples([self._clip_text(desc['text'])])}"
                    )
                    return

    def _collect_complex_layout_metrics(
        self,
        content_scope: str,
        text_blocks: List[Dict],
        content_text_blocks: List[Dict],
        rects: List[Dict],
        canvas_width: float,
        canvas_height: float,
    ) -> Dict[str, object]:
        """Extract coarse structural metrics for complex-page reasoning QA."""
        node_rects = [
            rect for rect in rects
            if 90 <= rect['width'] <= canvas_width * 0.78
            and 42 <= rect['height'] <= canvas_height * 0.38
        ]
        major_nodes = [
            rect for rect in node_rects
            if rect['width'] >= 120 and rect['height'] >= 52 and rect['area'] >= 12000
        ]
        lane_rects = [
            rect for rect in rects
            if (
                rect['width'] >= canvas_width * 0.55
                and 48 <= rect['height'] <= 180
            )
            or (
                48 <= rect['height'] <= 180
                and re.search(r'(?:data-slot|data-structure-role)=["\'][^"\']*(?:lane|collaboration)', rect['raw'], re.IGNORECASE)
            )
        ]
        hub_rects = [
            rect for rect in rects
            if rect['width'] >= 220
            and rect['height'] >= 60
            and rect['width'] <= canvas_width * 0.6
            and rect['y'] <= canvas_height * 0.45
        ]
        summary_rects = [
            rect for rect in rects
            if rect['width'] >= canvas_width * 0.45
            and 40 <= rect['height'] <= 140
            and rect['y'] >= canvas_height * 0.62
        ]
        side_summary_rects = [
            rect for rect in rects
            if 150 <= rect['width'] <= 340
            and rect['height'] >= 80
            and rect['x'] >= canvas_width * 0.72
        ]
        small_callouts = [
            rect for rect in rects
            if 90 <= rect['width'] <= 260 and 38 <= rect['height'] <= 160
        ]
        top_blocks = [
            block for block in text_blocks
            if not self._is_minor_label(block)
            and block['font_size'] >= 18
            and block['y'] <= 280
        ]
        top_judgment_blocks = [
            block for block in top_blocks
            if self._looks_like_judgment_sentence(block['text'])
        ]
        module_title_blocks = [
            block for block in content_text_blocks
            if not self._is_minor_label(block)
            and 13 <= block['font_size'] <= 18
            and canvas_height * 0.28 <= block['y'] <= canvas_height * 0.78
            and 3 <= self._count_cjk_chars(block['text']) <= 12
            and len(re.sub(r'\s+', '', block['text'])) <= 18
            and not self._looks_like_judgment_sentence(block['text'])
            and not self._looks_like_closure_sentence(block['text'])
            and not re.search(r'[。；!?！？]', block['text'])
        ]
        closure_blocks = [
            block for block in content_text_blocks
            if not self._is_minor_label(block)
            and block['y'] >= canvas_height * 0.7
        ]
        closure_band_blocks = [
            block for block in content_text_blocks
            if block['y'] >= canvas_height * 0.74
            and block['font_size'] >= 11
            and self._count_cjk_chars(block['text']) > 0
        ]
        closure_action_blocks = [
            block for block in closure_band_blocks
            if self._looks_like_closure_sentence(block['text'])
        ]
        metric_blocks = [
            block for block in content_text_blocks
            if block['font_size'] >= 22
            and re.search(r'\d', block['text'])
        ]
        evidence_keyword_blocks = [
            block for block in content_text_blocks
            if re.search(r'证据|证明|截图|结果|指标|成效|KPI|复测|留痕|命中|处置', block['text'], re.IGNORECASE)
        ]
        stage_keyword_blocks = [
            block for block in content_text_blocks
            if re.search(
                r'阶段|里程碑|演进|路线图|规划|建设路径|当前|目标|提升|暴露面|利用动作|落点控制|横向机会|发现定级|修复清理|复测验证|审计追踪|运营固化|回流',
                block['text'],
                re.IGNORECASE,
            )
        ]
        collaboration_keyword_blocks = [
            block for block in content_text_blocks
            if re.search(r'客户侧|长亭侧|甲方|乙方|协同|联动|战前|战中|战后', block['text'], re.IGNORECASE)
        ]
        governance_keyword_blocks = [
            block for block in content_text_blocks
            if re.search(
                r'治理|控制|动作|状态|优先级|域|矩阵|看板|风险统计|严重度分布|问题簇|收口|审计|清理|验证',
                block['text'],
                re.IGNORECASE,
            )
        ]
        maturity_keyword_blocks = [
            block for block in content_text_blocks
            if re.search(r'成熟度|等级|当前|目标|差距|提升路径|阶段', block['text'], re.IGNORECASE)
        ]
        result_keyword_blocks = [
            block for block in content_text_blocks
            if re.search(r'结果|影响|成效|接管|控制|上线|突破|结论', block['text'], re.IGNORECASE)
        ]

        centers_x = [rect['x'] + rect['width'] / 2 for rect in major_nodes]
        centers_y = [rect['y'] + rect['height'] / 2 for rect in major_nodes]

        image_count = len(re.findall(r'<image\b', content_scope))
        line_count = len(re.findall(r'<line\b', content_scope))
        polyline_count = len(re.findall(r'<polyline\b', content_scope))
        polygon_count = len(re.findall(r'<polygon\b', content_scope))
        connector_path_count = len(re.findall(r'<path\b[^>]*(?:stroke=|fill=["\']none["\'])', content_scope))
        connector_count = line_count + polyline_count + polygon_count + connector_path_count

        return {
            'major_nodes': len(major_nodes),
            'major_rects': major_nodes,
            'row_groups': self._cluster_positions(centers_y, tolerance=92.0),
            'col_groups': self._cluster_positions(centers_x, tolerance=120.0),
            'lane_count': len(lane_rects),
            'hub_count': len(hub_rects),
            'summary_rect_count': len(summary_rects),
            'side_summary_count': len(side_summary_rects),
            'callout_count': len(small_callouts),
            'headline_count': len(top_blocks),
            'headline_texts': [self._clip_text(block['text'], 40) for block in top_blocks[:4]],
            'headline_judgment_count': len(top_judgment_blocks),
            'module_title_count': len(module_title_blocks),
            'module_title_texts': [self._clip_text(block['text'], 24) for block in module_title_blocks[:8]],
            'closure_count': len(closure_blocks),
            'closure_band_count': len(closure_band_blocks),
            'closure_texts': [self._clip_text(block['text'], 40) for block in closure_band_blocks[:6]],
            'closure_action_count': len(closure_action_blocks),
            'metric_count': len(metric_blocks),
            'evidence_text_count': len(evidence_keyword_blocks),
            'stage_keyword_count': len(stage_keyword_blocks),
            'collaboration_keyword_count': len(collaboration_keyword_blocks),
            'governance_keyword_count': len(governance_keyword_blocks),
            'maturity_keyword_count': len(maturity_keyword_blocks),
            'result_keyword_count': len(result_keyword_blocks),
            'image_count': image_count,
            'connector_count': connector_count,
            'evidence_count': image_count + len(evidence_keyword_blocks) + min(len(small_callouts), 3),
        }

    def _cluster_positions(self, values: List[float], tolerance: float) -> int:
        """Cluster approximate positions so grid/lane structures can be estimated."""
        if not values:
            return 0
        groups: List[float] = []
        for value in sorted(values):
            if not groups or abs(value - groups[-1]) > tolerance:
                groups.append(value)
            else:
                groups[-1] = (groups[-1] + value) / 2
        return len(groups)

    def _check_complex_page_baseline(self, metrics: Dict[str, object], result: Dict):
        """Catch advanced pages that visually degrade into plain list/content pages."""
        major_nodes = int(metrics['major_nodes'])
        connector_count = int(metrics['connector_count'])
        headline_count = int(metrics['headline_count'])

        if major_nodes < 3 and connector_count == 0:
            result['errors'].append(
                "Complex page structure violation: advanced page is visually too simple and currently resembles a plain content/list page"
            )
        elif major_nodes < 4 and connector_count <= 1:
            result['warnings'].append(
                "Complex page structure risk: advanced page has too few structural modules or connectors, so the modeled logic may not be fully expressed"
            )

        if headline_count == 0:
            result['warnings'].append(
                "Complex page headline risk: no clear top-level headline/judgment block was detected near the page header"
            )

    def _check_complex_structure_by_type(
        self,
        structure_type: str,
        advanced_pattern: str,
        metrics: Dict[str, object],
        result: Dict,
    ):
        """Enforce coarse structural expectations by complex-page type."""
        major_nodes = int(metrics['major_nodes'])
        connector_count = int(metrics['connector_count'])
        row_groups = int(metrics['row_groups'])
        col_groups = int(metrics['col_groups'])
        lane_count = int(metrics['lane_count'])
        closure_count = int(metrics['closure_count'])
        metric_count = int(metrics['metric_count'])
        evidence_count = int(metrics['evidence_count'])

        if structure_type == 'chain':
            if major_nodes < 3:
                result['errors'].append(
                    "Complex page structure violation: chain-style page needs at least 3 structural nodes to express progression"
                )
            if max(row_groups, col_groups) < 3:
                result['warnings'].append(
                    "Complex page structure risk: chain-style page does not show a clear 3-step progression axis"
                )
            if connector_count < 2:
                result['warnings'].append(
                    "Complex page structure risk: chain-style page has too few connectors/arrows to explain causal progression"
                )

        elif structure_type == 'layered':
            if max(row_groups, col_groups) < 3:
                result['errors'].append(
                    "Complex page structure violation: layered page needs at least 3 visible levels or clusters"
                )

        elif structure_type == 'matrix':
            if major_nodes < 4 or row_groups < 2 or col_groups < 2:
                result['errors'].append(
                    "Complex page structure violation: matrix page needs a visible 2x2-or-above cross-axis structure"
                )

        elif structure_type == 'loop':
            if major_nodes < 3:
                result['errors'].append(
                    "Complex page structure violation: loop page needs at least 3 structural nodes"
                )
            if connector_count < 2:
                result['warnings'].append(
                    "Complex page structure risk: loop page has too few connectors to express circulation/feedback"
                )
            if closure_count == 0:
                result['warnings'].append(
                    "Complex page closure risk: loop page is missing a visible lower-page closure / management takeaway block"
                )

        elif structure_type == 'swimlane':
            if lane_count < 2:
                result['errors'].append(
                    "Complex page structure violation: swimlane page needs at least 2 visible lanes/bands"
                )
            if max(row_groups, col_groups) < 2:
                result['warnings'].append(
                    "Complex page structure risk: swimlane page does not show enough stage/role segmentation"
                )

        elif structure_type == 'evidence':
            if evidence_count < 2:
                result['errors'].append(
                    "Complex page evidence violation: evidence-oriented page needs visible proof modules, metrics, or screenshots"
                )
            if advanced_pattern == 'evidence_cockpit' and metric_count == 0:
                result['warnings'].append(
                    "Complex page evidence risk: evidence cockpit page is missing a clear metric/KPI anchor"
                )

        elif structure_type == 'hybrid':
            if major_nodes < 4 or connector_count < 2:
                result['warnings'].append(
                    "Complex page structure risk: hybrid page still needs enough structural modules and connectors to justify a mixed layout"
                )

    def _check_complex_role_expectation(
        self,
        page_role: str,
        model: Dict[str, str],
        metrics: Dict[str, object],
        result: Dict,
    ):
        """Check whether page-role expectations are visible in the SVG."""
        closure_count = int(metrics['closure_count'])
        closure_band_count = int(metrics.get('closure_band_count', 0) or 0)
        evidence_count = int(metrics['evidence_count'])
        headline_count = int(metrics['headline_count'])
        main_judgment = model.get('main_judgment', '').strip()
        closure = model.get('closure', '').strip()
        closure_visible = max(closure_count, closure_band_count)

        if main_judgment and headline_count == 0:
            result['errors'].append(
                "Complex page headline violation: model defines a `主判断`, but the SVG does not show a clear headline-level judgment block"
            )

        if page_role == 'evidence' and evidence_count < 2:
            result['errors'].append(
                "Complex page evidence violation: proof-oriented page lacks enough visible evidence modules to support its role"
            )

        if page_role == 'closure' and closure_visible == 0:
            result['errors'].append(
                "Complex page closure violation: closure page lacks a visible lower-page conclusion / recommendation region"
            )

        if page_role in {'overview', 'advance'} and headline_count == 0:
            result['warnings'].append(
                "Complex page headline risk: overview/advance page should expose a stronger top-level judgment or framing block"
            )

        if closure and closure_visible == 0:
            result['warnings'].append(
                "Complex page closure risk: model defines a `页面收束方式`, but the SVG does not show a clear closure block in the lower page area"
            )

    def _check_complex_headline_semantics(
        self,
        page_spec: Dict[str, str],
        model: Dict[str, str],
        metrics: Dict[str, object],
        result: Dict,
    ):
        """Check whether the visible top headline really expresses a consultant-style judgment."""
        headline_count = int(metrics.get('headline_count', 0) or 0)
        headline_texts = [str(item) for item in (metrics.get('headline_texts') or []) if str(item).strip()]
        headline_judgment_count = int(metrics.get('headline_judgment_count', 0) or 0)
        page_title = page_spec.get('title', '').strip()
        cleaned_page_title = re.sub(r'^(章节页|分节页|目录页|封面页|结束页)\s*[/／]\s*', '', page_title)
        main_judgment = (model.get('main_judgment') or page_spec.get('core_judgment') or '').strip()

        if headline_count == 0:
            return

        title_like_headlines = [
            text for text in headline_texts
            if cleaned_page_title
            and (
                self._normalize_title_key(text) == self._normalize_title_key(cleaned_page_title)
                or self._normalize_title_key(cleaned_page_title) in self._normalize_title_key(text)
                or self._normalize_title_key(text) in self._normalize_title_key(cleaned_page_title)
            )
        ]
        main_judgment_match = any(
            self._headline_matches_judgment(text, main_judgment)
            for text in headline_texts
        ) if main_judgment else False

        if main_judgment and not main_judgment_match and headline_judgment_count == 0:
            result['errors'].append(
                "Complex page headline violation: top headline remains title-like/section-like and does not expose the modeled `主判断` "
                f"{self._format_examples(headline_texts[:3])}"
            )
            return

        if main_judgment and title_like_headlines and not main_judgment_match:
            result['warnings'].append(
                "Complex page headline risk: top headline is still close to the page title rather than the modeled `主判断` "
                f"{self._format_examples(title_like_headlines[:2])}"
            )

        if title_like_headlines and headline_judgment_count == 0:
            result['warnings'].append(
                "Complex page headline risk: advanced page top area is dominated by section/title wording instead of a clear judgment sentence "
                f"{self._format_examples(title_like_headlines[:2])}"
            )

    def _check_complex_argument_cohesion(
        self,
        page_spec: Dict[str, str],
        model: Dict[str, str],
        metrics: Dict[str, object],
        result: Dict,
    ):
        """Check whether module titles echo the modeled reasoning instead of generic placeholders."""
        module_titles: List[str] = []
        seen_titles: Set[str] = set()
        for item in (metrics.get('module_title_texts') or []):
            title = str(item).strip()
            title_key = self._normalize_semantic_text(title)
            if not title or not title_key or title_key in seen_titles:
                continue
            if title_key in {self._normalize_semantic_text(item) for item in self.MODULE_SCAFFOLD_TITLES}:
                continue
            seen_titles.add(title_key)
            module_titles.append(title)
        if not module_titles:
            return

        reference_fields = [
            model.get('main_judgment', ''),
            page_spec.get('core_judgment', ''),
            model.get('page_intent', ''),
            page_spec.get('page_intent', ''),
            model.get('proof_goal', ''),
            page_spec.get('proof_goal', ''),
            model.get('sub_judgment', ''),
            model.get('key_nodes', ''),
            model.get('key_relations', ''),
            model.get('evidence_plan', ''),
        ]
        reference_fields = [item.strip() for item in reference_fields if str(item).strip()]

        generic_titles = [title for title in module_titles if self._looks_generic_module_title(title)]
        meaningful_titles = [title for title in module_titles if title not in generic_titles]
        anchored_titles = [
            title for title in meaningful_titles
            if self._module_title_matches_references(title, reference_fields)
        ]

        if len(module_titles) >= 3 and len(generic_titles) >= max(2, (len(module_titles) + 1) // 2):
            result['errors'].append(
                "Complex page argument cohesion violation: module titles are still dominated by generic栏目名 instead of page-specific logic anchors "
                f"{self._format_examples(generic_titles[:4])}"
            )
            return

        if reference_fields and len(meaningful_titles) >= 3 and not anchored_titles:
            result['errors'].append(
                "Complex page argument cohesion violation: module titles do not echo the modeled main judgment / proof goal / key nodes, so the page argument feels disconnected "
                f"{self._format_examples(module_titles[:4])}"
            )
            return

        if reference_fields and len(meaningful_titles) >= 4 and len(anchored_titles) <= 1:
            result['warnings'].append(
                "Complex page argument cohesion risk: only a small part of the module titles can be traced back to the modeled page reasoning "
                f"{self._format_examples(module_titles[:4])}"
            )

        main_judgment = (model.get('main_judgment') or page_spec.get('core_judgment') or '').strip()
        closure_texts = [str(item).strip() for item in (metrics.get('closure_texts') or []) if str(item).strip()]
        if main_judgment and closure_texts:
            closure_overlaps = [
                text for text in closure_texts
                if self._semantic_texts_overlap(text, main_judgment)
            ]
            if not closure_overlaps:
                result['warnings'].append(
                    "Complex page argument cohesion risk: lower-page closure text does not clearly收束回主判断，容易形成上中下三层各说各话 "
                    f"{self._format_examples(closure_texts[:3])}"
                )

    def _check_adjacent_complex_progression(
        self,
        page_spec: Dict[str, str],
        model: Dict[str, str],
        metrics: Dict[str, object],
        result: Dict,
    ):
        """Check whether consecutive complex pages have explicit transition and differentiated roles."""
        slide_num = self._extract_slide_number(result.get('file', ''))
        if slide_num is None:
            return

        current_pattern = self._normalize_advanced_pattern(page_spec.get('advanced_pattern', ''))
        current_role = self._normalize_page_role(model.get('page_role', '') or page_spec.get('page_role', ''))
        current_template = str(page_spec.get('preferred_template') or '').strip()
        current_title_key = self._normalize_progression_title_key(page_spec.get('title', ''))
        current_main_judgment = (model.get('main_judgment') or page_spec.get('core_judgment') or '').strip()

        prev_spec = self.page_specs.get(slide_num - 1, {})
        prev_model = (self.complex_page_models or {}).get('by_slide', {}).get(slide_num - 1, {})
        prev_is_complex = bool(prev_spec and (prev_spec.get('advanced_pattern') or prev_model))
        if prev_is_complex:
            previous_relation = str(page_spec.get('previous_relation') or '').strip()
            if not previous_relation:
                result['errors'].append(
                    "Adjacent complex progression violation: current complex page is adjacent to another complex page, but `与上一页关系` is missing"
                )
            elif self._relation_text_is_generic(previous_relation):
                result['warnings'].append(
                    "Adjacent complex progression risk: `与上一页关系` is too generic to explain why this complex page exists after the previous one "
                    f"{self._format_examples([previous_relation])}"
                )

            prev_pattern = self._normalize_advanced_pattern(prev_spec.get('advanced_pattern', ''))
            prev_role = self._normalize_page_role(
                prev_model.get('page_role', '') or prev_spec.get('page_role', '')
            )
            prev_template = str(prev_spec.get('preferred_template') or '').strip()
            prev_title_key = self._normalize_progression_title_key(prev_spec.get('title', ''))
            prev_main_judgment = (
                prev_model.get('main_judgment') or prev_spec.get('core_judgment') or ''
            ).strip()

            same_pattern = bool(current_pattern and prev_pattern and current_pattern == prev_pattern)
            same_role = bool(current_role and prev_role and current_role == prev_role)
            same_template = bool(current_template and prev_template and current_template == prev_template)
            same_title_base = bool(current_title_key and prev_title_key and current_title_key == prev_title_key)
            same_judgment_track = bool(
                current_main_judgment and prev_main_judgment
                and self._semantic_texts_overlap(current_main_judgment, prev_main_judgment)
            )

            if same_pattern and same_role and same_template:
                result['errors'].append(
                    "Adjacent complex progression violation: consecutive complex pages reuse the same advanced pattern, page role, and template, so the deck loses progression"
                )
            elif same_title_base and (same_pattern or same_template):
                result['errors'].append(
                    "Adjacent complex progression violation: consecutive complex pages still revolve around the same title bucket, which usually means the content should be merged or restructured "
                    f"{self._format_examples([prev_spec.get('title', ''), page_spec.get('title', '')])}"
                )
            elif same_pattern and same_role and same_judgment_track:
                result['errors'].append(
                    "Adjacent complex progression violation: consecutive complex pages keep almost the same argument track while only changing local content, so the story does not advance"
                )
            elif same_pattern and same_role and not (current_template and prev_template and current_template != prev_template):
                result['warnings'].append(
                    "Adjacent complex progression risk: consecutive complex pages still use the same pattern and page role, so transition pressure is high"
                )

        next_spec = self.page_specs.get(slide_num + 1, {})
        next_model = (self.complex_page_models or {}).get('by_slide', {}).get(slide_num + 1, {})
        next_is_complex = bool(next_spec and (next_spec.get('advanced_pattern') or next_model))
        if next_is_complex:
            next_relation = str(page_spec.get('next_relation') or '').strip()
            if not next_relation:
                result['errors'].append(
                    "Adjacent complex progression violation: current complex page is followed by another complex page, but `与下一页关系` is missing"
                )
            elif self._relation_text_is_generic(next_relation):
                result['warnings'].append(
                    "Adjacent complex progression risk: `与下一页关系` is too generic to explain the handoff into the next complex page "
                    f"{self._format_examples([next_relation])}"
                )

    def _check_complex_closure_semantics(
        self,
        model: Dict[str, str],
        metrics: Dict[str, object],
        result: Dict,
    ):
        """Check whether lower-page closure text really lands on judgment/action semantics."""
        closure = (model.get('closure') or '').strip()
        closure_band_count = int(metrics.get('closure_band_count', 0) or 0)
        closure_action_count = int(metrics.get('closure_action_count', 0) or 0)
        closure_texts = [str(item) for item in (metrics.get('closure_texts') or []) if str(item).strip()]

        if closure and closure_band_count == 0:
            result['errors'].append(
                "Complex page closure violation: model defines a `页面收束方式`, but the SVG lower band does not show visible closure/action text"
            )
            return

        if closure and closure_band_count > 0 and closure_action_count == 0:
            result['warnings'].append(
                "Complex page closure risk: lower-page closure text is visible, but it still looks generic and not like management judgment / action guidance "
                f"{self._format_examples(closure_texts[:3])}"
            )

    def _check_security_service_pattern_detail(
        self,
        advanced_pattern: str,
        metrics: Dict[str, object],
        model: Dict[str, str],
        result: Dict,
    ):
        """Refine security_service checks so each advanced pattern matches case-like structure."""
        if not advanced_pattern:
            return

        major_nodes = int(metrics['major_nodes'])
        connector_count = int(metrics['connector_count'])
        row_groups = int(metrics['row_groups'])
        col_groups = int(metrics['col_groups'])
        lane_count = int(metrics['lane_count'])
        hub_count = int(metrics['hub_count'])
        summary_rect_count = int(metrics['summary_rect_count'])
        side_summary_count = int(metrics['side_summary_count'])
        evidence_count = int(metrics['evidence_count'])
        metric_count = int(metrics['metric_count'])
        closure_count = int(metrics['closure_count'])
        closure_band_count = int(metrics.get('closure_band_count', 0) or 0)
        stage_keyword_count = int(metrics['stage_keyword_count'])
        collaboration_keyword_count = int(metrics['collaboration_keyword_count'])
        governance_keyword_count = int(metrics['governance_keyword_count'])
        maturity_keyword_count = int(metrics['maturity_keyword_count'])
        result_keyword_count = int(metrics['result_keyword_count'])
        callout_count = int(metrics['callout_count'])

        if advanced_pattern == 'layered_system_map':
            if hub_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: layered_system_map page is missing a visible central platform / hub block"
                )
            if major_nodes < 4:
                result['errors'].append(
                    "Security service pattern violation: layered_system_map page needs a hub plus 3-or-more domain modules"
                )
            if max(row_groups, col_groups) < 2:
                result['warnings'].append(
                    "Security service pattern risk: layered_system_map page does not show a clear total-to-domain hierarchy"
                )

        elif advanced_pattern == 'timeline_roadmap':
            if major_nodes < 3:
                result['errors'].append(
                    "Security service pattern violation: timeline_roadmap page needs at least 3 visible stage blocks"
                )
            if col_groups < 3 and row_groups < 3:
                result['warnings'].append(
                    "Security service pattern risk: timeline_roadmap page lacks a strong progression axis with 3-or-more stages"
                )
            if connector_count < 2:
                result['warnings'].append(
                    "Security service pattern risk: timeline_roadmap page has too few connectors to explain stage progression"
                )
            if stage_keyword_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: timeline_roadmap page lacks clear stage / milestone language"
                )

        elif advanced_pattern == 'attack_case_chain':
            if evidence_count < 2:
                result['errors'].append(
                    "Security service pattern violation: attack_case_chain page must carry visible evidence or proof callouts, not just a process chain"
                )
            if result_keyword_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: attack_case_chain page is missing a strong result/impact expression"
                )
            if closure_count == 0 and summary_rect_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: attack_case_chain page is missing a visible management takeaway / closure region"
                )

        elif advanced_pattern == 'attack_tree_architecture':
            if major_nodes < 4:
                result['errors'].append(
                    "Security service pattern violation: attack_tree_architecture page needs multiple branch nodes, not a single stacked block"
                )
            if max(row_groups, col_groups) < 3:
                result['warnings'].append(
                    "Security service pattern risk: attack_tree_architecture page does not show enough visible levels/branches"
                )
            if connector_count < 2:
                result['warnings'].append(
                    "Security service pattern risk: attack_tree_architecture page has too few branch connectors"
                )

        elif advanced_pattern == 'operation_loop':
            if major_nodes < 3:
                result['errors'].append(
                    "Security service pattern violation: operation_loop page needs at least 3 loop stages"
                )
            if connector_count < 3:
                result['warnings'].append(
                    "Security service pattern risk: operation_loop page has too few connectors to express a closed loop"
                )
            if row_groups < 2 and col_groups < 2:
                result['warnings'].append(
                    "Security service pattern risk: operation_loop page looks too linear and does not show a loop-like structure"
                )
            if closure_count == 0 and side_summary_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: operation_loop page should include a visible optimization / closure summary area"
                )

        elif advanced_pattern == 'swimlane_collaboration':
            if lane_count < 2:
                result['errors'].append(
                    "Security service pattern violation: swimlane_collaboration page needs at least 2 visible collaboration lanes"
                )
            if max(row_groups, col_groups) < 2:
                result['warnings'].append(
                    "Security service pattern risk: swimlane_collaboration page lacks enough stage or lane segmentation"
                )
            if collaboration_keyword_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: swimlane_collaboration page lacks clear collaboration-role language such as 客户侧/长亭侧/协同"
                )

        elif advanced_pattern == 'multi_lane_execution_chain':
            if lane_count < 2:
                result['errors'].append(
                    "Security service pattern violation: multi_lane_execution_chain page needs at least 2 visible execution lanes"
                )
            if max(row_groups, col_groups) < 3 and stage_keyword_count < 3:
                result['warnings'].append(
                    "Security service pattern risk: multi_lane_execution_chain page should show multiple execution stages in addition to lanes"
                )
            if connector_count < 2:
                result['warnings'].append(
                    "Security service pattern risk: multi_lane_execution_chain page has too few connectors between lanes/stages"
                )

        elif advanced_pattern == 'matrix_defense_map':
            if major_nodes < 4 or row_groups < 2 or col_groups < 2:
                result['errors'].append(
                    "Security service pattern violation: matrix_defense_map page needs a visible cross-axis matrix instead of loose cards"
                )
            if governance_keyword_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: matrix_defense_map page lacks enough matrix / control / domain language"
                )

        elif advanced_pattern == 'governance_control_matrix':
            if major_nodes < 4 or row_groups < 2 or col_groups < 2:
                result['errors'].append(
                    "Security service pattern violation: governance_control_matrix page needs a clear domain-state-action matrix structure"
                )
            if side_summary_count == 0 and closure_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: governance_control_matrix page should reserve a side/bottom insight area for priority judgments"
                )
            if governance_keyword_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: governance_control_matrix page lacks governance / control / priority expressions"
                )

        elif advanced_pattern == 'maturity_model':
            if major_nodes < 3:
                result['errors'].append(
                    "Security service pattern violation: maturity_model page needs at least 3 levels or stages"
                )
            if max(row_groups, col_groups) < 3:
                result['warnings'].append(
                    "Security service pattern risk: maturity_model page should show a visible level progression"
                )
            if maturity_keyword_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: maturity_model page lacks current-state / target-state / maturity language"
                )

        elif advanced_pattern == 'evidence_wall':
            if major_nodes < 4:
                result['errors'].append(
                    "Security service pattern violation: evidence_wall page needs multiple grouped evidence modules, not a sparse list"
                )
            if evidence_count < 4:
                result['errors'].append(
                    "Security service pattern violation: evidence_wall page needs enough visible evidence assets, groups, or proof-oriented modules"
                )
            if row_groups < 2 and col_groups < 3:
                result['warnings'].append(
                    "Security service pattern risk: evidence_wall page lacks the grouped-wall feeling seen in case materials"
                )

        elif advanced_pattern == 'evidence_cockpit':
            if metric_count == 0:
                result['errors'].append(
                    "Security service pattern violation: evidence_cockpit page needs a KPI / metric anchor"
                )
            if evidence_count < 2:
                result['errors'].append(
                    "Security service pattern violation: evidence_cockpit page needs a main proof graphic plus evidence/support modules"
                )
            if side_summary_count == 0 and max(closure_count, closure_band_count) == 0:
                result['warnings'].append(
                    "Security service pattern risk: evidence_cockpit page should include layered conclusions beside or below the main proof area"
                )

        elif advanced_pattern == 'evidence_attached_case_chain':
            if evidence_count < 3:
                result['errors'].append(
                    "Security service pattern violation: evidence_attached_case_chain page needs multiple evidence attachments tied to the chain"
                )
            if callout_count < 2 and metrics['image_count'] == 0:
                result['warnings'].append(
                    "Security service pattern risk: evidence_attached_case_chain page should show visible side-callouts or screenshots attached to nodes"
                )
            if result_keyword_count == 0:
                result['warnings'].append(
                    "Security service pattern risk: evidence_attached_case_chain page lacks a strong result-proof expression"
                )

    def _check_brand_consistency(self, content: str, result: Dict):
        """Ensure brand-locked templates keep approved Chaitin logo usage."""
        context = result.get('template_context', {})
        if not context.get('brand_required'):
            return

        brand_zone_matches = list(re.finditer(
            r'<(?:[\w.-]+:)?g\b[^>]*data-role=["\']brand-zone["\'][^>]*>.*?</(?:[\w.-]+:)?g>',
            content,
            re.DOTALL,
        ))
        if not brand_zone_matches:
            result['errors'].append(
                "Brand presence violation: this template page requires a protected Chaitin logo zone, but none was found"
            )
            return

        approved_assets = {
            self._normalize_brand_asset(asset)
            for asset in context.get('approved_brand_assets', [])
            if self._normalize_brand_asset(asset)
        }
        found_assets = []
        inspected_assets: Dict[str, Dict[str, float]] = {}
        page_family = str(context.get('page_family') or '').lower()
        svg_path = str(result.get('path') or '')

        for brand_zone in brand_zone_matches:
            zone_markup = brand_zone.group(0)
            zone_tag_match = re.match(r'<(?:[\w.-]+:)?g\b[^>]*>', zone_markup)
            zone_asset = None
            if zone_tag_match:
                zone_attrs = self._parse_attrs(zone_tag_match.group(0))
                zone_asset = zone_attrs.get('data-brand-asset')

            image_matches = list(re.finditer(r'<(?:[\w.-]+:)?image\b[^>]*>', zone_markup))
            if not image_matches:
                continue

            for image_match in image_matches:
                attrs = self._parse_attrs(image_match.group(0))
                asset = (
                    attrs.get('data-brand-asset')
                    or zone_asset
                    or attrs.get('href')
                    or attrs.get('{http://www.w3.org/1999/xlink}href')
                )
                normalized = self._normalize_brand_asset(asset)
                if normalized:
                    found_assets.append(normalized)
                    if approved_assets and normalized not in approved_assets:
                        result['errors'].append(
                            "Brand asset violation: detected an unapproved logo asset "
                            f"'{asset}' for template '{context.get('template_id')}'"
                        )
                    asset_path = self._resolve_asset_path(svg_path, asset)
                    if asset_path and normalized not in inspected_assets:
                        inspected_assets[normalized] = self._inspect_logo_asset(asset_path)

                    image_width = self._to_float(attrs.get('width')) or 0.0
                    image_height = self._to_float(attrs.get('height')) or 0.0
                    if page_family not in {'cover', 'hero-image'} and image_width < 150:
                        result['warnings'].append(
                            "Logo safe-zone risk: top-right logo is rendered too small for readable brand presentation "
                            f"{self._format_examples([f'{normalized} {int(image_width)}x{int(image_height)}'])}"
                        )

        if not found_assets:
            result['errors'].append(
                "Brand presence violation: brand zone exists, but it does not include a logo asset"
            )

        if isinstance(context.get('logo_safe_zone'), tuple):
            _, _, zone_width, zone_height = context['logo_safe_zone']
            if page_family not in {'cover', 'hero-image'} and (zone_width < 180 or zone_height < 52):
                result['warnings'].append(
                    "Logo safe-zone risk: template brand protection zone is undersized for Chaitin logo readability "
                    f"{self._format_examples([f'{int(zone_width)}x{int(zone_height)}'])}"
                )

        malformed_assets = []
        for normalized, metrics in inspected_assets.items():
            aspect_ratio = metrics.get('aspect_ratio')
            if aspect_ratio and aspect_ratio < 2.5:
                malformed_assets.append(f"{normalized} ratio={aspect_ratio:.2f}")
        if malformed_assets:
            result['errors'].append(
                "Brand asset integrity violation: approved logo file appears malformed or padded, which can cause overlap / white-plate rendering "
                f"{self._format_examples(malformed_assets[:3])}"
            )

        if context.get('brand_required') and not context.get('logo_safe_zone'):
            result['warnings'].append(
                "Brand metadata risk: required brand page is missing data-logo-safe-zone protection metadata"
            )

        if found_assets:
            result['info']['brand_assets'] = sorted(set(found_assets))
        if inspected_assets:
            result['info']['brand_asset_metrics'] = inspected_assets

    def _normalize_brand_asset(self, asset: Optional[str]) -> str:
        """Normalize brand asset identifiers for approval checks."""
        if not asset:
            return ''
        asset = asset.strip()
        if asset.startswith('data:'):
            return ''
        asset = asset.replace('\\', '/')
        basename = Path(asset).name
        if asset.startswith('images/'):
            return f"images/{basename}"
        return basename

    def _synthesize_issue_details(self, result: Dict):
        """Backfill structured issue metadata and compute blocking warnings."""
        existing = {(issue['severity'], issue['message']) for issue in result.get('issues', [])}
        context = result.get('template_context', {})

        for severity, messages in (('error', result.get('errors', [])), ('warning', result.get('warnings', []))):
            for message in messages:
                if (severity, message) in existing:
                    continue
                code = self._message_to_code(message)
                blocking = self._should_block_issue(context, code, severity)
                result.setdefault('issues', []).append({
                    'severity': severity,
                    'code': code,
                    'message': message,
                    'blocking': blocking,
                })

        result['blocking_issue_count'] = sum(
            1 for issue in result.get('issues', []) if issue.get('blocking')
        )

    def _message_to_code(self, message: str) -> str:
        """Map issue messages to stable QA codes."""
        lowered = message.lower()
        if 'file does not exist' in lowered:
            return 'file_missing'
        if 'brand presence violation' in lowered:
            return 'brand_presence'
        if 'brand asset violation' in lowered:
            return 'brand_asset_misuse'
        if 'brand asset integrity violation' in lowered:
            return 'brand_asset_malformed'
        if 'brand metadata risk' in lowered:
            return 'brand_metadata'
        if 'chapter number semantic violation' in lowered:
            return 'chapter_number_semantics'
        if 'chapter numbering risk' in lowered:
            return 'chapter_number_semantics'
        if 'chapter subtitle semantic violation' in lowered:
            return 'chapter_subtitle_semantics'
        if 'chapter subtitle semantic risk' in lowered:
            return 'chapter_subtitle_semantics'
        if 'planning tone leakage' in lowered:
            return 'semantic_planning_tone'
        if 'soft content blacklist violation' in lowered:
            return 'semantic_soft_blacklist'
        if 'visible ellipsis violation' in lowered:
            return 'visible_ellipsis'
        if 'footer zone violation' in lowered:
            return 'footer_zone_violation'
        if 'edge pressure violation' in lowered:
            return 'edge_pressure_card'
        if 'card overflow violation' in lowered:
            return 'card_overflow'
        if 'information density overload' in lowered:
            return 'dense_content'
        if 'layer separation violation' in lowered:
            return 'takeaway_overlap'
        if 'takeaway/body separation risk' in lowered:
            return 'takeaway_separation'
        if 'logo safe-zone risk' in lowered:
            return 'logo_safe_zone'
        if 'template safe-area risk' in lowered:
            return 'template_safe_area'
        if 'planning scaffold leakage' in lowered:
            return 'semantic_planning_leak'
        if 'fixed template mismatch' in lowered:
            return 'fixed_template_mismatch'
        if 'cover title semantic violation' in lowered:
            return 'cover_internal_slug'
        if 'toc completeness violation' in lowered:
            return 'toc_missing_section'
        if 'security service pattern violation' in lowered:
            return 'security_service_pattern'
        if 'security service pattern risk' in lowered:
            return 'security_service_pattern'
        if 'complex page evidence violation' in lowered:
            return 'complex_page_evidence'
        if 'complex page evidence risk' in lowered:
            return 'complex_page_evidence'
        if 'complex page closure violation' in lowered:
            return 'complex_page_closure'
        if 'complex page closure risk' in lowered:
            return 'complex_page_closure'
        if 'complex page argument cohesion violation' in lowered:
            return 'complex_page_argument_cohesion'
        if 'complex page argument cohesion risk' in lowered:
            return 'complex_page_argument_cohesion'
        if 'adjacent complex progression violation' in lowered:
            return 'adjacent_complex_progression'
        if 'adjacent complex progression risk' in lowered:
            return 'adjacent_complex_progression'
        if 'complex page headline' in lowered:
            return 'complex_page_headline'
        if 'complex page structure violation' in lowered:
            return 'complex_page_structure'
        if 'complex page structure risk' in lowered:
            return 'complex_page_structure'
        if 'toc consistency risk' in lowered:
            return 'toc_consistency'
        if 'top stack collision risk' in lowered:
            return 'top_stack_collision'
        if 'headline bundle collision risk' in lowered:
            return 'headline_bundle_collision'
        if 'chapter safe-zone risk' in lowered:
            return 'chapter_safe_zone'
        if 'information density risk' in lowered:
            return 'dense_content'
        if 'card overflow risk' in lowered:
            return 'card_overflow'
        if 'edge pressure risk' in lowered and 'canvas edges' in lowered:
            return 'edge_pressure_canvas'
        if 'edge pressure risk' in lowered:
            return 'edge_pressure_card'
        if 'chinese line-break risk' in lowered:
            return 'line_break_punctuation'
        if 'chinese readability risk' in lowered:
            return 'chinese_readability'
        if 'overflow' in lowered:
            return 'text_overflow'
        if 'font' in lowered:
            return 'font_issue'
        if 'viewbox' in lowered:
            return 'viewbox_issue'
        if 'forbidden' in lowered:
            return 'forbidden_svg_feature'
        if 'failed to read file' in lowered:
            return 'file_read_error'
        return 'other'

    def _should_block_issue(self, context: Dict[str, object], code: str, severity: str) -> bool:
        """Escalate template/layout warnings into hard gate failures when required."""
        if severity == 'error':
            return True
        if not code:
            return False
        advanced_pattern = context.get('advanced_pattern')
        if advanced_pattern and code in self.ADVANCED_PATTERN_WARNING_ONLY_CODES:
            return False
        if advanced_pattern and code in self.ADVANCED_PATTERN_BLOCKING_WARNING_CODES:
            return True
        if context.get('brand_required') and code in self.BRAND_BLOCKING_WARNING_CODES:
            return True
        if context.get('fixed_skeleton') and code in self.TEMPLATE_BLOCKING_WARNING_CODES:
            return True
        return False

    def _parse_zone(self, value: Optional[str]) -> Optional[Tuple[float, float, float, float]]:
        """Parse x,y,width,height zone declarations from data attributes."""
        if not value:
            return None
        parts = [part.strip() for part in value.split(',')]
        if len(parts) != 4:
            return None
        try:
            x, y, width, height = [float(part) for part in parts]
        except ValueError:
            return None
        return (x, y, width, height)

    def _resolve_horizontal_bounds(self, x: float, width: float, anchor: str) -> Tuple[float, float]:
        """Estimate left/right bounds from x + text-anchor."""
        if anchor == 'middle':
            return x - width / 2, x + width / 2
        if anchor == 'end':
            return x - width, x
        return x, x + width

    def _boxes_intersect(self, first: Dict, second: Dict, pad: float = 0.0) -> bool:
        """Check whether two estimated boxes intersect."""
        left = max(first['left'] if 'left' in first else first['x'], second['x'])
        right = min(first['right'] if 'right' in first else first['right'], second['right'])
        top = max(first['top'] if 'top' in first else first['y'], second['y'])
        bottom = min(first['bottom'], second['bottom'])
        return (right - left) > pad and (bottom - top) > pad

    def _estimate_text_width(self, text: str, font_size: float) -> float:
        """Estimate rendered width for mixed Chinese/Latin text."""
        total = 0.0
        for ch in text:
            total += self._char_visual_weight(ch)
        return total * font_size

    def _char_visual_weight(self, ch: str) -> float:
        """Approximate per-character width in em units."""
        if ch.isspace():
            return 0.28
        if self._is_cjk_char(ch):
            return 1.0
        if ch.isdigit():
            return 0.58
        if ch.isupper():
            return 0.62
        if ch.islower():
            return 0.56
        if unicodedata.east_asian_width(ch) in {'F', 'W'}:
            return 1.0
        return 0.38

    def _count_cjk_chars(self, text: str) -> int:
        """Count Chinese characters used as a rough readability signal."""
        return sum(1 for ch in text if self._is_cjk_char(ch))

    def _is_cjk_char(self, ch: str) -> bool:
        """Return True when the character belongs to common CJK ranges."""
        code = ord(ch)
        return (
            0x3400 <= code <= 0x4DBF
            or 0x4E00 <= code <= 0x9FFF
            or 0xF900 <= code <= 0xFAFF
        )

    def _strip_tags(self, text: str) -> str:
        """Remove nested tags and normalize whitespace."""
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()

    def _clip_text(self, text: str, limit: int = 22) -> str:
        """Shorten a text sample for warning messages."""
        text = text.strip()
        if len(text) <= limit:
            return text
        return text[:limit - 1] + "…"

    def _horizontal_overlap(self, first: Dict, second: Dict) -> float:
        """Return horizontal overlap between two rect-like dictionaries."""
        first_right = first['x'] + first['width']
        second_right = second['x'] + second['width']
        return max(0.0, min(first_right, second_right) - max(first['x'], second['x']))

    def _format_examples(self, examples: List[str]) -> str:
        """Render short warning examples."""
        if not examples:
            return ""
        return f" (examples: {', '.join(examples)})"

    def _is_minor_label(self, block: Dict) -> bool:
        """Ignore tiny numeric markers and other micro labels for card-padding heuristics."""
        text = re.sub(r'\s+', '', block['text'])
        if not text:
            return True
        if '{{' in text and '}}' in text:
            return True
        if len(text) <= 4 and self._count_cjk_chars(text) <= 2:
            return True
        if len(text) <= 6 and self._count_cjk_chars(text) <= 4:
            return True
        if block.get('font_size', 0) <= 14 and block.get('y', 9999) <= 180 and len(text) <= 10:
            return True
        if block.get('font_size', 0) <= 12.5 and len(text) <= 12 and not re.search(r'[。；：！？]', text):
            return True
        if re.fullmatch(r'[\d./:-]+', text):
            return True
        return False

    def _looks_like_toc(self, filename: str) -> bool:
        """Heuristic detection for directory / agenda pages."""
        lowered = filename.lower()
        return '目录' in filename or 'toc' in lowered or 'agenda' in lowered

    def _is_allowed_footer_element(self, element: Dict) -> bool:
        """Allow known footer assets when the checker must scan the full SVG."""
        raw = element['raw']
        x_val = element.get('x')
        y_val = element['y']
        width_match = re.search(r'\bwidth=["\'](\d+(?:\.\d+)?)["\']', raw)
        height_match = re.search(r'\bheight=["\'](\d+(?:\.\d+)?)["\']', raw)
        width = float(width_match.group(1)) if width_match else None
        height = float(height_match.group(1)) if height_match else None

        if element['type'] == 'image' and 590 <= y_val <= 645:
            if re.search(r'logo', raw, re.IGNORECASE):
                return True
            if x_val is not None and width is not None and height is not None:
                if 50 <= x_val <= 80 and 100 <= width <= 140 and 20 <= height <= 40:
                    return True

        if element['type'] in {'rect', 'image'} and x_val == 0 and y_val == 0:
            if width is not None and height is not None:
                if width >= 1200 and height >= 700:
                    return True
                if height >= 700 and width <= 20:
                    return True

        if element['type'] == 'image' and x_val is not None:
            if -4 <= x_val <= 4 and -4 <= y_val <= 4:
                if width is not None and height is not None and width >= 1200 and height >= 700:
                    return True

        if element['type'] == 'rect' and x_val == 0 and width is not None and height is not None:
            if y_val <= 10 and width >= 1200 and height <= 10:
                return True
            if y_val <= 10 and width <= 20 and height >= 700:
                return True

        if element['type'] == 'text' and 680 <= y_val <= 695 and x_val is not None:
            if 1170 <= x_val <= 1215:
                return True
            text_value = self._strip_tags(raw)
            if 40 <= x_val <= 90 and re.fullmatch(r'\d{1,3}', text_value):
                return True

        if element['type'] == 'rect' and 635 <= y_val <= 699 and x_val is not None:
            if 50 <= x_val <= 80:
                return True

        if element['type'] == 'rect' and y_val >= 680 and x_val == 0:
            if width is not None and height is not None:
                if width >= 1200 and height <= 60:
                    return True

        return False

    def _parse_attrs(self, tag: str) -> Dict[str, str]:
        """Parse a single SVG tag's attributes into a dictionary."""
        return dict(re.findall(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)=["\']([^"\']+)["\']', tag))

    def _to_float(self, value: Optional[str]) -> Optional[float]:
        """Convert numeric attribute values to float when possible."""
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _categorize_issue(self, error_msg: str) -> str:
        """Categorize issue type"""
        if 'viewBox' in error_msg:
            return 'viewBox issues'
        elif 'foreignObject' in error_msg:
            return 'foreignObject'
        elif 'footer zone' in error_msg.lower() or 'Footer zone' in error_msg:
            return 'Footer zone violation'
        elif 'font' in error_msg.lower():
            return 'Font issues'
        elif 'overflow' in error_msg.lower():
            return 'Text overflow'
        else:
            return 'Other'

    def check_directory(self, directory: str, expected_format: str = None, verbose: bool = True) -> List[Dict]:
        """
        Check all SVG files in a directory

        Args:
            directory: Directory path
            expected_format: Expected canvas format

        Returns:
            List of check results
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            print(f"[ERROR] Directory does not exist: {directory}")
            return []

        # Find all SVG files
        if dir_path.is_file():
            svg_files = [dir_path]
        else:
            if (dir_path / 'svg_final').exists():
                svg_root = dir_path / 'svg_final'
            elif (dir_path / 'svg_output').exists():
                svg_root = dir_path / 'svg_output'
            else:
                svg_root = dir_path
            svg_files = sorted(svg_root.glob('*.svg'))

        if not svg_files:
            if verbose:
                print(f"[WARN] No SVG files found")
            return []

        if verbose:
            print(f"\n[SCAN] Checking {len(svg_files)} SVG file(s)...\n")

        for svg_file in svg_files:
            result = self.check_file(str(svg_file), expected_format)
            if verbose:
                self._print_result(result)

        return self.results

    def _print_result(self, result: Dict):
        """Print check result for a single file"""
        if result.get('blocking_issue_count'):
            icon = "[BLOCK]"
            status = "Failed (blocking QA issues)"
        elif result['passed']:
            if result['warnings']:
                icon = "[WARN]"
                status = "Passed (with warnings)"
            else:
                icon = "[OK]"
                status = "Passed"
        else:
            icon = "[ERROR]"
            status = "Failed"

        print(f"{icon} {result['file']} - {status}")

        # Display basic info
        if result['info']:
            info_items = []
            if 'viewbox' in result['info']:
                info_items.append(f"viewBox: {result['info']['viewbox']}")
            if info_items:
                print(f"   {' | '.join(info_items)}")

        # Display errors
        if result['errors']:
            for error in result['errors']:
                print(f"   [ERROR] {error}")

        # Display warnings
        if result['warnings']:
            for warning in result['warnings'][:2]:  # Only show first 2 warnings
                print(f"   [WARN] {warning}")
            if len(result['warnings']) > 2:
                print(f"   ... and {len(result['warnings']) - 2} more warning(s)")

        print()

    def print_summary(self):
        """Print check summary"""
        print("=" * 80)
        print("[SUMMARY] Check Summary")
        print("=" * 80)

        print(f"\nTotal files: {self.summary['total']}")
        print(
            f"  [OK] Fully passed: {self.summary['passed']} ({self._percentage(self.summary['passed'])}%)")
        print(
            f"  [WARN] With warnings: {self.summary['warnings']} ({self._percentage(self.summary['warnings'])}%)")
        print(
            f"  [ERROR] With errors: {self.summary['errors']} ({self._percentage(self.summary['errors'])}%)")
        if self.summary['blocking']:
            print(
                f"  [BLOCK] Blocking QA files: {self.summary['blocking']} ({self._percentage(self.summary['blocking'])}%)")

        if self.issue_types:
            print(f"\nIssue categories:")
            for issue_type, count in sorted(self.issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {issue_type}: {count}")

        # Fix suggestions
        if self.summary['errors'] > 0 or self.summary['warnings'] > 0:
            print(f"\n[TIP] Common fixes:")
            print(f"  1. viewBox issues: Ensure consistency with canvas format (see references/canvas-formats.md)")
            print(f"  2. foreignObject: Use <text> + <tspan> for manual line breaks")
            print(f"  3. Font issues: Use system UI font stack")

    def _percentage(self, count: int) -> int:
        """Calculate percentage"""
        if self.summary['total'] == 0:
            return 0
        return int(count / self.summary['total'] * 100)

    def export_report(self, output_file: str = 'svg_quality_report.txt'):
        """Export check report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PPT Master SVG Quality Check Report\n")
            f.write("=" * 80 + "\n\n")

            for result in self.results:
                status = "[OK] Passed" if result['passed'] else "[ERROR] Failed"
                f.write(f"{status} - {result['file']}\n")
                f.write(f"Path: {result.get('path', 'N/A')}\n")

                if result['info']:
                    f.write(f"Info: {result['info']}\n")

                if result['errors']:
                    f.write(f"\nErrors:\n")
                    for error in result['errors']:
                        f.write(f"  - {error}\n")

                if result['warnings']:
                    f.write(f"\nWarnings:\n")
                    for warning in result['warnings']:
                        f.write(f"  - {warning}\n")

                f.write("\n" + "-" * 80 + "\n\n")

            # Write summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("Check Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total files: {self.summary['total']}\n")
            f.write(f"Fully passed: {self.summary['passed']}\n")
            f.write(f"With warnings: {self.summary['warnings']}\n")
            f.write(f"With errors: {self.summary['errors']}\n")

        print(f"\n[REPORT] Check report exported: {output_file}")


def infer_design_spec_path(target: str) -> Optional[Path]:
    """Infer the nearest project `design_spec.md` from a project/svg path."""
    path = Path(target).resolve()

    candidates: List[Path] = []
    if path.is_file():
        candidates.extend([
            path.parent / 'design_spec.md',
            path.parent.parent / 'design_spec.md',
        ])
    else:
        candidates.extend([
            path / 'design_spec.md',
            path.parent / 'design_spec.md',
        ])
        if path.name in {'svg_output', 'svg_final'}:
            candidates.insert(0, path.parent / 'design_spec.md')

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def main() -> None:
    """Run the CLI entry point."""
    if len(sys.argv) < 2:
        print("PPT Master - SVG Quality Check Tool\n")
        print("Usage:")
        print("  python3 scripts/svg_quality_checker.py <svg_file>")
        print("  python3 scripts/svg_quality_checker.py <directory>")
        print("  python3 scripts/svg_quality_checker.py --all examples")
        print("\nExamples:")
        print("  python3 scripts/svg_quality_checker.py examples/project/svg_output/slide_01.svg")
        print("  python3 scripts/svg_quality_checker.py examples/project/svg_output")
        print("  python3 scripts/svg_quality_checker.py examples/project")
        sys.exit(0)

    # Parse arguments
    target = sys.argv[1]
    expected_format = None
    design_spec_path = None

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            expected_format = sys.argv[idx + 1]

    if target != '--all':
        skip_next = False
        for arg in sys.argv[2:]:
            if skip_next:
                skip_next = False
                continue
            if arg in {'--format', '--output'}:
                skip_next = True
                continue
            if arg == '--export':
                continue
            if not arg.startswith('--'):
                design_spec_path = arg
                break

    if not design_spec_path and target != '--all':
        inferred = infer_design_spec_path(target)
        if inferred:
            design_spec_path = str(inferred)

    checker = SVGQualityChecker(design_spec_path=design_spec_path)

    # Execute check
    if target == '--all':
        # Check all example projects
        base_dir = sys.argv[2] if len(sys.argv) > 2 else 'examples'
        from project_utils import find_all_projects
        projects = find_all_projects(base_dir)

        for project in projects:
            print(f"\n{'=' * 80}")
            print(f"Checking project: {project.name}")
            print('=' * 80)
            checker.check_directory(str(project))
    else:
        checker.check_directory(target, expected_format)

    # Print summary
    checker.print_summary()

    # Export report (if specified)
    if '--export' in sys.argv:
        output_file = 'svg_quality_report.txt'
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                output_file = sys.argv[idx + 1]
        checker.export_report(output_file)

    # Return exit code
    if checker.summary['errors'] > 0 or checker.summary['blocking'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
