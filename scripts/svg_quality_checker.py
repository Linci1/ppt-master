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
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple, Optional
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

    FOOTER_PROTECTED_TOP = 570
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

            # 6. Check footer zone protection using actual occupied bottom edge
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

        text_blocks = self._extract_text_blocks(content)
        canvas_width, canvas_height = self._get_canvas_size(content)
        content_scope = self._extract_content_area(content) or content
        rects = self._collect_rect_containers(content_scope)

        # Check for text without tspan but with long content
        self._check_text_overflow(text_blocks, result)
        self._check_chinese_readability(text_blocks, result)
        self._check_edge_pressure(text_blocks, rects, canvas_width, canvas_height, result)
        self._check_card_text_fit(text_blocks, rects, result)
        self._check_takeaway_body_separation(rects, canvas_width, result)
        self._check_information_density(text_blocks, result)
        self._check_toc_consistency(result['file'], text_blocks, rects, result)

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
        result: Dict
    ):
        """Check whether text sits too close to card edges or canvas boundaries."""
        canvas_hits = 0
        card_hits = 0
        canvas_examples = []
        card_examples = []

        for block in text_blocks:
            if (block['left'] < self.CANVAS_EDGE_WARNING_GAP
                    or block['right'] > canvas_width - self.CANVAS_EDGE_WARNING_GAP
                    or block['top'] < self.CANVAS_EDGE_WARNING_GAP):
                canvas_hits += 1
                if len(canvas_examples) < 2:
                    canvas_examples.append(self._clip_text(block['text']))

            if self._is_minor_label(block):
                continue

            container = self._find_containing_rect(block, rects)
            if not container:
                continue

            left_pad = block['left'] - container['x']
            right_pad = container['right'] - block['right']
            top_pad = block['top'] - container['y']
            bottom_pad = container['bottom'] - block['bottom']

            if min(left_pad, right_pad) < self.CARD_MIN_PADDING or min(top_pad, bottom_pad) < 10:
                card_hits += 1
                if len(card_examples) < 3:
                    card_examples.append(self._clip_text(block['text']))

        if canvas_hits > 0:
            result['warnings'].append(
                f"Edge pressure risk: detected {canvas_hits} text block(s) too close to canvas edges"
                f"{self._format_examples(canvas_examples)}"
            )
        if card_hits > 0:
            result['warnings'].append(
                f"Edge pressure risk: detected {card_hits} text block(s) with insufficient card padding"
                f"{self._format_examples(card_examples)}"
            )

    def _check_card_text_fit(self, text_blocks: List[Dict], rects: List[Dict], result: Dict):
        """Estimate whether text is visually cramped inside its card container."""
        width_hits = 0
        height_hits = 0
        width_examples = []
        height_examples = []

        for block in text_blocks:
            if self._is_minor_label(block):
                continue
            container = self._find_containing_rect(block, rects)
            if not container:
                continue

            usable_width = container['width'] - self.CARD_COMFORT_PADDING * 2
            usable_height = container['height'] - self.CARD_MIN_PADDING * 2

            if block['estimated_width'] > usable_width:
                width_hits += 1
                if len(width_examples) < 2:
                    width_examples.append(self._clip_text(block['text']))
            if block['estimated_height'] > usable_height:
                height_hits += 1
                if len(height_examples) < 2:
                    height_examples.append(self._clip_text(block['text']))

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

    def _check_information_density(self, text_blocks: List[Dict], result: Dict):
        """Warn when a page is likely too dense for presentation-style reading."""
        major_blocks = [block for block in text_blocks if not self._is_minor_label(block)]
        total_lines = sum(len(block['lines']) for block in major_blocks)
        total_chars = sum(len(re.sub(r'\s+', '', block['text'])) for block in major_blocks)

        if (len(major_blocks) > self.DENSITY_MAX_MAJOR_BLOCKS
                or total_lines > self.DENSITY_MAX_TOTAL_LINES
                or total_chars > self.DENSITY_MAX_TOTAL_CHARS):
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

    def _check_footer_zone(self, content: str, result: Dict):
        """Check if content elements extend into the footer zone.

        The original implementation only looked at an element's starting y position,
        which misses wide takeaway bars whose top edge is above the footer line but
        whose actual visual bottom still pushes into the footer breathing zone.
        This version checks the occupied bottom edge of content elements instead.
        """
        content_scope = self._extract_content_area(content) or content
        footer_violations = []

        for element in self._collect_footer_candidates(content_scope):
            if self._is_allowed_footer_element(element):
                continue

            occupied_bottom = element['bottom']
            if occupied_bottom > self.FOOTER_PROTECTED_TOP:
                footer_violations.append(
                    f"{element['type']} bottom={element['bottom']:.1f} (y={element['y']:.1f})"
                )

        if footer_violations:
            unique_violations = list(dict.fromkeys(footer_violations))
            result['errors'].append(
                "Footer zone violation: "
                f"{len(unique_violations)} content element(s) cross the protected footer area "
                f"(bottom > {self.FOOTER_PROTECTED_TOP}). Elements: "
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
            if width < 120 or height < 40:
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
            estimated_height = positive_dy_sum + font_size * 0.9
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

    def _resolve_horizontal_bounds(self, x: float, width: float, anchor: str) -> Tuple[float, float]:
        """Estimate left/right bounds from x + text-anchor."""
        if anchor == 'middle':
            return x - width / 2, x + width / 2
        if anchor == 'end':
            return x - width, x
        return x, x + width

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
        if len(text) <= 4 and self._count_cjk_chars(text) <= 2:
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

        if element['type'] == 'text' and 680 <= y_val <= 695 and x_val is not None:
            if 1170 <= x_val <= 1215:
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
