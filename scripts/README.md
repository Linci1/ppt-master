# PPT Master 脚本总览

本目录存放 `ppt-master` 的用户侧脚本入口，覆盖 Agent 总控、项目管理、源内容转换、SVG QA、导出以及图片处理。

## 目录结构

- 顶层 `scripts/`：可直接运行的主脚本
- `scripts/image_backends/`：`image_gen.py` 的后端实现
- `scripts/svg_finalize/`：`finalize_svg.py` 使用的后处理模块
- `scripts/docs/`：按主题拆分的脚本文档
- `scripts/assets/`：脚本依赖的静态资源

## 推荐入口

现在推荐优先使用统一入口：

```bash
python3 scripts/ppt_agent.py new <project_name> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal> --format ppt169 --source <file_or_url>
```

它会把“新建项目 + `/plan` 产物生成 + 可选源材料导入”收口成一次调用，更符合 PPT Agent 的实际使用方式。

## 快速开始

典型全链路如下：

```bash
python3 scripts/ppt_agent.py new <project_name> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal> --format ppt169 --source <file_or_url>
python3 scripts/ppt_agent.py status <project_path>
python3 scripts/check_svg_text_fit.py <project_path>/svg_output
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/check_svg_text_fit.py <project_path>/svg_final
python3 scripts/render_svg_pages.py <project_path> -s final
python3 scripts/svg_to_pptx.py <project_path> -s final
python3 scripts/check_pptx_fonts.py <project_path>
python3 scripts/write_qa_manifest.py <project_path> --format ppt169
```

## 脚本分区

| 分区 | 主脚本 | 说明文档 |
|------|--------|----------|
| Agent 总控 | `ppt_agent.py`, `plan_interview.py`, `build_production_packet.py`, `build_design_spec_scaffold.py`, `build_design_spec_draft.py`, `build_project_design_spec.py`, `auto_repair_execution_artifacts.py`, `build_svg_execution_pack.py`, `ingest_reference_ppt.py`, `distill_case_patterns.py`, `build_project_brief.py`, `select_template_and_domain.py`, `build_storyline.py`, `update_learning_registry.py` | `../workflows/ppt-agent.md`, `../references/plan-question-bank.md` |
| 源内容转换 | `pdf_to_md.py`, `doc_to_md.py`, `web_to_md.py`, `web_to_md.cjs` | [docs/conversion.md](./docs/conversion.md) |
| 项目管理 | `project_manager.py`, `batch_validate.py`, `generate_examples_index.py`, `error_helper.py` | [docs/project.md](./docs/project.md) |
| SVG 主链路 | `finalize_svg.py`, `svg_to_pptx.py`, `total_md_split.py`, `svg_quality_checker.py`, `check_svg_text_fit.py`, `render_svg_pages.py`, `check_pptx_fonts.py`, `write_qa_manifest.py` | [docs/svg-pipeline.md](./docs/svg-pipeline.md) |
| 图片工具 | `image_gen.py`, `analyze_images.py`, `gemini_watermark_remover.py` | [docs/image.md](./docs/image.md) |
| 排障 | 校验、预览、导出、依赖问题 | [docs/troubleshooting.md](./docs/troubleshooting.md) |

## 高频命令

### 1. PPT Agent 入口

```bash
python3 scripts/ppt_agent.py new <project_name> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal> --format ppt169
python3 scripts/ppt_agent.py plan <project_path> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal> --source <file_or_url>
python3 scripts/ppt_agent.py produce <project_path>
python3 scripts/ppt_agent.py execute <project_path>
python3 scripts/ppt_agent.py run <project_path>
python3 scripts/ppt_agent.py learn <pptx_file> --domain <domain> --copy-source --distill
python3 scripts/ppt_agent.py improve <project_path> --findings <findings_file>
python3 scripts/ppt_agent.py improve <project_path>
python3 scripts/ppt_agent.py status <project_path>
```

如果信息还不完整，也可以直接先开项目：

```bash
python3 scripts/ppt_agent.py new <project_name> --industry <industry>
```

此时 Agent 不会硬生成 brief，而是先在项目下写出：

- `notes/plan_answers.json`
- `notes/plan_questions.md`
- `notes/plan_readiness.md`
- `notes/plan_agent_state.json`
- `notes/plan_next_turn.md`
- `notes/plan_rounds.json`
- `notes/plan_dialogue.md`
- `notes/plan_session_status.md`

并按“每轮最多 3 个问题”的方式组织下一轮追问。等你补齐核心信息后，再继续进入正式 `/plan`。

如果当前项目已经明显命中安服 / 长亭品牌语境，`/plan` 还会自动补一层行业化追问：

- 安服场景：优先追问“要证明什么、哪些页值得复杂化、是否允许直接使用证据截图”
- 长亭品牌场景：优先追问“应选哪套长亭模板、品牌骨架固定到什么程度”

当 `/plan` 补齐后，可以再执行：

```bash
python3 scripts/ppt_agent.py produce <project_path>
```

它会生成：

- `notes/production_readiness.md`
- `notes/production_packet.md`
- `notes/strategist_packet.md`
- `notes/complex_page_models.md`
- `notes/design_spec_scaffold.md`
- `notes/design_spec_draft.md`

用于判断是否已经可以稳定进入 Strategist / Executor。

通过后继续执行：

```bash
python3 scripts/ppt_agent.py execute <project_path>
```

它会生成：

- `design_spec.md`
- `notes/execution_readiness.md`
- `notes/execution_runbook.md`

并自动跑一轮 `design_spec_validator.py` 与 `check_complex_page_model.py`。

如果还希望继续生成 Strategist / Executor 的角色交接文件，再执行：

```bash
python3 scripts/ppt_agent.py run <project_path>
```

它会继续生成：

- `notes/strategist_handoff.md`
- `notes/executor_handoff.md`
- `notes/agent_run_status.md`
- `notes/auto_repair_report.md`
- `notes/svg_execution_queue.md`
- `notes/svg_generation_status.md`
- `notes/svg_execution_state.json`
- `notes/svg_current_bundle.md`
- `notes/svg_current_review.md`
- `notes/svg_execution_log.md`
- `notes/svg_postprocess_plan.md`
- `notes/page_briefs/`

如果要把正式 SVG 逐页执行做成状态化流程，可继续用：

```bash
python3 scripts/ppt_agent.py svg-exec init <project_path>
python3 scripts/ppt_agent.py svg-exec next <project_path>
python3 scripts/ppt_agent.py svg-exec render <project_path> --page <页码或SVG名>
python3 scripts/ppt_agent.py svg-exec complete <project_path> --page <页码或SVG名> --note "本页已通过 QA"
python3 scripts/ppt_agent.py svg-exec mark <project_path> --page <页码或SVG名> --status completed --note "本页已通过 QA"
python3 scripts/ppt_agent.py svg-exec sync <project_path>
python3 scripts/ppt_agent.py svg-exec summary <project_path>
```

其中：

- `notes/svg_current_bundle.md`：当前页统一执行总包
- `notes/svg_current_review.md`：当前页硬性 + 软性 QA 审核卡
- `notes/svg_execution_state.json`：机器可读状态源

如果希望把“当前页 SVG 先由脚本直接画出 starter 版本”，可以使用：

```bash
python3 scripts/ppt_agent.py svg-exec render <project_path> --page <页码或SVG名>
```

它会：

- 读取当前页 brief / outline / project brief
- 选择当前页模板 SVG
- 直接写出 `svg_output/<page>.svg`
- 立即做一次 `check_svg_text_fit` + `svg_quality_checker` 快照
- 在 `notes/page_execution/` 下输出本页自动执行报告

### 2. 底层项目管理

```bash
python3 scripts/project_manager.py init <project_name> --format ppt169
python3 scripts/project_manager.py import-sources <project_path> <source_files...> --move
python3 scripts/project_manager.py bootstrap-agent <project_path> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal>
python3 scripts/project_manager.py validate <project_path>
python3 scripts/project_manager.py info <project_path>
```

### 3. Agent 底层能力

```bash
python3 scripts/ingest_reference_ppt.py <pptx_file> --domain <domain> --copy-source
python3 scripts/distill_case_patterns.py <case_dir> -o <output.md>
python3 scripts/build_project_brief.py -o <project_path>/project_brief.md --project-name <name> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal>
python3 scripts/plan_interview.py <project_path> --industry <industry> --scenario <scenario>
python3 scripts/build_production_packet.py <project_path>
python3 scripts/build_design_spec_scaffold.py <project_path>
python3 scripts/build_design_spec_draft.py <project_path>
python3 scripts/build_project_design_spec.py <project_path>
python3 scripts/auto_repair_execution_artifacts.py <project_path>
python3 scripts/build_svg_execution_pack.py <project_path>
python3 scripts/select_template_and_domain.py <project_path>/project_brief.md -o <project_path>/notes/template_domain_recommendation.md
python3 scripts/build_storyline.py <project_path>/project_brief.md --storyline-output <project_path>/notes/storyline.md --outline-output <project_path>/notes/page_outline.md
python3 scripts/update_learning_registry.py <project_path> --findings <findings_file>
python3 scripts/update_learning_registry.py <project_path>
```

### 4. 后处理与导出

```bash
python3 scripts/total_md_split.py <project_path>
python3 scripts/finalize_svg.py <project_path>
python3 scripts/check_svg_text_fit.py <project_path>/svg_final
python3 scripts/render_svg_pages.py <project_path> -s final
python3 scripts/svg_to_pptx.py <project_path> -s final
python3 scripts/check_pptx_fonts.py <project_path>
python3 scripts/write_qa_manifest.py <project_path> --format ppt169
```

### 5. 图片处理

```bash
python3 scripts/image_gen.py "A modern futuristic workspace"
python3 scripts/image_gen.py --list-backends
python3 scripts/analyze_images.py <project_path>/images
```

## 使用建议

- 对“新做一份 PPT”的场景，优先从 `ppt_agent.py new` 开始，而不是手工拼接多条命令
- 对“学习历史案例”的场景，优先用 `ppt_agent.py learn` 把素材先进入 `case_library/`
- 对“已有项目复盘”的场景，优先用 `ppt_agent.py improve` 输出结构化学习回写建议
- 底层脚本仍保留，便于你按需插入更细粒度的控制点
- 对带 `qa_profile.md` 或固定品牌骨架的模板，`svg_quality_checker.py` 的阻塞告警必须视为硬失败
- 导出时优先使用 `svg_final/`，不要直接从 `svg_output/` 导出
- `svg_to_pptx.py` 导出前会自动刷新 `qa_manifest.json` 并执行硬门禁；存在阻断项时不会产出最终 PPT

## 相关文档

- [Agent 总控工作流](../workflows/ppt-agent.md)
- [转换工具](./docs/conversion.md)
- [项目工具](./docs/project.md)
- [SVG 流水线工具](./docs/svg-pipeline.md)
- [图片工具](./docs/image.md)
- [排障文档](./docs/troubleshooting.md)
- [仓库入口说明](../AGENTS.md)

_最后更新：2026-04-07_
