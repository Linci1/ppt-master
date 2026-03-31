#!/usr/bin/env python3
"""
PPT Master - SVG Quality Check Tool

Checks whether SVG files comply with project technical specifications.

Usage:
    python3 scripts/svg_quality_checker.py <svg_file>
    python3 scripts/svg_quality_checker.py <directory>
    python3 scripts/svg_quality_checker.py --all examples
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

try:
    from project_utils import CANVAS_FORMATS
    from error_helper import ErrorHelper
except ImportError:
    print("Warning: Unable to import dependency modules")
    CANVAS_FORMATS = {}
    ErrorHelper = None


class SVGQualityChecker:
    """SVG quality checker"""

    def __init__(self):
        self.results = []
        self.summary = {
            'total': 0,
            'passed': 0,
            'warnings': 0,
            'errors': 0
        }
        self.issue_types = defaultdict(int)

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
                'passed': False
            }

        result = {
            'file': svg_path.name,
            'path': str(svg_path),
            'exists': True,
            'errors': [],
            'warnings': [],
            'info': {},
            'passed': True
        }

        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                content = f.read()

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

            # 6. Check footer zone protection (y > 570)
            self._check_footer_zone(content, result)

            # Determine pass/fail
            result['passed'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"Failed to read file: {e}")
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

        # Categorize issue types
        for error in result['errors']:
            self.issue_types[self._categorize_issue(error)] += 1

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

        # Check for text without tspan but with long content
        self._check_text_overflow(content, result)

    def _check_text_overflow(self, content: str, result: Dict):
        """Check if text content might overflow its container based on character count"""
        # Find text elements and estimate if they might overflow
        # Pattern: <text x="..." y="..." ...>content</text>
        text_pattern = r'<text[^>]*x=["\'](\d+)["\'][^>]*>([^<]+)</text>'
        matches = re.findall(text_pattern, content)

        overflow_count = 0
        for x_pos, text_content in matches:
            # Estimate: if text is very long and x position is far right, likely overflow
            if len(text_content) > 60 and int(x_pos) > 400:
                overflow_count += 1

        if overflow_count > 0:
            result['warnings'].append(
                f"Detected {overflow_count} text element(s) with potential overflow (long text at right side)"
            )

    def _check_footer_zone(self, content: str, result: Dict):
        """Check if content elements extend into the footer zone (y > 570)

        Note: Footer elements (logo, page number, bottom bar) are allowed in the footer zone.
        This check detects CONTENT that should not be in the footer zone.
        """
        # Known allowed footer element patterns (not violations)
        allowed_patterns = [
            r'<image[^>]*chaitin_logo',  # Logo image
            r'<image[^>]*logo',           # Any logo image
            r'<text[^>]*page',            # Page number text
            r'<text[^>]*>\s*\d+\s*</text>',  # Page number (standalone digit)
            r'x=["\']118[0-9]["\']',      # Page number position (~1180)
            r'x=["\']60["\']\s+y=["\']64[0-9]',  # Bottom accent bar position
            r'y=["\']69[0-9]["\']',       # Bottom bar positions (690-699)
            r'y=["\']68[0-9]["\']',       # Page number y position (680-689)
        ]

        def is_allowed_element(elem_type: str, y_val: float, full_match: str) -> bool:
            """Check if element is an allowed footer element"""
            # Page number text at x~1180, y~686 is always allowed
            if elem_type == 'text' and y_val >= 680 and y_val <= 695:
                if re.search(r'x=["\']118[0-9]["\']', full_match):
                    return True
            # Bottom accent bar at x=60, y~640-695 is allowed
            if elem_type == 'rect' and y_val >= 640 and y_val <= 699:
                if re.search(r'x=["\']6[0-9]["\']', full_match):
                    return True
            # Logo image at y=600-640 is allowed
            if elem_type == 'image' and y_val >= 590 and y_val <= 645:
                if re.search(r'logo', full_match, re.IGNORECASE):
                    return True
            return False

        # Find elements with y position > 570 (footer zone starts)
        y_patterns = [
            (r'<rect[^>]*y=["\'](\d+(?:\.\d+)?)["\'][^>]*>', 'rect'),
            (r'<text[^>]*y=["\'](\d+(?:\.\d+)?)["\'][^>]*>', 'text'),
            (r'<image[^>]*y=["\'](\d+(?:\.\d+)?)["\'][^>]*>', 'image'),
        ]

        footer_violations = []

        for pattern, elem_type in y_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                y_val = float(match.group(1))
                if y_val > 570:
                    # Check if this is an allowed footer element
                    if not is_allowed_element(elem_type, y_val, match.group(0)):
                        footer_violations.append(f"{elem_type} at y={match.group(1)}")

        if footer_violations:
            # Deduplicate
            unique_violations = list(set(footer_violations))
            result['errors'].append(
                f"Footer zone violation: {len(unique_violations)} content element(s) in protected area (y > 570). "
                f"Elements: {', '.join(unique_violations[:3])}{'...' if len(unique_violations) > 3 else ''}"
            )

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

    def check_directory(self, directory: str, expected_format: str = None) -> List[Dict]:
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
            svg_output = dir_path / \
                'svg_output' if (
                    dir_path / 'svg_output').exists() else dir_path
            svg_files = sorted(svg_output.glob('*.svg'))

        if not svg_files:
            print(f"[WARN] No SVG files found")
            return []

        print(f"\n[SCAN] Checking {len(svg_files)} SVG file(s)...\n")

        for svg_file in svg_files:
            result = self.check_file(str(svg_file), expected_format)
            self._print_result(result)

        return self.results

    def _print_result(self, result: Dict):
        """Print check result for a single file"""
        if result['passed']:
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

    checker = SVGQualityChecker()

    # Parse arguments
    target = sys.argv[1]
    expected_format = None

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            expected_format = sys.argv[idx + 1]

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
    if checker.summary['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
