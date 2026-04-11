#!/usr/bin/env python3
"""
PPT Master - Design Spec Validator

Validates design_spec.md for required fields and format compliance.

Usage:
    python3 scripts/design_spec_validator.py <project_path>
    python3 scripts/design_spec_validator.py --all projects
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Tuple, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
LAYOUT_INDEX_PATH = SCRIPT_DIR.parent / 'templates' / 'layouts' / 'layouts_index.json'

try:
    from template_semantics import fixed_template_matches_entry
except ImportError:
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    from template_semantics import fixed_template_matches_entry  # type: ignore

# Required fields in design_spec.md
REQUIRED_FIELDS = [
    'canvas',
    'body_font_size',
    'color_scheme',
    'font_plan',
]

# Optional but recommended fields
RECOMMENDED_FIELDS = [
    'page_count',
    'target_audience',
    'style_objective',
]

DEFAULT_SECURITY_SERVICE_PATTERNS = {
    'layered_system_map',
    'timeline_roadmap',
    'attack_case_chain',
    'operation_loop',
    'swimlane_collaboration',
    'matrix_defense_map',
    'maturity_model',
    'evidence_wall',
}

SECURITY_SERVICE_REQUIRED_FIELDS = {
    'page_intent': [
        r'(?im)^\s*-\s*\*\*(?:页面意图|Page Intent)\*\*\s*[:：]',
    ],
    'proof_goal': [
        r'(?im)^\s*-\s*\*\*(?:证明目标|Proof Goal)\*\*\s*[:：]',
    ],
    'advanced_pattern': [
        r'(?im)^\s*-\s*\*\*(?:高级正文模式|Advanced Pattern)\*\*\s*[:：]',
    ],
    'preferred_template': [
        r'(?im)^\s*-\s*\*\*(?:优先页型|Preferred Template)\*\*\s*[:：]',
    ],
    'fallback_reason': [
        r'(?im)^\s*-\s*\*\*(?:回退原因|Fallback Reason)\*\*\s*[:：]',
    ],
    'page_role': [
        r'(?im)^\s*-\s*\*\*(?:页面角色|Page Role)\*\*\s*[:：]',
    ],
    'previous_relation': [
        r'(?im)^\s*-\s*\*\*(?:与上一页关系|Relation To Previous Page)\*\*\s*[:：]',
    ],
    'next_relation': [
        r'(?im)^\s*-\s*\*\*(?:与下一页关系|Relation To Next Page)\*\*\s*[:：]',
    ],
}

SECURITY_SERVICE_SKIP_TITLE_KEYWORDS = (
    '封面', 'cover',
    '目录', 'toc', 'agenda',
    '章节', 'chapter',
    '结束', 'ending', 'thank'
)
SECURITY_SERVICE_FIXED_TEMPLATES = {
    '01_cover.svg',
    '02_toc.svg',
    '02_chapter.svg',
    '04_ending.svg',
}
SECURITY_SERVICE_PAGE_ROLES = {
    '概览页',
    '推进页',
    '证明页',
    '收束页',
    'overview',
    'advance',
    'evidence',
    'closure',
}


class DesignSpecValidator:
    """Validates design specification files"""

    def __init__(self):
        self.results: List[Dict] = []
        self.security_service_strategy = self._load_security_service_strategy()

    def _load_security_service_strategy(self) -> Dict:
        patterns = {name: {} for name in DEFAULT_SECURITY_SERVICE_PATTERNS}
        fallback_templates = {'03_content.svg', '11_list.svg'}

        try:
            content = json.loads(LAYOUT_INDEX_PATH.read_text(encoding='utf-8'))
            strategy = (
                content.get('layouts', {})
                .get('security_service', {})
                .get('advancedPageStrategy', {})
            )
            pattern_meta = strategy.get('patterns', {})
            if isinstance(pattern_meta, dict) and pattern_meta:
                patterns = pattern_meta
            if strategy.get('fallbackReasonRequiredWhen'):
                fallback_templates = set(strategy['fallbackReasonRequiredWhen'])
            return {
                'patterns': patterns,
                'fallback_templates': fallback_templates,
            }
        except Exception:
            return {
                'patterns': patterns,
                'fallback_templates': fallback_templates,
            }

    @staticmethod
    def _extract_first_value(block: str, labels: Tuple[str, ...]) -> str | None:
        for label in labels:
            pattern = rf'(?im)^\s*-\s*\*\*{label}\*\*\s*[:：]\s*(.+)$'
            match = re.search(pattern, block)
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _normalize_advanced_pattern(raw_value: str | None) -> str | None:
        if not raw_value:
            return None
        cleaned = re.sub(r'[`*]', '', raw_value).strip()
        if re.search(r'(?i)\bnone\b', cleaned) or '无' in cleaned:
            return 'none'
        code_match = re.search(r'([a-z_]+)', cleaned)
        if code_match:
            return code_match.group(1)
        return cleaned

    @staticmethod
    def _extract_template_name(raw_value: str | None) -> str | None:
        if not raw_value:
            return None
        match = re.search(r'([0-9]{2}_[A-Za-z0-9_]+\.svg)', raw_value)
        if match:
            return match.group(1)
        return raw_value.strip()

    @staticmethod
    def _extract_page_blocks(content: str) -> List[Tuple[str, str]]:
        heading_re = re.compile(r'(?im)^####\s+(.+)$')
        matches = list(heading_re.finditer(content))
        blocks: List[Tuple[str, str]] = []
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
            title = match.group(1).strip()
            block = content[start:end]
            blocks.append((title, block))
        return blocks

    @staticmethod
    def _parse_heading_page(title: str) -> tuple[int | None, str]:
        match = re.match(r'^第\s*(\d+)\s*页\s*(.+)$', title.strip())
        if not match:
            return None, title.strip()
        return int(match.group(1)), match.group(2).strip()

    def _find_security_service_signal_hit(self, block_text: str) -> tuple[str, str] | None:
        for pattern_name, pattern_meta in self.security_service_strategy['patterns'].items():
            for signal in pattern_meta.get('triggerSignals', []):
                if signal and signal in block_text:
                    return pattern_name, signal
        return None

    def _validate_security_service_outline(self, content: str, errors: List[str], warnings: List[str]) -> None:
        if 'security_service' not in content and '长亭安服' not in content:
            return

        patterns = set(self.security_service_strategy['patterns'].keys())
        fallback_templates = self.security_service_strategy['fallback_templates']
        blocks = self._extract_page_blocks(content)
        total_pages = len(blocks)

        for title, block in blocks:
            page_num, page_title = self._parse_heading_page(title)
            title_lower = title.lower()
            preferred_template_raw = self._extract_first_value(block, ('优先页型', 'Preferred Template'))
            preferred_template = self._extract_template_name(preferred_template_raw)
            recommended_page_type = self._extract_first_value(block, ('Recommended Page Type', '推荐页型'))

            if preferred_template in SECURITY_SERVICE_FIXED_TEMPLATES:
                fixed_entry = {
                    'page_num': str(page_num or ''),
                    '页面类型': page_title,
                    '推荐页型': recommended_page_type,
                }
                if not fixed_template_matches_entry(
                    preferred_template,
                    fixed_entry,
                    page_num=page_num,
                    total_pages=total_pages,
                ):
                    errors.append(
                        f"`security_service` 页面“{title}”误用了固定模板 `{preferred_template}`，与页面语义不匹配"
                    )
                    continue
                continue

            if any(keyword in title_lower for keyword in SECURITY_SERVICE_SKIP_TITLE_KEYWORDS):
                continue

            missing = []
            for field_name, field_patterns in SECURITY_SERVICE_REQUIRED_FIELDS.items():
                if field_name in {'fallback_reason', 'page_role', 'previous_relation', 'next_relation'}:
                    continue
                found = any(re.search(pattern, block) for pattern in field_patterns)
                if not found:
                    missing.append(field_name)

            if missing:
                errors.append(
                    f"`security_service` 页面“{title}”缺少必填选页字段: {', '.join(missing)}"
                )
                continue

            advanced_pattern_raw = self._extract_first_value(block, ('高级正文模式', 'Advanced Pattern'))
            advanced_pattern = self._normalize_advanced_pattern(advanced_pattern_raw)

            if advanced_pattern not in patterns and advanced_pattern != 'none':
                errors.append(
                    f"`security_service` 页面“{title}”使用了未知的高级正文模式: {advanced_pattern_raw}"
                )

            if preferred_template in fallback_templates:
                has_fallback_reason = any(
                    re.search(pattern, block)
                    for pattern in SECURITY_SERVICE_REQUIRED_FIELDS['fallback_reason']
                )
                if not has_fallback_reason:
                    errors.append(
                        f"`security_service` 页面“{title}”使用 `{preferred_template}` 作为兜底页，但缺少 `回退原因`"
                    )

            if advanced_pattern and advanced_pattern != 'none':
                missing_complex = []
                for field_name in ('page_role', 'previous_relation', 'next_relation'):
                    found = any(
                        re.search(pattern, block)
                        for pattern in SECURITY_SERVICE_REQUIRED_FIELDS[field_name]
                    )
                    if not found:
                        missing_complex.append(field_name)
                if missing_complex:
                    errors.append(
                        f"`security_service` 复杂页“{title}”缺少复杂页规划字段: {', '.join(missing_complex)}"
                    )
                else:
                    page_role_raw = self._extract_first_value(block, ('页面角色', 'Page Role'))
                    if page_role_raw:
                        page_role = re.sub(r'[`*_]', '', page_role_raw).strip().lower()
                        valid = (
                            page_role_raw.strip() in SECURITY_SERVICE_PAGE_ROLES
                            or page_role in SECURITY_SERVICE_PAGE_ROLES
                        )
                        if not valid:
                            errors.append(
                                f"`security_service` 复杂页“{title}”使用了未知的 `页面角色`: {page_role_raw}"
                            )
                    previous_relation = self._extract_first_value(block, ('与上一页关系', 'Relation To Previous Page'))
                    next_relation = self._extract_first_value(block, ('与下一页关系', 'Relation To Next Page'))
                    if previous_relation and len(previous_relation.strip()) < 4:
                        warnings.append(
                            f"`security_service` 复杂页“{title}”的 `与上一页关系` 过短，可能不足以表达跨页递进"
                        )
                    if next_relation and len(next_relation.strip()) < 4:
                        warnings.append(
                            f"`security_service` 复杂页“{title}”的 `与下一页关系` 过短，可能不足以表达跨页递进"
                        )

            block_text = re.sub(r'[`*_]', '', block)
            if advanced_pattern == 'none':
                signal_hit = self._find_security_service_signal_hit(block_text)
                if signal_hit:
                    pattern_name, signal = signal_hit
                    message = (
                        f"`security_service` 页面“{title}”命中了 `{pattern_name}` 的触发信号“{signal}”，"
                        f"但 `高级正文模式` 仍为“无”"
                    )
                    if preferred_template in SECURITY_SERVICE_FIXED_TEMPLATES:
                        warnings.append(message)
                    else:
                        errors.append(message)

            if advanced_pattern in patterns:
                disallowed = set(
                    self.security_service_strategy['patterns']
                    .get(advanced_pattern, {})
                    .get('mustNotFallbackTo', [])
                )
                if preferred_template in disallowed:
                    errors.append(
                        f"`security_service` 页面“{title}”命中 `{advanced_pattern}`，"
                        f"但 `优先页型` 仍错误地使用了 `{preferred_template}`"
                    )

    def validate_file(self, spec_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a single design spec file

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        spec_file = Path(spec_path)
        if not spec_file.exists():
            return False, [f"Design spec not found: {spec_path}"], warnings

        try:
            content = spec_file.read_text(encoding='utf-8')
        except Exception as e:
            return False, [f"Failed to read file: {e}"], warnings

        # Check for required fields
        for field in REQUIRED_FIELDS:
            # Look for field in markdown format: ## Field Name or field_name:
            patterns = [
                rf'(?im)^\s*##\s+.*{re.escape(field)}.*$',  # ## Canvas Format
                rf'(?im)^\s*{re.escape(field)}\s*:',        # canvas:
            ]
            found = any(re.search(p, content) for p in patterns)
            if not found:
                errors.append(f"Missing required field: '{field}'")

        # Check for color format (#RRGGBB or #RGB)
        color_matches = re.findall(r'#[0-9A-Fa-f]{3,6}', content)
        if color_matches:
            # Validate each color format
            for color in color_matches:
                if not re.match(r'^#[0-9A-Fa-f]{6}$|^#[0-9A-Fa-f]{3}$', color):
                    warnings.append(f"Potentially invalid color format: {color}")

        # Check page count range
        page_count_match = re.search(r'page_count:\s*(\d+)', content)
        if page_count_match:
            page_count = int(page_count_match.group(1))
            if page_count < 1:
                errors.append(f"Page count must be >= 1, got {page_count}")
            elif page_count > 50:
                warnings.append(f"Page count ({page_count}) exceeds recommended maximum of 50")

        # Check for recommended fields
        for field in RECOMMENDED_FIELDS:
            patterns = [
                rf'(?im)^\s*##\s+.*{re.escape(field)}.*$',
                rf'(?im)^\s*{re.escape(field)}\s*:',
            ]
            found = any(re.search(p, content) for p in patterns)
            if not found:
                warnings.append(f"Missing recommended field: '{field}'")

        self._validate_security_service_outline(content, errors, warnings)

        return len(errors) == 0, errors, warnings

    def validate_directory(self, directory: str) -> List[Dict]:
        """
        Validate all design specs in a directory

        Returns:
            List of validation results
        """
        dir_path = Path(directory)
        results = []

        # Find all design_spec.md files
        for spec_file in dir_path.rglob('design_spec.md'):
            is_valid, errors, warnings = self.validate_file(str(spec_file))
            results.append({
                'file': str(spec_file.relative_to(dir_path.parent)),
                'is_valid': is_valid,
                'errors': errors,
                'warnings': warnings
            })

        return results


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("PPT Master - Design Spec Validator\n")
        print("Usage:")
        print("  python3 scripts/design_spec_validator.py <spec_file_or_directory>")
        print("  python3 scripts/design_spec_validator.py --all <directory>")
        sys.exit(0)

    validator = DesignSpecValidator()

    target = sys.argv[1]

    if target == '--all':
        if len(sys.argv) < 3:
            print("Error: --all requires a directory argument")
            sys.exit(1)
        directory = sys.argv[2]
        results = validator.validate_directory(directory)

        if not results:
            print(f"[WARN] No design_spec.md files found in {directory}")
            sys.exit(0)

        print(f"\n[SCAN] Validating {len(results)} design spec(s)...\n")

        valid_count = 0
        for result in results:
            status = "[OK]" if result['is_valid'] else "[ERROR]"
            print(f"{status} {result['file']}")

            if result['errors']:
                for error in result['errors']:
                    print(f"   [ERROR] {error}")

            if result['warnings']:
                for warning in result['warnings']:
                    print(f"   [WARN] {warning}")

            if result['is_valid'] and not result['warnings']:
                valid_count += 1

        print(f"\n[SUMMARY] {valid_count}/{len(results)} fully valid")

    else:
        is_valid, errors, warnings = validator.validate_file(target)

        print(f"\n[CHECK] {target}\n")

        if is_valid and not warnings:
            print("[OK] Design spec is valid")
        elif is_valid:
            print("[WARN] Design spec is valid with warnings:")
            for warning in warnings:
                print(f"   {warning}")
        else:
            print("[ERROR] Design spec has errors:")
            for error in errors:
                print(f"   {error}")
            if warnings:
                print("\nWarnings:")
                for warning in warnings:
                    print(f"   {warning}")

        sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
