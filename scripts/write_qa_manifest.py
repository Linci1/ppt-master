#!/usr/bin/env python3
from __future__ import annotations

"""Write a JSON QA manifest for a PPT project.

Usage:
    python3 scripts/write_qa_manifest.py <project_path>
    python3 scripts/write_qa_manifest.py <project_path> --visual-pages 02_目录.svg 05_内容页.svg
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from check_pptx_fonts import inspect_pptx, resolve_pptx
    _PPTX_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - dependency fallback
    inspect_pptx = None  # type: ignore
    resolve_pptx = None  # type: ignore
    _PPTX_IMPORT_ERROR = exc

try:
    from check_complex_page_model import validate as validate_complex_page_model
    _COMPLEX_MODEL_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - dependency fallback
    validate_complex_page_model = None  # type: ignore
    _COMPLEX_MODEL_IMPORT_ERROR = exc

try:
    from check_svg_text_fit import collect_svg_files, check_svg
    _TEXT_FIT_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - dependency fallback
    collect_svg_files = None  # type: ignore
    check_svg = None  # type: ignore
    _TEXT_FIT_IMPORT_ERROR = exc

try:
    from svg_quality_checker import SVGQualityChecker
    _QUALITY_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - dependency fallback
    SVGQualityChecker = None  # type: ignore
    _QUALITY_IMPORT_ERROR = exc


FIXED_TEMPLATE_FILES = {
    "01_cover.svg",
    "02_toc.svg",
    "02_chapter.svg",
    "15_section.svg",
    "04_ending.svg",
}
FIXED_PAGE_FAMILIES = {"cover", "toc", "chapter", "section", "ending"}
REPETITIVE_LAYOUT_SIMPLE_TEMPLATES = {
    "03_content.svg",
    "11_list.svg",
    "13_highlight.svg",
}

REQUIRED_BOOTSTRAP_FILES = {
    "project_brief": "project_brief.md",
    "template_domain_recommendation": "notes/template_domain_recommendation.md",
    "storyline": "notes/storyline.md",
    "page_outline": "notes/page_outline.md",
}


def svg_check_summary(target: Path) -> dict:
    if collect_svg_files is None or check_svg is None:
        message = f"check_svg_text_fit unavailable: {_TEXT_FIT_IMPORT_ERROR}"
        return {
            "path": str(target),
            "file_count": 0,
            "ok": False,
            "issue_count": 1,
            "issues_preview": [message],
        }
    svg_files = collect_svg_files(target)
    issues: list[str] = []
    for svg_file in svg_files:
        issues.extend(check_svg(svg_file))
    return {
        "path": str(target),
        "file_count": len(svg_files),
        "ok": len(svg_files) > 0 and not issues,
        "issue_count": len(issues),
        "issues_preview": issues[:20],
    }


def svg_quality_summary(
    target: Path,
    expected_format: str | None = None,
    design_spec_path: Path | None = None,
) -> dict:
    if SVGQualityChecker is None:
        message = f"svg_quality_checker unavailable: {_QUALITY_IMPORT_ERROR}"
        return {
            "path": str(target),
            "file_count": 0,
            "ok": False,
            "failed_file_count": 0,
            "blocking_file_count": 0,
            "failed_files": [],
            "blocking_files": [],
            "issue_codes": {"qa_checker_unavailable": 1},
            "issues_preview": [
                {
                    "file": "",
                    "severity": "error",
                    "code": "qa_checker_unavailable",
                    "blocking": True,
                    "message": message,
                }
            ],
        }
    checker = SVGQualityChecker(str(design_spec_path) if design_spec_path else None)
    results = checker.check_directory(str(target), expected_format=expected_format, verbose=False)

    issues_preview: list[dict[str, object]] = []
    issue_codes: dict[str, int] = {}
    failed_files: list[str] = []
    blocking_files: list[str] = []

    for result in results:
        if not result.get("passed", False):
            failed_files.append(result.get("file", ""))
        if result.get("blocking_issue_count", 0) > 0:
            blocking_files.append(result.get("file", ""))
        for issue in result.get("issues", []):
            code = str(issue.get("code", "other"))
            issue_codes[code] = issue_codes.get(code, 0) + 1
            if len(issues_preview) < 20:
                issues_preview.append(
                    {
                        "file": result.get("file"),
                        "severity": issue.get("severity"),
                        "code": code,
                        "blocking": bool(issue.get("blocking")),
                        "message": issue.get("message"),
                    }
                )

    return {
        "path": str(target),
        "file_count": checker.summary["total"],
        "ok": checker.summary["total"] > 0 and checker.summary["errors"] == 0 and checker.summary["blocking"] == 0,
        "failed_file_count": len(failed_files),
        "blocking_file_count": len(blocking_files),
        "failed_files": failed_files[:20],
        "blocking_files": blocking_files[:20],
        "issue_codes": issue_codes,
        "issues_preview": issues_preview,
    }


def _load_checker(design_spec_path: Path | None) -> SVGQualityChecker | None:
    if SVGQualityChecker is None:
        return None
    return SVGQualityChecker(str(design_spec_path) if design_spec_path else None)


def bootstrap_artifact_summary(project_path: Path) -> dict:
    missing: list[str] = []
    empty: list[str] = []
    issues_preview: list[dict[str, object]] = []
    issue_codes: dict[str, int] = {}

    for rel_path in REQUIRED_BOOTSTRAP_FILES.values():
        path = project_path / rel_path
        if not path.exists():
            missing.append(rel_path)
            issue_codes["missing_bootstrap_artifact"] = issue_codes.get("missing_bootstrap_artifact", 0) + 1
            issues_preview.append(
                {
                    "file": rel_path,
                    "severity": "error",
                    "code": "missing_bootstrap_artifact",
                    "blocking": True,
                    "message": f"Bootstrap artifact missing: {rel_path}",
                }
            )
            continue
        if not path.read_text(encoding="utf-8").strip():
            empty.append(rel_path)
            issue_codes["empty_bootstrap_artifact"] = issue_codes.get("empty_bootstrap_artifact", 0) + 1
            issues_preview.append(
                {
                    "file": rel_path,
                    "severity": "error",
                    "code": "empty_bootstrap_artifact",
                    "blocking": True,
                    "message": f"Bootstrap artifact is empty: {rel_path}",
                }
            )

    return {
        "path": str(project_path),
        "ok": not missing and not empty,
        "missing_files": missing[:20],
        "empty_files": empty[:20],
        "issue_codes": issue_codes,
        "issues_preview": issues_preview[:20],
    }


def _extract_slide_num(name: str) -> int | None:
    match = re.match(r"(\d+)", name)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _normalize_issue_map(summary: dict) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for key, value in (summary.get("issue_codes") or {}).items():
        try:
            normalized[str(key)] = int(value)
        except (TypeError, ValueError):
            normalized[str(key)] = 0
    return normalized


def _collect_svg_files(target: Path) -> list[Path]:
    return sorted(target.glob("*.svg"))


def _latest_svg_mtime(target: Path) -> float | None:
    latest = None
    for svg_file in _collect_svg_files(target):
        stat = svg_file.stat()
        latest = stat.st_mtime if latest is None else max(latest, stat.st_mtime)
    return latest


def fixed_page_integrity_summary(target: Path, design_spec_path: Path | None = None) -> dict:
    checker = _load_checker(design_spec_path)
    if checker is None:
        message = f"svg_quality_checker unavailable: {_QUALITY_IMPORT_ERROR}"
        return {
            "path": str(target),
            "ok": False,
            "missing_pages": [],
            "issue_codes": {"fixed_page_integrity_unavailable": 1},
            "issues_preview": [
                {
                    "file": "",
                    "severity": "error",
                    "code": "fixed_page_integrity_unavailable",
                    "blocking": True,
                    "message": message,
                }
            ],
        }

    expected_fixed_pages: list[tuple[int, str, str]] = []
    for slide_num, page_spec in sorted(checker.page_specs.items()):
        preferred_template = str(page_spec.get("preferred_template") or "").strip()
        if preferred_template in FIXED_TEMPLATE_FILES:
            expected_fixed_pages.append((slide_num, preferred_template, page_spec.get("title", "").strip()))

    actual_files_by_slide = {
        slide_num: svg_file.name
        for svg_file in _collect_svg_files(target)
        if (slide_num := _extract_slide_num(svg_file.name)) is not None
    }

    missing_pages: list[str] = []
    issues_preview: list[dict[str, object]] = []
    for slide_num, preferred_template, title in expected_fixed_pages:
        if slide_num in actual_files_by_slide:
            continue
        label = f"第 {slide_num} 页 {title or preferred_template}"
        missing_pages.append(label)
        if len(issues_preview) < 10:
            issues_preview.append(
                {
                    "file": "",
                    "severity": "error",
                    "code": "fixed_page_missing",
                    "blocking": True,
                    "message": f"Fixed-page integrity violation: expected fixed page is missing from export source ({label} / {preferred_template})",
                }
            )

    return {
        "path": str(target),
        "ok": not missing_pages,
        "missing_pages": missing_pages,
        "issue_codes": {"fixed_page_missing": len(missing_pages)} if missing_pages else {},
        "issues_preview": issues_preview,
    }


def _layout_signature(svg_file: Path, checker: SVGQualityChecker) -> dict[str, object] | None:
    try:
        content = svg_file.read_text(encoding="utf-8")
    except Exception:
        return None

    page_spec = checker._resolve_page_spec(svg_file.name) or {}  # type: ignore[attr-defined]
    preferred_template = str(page_spec.get("preferred_template") or "").strip()
    advanced_pattern = str(page_spec.get("advanced_pattern") or "").strip()

    hints = checker._extract_svg_hints(content)  # type: ignore[attr-defined]
    context = checker._resolve_template_context(hints)  # type: ignore[attr-defined]
    page_family = str(context.get("page_family") or "")
    if page_family in FIXED_PAGE_FAMILIES or preferred_template in FIXED_TEMPLATE_FILES:
        return None
    normalized_pattern = advanced_pattern.lower()
    is_complex_layout = bool(normalized_pattern and normalized_pattern not in {"无", "none"})
    if not preferred_template and not page_family and not is_complex_layout:
        return None

    content_scope = checker._extract_content_area(content) or content  # type: ignore[attr-defined]
    rects = checker._collect_rect_containers(content_scope)  # type: ignore[attr-defined]
    text_blocks = checker._extract_text_blocks(content_scope)  # type: ignore[attr-defined]
    major_rects = [
        rect for rect in rects
        if rect.get("width", 0) >= 140 and rect.get("height", 0) >= 40 and rect.get("y", 9999) < 660
    ]
    major_rects = sorted(
        major_rects,
        key=lambda rect: (-(rect.get("width", 0) * rect.get("height", 0)), rect.get("y", 0), rect.get("x", 0)),
    )[:6]
    rect_sig = [
        (
            round(rect.get("x", 0) / 24),
            round(rect.get("y", 0) / 24),
            round(rect.get("width", 0) / 24),
            round(rect.get("height", 0) / 24),
        )
        for rect in major_rects
    ]
    image_count = len(re.findall(r"<(?:[\w.-]+:)?image\b", content_scope))
    headline_count = sum(
        1 for block in text_blocks if float(block.get("font_size", 0) or 0) >= 20 and float(block.get("y", 9999) or 0) <= 220
    )
    signature = (
        tuple(rect_sig),
        min(len(major_rects), 6),
        min(image_count, 6),
        min(headline_count, 4),
    )
    slide_num = _extract_slide_num(svg_file.name)
    if slide_num is None:
        return None
    return {
        "slide_num": slide_num,
        "file": svg_file.name,
        "preferred_template": preferred_template or page_family or "body",
        "advanced_pattern": advanced_pattern,
        "complex_layout": is_complex_layout,
        "signature": signature,
    }


def layout_repetition_summary(target: Path, design_spec_path: Path | None = None) -> dict:
    checker = _load_checker(design_spec_path)
    if checker is None:
        message = f"svg_quality_checker unavailable: {_QUALITY_IMPORT_ERROR}"
        return {
            "path": str(target),
            "ok": False,
            "warning_count": 0,
            "blocking_count": 1,
            "issue_codes": {"layout_repeat_unavailable": 1},
            "issues_preview": [
                {
                    "file": "",
                    "severity": "error",
                    "code": "layout_repeat_unavailable",
                    "blocking": True,
                    "message": message,
                }
            ],
        }

    signatures = []
    for svg_file in _collect_svg_files(target):
        signature = _layout_signature(svg_file, checker)
        if signature:
            signatures.append(signature)
    signatures.sort(key=lambda item: int(item["slide_num"]))

    warnings: list[str] = []
    blocking_reasons: list[str] = []
    issues_preview: list[dict[str, object]] = []
    issue_codes: dict[str, int] = {}

    def consume_run(run_items: list[dict[str, object]]) -> None:
        if len(run_items) < 3:
            return
        files = [str(entry["file"]) for entry in run_items]
        template_labels = sorted({str(entry["preferred_template"]) for entry in run_items})
        complex_run = any(bool(entry.get("complex_layout")) for entry in run_items)
        message = (
            f"Layout repetition risk: consecutive body pages reuse nearly identical layout skeleton "
            f"(templates: {', '.join(template_labels)}; files: {', '.join(files)})"
        )
        blocking_threshold = 3 if complex_run else 4
        if len(run_items) >= blocking_threshold:
            blocking_reasons.append(message)
            issue_codes["repetitive_layout"] = issue_codes.get("repetitive_layout", 0) + 1
            issues_preview.append(
                {
                    "file": files[0],
                    "severity": "error",
                    "code": "repetitive_layout",
                    "blocking": True,
                    "message": message,
                }
            )
        else:
            warnings.append(message)
            issue_codes["repetitive_layout_warning"] = issue_codes.get("repetitive_layout_warning", 0) + 1
            issues_preview.append(
                {
                    "file": files[0],
                    "severity": "warning",
                    "code": "repetitive_layout_warning",
                    "blocking": False,
                    "message": message,
                }
            )

    run: list[dict[str, object]] = []
    for item in signatures:
        is_contiguous = bool(run) and int(item["slide_num"]) == int(run[-1]["slide_num"]) + 1
        same_signature = bool(run) and item["signature"] == run[-1]["signature"]
        if run and is_contiguous and same_signature:
            run.append(item)
            continue
        consume_run(run)
        run = [item]
    consume_run(run)

    return {
        "path": str(target),
        "ok": not blocking_reasons,
        "warning_count": len(warnings),
        "blocking_count": len(blocking_reasons),
        "warnings": warnings[:10],
        "blocking_reasons": blocking_reasons[:10],
        "issue_codes": issue_codes,
        "issues_preview": issues_preview[:10],
    }


def complex_page_model_summary(project_path: Path) -> dict:
    if validate_complex_page_model is None:
        return {
            "path": str(project_path / "notes" / "complex_page_models.md"),
            "ok": False,
            "complex_page_count": 0,
            "model_page_count": 0,
            "errors": [f"check_complex_page_model unavailable: {_COMPLEX_MODEL_IMPORT_ERROR}"],
            "warnings": [],
            "design_spec_path": str(project_path / "design_spec.md"),
        }
    ok, errors, warnings, summary = validate_complex_page_model(project_path)
    return {
        "path": str(project_path / "notes" / "complex_page_models.md"),
        "ok": ok,
        "complex_page_count": int(summary.get("complex_page_count", 0) or 0),
        "model_page_count": int(summary.get("model_page_count", 0) or 0),
        "errors": errors,
        "warnings": warnings,
        "design_spec_path": summary.get("design_spec_path"),
    }


def visual_summary(project_path: Path, visual_pages: list[str], render_dir: Path) -> dict:
    normalized_pages = []
    missing_renders = []
    for page in visual_pages:
        svg_name = page if page.endswith(".svg") else f"{page}.svg"
        png_name = f"{Path(svg_name).stem}.png"
        normalized_pages.append(svg_name)
        if not (render_dir / png_name).exists():
            missing_renders.append(png_name)
    return {
        "render_dir": str(render_dir),
        "required_pages": normalized_pages,
        "missing_renders": missing_renders,
        "ok": not missing_renders,
    }


def pptx_summary(project_path: Path) -> dict:
    if inspect_pptx is None or resolve_pptx is None:
        return {
            "pptx_path": "",
            "ok": False,
            "warnings": [f"check_pptx_fonts unavailable: {_PPTX_IMPORT_ERROR}"],
            "cjk_font_pairs": {},
        }
    try:
        pptx_path = resolve_pptx(project_path)
        warnings, counts = inspect_pptx(pptx_path)
        return {
            "pptx_path": str(pptx_path),
            "ok": not warnings,
            "warnings": warnings,
            "cjk_font_pairs": {f"{latin}|{ea}": count for (latin, ea), count in counts.items()},
        }
    except FileNotFoundError as exc:
        return {
            "pptx_path": "",
            "ok": False,
            "warnings": [str(exc)],
            "cjk_font_pairs": {},
        }


def _extract_report_value(content: str, label: str) -> str:
    match = re.search(rf"(?im)^-\s*{re.escape(label)}[：:]\s*`?(.+?)`?\s*$", content)
    return match.group(1).strip() if match else ""


def _parse_execution_report(report_file: Path) -> dict[str, object]:
    content = report_file.read_text(encoding="utf-8")
    page = _extract_report_value(content, "页面") or report_file.name.replace(".md", ".svg")
    status = _extract_report_value(content, "自动状态建议").lower()
    auto_repair_enabled = _extract_report_value(content, "auto_repair_enabled").lower() == "true"
    quality_passed = _extract_report_value(content, "quality_passed").lower() == "true"
    blocking_issue_raw = _extract_report_value(content, "blocking_issue_count")
    try:
        blocking_issue_count = int(blocking_issue_raw or 0)
    except ValueError:
        blocking_issue_count = 0
    findings = re.findall(r"(?im)^-\s*(error|warning):\s*([a-z0-9_]+)\s*-\s*(.+)$", content)
    return {
        "page": page,
        "status": status,
        "auto_repair_enabled": auto_repair_enabled,
        "quality_passed": quality_passed,
        "blocking_issue_count": blocking_issue_count,
        "findings": findings,
    }


def execution_trace_summary(project_path: Path) -> dict:
    trace_dir = project_path / "notes" / "page_execution"
    if not trace_dir.exists():
        return {
            "path": str(trace_dir),
            "ok": True,
            "trace_file_count": 0,
            "report_file_count": 0,
            "pages_with_auto_repair": [],
            "pages_with_progression_reframe": [],
            "pages_with_semantic_argument_rewrite": [],
            "pages_still_failed_after_repair": [],
            "pages_marked_qa_failed": [],
            "event_type_counts": {},
            "warnings": ["page_execution 目录不存在，暂无自动执行轨迹。"],
            "events_preview": [],
        }

    trace_files = sorted(trace_dir.glob("*.json"))
    report_files = sorted(trace_dir.glob("*.md"))
    event_type_counts: dict[str, int] = {}
    pages_with_auto_repair: list[str] = []
    pages_with_progression_reframe: list[str] = []
    pages_with_semantic_argument: list[str] = []
    pages_still_failed: list[str] = []
    pages_marked_qa_failed: list[str] = []
    warnings: list[str] = []
    events_preview: list[dict[str, object]] = []
    traced_pages: set[str] = set()

    for trace_file in trace_files:
        try:
            trace = json.loads(trace_file.read_text(encoding="utf-8"))
        except Exception as exc:
            warnings.append(f"执行轨迹读取失败：{trace_file.name} ({type(exc).__name__}: {exc})")
            continue

        page = str(trace.get("page") or trace_file.name.replace(".json", ".svg"))
        traced_pages.add(Path(page).stem)
        if int(trace.get("auto_repair_rounds_used", 0) or 0) > 0:
            pages_with_auto_repair.append(page)
        if trace.get("status") != "generated" and int(trace.get("auto_repair_rounds_used", 0) or 0) > 0:
            pages_still_failed.append(page)
        if trace.get("status") not in {"generated", "success", "completed"}:
            pages_marked_qa_failed.append(page)

        for event in trace.get("execution_events", []) or []:
            event_type = str(event.get("type") or "other")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            if event_type == "progression_reframe":
                pages_with_progression_reframe.append(page)
            if event_type == "semantic_argument_rewrite":
                pages_with_semantic_argument.append(page)
            if len(events_preview) < 20:
                events_preview.append(
                    {
                        "page": page,
                        "type": event_type,
                        "from_pattern": event.get("from_pattern"),
                        "to_pattern": event.get("to_pattern"),
                        "from_template": event.get("from_template"),
                        "to_template": event.get("to_template"),
                        "synced_artifacts": event.get("synced_artifacts", []),
                        "reason": event.get("reason", ""),
                    }
                )

    for report_file in report_files:
        if report_file.stem in traced_pages:
            continue
        try:
            report = _parse_execution_report(report_file)
        except Exception as exc:
            warnings.append(f"执行报告读取失败：{report_file.name} ({type(exc).__name__}: {exc})")
            continue

        page = str(report["page"])
        if report["auto_repair_enabled"]:
            pages_with_auto_repair.append(page)
        if report["status"] in {"qa_failed", "failed"} or not report["quality_passed"] or int(report["blocking_issue_count"]) > 0:
            pages_marked_qa_failed.append(page)
            if report["auto_repair_enabled"]:
                pages_still_failed.append(page)
        for severity, code, message in report["findings"]:
            event_type = f"report_{severity}"
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            if len(events_preview) < 20:
                events_preview.append(
                    {
                        "page": page,
                        "type": event_type,
                        "code": code,
                        "message": message,
                    }
                )

    return {
        "path": str(trace_dir),
        "ok": not pages_marked_qa_failed,
        "trace_file_count": len(trace_files),
        "report_file_count": len(report_files),
        "pages_with_auto_repair": sorted(set(pages_with_auto_repair))[:30],
        "pages_with_progression_reframe": sorted(set(pages_with_progression_reframe))[:30],
        "pages_with_semantic_argument_rewrite": sorted(set(pages_with_semantic_argument))[:30],
        "pages_still_failed_after_repair": sorted(set(pages_still_failed))[:30],
        "pages_marked_qa_failed": sorted(set(pages_marked_qa_failed))[:30],
        "event_type_counts": event_type_counts,
        "warnings": warnings[:20],
        "events_preview": events_preview,
    }


def build_manifest(
    project_path: Path,
    *,
    expected_format: str | None = None,
    visual_pages: list[str] | None = None,
    render_dir: Path | None = None,
    include_pptx: bool = True,
) -> dict:
    svg_output_dir = project_path / "svg_output"
    svg_final_dir = project_path / "svg_final"
    design_spec_path = project_path / "design_spec.md"
    resolved_render_dir = render_dir or (project_path / "visual_qc" / "svg_final")
    required_visual_pages = visual_pages or []

    checks = {
        "complex_page_model": complex_page_model_summary(project_path),
        "svg_output": svg_check_summary(svg_output_dir),
        "svg_final": svg_check_summary(svg_final_dir),
        "svg_output_quality": svg_quality_summary(svg_output_dir, expected_format, design_spec_path),
        "svg_final_quality": svg_quality_summary(svg_final_dir, expected_format, design_spec_path),
        "svg_output_fixed_pages": fixed_page_integrity_summary(svg_output_dir, design_spec_path),
        "svg_final_fixed_pages": fixed_page_integrity_summary(svg_final_dir, design_spec_path),
        "svg_output_layout_repetition": layout_repetition_summary(svg_output_dir, design_spec_path),
        "svg_final_layout_repetition": layout_repetition_summary(svg_final_dir, design_spec_path),
        "execution_trace": execution_trace_summary(project_path),
        "visual_qc": visual_summary(project_path, required_visual_pages, resolved_render_dir),
    }
    if include_pptx:
        checks["pptx_fonts"] = pptx_summary(project_path)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_path": str(project_path),
        "checks": checks,
    }
    manifest["overall_ok"] = all(section.get("ok", False) for section in checks.values())
    return manifest


def build_pre_export_gate(
    project_path: Path,
    *,
    target_dir: Path,
    source_dir_name: str,
    expected_format: str | None = None,
    design_spec_path: Path | None = None,
) -> dict:
    fit_summary = svg_check_summary(target_dir)
    quality_summary = svg_quality_summary(target_dir, expected_format, design_spec_path)
    complex_summary = complex_page_model_summary(project_path)
    bootstrap_summary = bootstrap_artifact_summary(project_path)
    fixed_page_summary = fixed_page_integrity_summary(target_dir, design_spec_path)
    layout_repeat_summary = layout_repetition_summary(target_dir, design_spec_path)
    execution_summary = execution_trace_summary(project_path)

    blocking_reasons: list[str] = []
    if not bootstrap_summary.get("ok", False):
        missing = bootstrap_summary.get("missing_files", [])
        empty = bootstrap_summary.get("empty_files", [])
        detail_parts = []
        if missing:
            detail_parts.append(f"缺失 {len(missing)} 个规划文件")
        if empty:
            detail_parts.append(f"{len(empty)} 个规划文件为空")
        blocking_reasons.append(
            "规划资料未完成："
            + ("，".join(detail_parts) if detail_parts else "缺少 bootstrap 产物")
        )
    if not fit_summary.get("ok", False):
        blocking_reasons.append(
            f"{source_dir_name} 文本适配未通过：{fit_summary.get('issue_count', 0)} 个问题"
        )
    if not quality_summary.get("ok", False):
        blocking_reasons.append(
            f"{source_dir_name} 质量检查未通过：{quality_summary.get('blocking_file_count', 0)} 个阻断页，"
            f"{quality_summary.get('failed_file_count', 0)} 个失败页"
        )
    if not complex_summary.get("ok", False):
        blocking_reasons.append(
            f"复杂页模型未通过：{len(complex_summary.get('errors', []))} 个错误"
        )
    if not fixed_page_summary.get("ok", False):
        blocking_reasons.append(
            f"{source_dir_name} 固定页完整性未通过：缺失 {len(fixed_page_summary.get('missing_pages', []))} 个固定页"
        )
    if layout_repeat_summary.get("blocking_count", 0) > 0:
        blocking_reasons.append(
            f"{source_dir_name} 连续正文布局重复：{layout_repeat_summary.get('blocking_count', 0)} 处阻断风险"
        )
    if execution_summary.get("pages_marked_qa_failed"):
        blocking_reasons.append(
            f"页级执行报告仍有 QA 失败：{len(execution_summary.get('pages_marked_qa_failed', []))} 页"
        )

    merged_issue_codes = _normalize_issue_map(quality_summary)
    for extra_summary in (bootstrap_summary, fixed_page_summary, layout_repeat_summary):
        for code, count in _normalize_issue_map(extra_summary).items():
            merged_issue_codes[code] = merged_issue_codes.get(code, 0) + count
    if execution_summary.get("pages_marked_qa_failed"):
        merged_issue_codes["page_execution_qa_failed"] = len(execution_summary.get("pages_marked_qa_failed", []))

    issues_preview = list(quality_summary.get("issues_preview", [])[:10])
    for extra_preview in bootstrap_summary.get("issues_preview", [])[:10]:
        if len(issues_preview) >= 10:
            break
        issues_preview.append(extra_preview)
    for extra_preview in fixed_page_summary.get("issues_preview", [])[:10]:
        if len(issues_preview) >= 10:
            break
        issues_preview.append(extra_preview)
    for extra_preview in layout_repeat_summary.get("issues_preview", [])[:10]:
        if len(issues_preview) >= 10:
            break
        issues_preview.append(extra_preview)
    if execution_summary.get("pages_marked_qa_failed"):
        for page in execution_summary.get("pages_marked_qa_failed", [])[:3]:
            if len(issues_preview) >= 10:
                break
            issues_preview.append(
                {
                    "file": str(page),
                    "severity": "error",
                    "code": "page_execution_qa_failed",
                    "blocking": True,
                    "message": "Execution report still marks this page as qa_failed / failed.",
                }
            )

    return {
        "source_dir": source_dir_name,
        "path": str(target_dir),
        "ok": not blocking_reasons,
        "blocking_reasons": blocking_reasons,
        "fit_issue_count": fit_summary.get("issue_count", 0),
        "quality_failed_file_count": quality_summary.get("failed_file_count", 0),
        "quality_blocking_file_count": quality_summary.get("blocking_file_count", 0),
        "issue_codes": merged_issue_codes,
        "issues_preview": issues_preview,
        "fit_issues_preview": fit_summary.get("issues_preview", [])[:10],
        "complex_page_model_errors": complex_summary.get("errors", [])[:10],
        "bootstrap_missing_files": bootstrap_summary.get("missing_files", [])[:10],
        "bootstrap_empty_files": bootstrap_summary.get("empty_files", [])[:10],
        "fixed_page_missing": fixed_page_summary.get("missing_pages", [])[:10],
        "layout_repeat_warnings": layout_repeat_summary.get("warnings", [])[:10],
        "layout_repeat_blocking_reasons": layout_repeat_summary.get("blocking_reasons", [])[:10],
        "execution_trace_failed_pages": execution_summary.get("pages_marked_qa_failed", [])[:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a JSON QA manifest for a PPT project.")
    parser.add_argument("project_path", help="Project directory path")
    parser.add_argument(
        "--visual-pages",
        nargs="*",
        default=[],
        help="SVG filenames that were visually rendered and should exist in visual_qc/svg_final/",
    )
    parser.add_argument(
        "--render-dir",
        help="Optional override for the visual render directory (default: <project>/visual_qc/svg_final)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Manifest output path (default: <project>/qa_manifest.json)",
    )
    parser.add_argument(
        "--format",
        help="Optional expected canvas format (for example: ppt169)",
    )
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        raise SystemExit(f"Project directory not found: {project_path}")

    render_dir = Path(args.render_dir).resolve() if args.render_dir else project_path / "visual_qc" / "svg_final"
    output_path = Path(args.output).resolve() if args.output else project_path / "qa_manifest.json"

    manifest = build_manifest(
        project_path,
        expected_format=args.format,
        visual_pages=args.visual_pages,
        render_dir=render_dir,
        include_pptx=True,
    )

    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0 if manifest["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
