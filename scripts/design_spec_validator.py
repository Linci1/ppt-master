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
from pathlib import Path
from typing import List, Tuple, Dict

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


class DesignSpecValidator:
    """Validates design specification files"""

    def __init__(self):
        self.results: List[Dict] = []

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
