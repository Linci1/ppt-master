#!/usr/bin/env python3
"""
PPT Master - Batch Project Validation Tool

Checks the structural integrity and compliance of multiple projects at once.

Usage:
    python3 scripts/batch_validate.py examples
    python3 scripts/batch_validate.py projects
    python3 scripts/batch_validate.py --all
    python3 scripts/batch_validate.py examples projects
"""

import sys
import re
from collections import defaultdict
from pathlib import Path

try:
    from project_utils import (
        find_all_projects,
        get_project_info,
        validate_project_structure,
        validate_svg_viewbox,
        CANVAS_FORMATS
    )
except ImportError:
    print("Error: Unable to import project_utils module")
    print("Please ensure project_utils.py is in the same directory")
    sys.exit(1)


class BatchValidator:
    """Batch validator"""

    def __init__(self):
        self.results: list[dict[str, object]] = []
        self.summary = {
            'total': 0,
            'valid': 0,
            'has_errors': 0,
            'has_warnings': 0,
            'missing_readme': 0,
            'missing_spec': 0,
            'svg_issues': 0,
            'naming_issues': 0,
            'notes_issues': 0
        }

    # ============================================================
    # SVG Naming Convention Check
    # ============================================================
    def validate_svg_naming(self, project_path: str) -> tuple[bool, list[str], list[str]]:
        """
        Validate SVG file naming convention (e.g., 01_xxx.svg)

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        project = Path(project_path)

        svg_dir = project / 'svg_output'
        if not svg_dir.exists():
            return True, [], []  # No SVG dir, skip check

        svg_files = list(svg_dir.glob('*.svg'))
        if not svg_files:
            warnings.append("No SVG files found in svg_output/")
            return True, [], warnings

        naming_pattern = re.compile(r'^\d{2,}_[^\s\/\\]+\.svg$')
        chinese_pattern = re.compile(r'^[\u4e00-\u9fff]')

        invalid_names = []
        for svg_file in svg_files:
            name = svg_file.name
            if not naming_pattern.match(name):
                # Check if it's Chinese naming (also valid)
                if chinese_pattern.match(name) and name.endswith('.svg'):
                    continue  # Chinese naming is valid
                invalid_names.append(name)

        if invalid_names:
            errors.append(
                f"SVG naming convention violation: {len(invalid_names)} file(s) don't match pattern 'NN_name.svg'. "
                f"Examples: {', '.join(invalid_names[:2])}"
            )

        return len(errors) == 0, errors, warnings

    # ============================================================
    # Speaker Notes Check
    # ============================================================
    def validate_speaker_notes(self, project_path: str) -> tuple[bool, list[str], list[str]]:
        """
        Validate speaker notes for common issues

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        project = Path(project_path)

        notes_dir = project / 'notes'
        if not notes_dir.exists():
            warnings.append("No notes/ directory found")
            return True, [], warnings

        # Check for total.md
        total_md = notes_dir / 'total.md'
        if not total_md.exists():
            errors.append("Missing notes/total.md")
            return False, errors, warnings

        try:
            content = total_md.read_text(encoding='utf-8')

            # Check for required markers
            required_markers = ['[Transition]', '[Pause]']
            found_markers = []
            for marker in required_markers:
                if marker in content:
                    found_markers.append(marker)

            missing_markers = set(required_markers) - set(found_markers)
            if missing_markers:
                warnings.append(
                    f"Missing speaker note markers: {', '.join(missing_markers)}. "
                    "Consider adding for better presentation flow."
                )

            # Check for language consistency (mixed Chinese/English markers)
            lines_with_brackets = [line for line in content.split('\n') if '[' in line and ']' in line]
            mixed_lang_count = 0
            for line in lines_with_brackets:
                has_chinese_markers = bool(re.search(r'[\u4e00-\u9fff]', line))
                has_english_markers = bool(re.search(r'\[(Transition|Pause|Interactive|Data)\]', line))
                if has_chinese_markers and has_english_markers:
                    mixed_lang_count += 1

            if mixed_lang_count > 3:
                warnings.append(
                    f"Potential language inconsistency: {mixed_lang_count} lines have mixed Chinese/English markers"
                )

            # Check for page count
            page_headers = re.findall(r'^# \d+_', content, re.MULTILINE)
            if page_headers:
                # Estimate total duration from notes
                duration_matches = re.findall(r'时长：(\d+)分钟', content)
                if duration_matches:
                    total_minutes = sum(int(d) for d in duration_matches)
                    if total_minutes > 30:
                        warnings.append(
                            f"Total estimated duration ({total_minutes} min) exceeds 30 min. "
                            "Consider trimming content."
                        )

        except Exception as e:
            warnings.append(f"Could not read notes/total.md: {e}")

        return len(errors) == 0, errors, warnings

    def validate_directory(self, directory: str, recursive: bool = False) -> list[dict[str, object]]:
        """
        Validate all projects in a directory

        Args:
            directory: Directory path
            recursive: Whether to recursively search subdirectories

        Returns:
            List of validation results
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"[ERROR] Directory does not exist: {directory}")
            return []

        print(f"\n[SCAN] Scanning directory: {directory}")
        print("=" * 80)

        projects = find_all_projects(directory)

        if not projects:
            print(f"[WARN] No projects found")
            return []

        print(f"Found {len(projects)} project(s)\n")

        for project_path in projects:
            self.validate_project(str(project_path))

        return self.results

    def validate_project(self, project_path: str) -> dict[str, object]:
        """
        Validate a single project

        Args:
            project_path: Project path

        Returns:
            Validation result dictionary
        """
        self.summary['total'] += 1

        # Get project info
        info = get_project_info(project_path)

        # Validate project structure
        is_valid, errors, warnings = validate_project_structure(project_path)

        # Validate SVG viewBox
        svg_warnings = []
        if info['svg_files']:
            project_path_obj = Path(project_path)
            svg_files = [project_path_obj / 'svg_output' /
                         f for f in info['svg_files']]
            svg_warnings = validate_svg_viewbox(svg_files, info['format'])

        # Validate SVG naming convention
        naming_valid, naming_errors, naming_warnings = self.validate_svg_naming(project_path)
        if naming_errors:
            errors.extend(naming_errors)
        if naming_warnings:
            svg_warnings.extend(naming_warnings)

        # Validate speaker notes
        notes_valid, notes_errors, notes_warnings = self.validate_speaker_notes(project_path)
        if notes_errors:
            errors.extend(notes_errors)
        if notes_warnings:
            svg_warnings.extend(notes_warnings)

        # Aggregate results
        result = {
            'path': project_path,
            'name': info['name'],
            'format': info['format_name'],
            'date': info['date_formatted'],
            'svg_count': info['svg_count'],
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings + svg_warnings,
            'has_readme': info['has_readme'],
            'has_spec': info['has_spec']
        }

        self.results.append(result)

        # Update statistics
        if is_valid and not warnings and not svg_warnings:
            self.summary['valid'] += 1
            status = "[OK]"
        elif errors:
            self.summary['has_errors'] += 1
            status = "[ERROR]"
        else:
            self.summary['has_warnings'] += 1
            status = "[WARN]"

        if not info['has_readme']:
            self.summary['missing_readme'] += 1
        if not info['has_spec']:
            self.summary['missing_spec'] += 1
        if svg_warnings:
            self.summary['svg_issues'] += 1
        if naming_errors:
            self.summary['naming_issues'] += 1
        if notes_errors:
            self.summary['notes_issues'] += 1

        # Print result
        print(f"{status} {info['name']}")
        print(f"   Path: {project_path}")
        print(
            f"   Format: {info['format_name']} | SVG: {info['svg_count']} file(s) | Date: {info['date_formatted']}")

        if errors:
            print(f"   [ERROR] Errors ({len(errors)}):")
            for error in errors:
                print(f"      - {error}")

        if warnings or svg_warnings:
            all_warnings = warnings + svg_warnings
            print(f"   [WARN] Warnings ({len(all_warnings)}):")
            for warning in all_warnings[:3]:  # Only show first 3 warnings
                print(f"      - {warning}")
            if len(all_warnings) > 3:
                print(f"      ... and {len(all_warnings) - 3} more warning(s)")

        print()

        return result

    def print_summary(self) -> None:
        """Print a summary of validation results."""
        print("\n" + "=" * 80)
        print("[Summary] Validation Summary")
        print("=" * 80)

        print(f"\nTotal projects: {self.summary['total']}")
        print(
            f"  [OK] Fully valid: {self.summary['valid']} ({self._percentage(self.summary['valid'])}%)")
        print(
            f"  [WARN] With warnings: {self.summary['has_warnings']} ({self._percentage(self.summary['has_warnings'])}%)")
        print(
            f"  [ERROR] With errors: {self.summary['has_errors']} ({self._percentage(self.summary['has_errors'])}%)")

        print(f"\nCommon issues:")
        print(f"  Missing README.md: {self.summary['missing_readme']} project(s)")
        print(f"  Missing design spec: {self.summary['missing_spec']} project(s)")
        print(f"  SVG format issues: {self.summary['svg_issues']} project(s)")
        print(f"  SVG naming issues: {self.summary['naming_issues']} project(s)")
        print(f"  Speaker notes issues: {self.summary['notes_issues']} project(s)")

        # Group statistics by format
        format_stats = defaultdict(int)
        for result in self.results:
            format_stats[result['format']] += 1

        if format_stats:
            print(f"\nCanvas format distribution:")
            for fmt, count in sorted(format_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"  {fmt}: {count} project(s)")

        # Provide fix suggestions
        if self.summary['has_errors'] > 0 or self.summary['has_warnings'] > 0:
            print(f"\n[TIP] Fix suggestions:")

            if self.summary['missing_readme'] > 0:
                print(f"  1. Create documentation for projects missing README")
                print(
                    f"     Reference: examples/google_annual_report_ppt169_20251116/README.md")

            if self.summary['svg_issues'] > 0:
                print(f"  2. Check and fix SVG viewBox settings")
                print(f"     Ensure consistency with canvas format")

            if self.summary['missing_spec'] > 0:
                print(f"  3. Add design specification files")

    def _percentage(self, count: int) -> int:
        """Calculate percentage"""
        if self.summary['total'] == 0:
            return 0
        return int(count / self.summary['total'] * 100)

    def export_report(self, output_file: str = 'validation_report.txt') -> None:
        """
        Export validation report to file

        Args:
            output_file: Output file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("PPT Master Project Validation Report\n")
            f.write("=" * 80 + "\n\n")

            for result in self.results:
                status = "[OK] Valid" if result['is_valid'] and not result['warnings'] else \
                    "[ERROR] Error" if result['errors'] else "[WARN] Warning"

                f.write(f"{status} - {result['name']}\n")
                f.write(f"Path: {result['path']}\n")
                f.write(
                    f"Format: {result['format']} | SVG: {result['svg_count']} file(s)\n")

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
            f.write("Validation Summary\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total projects: {self.summary['total']}\n")
            f.write(f"Fully valid: {self.summary['valid']}\n")
            f.write(f"With warnings: {self.summary['has_warnings']}\n")
            f.write(f"With errors: {self.summary['has_errors']}\n")

        print(f"\n[REPORT] Validation report exported: {output_file}")


def main() -> None:
    """Run the CLI entry point."""
    if len(sys.argv) < 2:
        print("PPT Master - Batch Project Validation Tool\n")
        print("Usage:")
        print("  python3 scripts/batch_validate.py <directory>")
        print("  python3 scripts/batch_validate.py <dir1> <dir2> ...")
        print("  python3 scripts/batch_validate.py --all")
        print("\nExamples:")
        print("  python3 scripts/batch_validate.py examples")
        print("  python3 scripts/batch_validate.py projects")
        print("  python3 scripts/batch_validate.py examples projects")
        print("  python3 scripts/batch_validate.py --all")
        sys.exit(0)

    validator = BatchValidator()

    # Process arguments
    if '--all' in sys.argv:
        directories = ['examples', 'projects']
    else:
        directories = [arg for arg in sys.argv[1:] if not arg.startswith('--')]

    # Validate each directory
    for directory in directories:
        if Path(directory).exists():
            validator.validate_directory(directory)
        else:
            print(f"[WARN] Skipping non-existent directory: {directory}\n")

    # Print summary
    validator.print_summary()

    # Export report (if specified)
    if '--export' in sys.argv:
        output_file = 'validation_report.txt'
        if '--output' in sys.argv:
            idx = sys.argv.index('--output')
            if idx + 1 < len(sys.argv):
                output_file = sys.argv[idx + 1]
        validator.export_report(output_file)

    # Return exit code
    if validator.summary['has_errors'] > 0:
        sys.exit(1)
    elif validator.summary['has_warnings'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
