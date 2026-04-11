# SVG Pipeline Tools

These tools cover post-processing, SVG validation, speaker notes, and PPTX export.

## Recommended Pipeline

Run these steps in order:

```bash
python3 scripts/check_svg_text_fit.py <project_path>/svg_output
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/check_svg_text_fit.py <project_path>/svg_final
python3 scripts/render_svg_pages.py <project_path> -s final
python3 scripts/svg_to_pptx.py <project_path> -s final
python3 scripts/check_pptx_fonts.py <project_path>
python3 scripts/write_qa_manifest.py <project_path> --format ppt169
```

## `finalize_svg.py`

Unified post-processing entry point. This is the preferred way to run SVG cleanup.

It aggregates:
- `embed_icons.py`
- `crop_images.py`
- `fix_image_aspect.py`
- `embed_images.py`
- `flatten_tspan.py`
- `svg_rect_to_path.py`

Typical usage:

```bash
python3 scripts/finalize_svg.py <project_path>
```

Use standalone sub-tools only when you need advanced debugging or one-off fixes.

## `svg_to_pptx.py`

Convert project SVGs into PPTX.

```bash
python3 scripts/svg_to_pptx.py <project_path> -s final
python3 scripts/svg_to_pptx.py <project_path> -s final --only native
python3 scripts/svg_to_pptx.py <project_path> -s final --only legacy
python3 scripts/svg_to_pptx.py <project_path> -s final --no-notes
python3 scripts/svg_to_pptx.py <project_path> -t none
python3 scripts/svg_to_pptx.py <project_path> -s final --auto-advance 3
```

Behavior:
- Default output: native editable PPTX + SVG reference PPTX
- Recommended source directory: `svg_final/`
- Speaker notes are embedded automatically unless `--no-notes` is used
- Before export, the command refreshes `<project>/qa_manifest.json` and runs a hard pre-export QA gate
- If the selected SVG source still has blocking issues, export is refused and no final PPTX is written

Dependency:

```bash
pip install python-pptx
```

## `total_md_split.py`

Split `total.md` into per-slide note files.

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/total_md_split.py <project_path> -o <output_directory>
python3 scripts/total_md_split.py <project_path> -q
```

Requirements:
- Each section begins with `# `
- Heading text matches the SVG filename
- Sections are separated by `---`

## `svg_quality_checker.py`

Validate SVG technical compliance.

```bash
python3 scripts/svg_quality_checker.py examples/project/svg_output/01_cover.svg
python3 scripts/svg_quality_checker.py examples/project/svg_output
python3 scripts/svg_quality_checker.py examples/project
python3 scripts/svg_quality_checker.py examples/project --format ppt169
python3 scripts/svg_quality_checker.py --all examples
python3 scripts/svg_quality_checker.py examples/project --export
```

Checks include:
- `viewBox`
- banned elements
- width/height consistency
- line-break structure
- template-aware brand presence / approved-logo checks
- blocking layout warnings for fixed-skeleton templates

## `check_svg_text_fit.py`

Check whether text is likely to overflow, collide inside cards, or whether large contained images become unreadably small.

```bash
python3 scripts/check_svg_text_fit.py <project_path>/svg_output
python3 scripts/check_svg_text_fit.py <project_path>/svg_final
python3 scripts/check_svg_text_fit.py path/to/page.svg
```

Use this as a hard gate before export. Fix all reported issues first.

## `render_svg_pages.py`

Render SVG pages to PNG previews for visual QA.

```bash
python3 scripts/render_svg_pages.py <project_path> -s final
python3 scripts/render_svg_pages.py <project_path>/svg_final --pages 02_目录.svg 05_问题汇总.svg
```

Use this to inspect TOC pages, dense content pages, image-heavy pages, and any template high-risk pages.

## `check_pptx_fonts.py`

Inspect the exported native PPTX for likely CJK font substitution or mixed-font runs.

```bash
python3 scripts/check_pptx_fonts.py <project_path>
python3 scripts/check_pptx_fonts.py path/to/output.pptx
```

## `write_qa_manifest.py`

Write a JSON manifest that records SVG checks, render coverage, and PPTX font-check status.

```bash
python3 scripts/write_qa_manifest.py <project_path> --format ppt169
python3 scripts/write_qa_manifest.py <project_path> --format ppt169 --visual-pages 02_目录.svg 05_密集内容页.svg
```

Notes:
- `svg_to_pptx.py` now refreshes `qa_manifest.json` automatically before export
- `write_qa_manifest.py` remains the explicit report command when you want a full QA snapshot or post-export font check

## `svg_position_calculator.py`

Analyze or pre-calculate chart coordinates.

Common commands:

```bash
python3 scripts/svg_position_calculator.py analyze <svg_file>
python3 scripts/svg_position_calculator.py interactive
python3 scripts/svg_position_calculator.py calc bar --data "East:185,South:142"
python3 scripts/svg_position_calculator.py calc pie --data "A:35,B:25,C:20"
python3 scripts/svg_position_calculator.py from-json config.json
```

Use this when chart geometry needs to be verified before or after AI generation.

## Advanced Standalone Tools

### `flatten_tspan.py`

```bash
python3 scripts/svg_finalize/flatten_tspan.py examples/<project>/svg_output
python3 scripts/svg_finalize/flatten_tspan.py path/to/input.svg path/to/output.svg
```

### `svg_rect_to_path.py`

```bash
python3 scripts/svg_finalize/svg_rect_to_path.py <project_path>
python3 scripts/svg_finalize/svg_rect_to_path.py <project_path> -s final
python3 scripts/svg_finalize/svg_rect_to_path.py path/to/file.svg
```

Use when rounded corners must survive PowerPoint shape conversion.

### `fix_image_aspect.py`

```bash
python3 scripts/svg_finalize/fix_image_aspect.py path/to/slide.svg
python3 scripts/svg_finalize/fix_image_aspect.py 01_cover.svg 02_toc.svg
python3 scripts/svg_finalize/fix_image_aspect.py --dry-run path/to/slide.svg
```

Use when embedded images stretch after PowerPoint shape conversion.

### `embed_icons.py`

```bash
python3 scripts/svg_finalize/embed_icons.py output.svg
python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg
python3 scripts/svg_finalize/embed_icons.py --dry-run svg_output/*.svg
```

Use for manual icon embedding checks outside `finalize_svg.py`.

## PPT Compatibility Rules

Use PowerPoint-safe transparency syntax:

| Avoid | Use instead |
|------|-------------|
| `fill=\"rgba(...)\"` | `fill=\"#hex\"` + `fill-opacity` |
| `<g opacity=\"...\">` | Set opacity on each child |
| `<image opacity=\"...\">` | Overlay with a mask layer |

PowerPoint also has trouble with:
- marker-based arrows
- unsupported filters
- direct SVG features not mapped to DrawingML
