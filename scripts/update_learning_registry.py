#!/usr/bin/env python3
"""Generate a learning update summary from findings, QA manifest and execution traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SECTION_ORDER = ("模板问题", "内容问题", "复杂页问题", "QA 漏检问题")


def unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def classify_issue(text: str) -> str:
    normalized = text.lower()
    if any(
        key in normalized
        for key in [
            "logo",
            "页脚",
            "页码",
            "背景",
            "保护区",
            "品牌",
            "装饰条",
            "章节页",
            "目录页",
            "骨架",
            "白底",
            "模板",
            "fixed_page",
            "fixed-page",
            "固定页",
            "封面",
            "chapter",
            "toc",
        ]
    ):
        return "模板问题"
    if any(
        key in text
        for key in [
            "复杂页",
            "攻击链",
            "矩阵",
            "证据",
            "泳道",
            "链路",
            "流程图",
            "关系图",
            "治理图",
            "驾驶舱",
            "重型骨架",
            "高级正文",
        ]
    ):
        return "复杂页问题"
    if any(
        key in normalized
        for key in [
            "漏检",
            "未检查",
            "未拦截",
            "qa",
            "gate",
            "强校验",
            "没卡住",
            "仍导出",
            "导出前",
        ]
    ):
        return "QA 漏检问题"
    return "内容问题"


def classify(lines: list[str]) -> dict[str, list[str]]:
    buckets = {name: [] for name in SECTION_ORDER}
    for line in lines:
        text = line.strip("- ").strip()
        if not text:
            continue
        buckets[classify_issue(text)].append(text)
    return {name: unique_keep_order(items) for name, items in buckets.items()}


def load_findings(findings_path: Path | None) -> dict[str, list[str]]:
    if findings_path is None:
        return {name: [] for name in SECTION_ORDER}
    lines = findings_path.read_text(encoding="utf-8").splitlines()
    return classify(lines)


def load_execution_traces(project: Path) -> list[dict[str, Any]]:
    trace_dir = project / "notes" / "page_execution"
    traces: list[dict[str, Any]] = []
    for trace_file in sorted(trace_dir.glob("*.json")):
        trace = load_json(trace_file)
        if trace:
            trace["_trace_file"] = str(trace_file)
            traces.append(trace)
    return traces


def trace_summary_from_files(traces: list[dict[str, Any]]) -> dict[str, Any]:
    event_type_counts: dict[str, int] = {}
    auto_repair_pages: list[str] = []
    progression_pages: list[str] = []
    argument_pages: list[str] = []
    failed_after_repair: list[str] = []
    event_preview: list[str] = []

    for trace in traces:
        page = str(trace.get("page") or Path(str(trace.get("_trace_file", ""))).stem)
        rounds_used = int(trace.get("auto_repair_rounds_used", 0) or 0)
        if rounds_used > 0:
            auto_repair_pages.append(page)
        if rounds_used > 0 and trace.get("status") != "generated":
            failed_after_repair.append(page)

        for event in trace.get("execution_events", []) or []:
            event_type = str(event.get("type") or "other")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            if event_type == "progression_reframe":
                progression_pages.append(page)
                event_preview.append(
                    f"{page}: {event.get('from_pattern') or '无'} -> {event.get('to_pattern') or '无'} / {event.get('to_template') or '无'}"
                )
            elif event_type == "semantic_argument_rewrite":
                argument_pages.append(page)
                event_preview.append(f"{page}: 重写模块标题 / 页尾收束")
            elif event_type == "semantic_headline_rewrite":
                event_preview.append(f"{page}: 重写 headline")
            elif event_type == "semantic_closure_rewrite":
                event_preview.append(f"{page}: 重写页尾收束")

    return {
        "trace_file_count": len(traces),
        "pages_with_auto_repair": unique_keep_order(auto_repair_pages),
        "pages_with_progression_reframe": unique_keep_order(progression_pages),
        "pages_with_semantic_argument_rewrite": unique_keep_order(argument_pages),
        "pages_still_failed_after_repair": unique_keep_order(failed_after_repair),
        "event_type_counts": event_type_counts,
        "events_preview": unique_keep_order(event_preview)[:20],
    }


def resolve_execution_trace(manifest: dict[str, Any], traces: list[dict[str, Any]]) -> dict[str, Any]:
    checks = manifest.get("checks") if isinstance(manifest, dict) else {}
    trace_summary = checks.get("execution_trace") if isinstance(checks, dict) else None
    if isinstance(trace_summary, dict) and trace_summary:
        return trace_summary
    return trace_summary_from_files(traces)


def build_manifest_issue_lines(manifest: dict[str, Any]) -> list[str]:
    checks = manifest.get("checks") if isinstance(manifest, dict) else {}
    if not isinstance(checks, dict):
        return []
    lines: list[str] = []
    for name, summary in checks.items():
        if not isinstance(summary, dict):
            continue
        if summary.get("ok", True):
            continue
        if int(summary.get("file_count", 0) or 0) == 0 and not summary.get("issues_preview") and not summary.get("warnings") and not summary.get("errors"):
            continue
        if summary.get("issues_preview"):
            for preview in summary.get("issues_preview", [])[:4]:
                if isinstance(preview, dict):
                    message = str(preview.get("message") or "").strip()
                    code = str(preview.get("code") or "").strip()
                    if message:
                        prefix = f"{name}: {code} - " if code else f"{name}: "
                        lines.append(prefix + message)
                elif preview:
                    lines.append(f"{name}: {preview}")
            continue
        if summary.get("missing_pages"):
            missing_pages = ", ".join(summary.get("missing_pages", [])[:4])
            lines.append(f"{name}: 缺失固定页 {missing_pages}")
            continue
        blocking_files = summary.get("blocking_files", []) or []
        if blocking_files:
            issue_codes = summary.get("issue_codes", {}) or {}
            issue_text = "，".join(f"{key}={value}" for key, value in sorted(issue_codes.items()))
            lines.append(
                f"{name}: {len(blocking_files)} 个阻断页未通过"
                + (f"（{issue_text}）" if issue_text else "")
            )
            continue
        if "blocking_reasons" in summary:
            for reason in summary.get("blocking_reasons", [])[:4]:
                lines.append(f"{name}: {reason}")
            continue
        if "warnings" in summary and summary.get("warnings"):
            for warning in summary.get("warnings", [])[:4]:
                lines.append(f"{name}: {warning}")
            continue
        if "errors" in summary and summary.get("errors"):
            for error in summary.get("errors", [])[:4]:
                lines.append(f"{name}: {error}")
            continue
        lines.append(f"{name}: ok=false")
    return unique_keep_order(lines)


def build_auto_repair_lines(trace_summary: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    auto_repair_pages = trace_summary.get("pages_with_auto_repair", []) or []
    progression_pages = trace_summary.get("pages_with_progression_reframe", []) or []
    argument_pages = trace_summary.get("pages_with_semantic_argument_rewrite", []) or []
    failed_pages = trace_summary.get("pages_still_failed_after_repair", []) or []

    if auto_repair_pages:
        lines.append(f"触发自动修复页：{', '.join(auto_repair_pages[:12])}")
    if progression_pages:
        lines.append(f"触发复杂页换骨架：{', '.join(progression_pages[:12])}")
    if argument_pages:
        lines.append(f"触发论证重写：{', '.join(argument_pages[:12])}")
    if failed_pages:
        lines.append(f"自动修复后仍失败：{', '.join(failed_pages[:12])}")

    event_counts = trace_summary.get("event_type_counts", {}) or {}
    if event_counts:
        count_text = "，".join(f"{key}={value}" for key, value in sorted(event_counts.items()))
        lines.append(f"自动事件计数：{count_text}")

    for item in trace_summary.get("events_preview", [])[:8]:
        if isinstance(item, dict):
            page = str(item.get("page") or "未知页")
            event_type = str(item.get("type") or "other")
            if event_type == "progression_reframe":
                lines.append(
                    "事件样例："
                    f"{page} 从 {item.get('from_pattern') or '无'} / {item.get('from_template') or '无'} "
                    f"切换到 {item.get('to_pattern') or '无'} / {item.get('to_template') or '无'}"
                )
            elif event_type == "semantic_argument_rewrite":
                lines.append(f"事件样例：{page} 触发论证重写")
            elif event_type == "semantic_headline_rewrite":
                lines.append(f"事件样例：{page} 触发 headline 重写")
            elif event_type == "semantic_closure_rewrite":
                lines.append(f"事件样例：{page} 触发收束语重写")
            else:
                lines.append(f"事件样例：{page} 触发 {event_type}")
        else:
            lines.append(f"事件样例：{item}")

    return unique_keep_order(lines)


def append_bucket_item(buckets: dict[str, list[str]], bucket: str, item: str) -> None:
    text = item.strip()
    if not text:
        return
    buckets[bucket].append(text)


def enrich_buckets(
    buckets: dict[str, list[str]],
    manifest_issues: list[str],
    trace_summary: dict[str, Any],
) -> dict[str, list[str]]:
    for item in manifest_issues:
        append_bucket_item(buckets, classify_issue(item), item)

    if trace_summary.get("pages_with_progression_reframe"):
        append_bucket_item(
            buckets,
            "复杂页问题",
            "出现连续复杂页推进同构，需要在渲染阶段自动切换复杂页骨架。",
        )
    if trace_summary.get("pages_with_semantic_argument_rewrite"):
        append_bucket_item(
            buckets,
            "内容问题",
            "复杂页存在模块标题、页尾收束与主判断不在同一论证线的问题，需要在自动修复阶段重写。",
        )
    if trace_summary.get("pages_still_failed_after_repair"):
        append_bucket_item(
            buckets,
            "QA 漏检问题",
            "部分页面自动修复后仍失败，后续应作为导出阻断页继续拦截。",
        )
    return {name: unique_keep_order(items) for name, items in buckets.items()}


def build_rule_suggestions(
    buckets: dict[str, list[str]],
    trace_summary: dict[str, Any],
    manifest_issues: list[str],
) -> dict[str, list[str]]:
    template_rules: list[str] = []
    industry_rules: list[str] = []
    qa_rules: list[str] = []

    if buckets["模板问题"]:
        template_rules.append("把品牌资产版本、Logo 位置、Logo 禁止白底/描边/底板、章节页/目录页骨架一致性固化为模板硬规则。")
    if any("章节页" in item or "目录页" in item for item in buckets["模板问题"]):
        template_rules.append("目录页与章节页的标题、副标题、编号结构必须成套一致，若缺字段则统一降级，不允许半套保留。")
    if trace_summary.get("pages_with_progression_reframe"):
        industry_rules.append("对安服复杂页增加跨页推进差异约束：相邻复杂页不得沿用同一 pattern / role / template 组合。")
    if trace_summary.get("pages_with_semantic_argument_rewrite") or buckets["内容问题"]:
        industry_rules.append("安服正文复杂页必须绑定“主判断 -> 分判断 -> 证据 -> 动作收束”四段论证，不允许出现空泛标题或不贴正文的术语。")
    if buckets["复杂页问题"]:
        industry_rules.append("复杂页优先按案例链、治理矩阵、证据闭环、协同机制等有限骨架生成，再在骨架内做内容适配，避免自由发挥导致结构失真。")

    if manifest_issues:
        qa_rules.append("把 manifest 中未通过的检查项直接回流到项目复盘，不再只依赖人工 findings。")
    if trace_summary.get("trace_file_count", 0):
        qa_rules.append("每页执行后必须写入 page_execution trace，并将自动修复事件同步进 qa_manifest 供导出前审计。")
    if trace_summary.get("pages_still_failed_after_repair"):
        qa_rules.append("对自动修复后仍失败的页面保持硬阻断，不允许继续导出或以人工忽略方式跳过。")
    if not qa_rules:
        qa_rules.append("继续保持‘生成即检查、失败即阻断、修复留痕’的 QA 节奏。")

    return {
        "模板层": unique_keep_order(template_rules),
        "行业层": unique_keep_order(industry_rules),
        "通用 QA 层": unique_keep_order(qa_rules),
    }


def build_merge_advice(
    buckets: dict[str, list[str]],
    trace_summary: dict[str, Any],
    manifest_issues: list[str],
) -> dict[str, list[str]]:
    immediate: list[str] = []
    observe: list[str] = []
    special_case: list[str] = []

    if buckets["模板问题"]:
        immediate.append("模板品牌骨架、Logo 资产版本与固定保护区规则直接并入模板。")
    if trace_summary.get("pages_with_progression_reframe"):
        immediate.append("复杂页跨页去同构规则并入安服行业包与执行器自动修复。")
    if trace_summary.get("pages_with_semantic_argument_rewrite"):
        immediate.append("复杂页论证一致性规则并入行业 QA / prompt 片段。")

    if buckets["内容问题"] and not trace_summary.get("pages_with_semantic_argument_rewrite"):
        observe.append("一般性文案提炼与中文可读性问题继续观察更多项目，再决定抽成通用重写规则。")
    if manifest_issues and not any("模板" in item for item in manifest_issues):
        observe.append("本轮 manifest 失败项可先观察是否跨项目复现，再决定是否升级为硬阻断。")

    if not buckets["模板问题"] and not buckets["内容问题"] and not buckets["复杂页问题"] and not manifest_issues:
        special_case.append("当前没有新增问题，暂不新增项目特例。")

    return {
        "建议立即合并": unique_keep_order(immediate),
        "建议观察更多案例后再合并": unique_keep_order(observe),
        "仅保留为项目特例": unique_keep_order(special_case),
    }


def build_markdown(
    project: Path,
    buckets: dict[str, list[str]],
    trace_summary: dict[str, Any],
    manifest_issues: list[str],
    rule_suggestions: dict[str, list[str]],
    merge_advice: dict[str, list[str]],
) -> str:
    lines = [
        "# Learning Update",
        "",
        f"- 项目：`{project}`",
        f"- 自动执行轨迹文件数：{int(trace_summary.get('trace_file_count', 0) or 0)}",
        "",
        "## 一、本次问题概览",
        "",
    ]
    for title in SECTION_ORDER:
        items = buckets[title]
        lines.append(f"### {title}")
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- 暂无")
        lines.append("")

    lines.extend(["## 二、自动修复轨迹", ""])
    auto_repair_lines = build_auto_repair_lines(trace_summary)
    if auto_repair_lines:
        lines.extend(f"- {item}" for item in auto_repair_lines)
    else:
        lines.append("- 暂无自动修复 / 自动重构轨迹。")
    lines.append("")

    lines.extend(["## 三、Manifest 摘要", ""])
    if manifest_issues:
        lines.extend(f"- {item}" for item in manifest_issues)
    else:
        lines.append("- 当前未读取到新的 manifest 失败项。")
    lines.append("")

    lines.extend(["## 四、建议新增规则", ""])
    for title in ("模板层", "行业层", "通用 QA 层"):
        lines.append(f"### {title}")
        items = rule_suggestions[title]
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- 暂无")
        lines.append("")

    lines.extend(["## 五、是否建议合并", ""])
    for title in ("建议立即合并", "建议观察更多案例后再合并", "仅保留为项目特例"):
        lines.append(f"### {title}")
        items = merge_advice[title]
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- 暂无")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="根据 findings、qa_manifest 与执行轨迹生成 learning update。")
    parser.add_argument("project_path", help="Project directory")
    parser.add_argument("--findings", help="可选：人工整理的问题清单（markdown / txt）")
    parser.add_argument("-o", "--output", help="Output path; defaults to <project>/notes/learning_update.md")
    args = parser.parse_args()

    project = Path(args.project_path).expanduser().resolve()
    findings_path = Path(args.findings).expanduser().resolve() if args.findings else None
    if findings_path and not findings_path.exists():
        raise FileNotFoundError(f"findings file not found: {findings_path}")

    manifest = load_json(project / "qa_manifest.json")
    traces = load_execution_traces(project)
    trace_summary = resolve_execution_trace(manifest, traces)
    manifest_issues = build_manifest_issue_lines(manifest)
    buckets = load_findings(findings_path)
    buckets = enrich_buckets(buckets, manifest_issues, trace_summary)
    rule_suggestions = build_rule_suggestions(buckets, trace_summary, manifest_issues)
    merge_advice = build_merge_advice(buckets, trace_summary, manifest_issues)

    output = Path(args.output).expanduser().resolve() if args.output else project / "notes" / "learning_update.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    content = build_markdown(
        project,
        buckets,
        trace_summary,
        manifest_issues,
        rule_suggestions,
        merge_advice,
    )
    output.write_text(content, encoding="utf-8")
    print(f"Wrote: {output}")


if __name__ == "__main__":
    main()
