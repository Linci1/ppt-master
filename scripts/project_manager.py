#!/usr/bin/env python3
"""PPT Master project management helpers.

Usage:
    python3 scripts/project_manager.py init <project_name> [--format ppt169] [--dir projects]
    python3 scripts/project_manager.py import-sources <project_path> <source1> [<source2> ...] [--move]
    python3 scripts/project_manager.py bootstrap-agent <project_path> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal> [--project-name <name>] [--template <template>] [--style <style>] [--priorities a,b,c] [--materials x,y,z] [--constraints p,q,r] [--answers-json <answers.json>]
    python3 scripts/project_manager.py validate <project_path>
    python3 scripts/project_manager.py info <project_path>
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

try:
    from project_utils import (
        CANVAS_FORMATS,
        get_project_info as get_project_info_common,
        normalize_canvas_format,
        validate_project_structure,
        validate_svg_viewbox,
    )
    from write_qa_manifest import build_pre_export_gate, execution_trace_summary
except ImportError:
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    from project_utils import (  # type: ignore
        CANVAS_FORMATS,
        get_project_info as get_project_info_common,
        normalize_canvas_format,
        validate_project_structure,
        validate_svg_viewbox,
    )
    from write_qa_manifest import build_pre_export_gate, execution_trace_summary  # type: ignore

TOOLS_DIR = Path(__file__).resolve().parent
SKILL_DIR = TOOLS_DIR.parent
REPO_ROOT = SKILL_DIR.parent.parent
SOURCE_DIRNAME = "sources"
TEXT_SOURCE_SUFFIXES = {".md", ".markdown", ".txt"}
PDF_SUFFIXES = {".pdf"}
DOC_SUFFIXES = {
    ".docx", ".doc", ".odt", ".rtf",          # Office documents
    ".epub",                                    # eBooks
    ".html", ".htm",                            # Web pages
    ".tex", ".latex", ".rst", ".org",           # Academic / technical
    ".ipynb", ".typ",                           # Notebooks / Typst
}
WECHAT_HOST_KEYWORDS = ("mp.weixin.qq.com", "weixin.qq.com")


def is_url(value: str) -> bool:
    """Return whether a string looks like an HTTP(S) URL."""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def sanitize_name(value: str) -> str:
    """Sanitize a user-facing name into a filesystem-safe token."""
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in value.strip())
    safe = safe.strip("._")
    while "__" in safe:
        safe = safe.replace("__", "_")
    return safe[:120] or "source"


def derive_url_basename(url: str) -> str:
    """Derive a stable base filename from a URL."""
    parsed = urlparse(url)
    parts = [sanitize_name(parsed.netloc)]
    if parsed.path and parsed.path != "/":
        path_part = sanitize_name(parsed.path.strip("/").replace("/", "_"))
        if path_part:
            parts.append(path_part)
    return "_".join(part for part in parts if part) or "web_source"


def is_within_path(path: Path, parent: Path) -> bool:
    """Return whether `path` resolves inside `parent`."""
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


class ProjectManager:
    """Create, inspect, validate, and populate project folders."""

    CANVAS_FORMATS = CANVAS_FORMATS

    def __init__(self, base_dir: str = "projects") -> None:
        self.base_dir = Path(base_dir)

    def init_project(
        self,
        project_name: str,
        canvas_format: str = "ppt169",
        base_dir: str | None = None,
    ) -> str:
        base_path = Path(base_dir) if base_dir else self.base_dir

        normalized_format = normalize_canvas_format(canvas_format)
        if normalized_format not in self.CANVAS_FORMATS:
            available = ", ".join(sorted(self.CANVAS_FORMATS.keys()))
            raise ValueError(
                f"Unsupported canvas format: {canvas_format} "
                f"(available: {available}; common alias: xhs -> xiaohongshu)"
            )

        date_str = datetime.now().strftime("%Y%m%d")
        project_dir_name = f"{project_name}_{normalized_format}_{date_str}"
        project_path = base_path / project_dir_name

        if project_path.exists():
            raise FileExistsError(f"Project directory already exists: {project_path}")

        for rel_path in (
            "svg_output",
            "svg_final",
            "images",
            "notes",
            "templates",
            SOURCE_DIRNAME,
        ):
            (project_path / rel_path).mkdir(parents=True, exist_ok=True)

        canvas_info = self.CANVAS_FORMATS[normalized_format]
        readme_path = project_path / "README.md"
        readme_path.write_text(
            (
                f"# {project_name}\n\n"
                f"- Canvas format: {normalized_format}\n"
                f"- Created: {date_str}\n\n"
                "## Directories\n\n"
                "- `svg_output/`: raw SVG output\n"
                "- `svg_final/`: finalized SVG output\n"
                "- `images/`: presentation assets\n"
                "- `notes/`: speaker notes\n"
                "- `templates/`: project templates\n"
                "- `sources/`: source materials and normalized markdown\n"
            ),
            encoding="utf-8",
        )

        print(f"Project created: {project_path}")
        print(f"Canvas: {canvas_info['name']} ({canvas_info['dimensions']})")
        return str(project_path)

    def _source_dir(self, project_path: Path) -> Path:
        sources_dir = project_path / SOURCE_DIRNAME
        sources_dir.mkdir(parents=True, exist_ok=True)
        return sources_dir

    def _ensure_unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path

        suffix = path.suffix
        stem = path.stem
        counter = 2
        while True:
            candidate = path.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def _resolve_design_spec_path(self, project_path: Path) -> Path | None:
        for candidate_name in (
            "design_spec.md",
            "设计规范与内容大纲.md",
            "design_specification.md",
            "设计规范.md",
        ):
            candidate = project_path / candidate_name
            if candidate.exists():
                return candidate
        return None

    def _svg_dir_latest_mtime(self, target_dir: Path) -> float | None:
        latest = None
        for svg_file in target_dir.glob("*.svg"):
            stat = svg_file.stat()
            latest = stat.st_mtime if latest is None else max(latest, stat.st_mtime)
        return latest

    def _resolve_export_gate_target(self, project_path: Path) -> tuple[Path | None, str]:
        for source_dir_name in ("svg_final", "svg_output"):
            target_dir = project_path / source_dir_name
            if target_dir.is_dir() and any(target_dir.glob("*.svg")):
                return target_dir, source_dir_name
        return None, ""

    def _build_export_gate_status(self, project_path: Path, expected_format: str | None = None) -> dict[str, object]:
        target_dir, source_dir_name = self._resolve_export_gate_target(project_path)
        if target_dir is None:
            return {
                "available": False,
                "status": "pending",
                "ok": False,
                "source_dir": "",
                "path": "",
                "blocking_reasons": [],
                "blocking_reason_count": 0,
                "fit_issue_count": 0,
                "quality_failed_file_count": 0,
                "quality_blocking_file_count": 0,
                "issue_codes": {},
                "issues_preview": [],
                "fit_issues_preview": [],
                "complex_page_model_errors": [],
                "working_source_dir": "",
            }

        svg_output_dir = project_path / "svg_output"
        svg_final_dir = project_path / "svg_final"
        svg_output_exists = svg_output_dir.is_dir() and any(svg_output_dir.glob("*.svg"))
        svg_final_exists = svg_final_dir.is_dir() and any(svg_final_dir.glob("*.svg"))
        output_mtime = self._svg_dir_latest_mtime(svg_output_dir) if svg_output_exists else None
        final_mtime = self._svg_dir_latest_mtime(svg_final_dir) if svg_final_exists else None

        if svg_output_exists and not svg_final_exists:
            return {
                "available": True,
                "status": "pending_finalize",
                "ok": False,
                "source_dir": "svg_output",
                "working_source_dir": "svg_output",
                "path": str(svg_output_dir),
                "blocking_reasons": [
                    "当前仅存在 `svg_output`，尚未生成最新 `svg_final`；请先执行 finalize 后再判断是否可导出。"
                ],
                "blocking_reason_count": 1,
                "fit_issue_count": 0,
                "quality_failed_file_count": 0,
                "quality_blocking_file_count": 0,
                "issue_codes": {"finalize_required": 1},
                "issues_preview": [],
                "fit_issues_preview": [],
                "complex_page_model_errors": [],
            }

        if svg_output_exists and svg_final_exists and output_mtime and final_mtime and output_mtime > final_mtime + 1:
            return {
                "available": True,
                "status": "stale_final",
                "ok": False,
                "source_dir": "svg_final",
                "working_source_dir": "svg_output",
                "path": str(svg_final_dir),
                "blocking_reasons": [
                    "`svg_final` 已落后于当前 `svg_output`，请重新执行 finalize 后再判断导出门禁。"
                ],
                "blocking_reason_count": 1,
                "fit_issue_count": 0,
                "quality_failed_file_count": 0,
                "quality_blocking_file_count": 0,
                "issue_codes": {"finalize_required": 1},
                "issues_preview": [],
                "fit_issues_preview": [],
                "complex_page_model_errors": [],
            }

        normalized_format = expected_format if expected_format and expected_format != "unknown" else None
        gate = build_pre_export_gate(
            project_path,
            target_dir=target_dir,
            source_dir_name=source_dir_name,
            expected_format=normalized_format,
            design_spec_path=self._resolve_design_spec_path(project_path),
        )
        gate["available"] = True
        gate["status"] = "pass" if gate.get("ok", False) else "block"
        gate["blocking_reason_count"] = len(gate.get("blocking_reasons", []))
        gate["working_source_dir"] = source_dir_name
        return gate

    def _format_issue_codes(self, issue_codes: dict[str, object]) -> str:
        if not issue_codes:
            return ""

        def sort_key(item: tuple[str, object]) -> tuple[int, str]:
            raw_value = item[1]
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                value = 0
            return (-value, item[0])

        return ", ".join(f"{code}={count}" for code, count in sorted(issue_codes.items(), key=sort_key))

    def _bootstrap_paths(self, project_path: Path) -> dict[str, Path]:
        return {
            "project_brief": project_path / "project_brief.md",
            "template_domain_recommendation": project_path / "notes" / "template_domain_recommendation.md",
            "storyline": project_path / "notes" / "storyline.md",
            "page_outline": project_path / "notes" / "page_outline.md",
            "agent_bootstrap_summary": project_path / "notes" / "agent_bootstrap_summary.md",
        }

    def _build_project_runtime_snapshot(
        self,
        project_path: Path,
        *,
        expected_format: str | None = None,
    ) -> dict[str, object]:
        bootstrap_status = {name: path.exists() for name, path in self._bootstrap_paths(project_path).items()}
        export_gate = self._build_export_gate_status(
            project_path,
            expected_format=expected_format,
        )
        return {
            "bootstrap_status": bootstrap_status,
            "has_agent_bootstrap": all(bootstrap_status.values()),
            "export_gate": export_gate,
            "export_gate_issue_code_summary": self._format_issue_codes(export_gate.get("issue_codes", {})),
        }

    def _copy_or_move_file(self, source: Path, destination: Path, move: bool) -> Path:
        try:
            if source.resolve() == destination.resolve():
                return destination
        except FileNotFoundError:
            pass

        destination = self._ensure_unique_path(destination)
        if move:
            shutil.move(str(source), str(destination))
        else:
            shutil.copy2(source, destination)
        return destination

    def _copy_or_move_tree(self, source: Path, destination: Path, move: bool) -> Path:
        try:
            if source.resolve() == destination.resolve():
                return destination
        except FileNotFoundError:
            pass

        destination = self._ensure_unique_path(destination)
        if move:
            shutil.move(str(source), str(destination))
        else:
            shutil.copytree(source, destination)
        return destination

    def _run_tool(self, args: list[str]) -> None:
        try:
            result = subprocess.run(
                args,
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"Missing executable: {args[0]}") from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or exc.stdout or "").strip()
            raise RuntimeError(details or "tool execution failed") from exc

        if result.stdout.strip():
            print(result.stdout.strip())

    def _import_pdf(self, pdf_path: Path, markdown_path: Path) -> None:
        self._run_tool(
            [
                sys.executable,
                str(TOOLS_DIR / "pdf_to_md.py"),
                str(pdf_path),
                "-o",
                str(markdown_path),
            ]
        )

    def _import_doc(self, doc_path: Path, markdown_path: Path) -> None:
        self._run_tool(
            [
                sys.executable,
                str(TOOLS_DIR / "doc_to_md.py"),
                str(doc_path),
                "-o",
                str(markdown_path),
            ]
        )

    def _import_url(self, url: str, markdown_path: Path) -> None:
        host = urlparse(url).netloc.lower()
        if any(keyword in host for keyword in WECHAT_HOST_KEYWORDS):
            command = ["node", str(TOOLS_DIR / "web_to_md.cjs"), url, "-o", str(markdown_path)]
        else:
            command = [
                sys.executable,
                str(TOOLS_DIR / "web_to_md.py"),
                url,
                "-o",
                str(markdown_path),
            ]
        self._run_tool(command)

    def _archive_url_record(self, sources_dir: Path, url: str) -> Path:
        file_path = self._ensure_unique_path(sources_dir / f"{derive_url_basename(url)}.url.txt")
        file_path.write_text(
            f"URL: {url}\nImported: {datetime.now().isoformat(timespec='seconds')}\n",
            encoding="utf-8",
        )
        return file_path

    def _normalize_text_source(self, source_path: Path, sources_dir: Path) -> Path:
        target = self._ensure_unique_path(sources_dir / f"{source_path.stem}.md")
        content = source_path.read_text(encoding="utf-8", errors="replace")
        target.write_text(content, encoding="utf-8")
        return target

    def _canonicalize_markdown_content(self, content: str) -> str:
        canonical = content.replace("\r\n", "\n")
        canonical = re.sub(r"(?m)^(\s*Crawled:\s+).*$", r"\1__IGNORED__", canonical)
        canonical = re.sub(r"(?m)^(\s*Imported:\s+).*$", r"\1__IGNORED__", canonical)
        canonical = re.sub(r"([^\s\]()/]+_files)/", "__ASSET_DIR__/", canonical)
        return canonical.strip()

    def _find_equivalent_markdown(self, source_path: Path, sources_dir: Path) -> Path | None:
        source_content = source_path.read_text(encoding="utf-8", errors="replace")
        canonical_source = self._canonicalize_markdown_content(source_content)

        for existing in sorted(sources_dir.iterdir()):
            if existing.suffix.lower() not in {".md", ".markdown"}:
                continue
            try:
                if existing.resolve() == source_path.resolve():
                    continue
            except FileNotFoundError:
                pass

            existing_content = existing.read_text(encoding="utf-8", errors="replace")
            if self._canonicalize_markdown_content(existing_content) == canonical_source:
                return existing

        return None

    def _companion_asset_dir(self, source_path: Path) -> Path | None:
        candidate = source_path.with_name(f"{source_path.stem}_files")
        if candidate.exists() and candidate.is_dir():
            return candidate
        return None

    def _rewrite_markdown_asset_refs(
        self,
        markdown_path: Path,
        original_asset_dirname: str,
        imported_asset_dirname: str,
    ) -> None:
        if original_asset_dirname == imported_asset_dirname:
            return

        content = markdown_path.read_text(encoding="utf-8", errors="replace")
        updated = content.replace(f"{original_asset_dirname}/", f"{imported_asset_dirname}/")
        if updated != content:
            markdown_path.write_text(updated, encoding="utf-8")

    def _import_markdown_with_assets(
        self,
        source_path: Path,
        sources_dir: Path,
        move: bool,
    ) -> tuple[Path, Path | None, str | None]:
        archived_markdown = self._copy_or_move_file(
            source_path,
            sources_dir / source_path.name,
            move=move,
        )

        asset_dir = self._companion_asset_dir(source_path)
        if asset_dir is None:
            return archived_markdown, None, None

        imported_asset_dir = self._copy_or_move_tree(
            asset_dir,
            sources_dir / f"{archived_markdown.stem}_files",
            move=move,
        )
        self._rewrite_markdown_asset_refs(
            archived_markdown,
            original_asset_dirname=asset_dir.name,
            imported_asset_dirname=imported_asset_dir.name,
        )

        note = None
        if archived_markdown.stem != source_path.stem:
            note = (
                f"{source_path}: renamed imported markdown to {archived_markdown.name} "
                f"and rewrote asset references to {imported_asset_dir.name}/"
            )
        return archived_markdown, imported_asset_dir, note

    def import_sources(
        self,
        project_path: str,
        source_items: list[str],
        move: bool = False,
    ) -> dict[str, list[str]]:
        project_dir = Path(project_path)
        if not project_dir.exists() or not project_dir.is_dir():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")
        if not source_items:
            raise ValueError("At least one source path or URL is required")

        sources_dir = self._source_dir(project_dir)
        summary: dict[str, list[str]] = {
            "archived": [],
            "markdown": [],
            "assets": [],
            "notes": [],
            "skipped": [],
        }
        explicit_markdown_stems = {
            Path(item).stem
            for item in source_items
            if not is_url(item)
            and Path(item).exists()
            and Path(item).is_file()
            and Path(item).suffix.lower() in {".md", ".markdown"}
        }

        for item in source_items:
            if is_url(item):
                archived = self._archive_url_record(sources_dir, item)
                markdown_path = self._ensure_unique_path(
                    sources_dir / f"{derive_url_basename(item)}.md"
                )
                try:
                    self._import_url(item, markdown_path)
                except Exception as exc:  # pragma: no cover - summary path
                    summary["skipped"].append(f"{item}: {exc}")
                    continue

                summary["archived"].append(str(archived))
                summary["markdown"].append(str(markdown_path))
                continue

            source_path = Path(item)
            if not source_path.exists():
                summary["skipped"].append(f"{item}: path not found")
                continue
            if source_path.is_dir():
                summary["skipped"].append(f"{item}: directories are not supported")
                continue

            effective_move = move or is_within_path(source_path, REPO_ROOT)
            suffix = source_path.suffix.lower()

            if suffix in {".md", ".markdown"}:
                duplicate_markdown = self._find_equivalent_markdown(source_path, sources_dir)
                if duplicate_markdown is not None:
                    summary["markdown"].append(str(duplicate_markdown))
                    summary["notes"].append(
                        f"{item}: skipped duplicate markdown import because equivalent content already exists as {duplicate_markdown.name}"
                    )
                    continue

                archived_markdown, asset_dir, note = self._import_markdown_with_assets(
                    source_path,
                    sources_dir,
                    move=effective_move,
                )
                summary["archived"].append(str(archived_markdown))
                summary["markdown"].append(str(archived_markdown))
                if asset_dir is not None:
                    summary["assets"].append(str(asset_dir))
                if note:
                    summary["notes"].append(note)
                continue

            archived_path = self._copy_or_move_file(
                source_path,
                sources_dir / source_path.name,
                move=effective_move,
            )
            summary["archived"].append(str(archived_path))

            if suffix in PDF_SUFFIXES:
                canonical_markdown_path = sources_dir / f"{archived_path.stem}.md"
                if archived_path.stem in explicit_markdown_stems:
                    summary["notes"].append(
                        f"{item}: skipped PDF auto-conversion because a same-stem Markdown source was provided"
                    )
                    continue
                if canonical_markdown_path.exists():
                    summary["markdown"].append(str(canonical_markdown_path))
                    summary["notes"].append(
                        f"{item}: skipped PDF auto-conversion because {canonical_markdown_path.name} already exists"
                    )
                    continue
                markdown_path = canonical_markdown_path
                try:
                    self._import_pdf(archived_path, markdown_path)
                    summary["markdown"].append(str(markdown_path))
                except Exception as exc:  # pragma: no cover - summary path
                    summary["skipped"].append(f"{item}: PDF conversion failed ({exc})")
            elif suffix in DOC_SUFFIXES:
                canonical_markdown_path = sources_dir / f"{archived_path.stem}.md"
                if archived_path.stem in explicit_markdown_stems:
                    summary["notes"].append(
                        f"{item}: skipped document auto-conversion because a same-stem Markdown source was provided"
                    )
                    continue
                if canonical_markdown_path.exists():
                    summary["markdown"].append(str(canonical_markdown_path))
                    summary["notes"].append(
                        f"{item}: skipped document auto-conversion because {canonical_markdown_path.name} already exists"
                    )
                    continue
                markdown_path = canonical_markdown_path
                try:
                    self._import_doc(archived_path, markdown_path)
                    summary["markdown"].append(str(markdown_path))
                except Exception as exc:  # pragma: no cover - summary path
                    summary["skipped"].append(f"{item}: document conversion failed ({exc})")
            elif suffix == ".txt":
                markdown_path = self._normalize_text_source(archived_path, sources_dir)
                summary["markdown"].append(str(markdown_path))
            else:
                summary["notes"].append(f"{item}: archived only, no automatic conversion")

        return summary

    def bootstrap_agent(
        self,
        project_path: str,
        *,
        project_name: str | None = None,
        industry: str,
        scenario: str,
        audience: str,
        goal: str,
        priorities: str = "",
        template: str = "",
        style: str = "",
        materials: str = "",
        constraints: str = "",
        answers_json: str = "",
        language: str = "中文",
    ) -> dict[str, str]:
        project_dir = Path(project_path).expanduser().resolve()
        if not project_dir.exists() or not project_dir.is_dir():
            raise FileNotFoundError(f"Project directory not found: {project_dir}")

        project_info = get_project_info_common(str(project_dir))
        detected_format = project_info.get("format") or "ppt169"
        resolved_project_name = project_name or project_info.get("name") or project_dir.name

        brief_path = project_dir / "project_brief.md"
        recommendation_path = project_dir / "notes" / "template_domain_recommendation.md"
        storyline_path = project_dir / "notes" / "storyline.md"
        outline_path = project_dir / "notes" / "page_outline.md"
        summary_path = project_dir / "notes" / "agent_bootstrap_summary.md"
        plan_state_path = project_dir / "notes" / "plan_agent_state.json"

        brief_command = [
            sys.executable,
            str(TOOLS_DIR / "build_project_brief.py"),
            "-o",
            str(brief_path),
            "--project-name",
            str(resolved_project_name),
            "--industry",
            industry,
            "--scenario",
            scenario,
            "--audience",
            audience,
            "--goal",
            goal,
            "--priorities",
            priorities,
            "--template",
            template,
            "--style",
            style,
            "--lang",
            language,
            "--format",
            str(detected_format),
        ]
        if answers_json:
            brief_command.extend(["--json", str(Path(answers_json).expanduser().resolve())])
        if plan_state_path.exists():
            brief_command.extend(["--plan-state-json", str(plan_state_path)])

        self._run_tool(brief_command)
        self._run_tool(
            [
                sys.executable,
                str(TOOLS_DIR / "select_template_and_domain.py"),
                str(brief_path),
                "-o",
                str(recommendation_path),
            ]
        )
        self._run_tool(
            [
                sys.executable,
                str(TOOLS_DIR / "build_storyline.py"),
                str(brief_path),
                "--storyline-output",
                str(storyline_path),
                "--outline-output",
                str(outline_path),
            ]
        )

        summary_path.write_text(
            (
                "# Agent Bootstrap Summary\n\n"
                f"- project_brief: `{brief_path}`\n"
                f"- template/domain recommendation: `{recommendation_path}`\n"
                f"- storyline: `{storyline_path}`\n"
                f"- page outline: `{outline_path}`\n"
                f"- plan_agent_state: `{plan_state_path}`\n"
            ),
            encoding="utf-8",
        )

        return {
            "brief": str(brief_path),
            "recommendation": str(recommendation_path),
            "storyline": str(storyline_path),
            "outline": str(outline_path),
            "summary": str(summary_path),
        }

    def validate_project(self, project_path: str) -> tuple[bool, list[str], list[str]]:
        project_path_obj = Path(project_path)
        is_valid, errors, warnings = validate_project_structure(str(project_path_obj))

        if project_path_obj.exists() and project_path_obj.is_dir():
            info = get_project_info_common(str(project_path_obj))
            if info.get("svg_files"):
                svg_files = [project_path_obj / "svg_output" / name for name in info["svg_files"]]
                expected_format = info.get("format")
                if expected_format == "unknown":
                    expected_format = None
                warnings.extend(validate_svg_viewbox(svg_files, expected_format))

            runtime_snapshot = self._build_project_runtime_snapshot(
                project_path_obj,
                expected_format=info.get("format"),
            )
            bootstrap_status = runtime_snapshot["bootstrap_status"]
            bootstrap_exists = list(bootstrap_status.values())
            if any(bootstrap_exists) and not all(bootstrap_exists):
                warnings.append("Agent bootstrap artifacts are incomplete; re-run `project_manager.py bootstrap-agent`.")
            elif not any(bootstrap_exists):
                warnings.append("Agent bootstrap has not been run yet; generate `project_brief.md` and planning files before formal PPT production.")

            export_gate = runtime_snapshot["export_gate"]
            if export_gate.get("available") and not export_gate.get("ok", False):
                source_dir_name = str(export_gate.get("source_dir", "") or "svg_output")
                warnings.append(
                    f"[BLOCK] Export gate failed on `{source_dir_name}`; stop PPT export until blocking QA issues are fixed."
                )
                blocking_reasons = export_gate.get("blocking_reasons", [])
                if blocking_reasons:
                    warnings.append(f"Export gate reasons: {'; '.join(str(item) for item in blocking_reasons[:3])}")
                issue_code_summary = str(runtime_snapshot["export_gate_issue_code_summary"])
                if issue_code_summary:
                    warnings.append(f"Export gate issue codes: {issue_code_summary}")

        return is_valid, errors, warnings

    def get_project_info(self, project_path: str) -> dict[str, object]:
        shared = get_project_info_common(project_path)
        project_dir = Path(project_path)
        runtime_snapshot = self._build_project_runtime_snapshot(
            project_dir,
            expected_format=shared.get("format"),
        )
        bootstrap_status = runtime_snapshot["bootstrap_status"]
        export_gate = runtime_snapshot["export_gate"]
        execution_trace = execution_trace_summary(project_dir)
        return {
            "name": shared.get("name", Path(project_path).name),
            "path": shared.get("path", str(project_path)),
            "exists": shared.get("exists", False),
            "svg_count": shared.get("svg_count", 0),
            "has_spec": shared.get("has_spec", False),
            "has_source": shared.get("has_source", False),
            "source_count": shared.get("source_count", 0),
            "canvas_format": shared.get("format_name", "Unknown"),
            "create_date": shared.get("date_formatted", "Unknown"),
            "has_agent_bootstrap": bool(runtime_snapshot["has_agent_bootstrap"]),
            "bootstrap_status": bootstrap_status,
            "export_gate_available": bool(export_gate.get("available", False)),
            "export_gate_ok": bool(export_gate.get("ok", False)) if export_gate.get("available") else False,
            "export_gate_status": export_gate.get("status", "pending"),
            "export_gate_source": export_gate.get("source_dir", ""),
            "export_gate_working_source": export_gate.get("working_source_dir", ""),
            "export_gate_path": export_gate.get("path", ""),
            "export_gate_blocking_reasons": export_gate.get("blocking_reasons", []),
            "export_gate_blocking_reason_count": export_gate.get("blocking_reason_count", 0),
            "export_gate_fit_issue_count": export_gate.get("fit_issue_count", 0),
            "export_gate_failed_file_count": export_gate.get("quality_failed_file_count", 0),
            "export_gate_blocking_file_count": export_gate.get("quality_blocking_file_count", 0),
            "export_gate_issue_codes": export_gate.get("issue_codes", {}),
            "export_gate_issue_code_summary": runtime_snapshot["export_gate_issue_code_summary"],
            "export_gate_issues_preview": export_gate.get("issues_preview", []),
            "export_gate_fit_issues_preview": export_gate.get("fit_issues_preview", []),
            "export_gate_complex_page_model_errors": export_gate.get("complex_page_model_errors", []),
            "execution_trace_available": bool(execution_trace.get("trace_file_count", 0)),
            "execution_trace_file_count": execution_trace.get("trace_file_count", 0),
            "execution_trace_auto_repair_pages": execution_trace.get("pages_with_auto_repair", []),
            "execution_trace_progression_reframe_pages": execution_trace.get("pages_with_progression_reframe", []),
            "execution_trace_argument_rewrite_pages": execution_trace.get("pages_with_semantic_argument_rewrite", []),
            "execution_trace_failed_after_repair_pages": execution_trace.get("pages_still_failed_after_repair", []),
            "execution_trace_event_counts": execution_trace.get("event_type_counts", {}),
            "execution_trace_warnings": execution_trace.get("warnings", []),
        }


def print_usage() -> None:
    """Print CLI usage information from the module docstring."""
    print(__doc__)


def parse_init_args(argv: list[str]) -> tuple[str, str, str]:
    """Parse arguments for the `init` subcommand."""
    if len(argv) < 3:
        raise ValueError("Project name is required")

    project_name = argv[2]
    canvas_format = "ppt169"
    base_dir = "projects"

    i = 3
    while i < len(argv):
        if argv[i] == "--format" and i + 1 < len(argv):
            canvas_format = argv[i + 1]
            i += 2
        elif argv[i] == "--dir" and i + 1 < len(argv):
            base_dir = argv[i + 1]
            i += 2
        else:
            i += 1

    return project_name, canvas_format, base_dir


def parse_import_args(argv: list[str]) -> tuple[str, list[str], bool]:
    """Parse arguments for the `import-sources` subcommand."""
    if len(argv) < 4:
        raise ValueError("Project path and at least one source are required")

    project_path = argv[2]
    move = False
    sources: list[str] = []

    for arg in argv[3:]:
        if arg == "--move":
            move = True
        else:
            sources.append(arg)

    return project_path, sources, move


def parse_bootstrap_args(argv: list[str]) -> dict[str, str]:
    """Parse arguments for the `bootstrap-agent` subcommand."""
    if len(argv) >= 3 and argv[2] in {"-h", "--help"}:
        raise ValueError(
            "Usage: python3 scripts/project_manager.py bootstrap-agent <project_path> "
            "--industry <industry> --scenario <scenario> --audience <audience> --goal <goal> "
            "[--project-name <name>] [--template <template>] [--style <style>] "
            "[--priorities a,b,c] [--materials x,y,z] [--constraints p,q,r] [--answers-json <answers.json>] [--lang 中文]"
        )
    if len(argv) < 3:
        raise ValueError("Project path is required")

    project_path = argv[2]
    result: dict[str, str] = {
        "project_path": project_path,
        "project_name": "",
        "industry": "",
        "scenario": "",
        "audience": "",
        "goal": "",
        "priorities": "",
        "template": "",
        "style": "",
        "materials": "",
        "constraints": "",
        "answers_json": "",
        "language": "中文",
    }

    required = {"--industry": "industry", "--scenario": "scenario", "--audience": "audience", "--goal": "goal"}
    optional = {
        "--project-name": "project_name",
        "--priorities": "priorities",
        "--template": "template",
        "--style": "style",
        "--materials": "materials",
        "--constraints": "constraints",
        "--answers-json": "answers_json",
        "--lang": "language",
    }

    i = 3
    while i < len(argv):
        arg = argv[i]
        if arg in required and i + 1 < len(argv):
            result[required[arg]] = argv[i + 1]
            i += 2
        elif arg in optional and i + 1 < len(argv):
            result[optional[arg]] = argv[i + 1]
            i += 2
        else:
            raise ValueError(f"Unknown or incomplete bootstrap-agent argument: {arg}")

    missing = [flag for flag, key in required.items() if not result[key]]
    if missing:
        raise ValueError(f"Missing required bootstrap-agent arguments: {', '.join(missing)}")

    return result


def main() -> None:
    """Run the CLI entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]
    manager = ProjectManager()

    try:
        if command == "init":
            project_name, canvas_format, base_dir = parse_init_args(sys.argv)
            project_path = manager.init_project(project_name, canvas_format, base_dir=base_dir)
            print(f"[OK] Project initialized: {project_path}")
            print("Next:")
            print("1. Run bootstrap-agent to generate project_brief and storyline")
            print("2. Put source files into sources/ (or use import-sources)")
            print("3. Save your design spec to the project root")
            print("4. Generate SVG files into svg_output/")
            return

        if command == "import-sources":
            project_path, sources, move = parse_import_args(sys.argv)
            summary = manager.import_sources(project_path, sources, move=move)
            print(f"[OK] Imported sources into: {project_path}")
            if summary["archived"]:
                print("\nArchived originals / URL records:")
                for item in summary["archived"]:
                    print(f"  - {item}")
            if summary["markdown"]:
                print("\nNormalized markdown:")
                for item in summary["markdown"]:
                    print(f"  - {item}")
            if summary["assets"]:
                print("\nImported asset directories:")
                for item in summary["assets"]:
                    print(f"  - {item}")
            if summary["notes"]:
                print("\nNotes:")
                for item in summary["notes"]:
                    print(f"  - {item}")
            if summary["skipped"]:
                print("\nSkipped:")
                for item in summary["skipped"]:
                    print(f"  - {item}")
            return

        if command == "bootstrap-agent":
            if len(sys.argv) >= 3 and sys.argv[2] in {"-h", "--help"}:
                print(
                    "Usage: python3 scripts/project_manager.py bootstrap-agent <project_path> "
                    "--industry <industry> --scenario <scenario> --audience <audience> --goal <goal> "
                    "[--project-name <name>] [--template <template>] [--style <style>] "
                    "[--priorities a,b,c] [--materials x,y,z] [--constraints p,q,r] [--answers-json <answers.json>] [--lang 中文]"
                )
                return
            options = parse_bootstrap_args(sys.argv)
            outputs = manager.bootstrap_agent(
                options["project_path"],
                project_name=options["project_name"] or None,
                industry=options["industry"],
                scenario=options["scenario"],
                audience=options["audience"],
                goal=options["goal"],
                priorities=options["priorities"],
                template=options["template"],
                style=options["style"],
                materials=options["materials"],
                constraints=options["constraints"],
                answers_json=options["answers_json"],
                language=options["language"],
            )
            print(f"[OK] Agent bootstrap completed: {options['project_path']}")
            print("Generated:")
            for label, path in outputs.items():
                print(f"  - {label}: {path}")
            print("Next:")
            print("1. Review project_brief and template/domain recommendation")
            print("2. Confirm template choice and storyline")
            print("3. Continue with source import / Strategist / Executor")
            return

        if command == "validate":
            if len(sys.argv) < 3:
                raise ValueError("Project path is required")

            project_path = sys.argv[2]
            info = manager.get_project_info(project_path)
            is_valid, errors, warnings = manager.validate_project(project_path)
            export_gate_available = bool(info.get("export_gate_available"))
            export_gate_ok = bool(info.get("export_gate_ok"))

            print(f"\nProject validation: {project_path}")
            print("=" * 60)

            if errors:
                print("\n[ERROR]")
                for error in errors:
                    print(f"  - {error}")

            if warnings:
                print("\n[WARN]")
                for warning in warnings:
                    print(f"  - {warning}")

            if export_gate_available:
                print("\n[EXPORT GATE]")
                print(f"  - Source: {info['export_gate_source']}")
                if info.get("export_gate_working_source") and info["export_gate_working_source"] != info["export_gate_source"]:
                    print(f"  - Working source: {info['export_gate_working_source']}")
                print(f"  - Status: {'PASS' if export_gate_ok else 'BLOCK'}")
                if not export_gate_ok:
                    for reason in info["export_gate_blocking_reasons"]:
                        print(f"  - {reason}")
                    if info["export_gate_issue_code_summary"]:
                        print(f"  - Issue codes: {info['export_gate_issue_code_summary']}")
            else:
                print("\n[EXPORT GATE]")
                print("  - Status: PENDING (no SVG pages available for gate validation yet)")

            if not is_valid:
                print("\n[ERROR] Project structure is invalid.")
                sys.exit(1)
            if export_gate_available and not export_gate_ok:
                print("\n[BLOCK] Project structure is valid, but export gate failed. Fix blocking QA issues before PPT export.")
                sys.exit(1)
            if is_valid and not warnings:
                print("\n[OK] Project structure is complete.")
            else:
                print("\n[OK] Project structure is valid, with warnings.")
            return

        if command == "info":
            if len(sys.argv) < 3:
                raise ValueError("Project path is required")

            project_path = sys.argv[2]
            info = manager.get_project_info(project_path)

            print(f"\nProject info: {info['name']}")
            print("=" * 60)
            print(f"Path: {info['path']}")
            print(f"Exists: {'Yes' if info['exists'] else 'No'}")
            print(f"SVG files: {info['svg_count']}")
            print(f"Design spec: {'Yes' if info['has_spec'] else 'No'}")
            print(f"Source materials: {'Yes' if info['has_source'] else 'No'}")
            print(f"Source count: {info['source_count']}")
            print(f"Canvas format: {info['canvas_format']}")
            print(f"Created: {info['create_date']}")
            print(f"Agent bootstrap: {'Yes' if info['has_agent_bootstrap'] else 'No'}")
            if info["export_gate_available"]:
                print(f"Export gate: {'Yes' if info['export_gate_ok'] else 'No'}")
                print(f"Export gate source: {info['export_gate_source']}")
                if info.get("export_gate_working_source") and info["export_gate_working_source"] != info["export_gate_source"]:
                    print(f"Export gate working source: {info['export_gate_working_source']}")
                if not info["export_gate_ok"]:
                    print("Export gate blocking reasons:")
                    for reason in info["export_gate_blocking_reasons"]:
                        print(f"  - {reason}")
                    if info["export_gate_issue_code_summary"]:
                        print(f"Export gate issue codes: {info['export_gate_issue_code_summary']}")
            else:
                print("Export gate: Pending (no SVG pages available yet)")
            print("Bootstrap files:")
            for name, exists in info["bootstrap_status"].items():
                print(f"  - {name}: {'Yes' if exists else 'No'}")
            return

        raise ValueError(f"Unknown command: {command}")
    except Exception as exc:
        print(f"[ERROR] {exc}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
