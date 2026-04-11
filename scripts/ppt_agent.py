#!/usr/bin/env python3
"""Unified PPT Agent entry for ppt-master.

Usage:
    python3 scripts/ppt_agent.py new <project_name> [--industry <industry>] [--scenario <scenario>] [--audience <audience>] [--goal <goal>] [--format ppt169] [--dir projects] [--source <file_or_url> ...] [--answers-json <plan_answers.json>] [--template <template>] [--style <style>] [--priorities a,b,c] [--lang 中文] [--keep-source]
    python3 scripts/ppt_agent.py plan <project_path> [--industry <industry>] [--scenario <scenario>] [--audience <audience>] [--goal <goal>] [--source <file_or_url> ...] [--answers-json <plan_answers.json>] [--template <template>] [--style <style>] [--priorities a,b,c] [--lang 中文] [--keep-source]
    python3 scripts/ppt_agent.py produce <project_path>
    python3 scripts/ppt_agent.py execute <project_path> [--refresh-design-spec] [--auto-repair]
    python3 scripts/ppt_agent.py run <project_path> [--refresh-design-spec]
    python3 scripts/ppt_agent.py svg-exec <init|sync|next|render|complete|mark|summary> <project_path> [--force] [--page <page>] [--status <status>] [--note <note>] [--max-auto-repair-rounds <n>] [--no-auto-repair]
    python3 scripts/ppt_agent.py learn <pptx> [<pptx> ...] [--domain general] [--case-name <name>] [--copy-source] [--distill] [-o <output.md>]
    python3 scripts/ppt_agent.py improve <project_path> [--findings <findings.md>] [-o <output.md>]
    python3 scripts/ppt_agent.py status <project_path>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from auto_repair_execution_artifacts import repair_execution_artifacts
    from build_production_packet import build_production_packet
    from build_project_design_spec import build_project_design_spec
    from build_svg_execution_pack import build_svg_execution_pack
    from check_complex_page_model import validate as validate_complex_page_model
    from design_spec_validator import DesignSpecValidator
    from project_manager import ProjectManager
    from plan_interview import prepare_plan_packet
    from svg_execution_runner import load_or_init_state as load_svg_execution_state
    from svg_execution_runner import save_state_bundle as save_svg_execution_bundle
    from svg_execution_runner import sync_state_with_files as sync_svg_execution_state
except ImportError:
    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from auto_repair_execution_artifacts import repair_execution_artifacts  # type: ignore
    from build_production_packet import build_production_packet  # type: ignore
    from build_project_design_spec import build_project_design_spec  # type: ignore
    from build_svg_execution_pack import build_svg_execution_pack  # type: ignore
    from check_complex_page_model import validate as validate_complex_page_model  # type: ignore
    from design_spec_validator import DesignSpecValidator  # type: ignore
    from project_manager import ProjectManager  # type: ignore
    from plan_interview import prepare_plan_packet  # type: ignore
    from svg_execution_runner import load_or_init_state as load_svg_execution_state  # type: ignore
    from svg_execution_runner import save_state_bundle as save_svg_execution_bundle  # type: ignore
    from svg_execution_runner import sync_state_with_files as sync_svg_execution_state  # type: ignore


TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
CASE_LIBRARY = ROOT / "case_library"


def slugify(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", value.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "item"


def run_python_script(script_name: str, extra_args: list[str]) -> None:
    command = [sys.executable, str(TOOLS_DIR / script_name), *extra_args]
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"{script_name} failed")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hash_path(path: Path, digest: "hashlib._Hash") -> None:
    if not path.exists():
        digest.update(f"MISSING:{path.as_posix()}".encode("utf-8"))
        return
    if path.is_file():
        digest.update(f"FILE:{path.as_posix()}".encode("utf-8"))
        digest.update(path.read_bytes())
        return
    digest.update(f"DIR:{path.as_posix()}".encode("utf-8"))
    for child in sorted(path.rglob("*")):
        relative = child.relative_to(path).as_posix()
        digest.update(relative.encode("utf-8"))
        if child.is_file():
            digest.update(child.read_bytes())


def hash_paths(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        hash_path(path, digest)
    return digest.hexdigest()


def hash_stage_inputs(paths: list[Path], extra_values: list[str] | None = None) -> str:
    digest = hashlib.sha256()
    for path in paths:
        hash_path(path, digest)
    for value in extra_values or []:
        digest.update(f"EXTRA:{value}".encode("utf-8"))
    return digest.hexdigest()


def fingerprint_path(project_path: Path) -> Path:
    return project_path / "notes" / "pipeline_fingerprints.json"


def load_pipeline_fingerprints(project_path: Path) -> dict[str, object]:
    data = read_json(fingerprint_path(project_path))
    stages = data.get("stages")
    if not isinstance(stages, dict):
        data["stages"] = {}
    return data


def save_pipeline_fingerprints(project_path: Path, data: dict[str, object]) -> None:
    data["updated_at"] = now_iso()
    write_json(fingerprint_path(project_path), data)


def ensure_serializable(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): ensure_serializable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [ensure_serializable(item) for item in value]
    return value


def stage_output_hash(paths: list[Path]) -> str:
    return hash_paths(paths)


def stage_is_fresh(
    project_path: Path,
    stage_name: str,
    *,
    input_paths: list[Path],
    output_paths: list[Path],
    extra_values: list[str] | None = None,
    force: bool = False,
) -> tuple[bool, str, dict[str, object]]:
    fingerprints = load_pipeline_fingerprints(project_path)
    stages = fingerprints.setdefault("stages", {})
    stage_data = stages.get(stage_name) if isinstance(stages, dict) else {}
    if force or not isinstance(stage_data, dict):
        return False, hash_stage_inputs(input_paths, extra_values), {}
    input_hash = hash_stage_inputs(input_paths, extra_values)
    output_hash = stage_output_hash(output_paths)
    if stage_data.get("inputs_hash") != input_hash:
        return False, input_hash, stage_data
    if stage_data.get("outputs_hash") != output_hash:
        return False, input_hash, stage_data
    return True, input_hash, stage_data


def save_stage_fingerprint(
    project_path: Path,
    stage_name: str,
    *,
    input_hash: str,
    output_paths: list[Path],
    result: dict[str, object],
) -> None:
    fingerprints = load_pipeline_fingerprints(project_path)
    stages = fingerprints.setdefault("stages", {})
    assert isinstance(stages, dict)
    stages[stage_name] = {
        "inputs_hash": input_hash,
        "outputs_hash": stage_output_hash(output_paths),
        "generated_at": now_iso(),
        "result": ensure_serializable(result),
    }
    save_pipeline_fingerprints(project_path, fingerprints)


def stage_status_payload(
    stage_name: str,
    *,
    cache_hit: bool,
    input_hash: str,
    stage_data: dict[str, object] | None = None,
    forced: bool = False,
) -> dict[str, object]:
    payload = {
        "stage": stage_name,
        "status": "forced_rebuild" if forced else ("cache_hit" if cache_hit else "cache_miss"),
        "cache_hit": cache_hit,
        "inputs_hash": input_hash[:12],
    }
    existing = stage_data or {}
    generated_at = existing.get("generated_at")
    if cache_hit and generated_at:
        payload["generated_at"] = generated_at
    return payload


def print_stage_statuses(stage_statuses: dict[str, object]) -> None:
    if not stage_statuses:
        return
    print("\n缓存观测:")
    for stage_name in ("produce_artifacts", "design_spec_validation", "svg_execution_pack"):
        entry = stage_statuses.get(stage_name)
        if not isinstance(entry, dict):
            continue
        generated_at = str(entry.get("generated_at") or "")
        extra = f", generated_at={generated_at}" if generated_at else ""
        print(
            f"  - {stage_name}: {entry.get('status', 'unknown')}"
            f" (inputs={entry.get('inputs_hash', 'n/a')}{extra})"
        )


def print_import_summary(summary: dict[str, list[str]]) -> None:
    section_titles = {
        "archived": "归档源文件",
        "markdown": "标准化 Markdown",
        "assets": "导入素材目录",
        "notes": "说明",
        "skipped": "跳过项",
    }
    for key in ("archived", "markdown", "assets", "notes", "skipped"):
        items = summary.get(key) or []
        if not items:
            continue
        print(f"\n{section_titles[key]}:")
        for item in items:
            print(f"  - {item}")


def add_plan_arguments(parser: argparse.ArgumentParser, include_format: bool = False) -> None:
    if include_format:
        parser.add_argument("--format", default="ppt169", help="画布格式，默认 ppt169")
        parser.add_argument("--dir", default="projects", help="项目根目录，默认 projects")
    parser.add_argument("--industry", default="", help="行业，例如 安服 / 金融 / 政务")
    parser.add_argument("--scenario", default="", help="场景，例如 攻防演练复盘")
    parser.add_argument("--audience", default="", help="受众，例如 客户管理层与技术团队")
    parser.add_argument("--goal", default="", help="本次 PPT 核心目标")
    parser.add_argument("--priorities", default="", help="展示重点，逗号分隔")
    parser.add_argument("--template", default="", help="指定模板 ID 或模板名")
    parser.add_argument("--style", default="", help="风格偏好")
    parser.add_argument("--answers-json", default="", help="已有的 /plan 结构化答案文件")
    parser.add_argument("--lang", default="中文", help="输出语言，默认 中文")
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="源文件或 URL，可重复传入多次",
    )
    parser.add_argument(
        "--keep-source",
        action="store_true",
        help="保留原始源文件；默认会把源文件移动到项目 sources/ 做统一归档",
    )


def build_plan_cli_answers(args: argparse.Namespace, project_name: str = "") -> dict[str, object]:
    source_items = [str(item) for item in (args.source or [])]
    return {
        "project_name": project_name,
        "industry": args.industry,
        "scenario": args.scenario,
        "audience": args.audience,
        "goal": args.goal,
        "priorities": args.priorities,
        "template": args.template,
        "style": args.style,
        "language": args.lang,
        "format": getattr(args, "format", "ppt169"),
        "source_docs": source_items,
    }


def print_plan_gap(readiness: dict[str, object], paths: dict[str, str]) -> None:
    print("\n[WAIT] 当前还不能稳定进入正式 brief，我已先生成多轮 /plan 收集包。")
    print("请优先查看:")
    print(f"  - 结构化答案: {paths['answers']}")
    print(f"  - 追问清单: {paths['questions']}")
    print(f"  - 就绪度报告: {paths['readiness']}")
    if "agent_state" in paths:
        print(f"  - Agent 状态: {paths['agent_state']}")
    if "next_turn" in paths:
        print(f"  - 下一轮话术: {paths['next_turn']}")
    if "dialogue" in paths:
        print(f"  - 轮次记录: {paths['dialogue']}")
    if "session_status" in paths:
        print(f"  - 会话状态: {paths['session_status']}")

    conversation_stage = readiness.get("conversation_stage")
    round_objective = readiness.get("round_objective")
    domain_context = readiness.get("domain_context") or {}
    if conversation_stage or round_objective:
        print("\n当前轮次:")
        if conversation_stage:
            print(f"  - 阶段: {conversation_stage}")
        if round_objective:
            print(f"  - 目标: {round_objective}")
        if domain_context.get("domain_label"):
            print(f"  - 识别领域: {domain_context['domain_label']}")
        if domain_context.get("template_hint"):
            print(f"  - 模板倾向建议: {domain_context['template_hint']}")

    next_questions = readiness.get("next_questions") or []
    if next_questions:
        print("\n建议这一轮最多先确认 3 个问题:")
        for index, item in enumerate(next_questions, start=1):
            print(f"{index}. [{item['group']}] {item['question']}")
            reason = item.get("reason")
            suggestions = item.get("suggestions") or []
            if reason:
                print(f"   - 原因: {reason}")
            if suggestions:
                print(f"   - 可给用户的建议方向: {' / '.join(suggestions)}")
    print("\n补齐后，可直接再次执行当前命令，或传入 `--answers-json` 继续。")


def build_export_gate_markdown_lines(info: dict[str, object], heading: str = "## 当前导出门禁快照") -> list[str]:
    lines = [heading]
    if info.get("export_gate_available"):
        export_gate_ok = bool(info.get("export_gate_ok"))
        working_source = info.get("export_gate_working_source")
        lines.extend(
            [
                f"- 当前状态：{'通过' if export_gate_ok else '未通过'}",
                f"- 检查源：`{info.get('export_gate_source')}`",
                "- 说明：这是基于当前项目内现有 SVG 快照的门禁结果；真正导出前，系统仍会再次执行同一套 gate。",
            ]
        )
        if working_source and working_source != info.get("export_gate_source"):
            lines.append(f"- 当前工作快照：`{working_source}`")
        if not export_gate_ok:
            for reason in info.get("export_gate_blocking_reasons", []):
                lines.append(f"- BLOCK: {reason}")
            if info.get("export_gate_issue_code_summary"):
                lines.append(f"- issue_codes: {info['export_gate_issue_code_summary']}")
    else:
        lines.extend(
            [
                "- 当前状态：待执行",
                "- 说明：当前还没有可校验的 SVG 快照；完成 SVG 生成与 finalize 后，再看同一套 export gate。",
            ]
        )
    return lines


def build_execution_trace_markdown_lines(info: dict[str, object], heading: str = "## 自动修复轨迹快照") -> list[str]:
    lines = [heading]
    trace_count = int(info.get("execution_trace_file_count", 0) or 0)
    if trace_count <= 0:
        lines.extend(
            [
                "- 当前状态：暂无轨迹",
                "- 说明：还没有 `notes/page_execution/*.json`，说明当前尚未通过独立执行器沉淀自动修复事件。",
            ]
        )
        return lines

    lines.append(f"- 轨迹文件数：{trace_count}")
    auto_repair_pages = info.get("execution_trace_auto_repair_pages") or []
    progression_pages = info.get("execution_trace_progression_reframe_pages") or []
    argument_pages = info.get("execution_trace_argument_rewrite_pages") or []
    failed_pages = info.get("execution_trace_failed_after_repair_pages") or []
    event_counts = info.get("execution_trace_event_counts") or {}

    if auto_repair_pages:
        lines.append(f"- 自动修复页：{', '.join(str(item) for item in auto_repair_pages[:8])}")
    if progression_pages:
        lines.append(f"- 复杂页换骨架：{', '.join(str(item) for item in progression_pages[:8])}")
    if argument_pages:
        lines.append(f"- 论证重写页：{', '.join(str(item) for item in argument_pages[:8])}")
    if failed_pages:
        lines.append(f"- 自动修复后仍失败：{', '.join(str(item) for item in failed_pages[:8])}")
    if event_counts:
        lines.append(
            "- 事件计数："
            + "，".join(f"{key}={value}" for key, value in sorted(event_counts.items()))
        )
    for warning in info.get("execution_trace_warnings", [])[:4]:
        lines.append(f"- warning: {warning}")
    return lines


def produce_stage_inputs(project_path: Path) -> list[Path]:
    paths = [
        project_path / "project_brief.md",
        project_path / "notes" / "storyline.md",
        project_path / "notes" / "page_outline.md",
        project_path / "notes" / "template_domain_recommendation.md",
        project_path / "sources",
        TOOLS_DIR / "build_production_packet.py",
    ]
    return paths


def validation_stage_inputs(project_path: Path) -> list[Path]:
    return [
        project_path / "project_brief.md",
        project_path / "notes" / "storyline.md",
        project_path / "notes" / "page_outline.md",
        project_path / "notes" / "complex_page_models.md",
        project_path / "design_spec.md",
        TOOLS_DIR / "build_project_design_spec.py",
        TOOLS_DIR / "design_spec_validator.py",
        TOOLS_DIR / "check_complex_page_model.py",
        TOOLS_DIR / "auto_repair_execution_artifacts.py",
    ]


def svg_pack_stage_inputs(project_path: Path) -> list[Path]:
    return [
        project_path / "design_spec.md",
        project_path / "notes" / "complex_page_models.md",
        project_path / "notes" / "execution_readiness.md",
        project_path / "notes" / "execution_runbook.md",
        project_path / "notes" / "auto_repair_report.md",
        TOOLS_DIR / "build_svg_execution_pack.py",
        TOOLS_DIR / "svg_execution_runner.py",
    ]


def expected_svg_pack_outputs(project_path: Path) -> dict[str, str]:
    notes_dir = project_path / "notes"
    return {
        "queue": str(notes_dir / "svg_execution_queue.md"),
        "queue_machine": str(notes_dir / "svg_execution_queue.machine.json"),
        "status": str(notes_dir / "svg_generation_status.md"),
        "postprocess": str(notes_dir / "svg_postprocess_plan.md"),
        "contracts": str(notes_dir / "page_execution_contracts.json"),
        "page_briefs": str(notes_dir / "page_briefs"),
        "page_context_min": str(notes_dir / "page_context_min"),
        "total_md": str(notes_dir / "total.md"),
    }


def run_bundle_output_paths(
    project_path: Path,
    svg_pack: dict[str, str],
) -> list[Path]:
    notes_dir = project_path / "notes"
    return [
        Path(svg_pack["queue"]),
        Path(svg_pack.get("queue_machine", notes_dir / "svg_execution_queue.machine.json")),
        Path(svg_pack["status"]),
        Path(svg_pack["postprocess"]),
        Path(svg_pack["contracts"]),
        Path(svg_pack["page_briefs"]),
        Path(svg_pack.get("page_context_min", notes_dir / "page_context_min")),
        Path(svg_pack.get("total_md", notes_dir / "total.md")),
        notes_dir / "strategist_handoff.md",
        notes_dir / "executor_handoff.md",
        notes_dir / "agent_run_status.md",
        notes_dir / "svg_execution_state.json",
        notes_dir / "svg_current_task.md",
        notes_dir / "svg_current_prompt.md",
        notes_dir / "svg_current_context_pack.md",
        notes_dir / "svg_current_review.md",
        notes_dir / "svg_execution_log.md",
    ]


def build_run_bundle(
    project_path: Path,
    *,
    outputs: dict[str, str],
    svg_pack: dict[str, str] | None,
    design_spec_path: Path,
    execution_readiness_path: Path,
    execution_runbook_path: Path,
    auto_repair_report_path: Path | None,
    export_gate_info: dict[str, object],
    ready: bool,
    force_state: bool,
) -> dict[str, Path]:
    svg_pack = dict(svg_pack or build_svg_execution_pack(project_path))
    svg_execution_queue_path = Path(svg_pack["queue"])
    svg_execution_queue_machine_path = Path(svg_pack.get("queue_machine", project_path / "notes" / "svg_execution_queue.machine.json"))
    svg_generation_status_path = Path(svg_pack["status"])
    svg_postprocess_plan_path = Path(svg_pack["postprocess"])
    svg_contracts_path = Path(svg_pack["contracts"])
    page_briefs_dir = Path(svg_pack["page_briefs"])
    svg_state, svg_state_paths = load_svg_execution_state(project_path, force=force_state)
    svg_state = sync_svg_execution_state(svg_state, project_path)
    save_svg_execution_bundle(svg_state, project_path, svg_state_paths)
    svg_execution_state_path = svg_state_paths["state"]
    svg_current_task_path = svg_state_paths["current_task"]
    svg_current_prompt_path = svg_state_paths["current_prompt"]
    svg_current_context_path = svg_state_paths["current_context"]
    svg_current_review_path = svg_state_paths["current_review"]
    svg_execution_log_path = svg_state_paths["log"]

    strategist_handoff_path = project_path / "notes" / "strategist_handoff.md"
    executor_handoff_path = project_path / "notes" / "executor_handoff.md"
    run_status_path = project_path / "notes" / "agent_run_status.md"

    write_text(
        strategist_handoff_path,
        build_strategist_handoff_text(project_path, outputs, design_spec_path, auto_repair_report_path),
    )
    write_text(
        executor_handoff_path,
        build_executor_handoff_text(project_path, outputs, design_spec_path, svg_pack, auto_repair_report_path),
    )
    write_text(
        run_status_path,
        build_run_status_text(
            project_path,
            design_spec_path,
            execution_readiness_path,
            execution_runbook_path,
            strategist_handoff_path,
            executor_handoff_path,
            svg_execution_queue_path,
            svg_execution_queue_machine_path,
            svg_generation_status_path,
            svg_execution_state_path,
            svg_current_task_path,
            svg_current_prompt_path,
            svg_current_context_path,
            svg_current_review_path,
            svg_execution_log_path,
            svg_postprocess_plan_path,
            page_briefs_dir,
            auto_repair_report_path,
            ready,
            export_gate_info,
        ),
    )
    return {
        "svg_execution_queue_path": svg_execution_queue_path,
        "svg_execution_queue_machine_path": svg_execution_queue_machine_path,
        "svg_generation_status_path": svg_generation_status_path,
        "svg_postprocess_plan_path": svg_postprocess_plan_path,
        "svg_contracts_path": svg_contracts_path,
        "page_briefs_dir": page_briefs_dir,
        "svg_execution_state_path": svg_execution_state_path,
        "svg_current_task_path": svg_current_task_path,
        "svg_current_prompt_path": svg_current_prompt_path,
        "svg_current_context_path": svg_current_context_path,
        "svg_current_review_path": svg_current_review_path,
        "svg_execution_log_path": svg_execution_log_path,
        "strategist_handoff_path": strategist_handoff_path,
        "executor_handoff_path": executor_handoff_path,
        "run_status_path": run_status_path,
        "page_context_dir": Path(svg_pack.get("page_context_min", project_path / "notes" / "page_context_min")),
    }


def print_export_gate_snapshot(info: dict[str, object], title: str = "当前导出门禁快照:") -> None:
    print(f"\n{title}")
    if info.get("export_gate_available"):
        export_gate_ok = bool(info.get("export_gate_ok"))
        print(f"  - 状态：{'通过' if export_gate_ok else '未通过'}")
        print(f"  - 检查源：{info['export_gate_source']}")
        print("  - 说明：这是当前项目内现有 SVG 快照的门禁状态；真正导出前仍会再跑同一套 gate。")
        if info.get("export_gate_working_source") and info.get("export_gate_working_source") != info.get("export_gate_source"):
            print(f"  - 当前工作快照：{info['export_gate_working_source']}")
        if not export_gate_ok:
            for reason in info.get("export_gate_blocking_reasons", []):
                print(f"  - {reason}")
            if info.get("export_gate_issue_code_summary"):
                print(f"  - 问题类型：{info['export_gate_issue_code_summary']}")
    else:
        print("  - 状态：待执行")
        print("  - 说明：当前还没有可校验的 SVG 快照；完成 SVG 生成与 finalize 后，再看同一套 export gate。")


def print_execution_trace_snapshot(info: dict[str, object], title: str = "自动修复轨迹快照:") -> None:
    print(f"\n{title}")
    trace_count = int(info.get("execution_trace_file_count", 0) or 0)
    if trace_count <= 0:
        print("  - 状态：暂无轨迹")
        print("  - 说明：还没有 `notes/page_execution/*.json`，当前还无法追踪自动修复事件。")
        return

    print(f"  - 轨迹文件数：{trace_count}")
    auto_repair_pages = info.get("execution_trace_auto_repair_pages") or []
    progression_pages = info.get("execution_trace_progression_reframe_pages") or []
    argument_pages = info.get("execution_trace_argument_rewrite_pages") or []
    failed_pages = info.get("execution_trace_failed_after_repair_pages") or []
    event_counts = info.get("execution_trace_event_counts") or {}
    if auto_repair_pages:
        print(f"  - 自动修复页：{', '.join(str(item) for item in auto_repair_pages[:8])}")
    if progression_pages:
        print(f"  - 复杂页换骨架：{', '.join(str(item) for item in progression_pages[:8])}")
    if argument_pages:
        print(f"  - 论证重写页：{', '.join(str(item) for item in argument_pages[:8])}")
    if failed_pages:
        print(f"  - 自动修复后仍失败：{', '.join(str(item) for item in failed_pages[:8])}")
    if event_counts:
        print("  - 事件计数：" + "，".join(f"{key}={value}" for key, value in sorted(event_counts.items())))
    for warning in info.get("execution_trace_warnings", [])[:4]:
        print(f"  - warning: {warning}")


def rel_ref(project_path: Path, path: Path | str) -> str:
    value = Path(path) if not isinstance(path, Path) else path
    try:
        return value.resolve().relative_to(project_path.resolve()).as_posix()
    except Exception:
        return str(path)


def run_plan_stage(
    manager: ProjectManager,
    project_path: str,
    *,
    project_name: str = "",
    args: argparse.Namespace,
) -> None:
    cli_answers = build_plan_cli_answers(args, project_name=project_name)
    merged_answers, readiness, packet_paths = prepare_plan_packet(
        project_path,
        cli_answers,
        answers_json=args.answers_json or None,
    )
    if not readiness["ready_for_brief"]:
        print_plan_gap(readiness, packet_paths)
        return

    outputs = manager.bootstrap_agent(
        project_path,
        project_name=project_name or None,
        industry=str(merged_answers.get("industry", "")),
        scenario=str(merged_answers.get("scenario", "")),
        audience=str(merged_answers.get("audience", "")),
        goal=str(merged_answers.get("goal", "")),
        priorities=",".join(merged_answers.get("priorities", [])),
        template=str(merged_answers.get("template", "")),
        style=str(merged_answers.get("style", "")),
        answers_json=packet_paths["answers"],
        language=str(merged_answers.get("language", args.lang)),
    )

    print(f"\n[OK] 已完成 /plan：{project_path}")
    print("已生成规划产物:")
    for label, path in outputs.items():
        print(f"  - {label}: {path}")
    print("\n同时已保留 /plan 收集包:")
    for label, path in packet_paths.items():
        print(f"  - {label}: {path}")


def command_new(args: argparse.Namespace) -> None:
    manager = ProjectManager(base_dir=args.dir)
    project_path = manager.init_project(args.project_name, args.format, base_dir=args.dir)

    if args.source:
        summary = manager.import_sources(project_path, args.source, move=not args.keep_source)
        print_import_summary(summary)

    run_plan_stage(manager, project_path, project_name=args.project_name, args=args)


def command_plan(args: argparse.Namespace) -> None:
    manager = ProjectManager()
    project_path = str(Path(args.project_path).expanduser().resolve())

    if args.source:
        summary = manager.import_sources(project_path, args.source, move=not args.keep_source)
        print_import_summary(summary)

    run_plan_stage(manager, project_path, args=args)


def command_learn(args: argparse.Namespace) -> None:
    domain = slugify(args.domain)
    case_dirs: list[Path] = []

    if args.case_name and len(args.pptx) != 1:
        raise SystemExit("--case-name 只能在单个 PPT 案例入库时使用")

    for index, value in enumerate(args.pptx):
        pptx_path = Path(value).expanduser().resolve()
        if not pptx_path.exists():
            raise SystemExit(f"PPTX not found: {pptx_path}")

        case_name = args.case_name if index == 0 and args.case_name else pptx_path.stem
        run_args = [str(pptx_path), "--domain", domain]
        if index == 0 and args.case_name:
            run_args.extend(["--case-name", args.case_name])
        if args.copy_source:
            run_args.append("--copy-source")
        run_python_script("ingest_reference_ppt.py", run_args)
        case_dirs.append(CASE_LIBRARY / domain / slugify(case_name))

    should_distill = args.distill or len(case_dirs) > 1
    if should_distill:
        output = Path(args.output).expanduser().resolve() if args.output else CASE_LIBRARY / domain / "distilled_patterns.md"
        distill_args = [str(case_dir) for case_dir in case_dirs] + ["-o", str(output)]
        run_python_script("distill_case_patterns.py", distill_args)
        print(f"\n[OK] 案例蒸馏完成：{output}")
    else:
        print("\n[OK] 案例已入库；当前未执行跨案例蒸馏。")

    print("下一步建议:")
    print("1. 先检查案例目录中的 deck_outline / page_patterns / writing_logic")
    print("2. 再判断哪些属于模板骨架、哪些属于行业规则、哪些只保留为案例技巧")


def command_produce(args: argparse.Namespace) -> None:
    project_path = str(Path(args.project_path).expanduser().resolve())
    analysis, outputs = build_production_packet(project_path)

    if analysis["blockers"]:
        print("\n[WAIT] 当前项目还不能稳定进入正式生成，我已输出生产就绪报告。")
        print(f"  - readiness: {outputs['readiness']}")
        print(f"  - packet: {outputs['packet']}")
        print(f"  - strategist_packet: {outputs['strategist_packet']}")
        print(f"  - complex_models: {outputs['complex_models']}")
        print(f"  - design_spec_scaffold: {outputs['design_spec_scaffold']}")
        print(f"  - design_spec_draft: {outputs['design_spec_draft']}")
        print("\n阻塞问题:")
        for item in analysis["blockers"]:
            print(f"  - {item}")
        print("\n建议先补齐规划层，再重新执行 `ppt_agent.py produce <project_path>`。")
        return

    print("\n[OK] 项目已具备进入正式生成的基础条件。")
    print(f"  - readiness: {outputs['readiness']}")
    print(f"  - packet: {outputs['packet']}")
    print(f"  - strategist_packet: {outputs['strategist_packet']}")
    print(f"  - complex_models: {outputs['complex_models']}")
    print(f"  - design_spec_scaffold: {outputs['design_spec_scaffold']}")
    print(f"  - design_spec_draft: {outputs['design_spec_draft']}")
    print("\n下一步执行顺序:")
    print("1. 让 Strategist 先读取 production packet + strategist packet + design_spec_scaffold + design_spec_draft + 规划文件，完成八项确认与 design_spec")
    print("2. 命中复杂页时，先把 `complex_page_models.md` 从骨架补成完整建模结果")
    print("3. 确认模板骨架、行业包与复杂页命中方式")
    print("4. 进入 Executor，按页顺序生成 SVG，并执行逐页视觉复核")


def build_execution_readiness_text(
    project_path: Path,
    analysis: dict[str, object],
    outputs: dict[str, str],
    design_spec_path: Path,
    design_spec_written: bool,
    design_spec_note: str,
    design_spec_ok: bool,
    design_spec_errors: list[str],
    design_spec_warnings: list[str],
    complex_ok: bool,
    complex_errors: list[str],
    complex_warnings: list[str],
    export_gate_info: dict[str, object],
    auto_repair_report: Path | None = None,
) -> str:
    ready = not analysis["blockers"] and design_spec_ok and complex_ok
    lines = [
        "# 执行就绪度",
        "",
        f"- 项目路径：`{project_path}`",
        f"- 是否可进入 Executor：{'是' if ready else '否'}",
        f"- `produce` 是否通过：{'是' if not analysis['blockers'] else '否'}",
        f"- `design_spec.md`：`{design_spec_path}`",
        f"- design_spec 本轮是否写入：{'是' if design_spec_written else '否'}",
        f"- 说明：{design_spec_note}",
        "",
        "## 1. `produce` 产物",
        f"- readiness: `{outputs['readiness']}`",
        f"- packet: `{outputs['packet']}`",
        f"- strategist_packet: `{outputs['strategist_packet']}`",
        f"- complex_models: `{outputs['complex_models']}`",
        f"- design_spec_scaffold: `{outputs['design_spec_scaffold']}`",
        f"- design_spec_draft: `{outputs['design_spec_draft']}`",
        "",
        "## 2. design_spec 校验",
        f"- 结果：{'通过' if design_spec_ok else '失败'}",
    ]
    if design_spec_errors:
        lines.extend(f"- ERROR: {item}" for item in design_spec_errors)
    if design_spec_warnings:
        lines.extend(f"- WARN: {item}" for item in design_spec_warnings)
    if not design_spec_errors and not design_spec_warnings:
        lines.append("- 无")

    lines.extend(
        [
            "",
            "## 3. 复杂页建模校验",
            f"- 结果：{'通过' if complex_ok else '失败'}",
        ]
    )
    if complex_errors:
        lines.extend(f"- ERROR: {item}" for item in complex_errors)
    if complex_warnings:
        lines.extend(f"- WARN: {item}" for item in complex_warnings)
    if not complex_errors and not complex_warnings:
        lines.append("- 无")

    if auto_repair_report:
        lines.extend(
            [
                "",
                "## 3.5 自动修补记录",
                f"- report: `{auto_repair_report}`",
                "- 若本轮有 warning 类问题，已优先尝试自动修补后再重新校验。",
            ]
        )

    lines.extend(["", *build_export_gate_markdown_lines(export_gate_info, heading="## 4. 当前导出门禁快照")])
    lines.extend(["", "## 5. 下一步"])
    if ready:
        lines.extend(
            [
                "- 现在可按 `design_spec.md` 与 `notes/complex_page_models.md` 进入 Executor。",
                "- 仍需保持逐页 QA：文本断句、贴边、溢出、品牌保护区、信息密度、图文打架。",
                "- 若执行中调整复杂页标题，先同步更新 `design_spec.md` 与 `notes/complex_page_models.md`。",
                "- 全部页面完成并 finalize 后，仍需再看同一套 export gate；只有 gate pass 才能导出 PPT。",
            ]
        )
    else:
        lines.extend(
            [
                "- 先处理所有 design_spec 或复杂页模型错误，再重新执行 `ppt_agent.py execute <project_path>`。",
                "- 对 warnings 可按优先级处理，但若涉及 soft QA 或跨页逻辑，建议一并修正。",
                "- 即使当前已有 SVG 快照，也不要绕过 export gate 直接导出。",
            ]
        )
    return "\n".join(lines) + "\n"


def build_execution_runbook_text(
    project_path: Path,
    analysis: dict[str, object],
    outputs: dict[str, str],
    design_spec_path: Path,
) -> str:
    complex_pages = analysis.get("complex_pages") or []
    template_name = analysis.get("primary_template") or "待确认"
    domain_name = analysis.get("recommended_domain") or "待确认"
    lines = [
        "# Executor Runbook",
        "",
        f"- Project Path: `{project_path}`",
        f"- design_spec: `{design_spec_path}`",
        f"- Primary Template: `{template_name}`",
        f"- Domain Pack: `{domain_name}`",
        f"- Complex Page Count: {len(complex_pages)}",
        "",
        "## 1. 启动顺序",
        "1. 先读 `design_spec.md`，再读 `notes/production_packet.md` 与 `notes/strategist_packet.md`。",
        "2. 若存在复杂页，再读 `notes/complex_page_models.md`，确认标题与 design_spec 完全一致。",
        "3. 按页顺序执行固定页 -> 概览页 -> 推进页 -> 证明页 -> 收束页，不跳页补画。",
        "4. 每页生成后立即做软性 QA，不要等整套导出后再补。",
        "",
        "## 2. 强制输入",
        "- `project_brief.md`",
        "- `notes/template_domain_recommendation.md`",
        "- `notes/storyline.md`",
        "- `notes/page_outline.md`",
        f"- `{outputs['packet']}`",
        f"- `{outputs['strategist_packet']}`",
        f"- `{design_spec_path}`",
        "",
        "## 3. 复杂页执行规则",
    ]
    if complex_pages:
        lines.extend(
            [
                "- 复杂页必须先看主判断、结构类型、关键节点、关键关系、证据挂载，再决定 SVG 构图。",
                "- 若复杂页模型仍是占位文本，只能继续补模型，不能直接画图。",
                "- 若复杂结构讲不清“为什么必须复杂”，应回退为普通页型并同步修订 design_spec。",
            ]
        )
    else:
        lines.append("- 当前项目未命中复杂页，可按常规正文页执行，但仍需逐页做软性 QA。")

    lines.extend(
        [
            "",
            "## 4. 逐页 QA 闸门",
            "- 文本断句是否自然、中文是否可读，避免半句换行和 AI 自造术语。",
            "- 标题、正文、卡片、图示是否侵入 Logo / 页脚 / 装饰保护区。",
            "- 卡片内文字是否拥挤、贴边、视觉溢出，必要时先删改文案再调布局。",
            "- 图形与正文是否互相遮挡，复杂页是否存在模块重叠或焦点混乱。",
            "- 当前页信息密度是否过高；若过高，优先拆页或重构，而非盲目缩字号。",
            "",
            "## 5. 失败回退规则",
            "- 若 design_spec 与模型标题不一致，先统一标题。",
            "- 若页型选错，先回到 design_spec 修页型，再重做页面。",
            "- 若品牌元素不清楚，优先回读模板文档，不允许临时自造 Logo 样式或底板。",
            "",
            "## 6. 本轮产物索引",
            f"- `{outputs['readiness']}`",
            f"- `{outputs['packet']}`",
            f"- `{outputs['strategist_packet']}`",
            f"- `{outputs['complex_models']}`",
            f"- `{outputs['design_spec_scaffold']}`",
            f"- `{outputs['design_spec_draft']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def build_strategist_handoff_text(
    project_path: Path,
    outputs: dict[str, str],
    design_spec_path: Path,
    auto_repair_report: Path | None,
) -> str:
    required_inputs = [
        "project_brief.md",
        "notes/template_domain_recommendation.md",
        "notes/storyline.md",
        "notes/page_outline.md",
        rel_ref(project_path, outputs["design_spec_scaffold"]),
        rel_ref(project_path, outputs["design_spec_draft"]),
        rel_ref(project_path, design_spec_path),
    ]
    fallback_inputs = [
        rel_ref(project_path, outputs["packet"]),
        rel_ref(project_path, outputs["strategist_packet"]),
    ]
    if auto_repair_report:
        fallback_inputs.append(rel_ref(project_path, auto_repair_report))
    lines = [
        "# Strategist Handoff",
        "",
        f"- Project: `{project_path}`",
        f"- 当前唯一页面真相源：`{rel_ref(project_path, design_spec_path)}`",
        "",
        "## 1. 最小必读",
    ]
    lines.extend(f"- `{item}`" for item in required_inputs)
    lines.extend(
        [
            "",
            "## 2. 只做这 4 件事",
            "- 只在现有 `design_spec.md` 上确认，不另起新结构、不重写整套大纲。",
            "- 逐页确认 `页面意图 / 证明目标 / 优先页型 / 高级正文模式` 是否真的一致。",
            "- 复杂页重点看 `页面角色 / 上下页关系 / 复杂度是否成立`，不成立就直接降级页型。",
            "- 若改动影响复杂页表达，同步修 `notes/complex_page_models.md`，避免规划层与执行层脱节。",
            "",
            "## 3. 补充资料（按需回退）",
        ]
    )
    lines.extend(f"- `{item}`" for item in fallback_inputs)
    lines.extend(
        [
            "",
            "## 4. 完成标准",
            "- `design_spec.md` 可直接交给 Executor，不需要再读一遍大包才能理解当前页。",
            "- 不保留 AI 自造术语、逻辑跳步标题、无意义复杂页。",
            "- 不破坏模板固定骨架、品牌元素、安全区规则。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_executor_handoff_text(
    project_path: Path,
    outputs: dict[str, str],
    design_spec_path: Path,
    svg_pack: dict[str, str],
    auto_repair_report: Path | None,
) -> str:
    primary_inputs = [
        "notes/svg_current_task.md",
        "notes/svg_current_prompt.md",
        "notes/svg_current_context_pack.md",
        "notes/svg_current_review.md",
    ]
    fallback_inputs = [
        rel_ref(project_path, svg_pack["queue"]),
        rel_ref(project_path, svg_pack["page_briefs"]),
        rel_ref(project_path, svg_pack["status"]),
        rel_ref(project_path, svg_pack["postprocess"]),
        rel_ref(project_path, outputs["complex_models"]),
        rel_ref(project_path, design_spec_path),
    ]
    if auto_repair_report:
        fallback_inputs.append(rel_ref(project_path, auto_repair_report))
    lines = [
        "# Executor Handoff",
        "",
        f"- Project: `{project_path}`",
        "- 默认只围绕当前页执行；不要把整套文档重新读一遍。",
        "",
        "## 1. 当前页最小必读",
    ]
    lines.extend(f"- `{item}`" for item in primary_inputs)
    lines.extend(
        [
            "- `references/executor-base.md`",
            "- `references/executor-visual-review.md`",
            "",
            "## 2. 当前页执行规则",
            "- 先读 `svg_current_context_pack.md` 锁定当前页事实，再读 brief 与 QA 卡开始出图。",
            "- 只生成当前页，不跳页；完成后立即当页自检，再决定 `generated / completed / qa_failed / blocked`。",
            "- 命中复杂页时，若当前上下文缺字段，才回退 `complex_page_models.md` 或 `design_spec.md`。",
            "- 不直接导出；全部完成后只按 `notes/svg_postprocess_plan.md` 和 export gate 放行。",
            "",
            "## 3. 出现问题时回退",
        ]
    )
    lines.extend(f"- `{item}`" for item in fallback_inputs)
    lines.extend(
        [
            "",
            "## 4. 当页硬门禁",
            "- 中文断句、标题逻辑、信息密度、卡片贴边、模块重叠必须当页处理。",
            "- 若页面与 `design_spec.md` 的页型或证明目标不一致，先回退规划层，不要硬修图。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_run_status_text(
    project_path: Path,
    design_spec_path: Path,
    execution_readiness_path: Path,
    execution_runbook_path: Path,
    strategist_handoff_path: Path,
    executor_handoff_path: Path,
    svg_execution_queue_path: Path,
    svg_execution_queue_machine_path: Path,
    svg_generation_status_path: Path,
    svg_execution_state_path: Path,
    svg_current_task_path: Path,
    svg_current_prompt_path: Path,
    svg_current_context_path: Path,
    svg_current_review_path: Path,
    svg_execution_log_path: Path,
    svg_postprocess_plan_path: Path,
    page_briefs_dir: Path,
    auto_repair_report: Path | None,
    ready: bool,
    export_gate_info: dict[str, object],
) -> str:
    current_page_bundle = [
        rel_ref(project_path, svg_current_task_path),
        rel_ref(project_path, svg_current_prompt_path),
        rel_ref(project_path, svg_current_context_path),
        rel_ref(project_path, svg_current_review_path),
    ]
    fallback_bundle = [
        rel_ref(project_path, execution_readiness_path),
        rel_ref(project_path, execution_runbook_path),
        rel_ref(project_path, svg_execution_queue_path),
        rel_ref(project_path, svg_execution_queue_machine_path),
        rel_ref(project_path, svg_generation_status_path),
        rel_ref(project_path, svg_postprocess_plan_path),
        rel_ref(project_path, page_briefs_dir),
    ]
    lines = [
        "# Agent Run Status",
        "",
        f"- Project: `{project_path}`",
        f"- Ready For Executor: {'yes' if ready else 'no'}",
        f"- 页面真相源：`{rel_ref(project_path, design_spec_path)}`",
        f"- Strategist 入口：`{rel_ref(project_path, strategist_handoff_path)}`",
        f"- Executor 入口：`{rel_ref(project_path, executor_handoff_path)}`",
        f"- 机器状态源：`{rel_ref(project_path, svg_execution_state_path)}`",
        f"- 当前页执行包：`{current_page_bundle[0]}` / `{current_page_bundle[1]}` / `{current_page_bundle[2]}` / `{current_page_bundle[3]}`",
        f"- 日志：`{rel_ref(project_path, svg_execution_log_path)}`",
    ]
    if auto_repair_report:
        lines.append(f"- 自动修复报告：`{rel_ref(project_path, auto_repair_report)}`")
    lines.extend(
        [
            "",
            "## 备用索引（按需回退）",
        ]
    )
    lines.extend(f"- `{item}`" for item in fallback_bundle)
    lines.extend(["", *build_export_gate_markdown_lines(export_gate_info)])
    lines.extend(["", *build_execution_trace_markdown_lines(export_gate_info)])
    lines.extend(
        [
            "",
            "## Next",
            "- 若 `Ready For Executor = no`，先处理 `execution_readiness.md` 中的阻断项。",
            "- 若 `Ready For Executor = yes`，Strategist 只看 `strategist_handoff.md`，Executor 默认只看当前页执行包。",
            "- 全部页面完成并 finalize 后，再看 export gate；只有 pass 才允许导出 PPT。",
        ]
    )
    return "\n".join(lines) + "\n"


def execute_pipeline(
    project_path: Path,
    *,
    refresh_design_spec: bool,
    auto_repair: bool,
    force_produce: bool = False,
    force_execute: bool = False,
) -> dict[str, object]:
    stage_statuses: dict[str, object] = {}
    produce_output_paths = [
        project_path / "notes" / "production_readiness.md",
        project_path / "notes" / "production_packet.md",
        project_path / "notes" / "strategist_packet.md",
        project_path / "notes" / "design_spec_scaffold.md",
        project_path / "notes" / "design_spec_draft.md",
    ]
    produce_fresh, produce_input_hash, produce_stage = stage_is_fresh(
        project_path,
        "produce_artifacts",
        input_paths=produce_stage_inputs(project_path),
        output_paths=produce_output_paths,
        force=force_produce,
    )
    if produce_fresh:
        produce_result = dict(produce_stage.get("result") or {})
        analysis = dict(produce_result.get("analysis") or {})
        outputs = dict(produce_result.get("outputs") or {})
    else:
        analysis, outputs = build_production_packet(project_path)
        save_stage_fingerprint(
            project_path,
            "produce_artifacts",
            input_hash=produce_input_hash,
            output_paths=produce_output_paths,
            result={"analysis": analysis, "outputs": outputs},
        )
    stage_statuses["produce_artifacts"] = stage_status_payload(
        "produce_artifacts",
        cache_hit=produce_fresh,
        input_hash=produce_input_hash,
        stage_data=produce_stage,
        forced=force_produce,
    )
    if analysis["blockers"]:
        return {
            "blocked": True,
            "analysis": analysis,
            "outputs": outputs,
            "stage_statuses": stage_statuses,
        }

    validation_output_paths = [
        project_path / "design_spec.md",
        project_path / "notes" / "complex_page_models.md",
        project_path / "notes" / "execution_readiness.md",
        project_path / "notes" / "execution_runbook.md",
        project_path / "notes" / "auto_repair_report.md",
    ]
    validation_fresh, validation_input_hash, validation_stage = stage_is_fresh(
        project_path,
        "design_spec_validation",
        input_paths=validation_stage_inputs(project_path),
        output_paths=validation_output_paths,
        extra_values=[f"auto_repair={bool(auto_repair)}"],
        force=force_execute or refresh_design_spec,
    )
    if validation_fresh:
        validation_result = dict(validation_stage.get("result") or {})
        result = {
            "blocked": False,
            "analysis": analysis,
            "outputs": outputs,
            "stage_statuses": stage_statuses,
            "design_spec_path": Path(str(validation_result.get("design_spec_path") or project_path / "design_spec.md")),
            "design_spec_written": bool(validation_result.get("design_spec_written", False)),
            "design_spec_note": str(validation_result.get("design_spec_note") or ""),
            "design_spec_ok": bool(validation_result.get("design_spec_ok", False)),
            "design_spec_errors": list(validation_result.get("design_spec_errors") or []),
            "design_spec_warnings": list(validation_result.get("design_spec_warnings") or []),
            "complex_ok": bool(validation_result.get("complex_ok", False)),
            "complex_errors": list(validation_result.get("complex_errors") or []),
            "complex_warnings": list(validation_result.get("complex_warnings") or []),
            "export_gate_info": dict(validation_result.get("export_gate_info") or {}),
            "auto_repair_result": dict(validation_result.get("auto_repair_result") or {}) or None,
            "auto_repair_report_path": Path(str(validation_result["auto_repair_report_path"])) if validation_result.get("auto_repair_report_path") else None,
            "execution_readiness_path": Path(str(validation_result.get("execution_readiness_path") or project_path / "notes" / "execution_readiness.md")),
            "execution_runbook_path": Path(str(validation_result.get("execution_runbook_path") or project_path / "notes" / "execution_runbook.md")),
        }
        stage_statuses["design_spec_validation"] = stage_status_payload(
            "design_spec_validation",
            cache_hit=True,
            input_hash=validation_input_hash,
            stage_data=validation_stage,
            forced=force_execute or refresh_design_spec,
        )
        return result

    design_spec_path, design_spec_written, design_spec_note = build_project_design_spec(
        project_path,
        force=refresh_design_spec or force_execute,
    )

    validator = DesignSpecValidator()
    design_spec_ok, design_spec_errors, design_spec_warnings = validator.validate_file(str(design_spec_path))
    complex_ok, complex_errors, complex_warnings, _summary = validate_complex_page_model(project_path)

    auto_repair_result: dict[str, object] | None = None
    auto_repair_report_path: Path | None = None
    if auto_repair and (design_spec_errors or design_spec_warnings or complex_errors or complex_warnings):
        auto_repair_result = repair_execution_artifacts(project_path)
        auto_repair_report_path = Path(str(auto_repair_result["report"]))
        design_spec_ok = bool(auto_repair_result["design_ok"])
        design_spec_errors = list(auto_repair_result["design_errors"])
        design_spec_warnings = list(auto_repair_result["design_warnings"])
        complex_ok = bool(auto_repair_result["complex_ok"])
        complex_errors = list(auto_repair_result["complex_errors"])
        complex_warnings = list(auto_repair_result["complex_warnings"])

    export_gate_info = ProjectManager().get_project_info(str(project_path))

    notes_dir = project_path / "notes"
    execution_readiness_path = notes_dir / "execution_readiness.md"
    execution_runbook_path = notes_dir / "execution_runbook.md"
    write_text(
        execution_readiness_path,
        build_execution_readiness_text(
            project_path,
            analysis,
            outputs,
            design_spec_path,
            design_spec_written,
            design_spec_note,
            design_spec_ok,
            design_spec_errors,
            design_spec_warnings,
            complex_ok,
            complex_errors,
            complex_warnings,
            export_gate_info,
            auto_repair_report=auto_repair_report_path,
        ),
    )
    write_text(
        execution_runbook_path,
        build_execution_runbook_text(project_path, analysis, outputs, design_spec_path),
    )

    result = {
        "blocked": False,
        "analysis": analysis,
        "outputs": outputs,
        "stage_statuses": stage_statuses,
        "design_spec_path": design_spec_path,
        "design_spec_written": design_spec_written,
        "design_spec_note": design_spec_note,
        "design_spec_ok": design_spec_ok,
        "design_spec_errors": design_spec_errors,
        "design_spec_warnings": design_spec_warnings,
        "complex_ok": complex_ok,
        "complex_errors": complex_errors,
        "complex_warnings": complex_warnings,
        "export_gate_info": export_gate_info,
        "auto_repair_result": auto_repair_result,
        "auto_repair_report_path": auto_repair_report_path,
        "execution_readiness_path": execution_readiness_path,
        "execution_runbook_path": execution_runbook_path,
    }
    stage_statuses["design_spec_validation"] = stage_status_payload(
        "design_spec_validation",
        cache_hit=False,
        input_hash=validation_input_hash,
        stage_data=validation_stage,
        forced=force_execute or refresh_design_spec,
    )
    save_stage_fingerprint(
        project_path,
        "design_spec_validation",
        input_hash=validation_input_hash,
        output_paths=validation_output_paths,
        result=result,
    )
    return result


def command_execute(args: argparse.Namespace) -> None:
    project_path = Path(args.project_path).expanduser().resolve()
    result = execute_pipeline(
        project_path,
        refresh_design_spec=args.refresh_design_spec,
        auto_repair=args.auto_repair,
        force_produce=getattr(args, "force_produce", False),
        force_execute=getattr(args, "force_execute", False),
    )
    analysis = result["analysis"]
    outputs = result["outputs"]
    stage_statuses = dict(result.get("stage_statuses") or {})

    if result["blocked"]:
        print("\n[WAIT] 当前项目还不能进入 execute，我已先刷新 `produce` 产物。")
        print_stage_statuses(stage_statuses)
        print(f"  - readiness: {outputs['readiness']}")
        print(f"  - packet: {outputs['packet']}")
        print(f"  - strategist_packet: {outputs['strategist_packet']}")
        print(f"  - complex_models: {outputs['complex_models']}")
        print(f"  - design_spec_scaffold: {outputs['design_spec_scaffold']}")
        print(f"  - design_spec_draft: {outputs['design_spec_draft']}")
        print("\n阻塞问题:")
        for item in analysis["blockers"]:
            print(f"  - {item}")
        print("\n请先补齐规划层，再执行 `ppt_agent.py execute <project_path>`。")
        return

    design_spec_path = result["design_spec_path"]
    execution_readiness_path = result["execution_readiness_path"]
    execution_runbook_path = result["execution_runbook_path"]
    design_spec_ok = bool(result["design_spec_ok"])
    complex_ok = bool(result["complex_ok"])
    design_spec_errors = list(result["design_spec_errors"])
    complex_errors = list(result["complex_errors"])
    design_spec_warnings = list(result["design_spec_warnings"])
    complex_warnings = list(result["complex_warnings"])
    export_gate_info = dict(result["export_gate_info"])
    auto_repair_report_path = result["auto_repair_report_path"]

    ready = design_spec_ok and complex_ok
    print("\n[OK] execute 阶段已完成执行交接产物生成。")
    print_stage_statuses(stage_statuses)
    print(f"  - design_spec: {design_spec_path}")
    print(f"  - execution_readiness: {execution_readiness_path}")
    print(f"  - execution_runbook: {execution_runbook_path}")
    print(f"  - design_spec_check: {'pass' if design_spec_ok else 'fail'}")
    print(f"  - complex_model_check: {'pass' if complex_ok else 'fail'}")
    if auto_repair_report_path:
        print(f"  - auto_repair_report: {auto_repair_report_path}")
    print_export_gate_snapshot(export_gate_info)
    if design_spec_warnings or complex_warnings:
        print("\n警告:")
        for item in [*design_spec_warnings, *complex_warnings]:
            print(f"  - {item}")
    if not ready:
        print("\n[WAIT] 尚未完全具备进入 Executor 的条件，请先修正错误。")
        for item in [*design_spec_errors, *complex_errors]:
            print(f"  - {item}")
        raise SystemExit(1)

    print("\n下一步执行顺序:")
    print("1. 先读 `design_spec.md` + `notes/execution_runbook.md`")
    print("2. 命中复杂页时，按 `notes/complex_page_models.md` 先建模后出图")
    print("3. 开始逐页 SVG 生成，并在每页完成后立即执行视觉与软性 QA")


def command_run(args: argparse.Namespace) -> None:
    project_path = Path(args.project_path).expanduser().resolve()
    result = execute_pipeline(
        project_path,
        refresh_design_spec=args.refresh_design_spec,
        auto_repair=True,
        force_produce=getattr(args, "force_produce", False),
        force_execute=getattr(args, "force_execute", False),
    )
    analysis = result["analysis"]
    outputs = result["outputs"]
    stage_statuses = dict(result.get("stage_statuses") or {})

    if result["blocked"]:
        print("\n[WAIT] 当前项目还不能进入 run，我已先刷新 `produce` 产物。")
        print_stage_statuses(stage_statuses)
        print(f"  - readiness: {outputs['readiness']}")
        print(f"  - packet: {outputs['packet']}")
        print(f"  - strategist_packet: {outputs['strategist_packet']}")
        for item in analysis["blockers"]:
            print(f"  - blocker: {item}")
        print("\n请先补齐规划层，再执行 `ppt_agent.py run <project_path>`。")
        return

    design_spec_path = Path(str(result["design_spec_path"]))
    execution_readiness_path = Path(str(result["execution_readiness_path"]))
    execution_runbook_path = Path(str(result["execution_runbook_path"]))
    auto_repair_report_path = result["auto_repair_report_path"]
    export_gate_info = dict(result["export_gate_info"])
    ready = bool(result["design_spec_ok"]) and bool(result["complex_ok"])
    probe_pack = expected_svg_pack_outputs(project_path)
    svg_pack_output_paths = run_bundle_output_paths(project_path, probe_pack)
    svg_pack_fresh, svg_pack_input_hash, _svg_pack_stage = stage_is_fresh(
        project_path,
        "svg_execution_pack",
        input_paths=svg_pack_stage_inputs(project_path),
        output_paths=svg_pack_output_paths,
        force=getattr(args, "force_svg_pack", False),
    )
    stage_statuses["svg_execution_pack"] = stage_status_payload(
        "svg_execution_pack",
        cache_hit=svg_pack_fresh,
        input_hash=svg_pack_input_hash,
        stage_data=_svg_pack_stage,
        forced=getattr(args, "force_svg_pack", False),
    )
    if svg_pack_fresh:
        bundle_paths = {
            "svg_execution_queue_path": Path(probe_pack["queue"]),
            "svg_execution_queue_machine_path": Path(probe_pack.get("queue_machine", project_path / "notes" / "svg_execution_queue.machine.json")),
            "svg_generation_status_path": Path(probe_pack["status"]),
            "svg_postprocess_plan_path": Path(probe_pack["postprocess"]),
            "svg_contracts_path": Path(probe_pack["contracts"]),
            "page_briefs_dir": Path(probe_pack["page_briefs"]),
            "svg_execution_state_path": project_path / "notes" / "svg_execution_state.json",
            "svg_current_task_path": project_path / "notes" / "svg_current_task.md",
            "svg_current_prompt_path": project_path / "notes" / "svg_current_prompt.md",
            "svg_current_context_path": project_path / "notes" / "svg_current_context_pack.md",
            "svg_current_review_path": project_path / "notes" / "svg_current_review.md",
            "svg_execution_log_path": project_path / "notes" / "svg_execution_log.md",
            "strategist_handoff_path": project_path / "notes" / "strategist_handoff.md",
            "executor_handoff_path": project_path / "notes" / "executor_handoff.md",
            "run_status_path": project_path / "notes" / "agent_run_status.md",
            "page_context_dir": Path(probe_pack["page_context_min"]),
        }
    else:
        actual_svg_pack = build_svg_execution_pack(project_path)
        bundle_paths = build_run_bundle(
            project_path,
            outputs=outputs,
            svg_pack=actual_svg_pack,
            design_spec_path=design_spec_path,
            execution_readiness_path=execution_readiness_path,
            execution_runbook_path=execution_runbook_path,
            auto_repair_report_path=auto_repair_report_path,
            export_gate_info=export_gate_info,
            ready=ready,
            force_state=True,
        )
        save_stage_fingerprint(
            project_path,
            "svg_execution_pack",
            input_hash=svg_pack_input_hash,
            output_paths=run_bundle_output_paths(project_path, actual_svg_pack),
            result={
                "queue": str(bundle_paths["svg_execution_queue_path"]),
                "queue_machine": str(bundle_paths["svg_execution_queue_machine_path"]),
                "status": str(bundle_paths["svg_generation_status_path"]),
                "postprocess": str(bundle_paths["svg_postprocess_plan_path"]),
                "contracts": str(bundle_paths["svg_contracts_path"]),
                "page_briefs": str(bundle_paths["page_briefs_dir"]),
                "page_context_min": str(bundle_paths["page_context_dir"]),
                "state": str(bundle_paths["svg_execution_state_path"]),
                "strategist_handoff": str(bundle_paths["strategist_handoff_path"]),
                "executor_handoff": str(bundle_paths["executor_handoff_path"]),
                "run_status": str(bundle_paths["run_status_path"]),
            },
        )

    print("\n[OK] run 阶段已完成 Agent 调度准备。")
    print_stage_statuses(stage_statuses)
    print(f"  - design_spec: {design_spec_path}")
    print(f"  - execution_readiness: {execution_readiness_path}")
    print(f"  - execution_runbook: {execution_runbook_path}")
    print(f"  - strategist_handoff: {bundle_paths['strategist_handoff_path']}")
    print(f"  - executor_handoff: {bundle_paths['executor_handoff_path']}")
    print(f"  - svg_execution_queue: {bundle_paths['svg_execution_queue_path']}")
    print(f"  - svg_execution_queue_machine: {bundle_paths['svg_execution_queue_machine_path']}")
    print(f"  - svg_generation_status: {bundle_paths['svg_generation_status_path']}")
    print(f"  - svg_execution_state: {bundle_paths['svg_execution_state_path']}")
    print(f"  - svg_current_task: {bundle_paths['svg_current_task_path']}")
    print(f"  - svg_current_prompt: {bundle_paths['svg_current_prompt_path']}")
    print(f"  - svg_current_context: {bundle_paths['svg_current_context_path']}")
    print(f"  - svg_current_review: {bundle_paths['svg_current_review_path']}")
    print(f"  - svg_execution_log: {bundle_paths['svg_execution_log_path']}")
    print(f"  - svg_postprocess_plan: {bundle_paths['svg_postprocess_plan_path']}")
    print(f"  - svg_contracts: {bundle_paths['svg_contracts_path']}")
    print(f"  - page_briefs_dir: {bundle_paths['page_briefs_dir']}")
    print(f"  - agent_run_status: {bundle_paths['run_status_path']}")
    if auto_repair_report_path:
        print(f"  - auto_repair_report: {auto_repair_report_path}")
    print(f"  - ready_for_executor: {'yes' if ready else 'no'}")
    print_export_gate_snapshot(export_gate_info)

    if not ready:
        print("\n[WAIT] 还不能直接进入 Executor，请先按 `execution_readiness.md` 修完错误。")
        raise SystemExit(1)

    print("\n下一步执行顺序:")
    print("1. Strategist 先读 `notes/strategist_handoff.md` 做最终确认")
    print("2. 然后 Executor 读 `notes/executor_handoff.md` + `notes/svg_current_task.md` + `notes/svg_current_prompt.md` + `notes/svg_current_context_pack.md` + `notes/svg_current_review.md` 开始当前页 SVG 生成与当页审核")
    print("3. 每完成一页，优先用 `svg_execution_runner.py complete` 自动推进下一页；必要时再用 mark/sync/next")
    print("4. 全部完成后按 `notes/svg_postprocess_plan.md` 继续执行 finalize/export/QA 主链路，并以 export gate 结果决定是否允许导出")


def command_improve(args: argparse.Namespace) -> None:
    run_args = [str(Path(args.project_path).expanduser().resolve())]
    if args.findings:
        run_args.extend(["--findings", str(Path(args.findings).expanduser().resolve())])
    if args.output:
        run_args.extend(["-o", str(Path(args.output).expanduser().resolve())])
    run_python_script("update_learning_registry.py", run_args)
    print("\n[OK] 项目复盘建议已生成，可继续人工确认后回写模板或行业包。")


def command_status(args: argparse.Namespace) -> None:
    manager = ProjectManager()
    project_path = str(Path(args.project_path).expanduser().resolve())
    info = manager.get_project_info(project_path)
    is_valid, errors, warnings = manager.validate_project(project_path)
    export_gate_available = bool(info.get("export_gate_available"))
    export_gate_ok = bool(info.get("export_gate_ok"))

    print(f"项目：{info['name']}")
    print(f"路径：{info['path']}")
    print(f"画布：{info['canvas_format']}")
    print(f"源文件数量：{info['source_count']}")
    print(f"SVG 数量：{info['svg_count']}")
    print(f"已有 design_spec：{'是' if info['has_spec'] else '否'}")
    print(f"已完成 Agent /plan：{'是' if info['has_agent_bootstrap'] else '否'}")
    if export_gate_available:
        print(f"导出门禁：{'通过' if export_gate_ok else '未通过'}")
        print(f"门禁检查源：{info['export_gate_source']}")
        if info.get("export_gate_working_source") and info["export_gate_working_source"] != info["export_gate_source"]:
            print(f"当前工作快照：{info['export_gate_working_source']}")
        if info["export_gate_issue_code_summary"]:
            print(f"门禁问题类型：{info['export_gate_issue_code_summary']}")
        if not export_gate_ok:
            print("门禁阻断原因:")
            for item in info["export_gate_blocking_reasons"]:
                print(f"  - {item}")
    else:
        print("导出门禁：待执行（当前还没有可校验的 SVG 页面）")
    print_execution_trace_snapshot(info)
    print("\n规划产物状态:")
    for name, exists in info["bootstrap_status"].items():
        print(f"  - {name}: {'已生成' if exists else '缺失'}")

    if errors:
        print("\n错误:")
        for item in errors:
            print(f"  - {item}")
    if warnings:
        print("\n警告:")
        for item in warnings:
            print(f"  - {item}")

    if not is_valid:
        print("\n[ERROR] 项目结构不完整，需先修复。")
        raise SystemExit(1)
    if export_gate_available and not export_gate_ok:
        print("\n[BLOCK] 项目结构可用，但导出门禁未通过；请先修复阻断项后再导出 PPT。")
        raise SystemExit(1)
    if is_valid and not warnings:
        print("\n[OK] 项目结构完整，可继续正式生成流程。")
    else:
        print("\n[OK] 项目可用，但建议先处理上述警告。")


def command_svg_exec(args: argparse.Namespace) -> None:
    run_args = [args.action, str(Path(args.project_path).expanduser().resolve())]
    if args.action == "render":
        render_args = [str(Path(args.project_path).expanduser().resolve())]
        if getattr(args, "force", False):
            render_args.append("--force")
        if getattr(args, "page", ""):
            render_args.extend(["--page", args.page])
        if getattr(args, "note", ""):
            render_args.extend(["--note", args.note])
        if getattr(args, "max_auto_repair_rounds", None) is not None:
            render_args.extend(["--max-auto-repair-rounds", str(args.max_auto_repair_rounds)])
        if getattr(args, "no_auto_repair", False):
            render_args.append("--no-auto-repair")
        run_python_script("svg_page_executor.py", render_args)
        return
    if getattr(args, "force", False):
        run_args.append("--force")
    if getattr(args, "note", ""):
        run_args.extend(["--note", args.note])
    if getattr(args, "page", ""):
        run_args.extend(["--page", args.page])
    if getattr(args, "status_value", ""):
        run_args.extend(["--status", args.status_value])
    run_python_script("svg_execution_runner.py", run_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="`ppt-master` 的统一 PPT Agent 入口：用于 learn / plan / produce / execute / run / improve 等总控动作。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="新建项目并完成 /plan")
    new_parser.add_argument("project_name", help="项目名")
    add_plan_arguments(new_parser, include_format=True)
    new_parser.set_defaults(func=command_new)

    plan_parser = subparsers.add_parser("plan", help="对已有项目执行或刷新 /plan")
    plan_parser.add_argument("project_path", help="已有项目路径")
    add_plan_arguments(plan_parser, include_format=False)
    plan_parser.set_defaults(func=command_plan)

    produce_parser = subparsers.add_parser("produce", help="生成正式进入 Strategist / Executor 前的生产执行包")
    produce_parser.add_argument("project_path", help="项目路径")
    produce_parser.set_defaults(func=command_produce)

    execute_parser = subparsers.add_parser("execute", help="刷新生产包、补齐根 design_spec，并生成正式执行交接文件")
    execute_parser.add_argument("project_path", help="项目路径")
    execute_parser.add_argument("--refresh-design-spec", action="store_true", help="已存在 design_spec.md 时强制按当前规划结果刷新")
    execute_parser.add_argument("--auto-repair", action="store_true", help="发现 warning / 软问题时自动二次修补 design_spec 与复杂页建模")
    execute_parser.add_argument("--force-produce", action="store_true", help="忽略 produce 阶段缓存，强制重建生产包")
    execute_parser.add_argument("--force-execute", action="store_true", help="忽略 execute 阶段缓存，强制重跑 design_spec 与校验")
    execute_parser.set_defaults(func=command_execute)

    run_parser = subparsers.add_parser("run", help="执行 produce+execute+auto-repair，并输出 Strategist / Executor 调度入口")
    run_parser.add_argument("project_path", help="项目路径")
    run_parser.add_argument("--refresh-design-spec", action="store_true", help="已存在 design_spec.md 时强制按当前规划结果刷新")
    run_parser.add_argument("--force-produce", action="store_true", help="忽略 produce 阶段缓存，强制重建生产包")
    run_parser.add_argument("--force-execute", action="store_true", help="忽略 execute 阶段缓存，强制重跑 design_spec 与校验")
    run_parser.add_argument("--force-svg-pack", action="store_true", help="忽略 svg 执行包缓存，强制重建 queue / brief / state / handoff")
    run_parser.set_defaults(func=command_run)

    learn_parser = subparsers.add_parser("learn", help="把历史 PPT 案例入库并可选蒸馏")
    learn_parser.add_argument("pptx", nargs="+", help="一个或多个历史 PPTX")
    learn_parser.add_argument("--domain", default="general", help="案例所属行业包")
    learn_parser.add_argument("--case-name", help="单案例自定义名称")
    learn_parser.add_argument("--copy-source", action="store_true", help="复制源 PPT 到案例目录")
    learn_parser.add_argument("--distill", action="store_true", help="入库后立即蒸馏")
    learn_parser.add_argument("-o", "--output", help="蒸馏输出路径")
    learn_parser.set_defaults(func=command_learn)

    improve_parser = subparsers.add_parser("improve", help="把项目问题整理成学习回写建议")
    improve_parser.add_argument("project_path", help="项目路径")
    improve_parser.add_argument("--findings", help="可选：人工整理的问题清单文件")
    improve_parser.add_argument("-o", "--output", help="输出文件路径")
    improve_parser.set_defaults(func=command_improve)

    status_parser = subparsers.add_parser("status", help="查看项目 Agent 状态与结构健康度")
    status_parser.add_argument("project_path", help="项目路径")
    status_parser.set_defaults(func=command_status)

    svg_exec_parser = subparsers.add_parser("svg-exec", help="管理正式 SVG 逐页执行状态")
    svg_exec_parser.add_argument("action", choices=["init", "sync", "next", "render", "complete", "mark", "summary"], help="执行动作")
    svg_exec_parser.add_argument("project_path", help="项目路径")
    svg_exec_parser.add_argument("--force", action="store_true", help="init 时强制重建状态；render 时忽略页面缓存并强制重跑")
    svg_exec_parser.add_argument("--page", default="", help="用于 render / mark / complete：页码、标题或预期 SVG 文件名")
    svg_exec_parser.add_argument("--status", dest="status_value", default="", help="仅 mark 时生效：pending/in_progress/generated/qa_failed/blocked/completed")
    svg_exec_parser.add_argument("--note", default="", help="可选备注")
    svg_exec_parser.add_argument("--max-auto-repair-rounds", type=int, default=None, help="仅 render 时生效：可选覆盖默认自动修复轮数；未指定时按页面执行策略决定")
    svg_exec_parser.add_argument("--no-auto-repair", action="store_true", help="仅 render 时生效：关闭自动修复与重渲染")
    svg_exec_parser.set_defaults(func=command_svg_exec)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
