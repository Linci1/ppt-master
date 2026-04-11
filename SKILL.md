---
name: ppt-master
description: >
  基于 AI 的多格式 SVG 内容生成系统。可将源文档（PDF/DOCX/URL/Markdown）
  转换为高质量 SVG 页面，并通过多角色协作导出为 PPTX。适用于用户提出
  “创建 PPT”“make presentation”“生成PPT”“做PPT”“制作演示文稿”或提到
  “ppt-master” 的场景。
---

# PPT Master 技能说明

> 基于 AI 的多格式 SVG 内容生成系统。将源文档通过多角色协作转换为高质量 SVG 页面，并最终导出为 PPTX。

**核心流水线**：`源文档 → 创建项目 → 模板选择 → Strategist → [Image_Generator] → Executor → 后处理 → 导出`

> [!CAUTION]
> ## 🚨 全局执行纪律（强制）
>
> **本工作流是严格串行流水线。以下规则优先级最高——违反任意一条都视为执行失败：**
>
> 1. **串行执行** —— 各步骤必须按顺序执行；上一步输出就是下一步输入。相邻的非阻塞步骤在满足前置条件后可连续推进，不需要等待用户再说“继续”
> 2. **阻塞 = 必须停下** —— 标记为 ⛔ BLOCKING 的步骤必须完全暂停；AI 必须等待用户明确回复，且不得替用户做决定
> 3. **禁止跨阶段打包执行** —— 严禁把多个阶段混在一起执行。（注意：第 4 步中的“八项确认”属于 ⛔ BLOCKING —— AI 必须先给出建议并等待用户明确确认后才能继续。一旦用户确认，后续所有非阻塞步骤——设计规格输出、SVG 生成、讲稿生成、后处理——都应自动连续执行）
> 4. **先过门禁再进入** —— 每个步骤开头列出的前置条件（🚧 GATE）都必须先验证通过，才能开始该步骤
> 5. **禁止预执行** —— 不允许提前准备后续阶段内容（例如在 Strategist 阶段就开始写 SVG）
> 6. **禁止子代理生成 SVG** —— 第 6 步 Executor 阶段的 SVG 生成强依赖上下文，必须由当前主代理完整执行到底，禁止委托给子代理逐页生成
> 7. **SVG 页面必须严格顺序生成** —— 在第 6 步中，确认全局设计上下文后，所有页面必须按页码顺序连续逐页生成，禁止分批生成（例如每次生成 5 页）

> [!IMPORTANT]
> ## 🌐 语言与沟通规则
>
> - **回复语言**：始终与用户输入语言和源材料语言保持一致。例如用户用中文提问，就用中文回复；如果源材料是英文，也可按英文处理
> - **显式覆盖**：如果用户明确要求使用某种语言（如“请用英文回答”），则以用户指定语言为准
> - **模板格式**：`design_spec.md` 文件必须始终保持其原始英文模板结构（标题、字段名不变），不受对话语言影响；但字段内容可以使用用户语言

> [!IMPORTANT]
> ## 🔌 与通用编程类技能的兼容规则
>
> - `ppt-master` 是仓库专用工作流 skill，不是通用项目脚手架
> - 默认不要创建或要求 `.worktrees/`、`tests/`、分支流程等通用工程结构
> - 如果其他通用编程 skill 的建议与本工作流冲突，除非用户明确要求，否则优先遵循本 skill

## 主流水线脚本

| 脚本 | 用途 |
|--------|---------|
| `${SKILL_DIR}/scripts/pdf_to_md.py` | PDF 转 Markdown |
| `${SKILL_DIR}/scripts/doc_to_md.py` | 通过 Pandoc 将文档转为 Markdown（DOCX、EPUB、HTML、LaTeX、RST 等） |
| `${SKILL_DIR}/scripts/web_to_md.py` | 网页转 Markdown |
| `${SKILL_DIR}/scripts/web_to_md.cjs` | 微信文章 / 高安全站点转 Markdown |
| `${SKILL_DIR}/scripts/ppt_agent.py` | 统一 Agent 入口：`new / plan / produce / execute / run / learn / improve / status` |
| `${SKILL_DIR}/scripts/plan_interview.py` | `/plan` 结构化问卷、追问清单与就绪度报告生成 |
| `${SKILL_DIR}/scripts/build_production_packet.py` | `produce` 阶段的生产就绪报告与执行包生成 |
| `${SKILL_DIR}/scripts/build_design_spec_scaffold.py` | 基于当前规划结果生成 `design_spec` 草案骨架 |
| `${SKILL_DIR}/scripts/build_design_spec_draft.py` | 基于当前规划结果生成更接近可用的 `design_spec` 初稿 |
| `${SKILL_DIR}/scripts/build_project_design_spec.py` | 基于规划层结果生成项目根目录 `design_spec.md` 首稿 |
| `${SKILL_DIR}/scripts/auto_repair_execution_artifacts.py` | 自动修补 `design_spec.md` 与 `complex_page_models.md` 中的 warning / 软问题 |
| `${SKILL_DIR}/scripts/build_svg_execution_pack.py` | 生成 SVG 正式执行编排包、逐页 brief 与后处理计划 |
| `${SKILL_DIR}/scripts/project_manager.py` | 项目初始化 / 校验 / 管理 |
| `${SKILL_DIR}/scripts/ingest_reference_ppt.py` | 历史 PPT 案例入库与结构化拆解 |
| `${SKILL_DIR}/scripts/distill_case_patterns.py` | 跨案例模式蒸馏 |
| `${SKILL_DIR}/scripts/build_project_brief.py` | `/plan` 阶段输出标准 brief |
| `${SKILL_DIR}/scripts/select_template_and_domain.py` | 根据 brief 推荐模板与行业包 |
| `${SKILL_DIR}/scripts/build_storyline.py` | 生成 storyline / page outline 骨架 |
| `${SKILL_DIR}/scripts/update_learning_registry.py` | 项目问题复盘与规则回写建议 |
| `${SKILL_DIR}/scripts/analyze_images.py` | 图片分析 |
| `${SKILL_DIR}/scripts/image_gen.py` | AI 图片生成（多供应商） |
| `${SKILL_DIR}/scripts/check_complex_page_model.py` | 复杂页建模中间层校验 |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG 质量检查 |
| `${SKILL_DIR}/scripts/check_svg_text_fit.py` | SVG 文本越界与卡片内碰撞检查 |
| `${SKILL_DIR}/scripts/render_svg_pages.py` | SVG 渲染图抽检（视觉 QA） |
| `${SKILL_DIR}/scripts/check_pptx_fonts.py` | 导出后 PPTX 字体一致性检查 |
| `${SKILL_DIR}/scripts/write_qa_manifest.py` | QA 结果记录输出 |
| `${SKILL_DIR}/scripts/total_md_split.py` | 讲稿拆分 |
| `${SKILL_DIR}/scripts/finalize_svg.py` | SVG 后处理（统一入口） |
| `${SKILL_DIR}/scripts/svg_to_pptx.py` | 导出 PPTX |

完整脚本文档见 `${SKILL_DIR}/scripts/README.md`。

## 模板索引

| 索引 | 路径 | 用途 |
|-------|------|---------|
| 布局模板 | `${SKILL_DIR}/templates/layouts/layouts_index.json` | 查询可用页面布局模板 |
| 图表模板 | `${SKILL_DIR}/templates/charts/charts_index.json` | 查询可用图表 SVG 模板 |
| 图标库 | `${SKILL_DIR}/templates/icons/icons_index.json` | 查询可用图标名称与分类 |

## Agent 资产

| 资产 | 路径 | 用途 |
|------|------|------|
| Agent 总控流 | `${SKILL_DIR}/workflows/ppt-agent.md` | 定义 `learn / plan / produce / execute / run / improve` 六模式 |
| `/plan` 提问题库 | `${SKILL_DIR}/references/plan-question-bank.md` | 需求澄清与 brief 收敛 |
| Brief 模板 | `${SKILL_DIR}/references/project-brief-template.md` | 统一项目简报结构 |
| Storyline 模板 | `${SKILL_DIR}/references/storyline-template.md` | 统一叙事结构草案 |
| Page Outline 模板 | `${SKILL_DIR}/references/page-outline-template.md` | 统一逐页任务定义 |
| 案例库 | `${SKILL_DIR}/case_library/` | 存放历史 PPT 案例与蒸馏结果 |
| 行业包 | `${SKILL_DIR}/domain_packs/` | 行业表达、术语、页型与 QA 规则 |

## 独立工作流

| 工作流 | 路径 | 用途 |
|----------|------|---------|
| `create-template` | `workflows/create-template.md` | 独立模板创建工作流 |
| `ppt-agent` | `workflows/ppt-agent.md` | 总控 Agent：先澄清需求，再生成与沉淀 |

---

## 当前 Agent 落地方式

`ppt-master` 现在已经不是单纯的“文档转 PPT”脚本集合，而是一个分层运行的 PPT Agent。实际执行时，优先按下面的理解推进：

- 规划层：`new / plan / produce`
- 执行准备层：`execute / run`
- 正式生成层：`Strategist / Image_Generator / Executor / QA / Export`

对用户而言，真正需要明确给指令的关键节点通常只有这几处：

1. 立项时说明行业、场景、受众、目标、展示重点、模板偏好
2. `/plan` 追问后补齐缺失信息
3. 模板与页纲出来后确认页数、复杂页比例、品牌约束
4. 成品复盘时把问题反馈回 `improve`

其余像 `produce -> execute -> run` 这些中间层，在前置条件满足时应自动连续推进，不要要求用户机械重复“继续”。

> 注意：当前 `run` 已能生成执行交接包、SVG 执行队列、当前页上下文包和当前页 QA 审核卡，但“正式 SVG 逐页视觉内容由 runner 独立生成”和“成熟顾问表达的软性判断完全自动闭环修复”仍未完全脚本化，因此本系统目前更准确地说是“可用的半自动 PPT Agent”。

> 现阶段补充说明：仓库已新增“当前页独立执行器”入口，可由脚本直接把当前页写成 starter SVG 并立即做一轮技术 QA；同时 `run` 会生成 `notes/page_execution_contracts.json`，把每页冻结为固定页 / 普通页 / 复杂页三类执行通道，并给出默认自动修复轮数。默认策略为：固定页 `0` 轮、普通页 `1` 轮、复杂页 `1` 轮；相邻复杂页如需换骨架，只允许在首轮渲染前预处理一次，不再在 render 失败后晚重构。QA 也按层级分流：固定页走 `brand_skeleton`，普通页走 `layout_and_density`，复杂页保留 `complex_full`。

---

## 工作流

### Step 0：Agent 模式识别与 `/plan` 前置门

🚧 **GATE**：用户已明确本次任务是“吸收案例 / 生成新 PPT / 复盘已有项目”中的一种。

首先读取：
```text
Read workflows/ppt-agent.md
Read references/plan-question-bank.md
Read references/project-brief-template.md
```

按以下规则先判定模式：

- 若用户提供的是历史优秀 `.pptx` 素材，并希望“学习 / 吸收 / 抽象规律”，进入 `learn`
- 若用户希望做一份新的 PPT，进入 `plan`
- 若用户已经有产出并希望“检查 / 修复 / 总结问题 / 沉淀规则”，进入 `improve`

#### Step 0.1 `learn`：案例吸收

当命中 `learn` 时，先做案例入库，而不是直接改模板：

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py learn <pptx_file> --domain <domain> --copy-source --distill
```

- 案例先进入 `${SKILL_DIR}/case_library/`
- 只有当多案例重复出现的规律成立时，才建议升级为模板规则或行业规则
- 品牌骨架优先回写模板目录；行业逻辑、术语、复杂页打法优先回写 `${SKILL_DIR}/domain_packs/`

#### Step 0.2 `plan`：需求澄清

当命中“新建 PPT”时，**默认先进入 `/plan`**，不得直接进入源内容处理或 SVG 生成。

如果用户信息还不完整，也不要强行要求一次性补齐所有参数。此时可先生成 `/plan` 收集包：

```bash
python3 ${SKILL_DIR}/scripts/plan_interview.py <project_path> \
  [--industry <industry>] \
  [--scenario <scenario>] \
  [--audience <audience>] \
  [--goal <goal>]
```

它会在项目下生成：

- `notes/plan_answers.json`
- `notes/plan_questions.md`
- `notes/plan_readiness.md`

只有当 `plan_readiness.md` 判定核心字段已齐备后，才进入 `build_project_brief.py` / `bootstrap-agent`。

`/plan` 至少要澄清：

1. 行业与场景
2. 展示对象
3. 本次目标
4. 展示重点
5. 品牌与模板要求
6. 材料与资源
7. 交付约束

推荐输出：

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py new <project_name> \
  --industry <industry> \
  --scenario <scenario> \
  --audience <audience> \
  --goal <goal> \
  [--format ppt169] \
  [--source <file_or_url>] \
  [--template <template>] \
  [--style <style>] \
  [--priorities a,b,c] \
  [--materials x,y,z] \
  [--constraints p,q,r]
```

若项目已经存在，则改用：

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py plan <project_path> \
  --industry <industry> \
  --scenario <scenario> \
  --audience <audience> \
  --goal <goal> \
  [--source <file_or_url>] \
  [--template <template>] \
  [--style <style>] \
  [--priorities a,b,c] \
  [--materials x,y,z] \
  [--constraints p,q,r]
```

> `ppt_agent.py new/plan` 现在支持“信息不完整先停在 `/plan` 收集层”的模式：若行业、场景、受众、目标、展示重点未补齐，不会直接生成 brief，而是先写出 `plan_answers.json`、`plan_questions.md`、`plan_readiness.md`。

> ⚠️ 若 `project_brief.md` 尚未形成，或用户目标、受众、重点仍不清晰，不得直接进入 Step 1。

#### Step 0.3 `produce`：故事线预规划

在正式源内容处理前，若已执行 `ppt_agent.py new/plan`（底层会调用 `bootstrap-agent`），则 `project_brief.md`、`notes/template_domain_recommendation.md`、`notes/storyline.md`、`notes/page_outline.md` 应已同步产出。

进入正式生成前，建议再执行一次：

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py produce <project_path>
```

它会输出：

- `notes/production_readiness.md`
- `notes/production_packet.md`
- `notes/strategist_packet.md`
- `notes/complex_page_models.md`
- `notes/design_spec_scaffold.md`
- `notes/design_spec_draft.md`

用来确认规划层是否仍有待确认字段、是否缺少源材料、是否已经可以稳定进入 Strategist / Executor；同时为 Strategist、`design_spec` 草案 / 初稿编写和复杂页建模准备直接可读的执行骨架。

这样后续 Strategist 与 Executor 不再只是“看文档临场发挥”，而是先围绕 brief、模板、行业包和案例模式做页级规划。

#### Step 0.4 `execute`：正式执行交接

当 `produce` 已通过后，再执行：

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py execute <project_path> [--auto-repair]
```

它会自动：

- 刷新 `notes/production_readiness.md`、`notes/production_packet.md`
- 生成或保留项目根目录 `design_spec.md`
- 输出 `notes/execution_readiness.md`
- 输出 `notes/execution_runbook.md`
- 自动运行 `design_spec_validator.py`
- 自动运行 `check_complex_page_model.py`

如果加上 `--auto-repair`，还会额外：

- 自动修补 `design_spec.md` 中的复杂页误判、页型回退说明、关系字段缺漏
- 自动补强 `notes/complex_page_models.md` 中的分判断、论证主线、证据分级、视觉焦点排序
- 输出 `notes/auto_repair_report.md`

如果项目里已经有人手工完善过 `design_spec.md`，默认不会覆盖；只有显式加 `--refresh-design-spec` 才会按当前规划结果重刷。

#### Step 0.5 `run`：进入 Strategist / Executor 调度入口

如果你希望一条命令把 `produce + execute + auto-repair + 角色交接文件` 全部串起来，可直接执行：

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py run <project_path>
```

它会额外生成：

- `notes/strategist_handoff.md`
- `notes/executor_handoff.md`
- `notes/agent_run_status.md`
- `notes/svg_execution_queue.md`
- `notes/svg_generation_status.md`
- `notes/svg_postprocess_plan.md`
- `notes/page_execution_contracts.json`
- `notes/page_briefs/`

用于把项目正式推进到 Strategist / Executor 主链路，而不是只停留在“文件已准备好”的状态。

#### Step 0.6 `improve`：项目复盘沉淀

当命中已有项目复盘时，可在 QA 或修复结束后输出：

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py improve <project_path> \
  --findings <findings_file>
python3 ${SKILL_DIR}/scripts/ppt_agent.py improve <project_path>
```

- 输出位置默认：`<project_path>/notes/learning_update.md`
- 目标是把问题分为：模板问题 / 内容问题 / 复杂页问题 / QA 漏检问题
- 若未额外提供 `findings`，也会自动吸收 `qa_manifest.json` 与 `notes/page_execution/*.json` 中的自动修复轨迹
- 仅在人工确认后，再决定是否写回模板或行业包

**✅ 检查点——已完成模式识别；若为新建 PPT，`/plan` 已完成且 `project_brief.md` 可用，再进入 Step 1。**

### Step 1：源内容处理

🚧 **GATE**：Step 0 已完成；若任务属于“新建 PPT”，则 `project_brief.md` 已存在，且用户已经提供源材料（PDF / DOCX / EPUB / URL / Markdown 文件 / 文本描述 / 对话内容——任意一种都可以）。

当用户提供的不是 Markdown 内容时，要立即转换：

| 用户提供 | 命令 |
|---------------|---------|
| PDF 文件 | `python3 ${SKILL_DIR}/scripts/pdf_to_md.py <file>` |
| DOCX / Word / Office 文档 | `python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| EPUB / HTML / LaTeX / RST / 其他 | `python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| 网页链接 | `python3 ${SKILL_DIR}/scripts/web_to_md.py <URL>` |
| 微信文章 / 高安全站点 | `node ${SKILL_DIR}/scripts/web_to_md.cjs <URL>` |
| Markdown | 直接读取 |

**✅ 检查点——确认源内容已准备好，进入 Step 2。**

---

### Step 2：项目初始化

🚧 **GATE**：Step 1 已完成；源内容已准备好（Markdown 文件、用户在对话中直接提供的文本、或对需求的文字说明都可以）。

```bash
python3 ${SKILL_DIR}/scripts/ppt_agent.py new <project_name> --format <format> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal>
```

格式选项：`ppt169`（默认）、`ppt43`、`xhs`、`story` 等。完整格式列表见 `references/canvas-formats.md`。

导入源内容（按实际情况选择）：

| 场景 | 动作 |
|-----------|--------|
| 有源文件（PDF/MD 等） | `python3 ${SKILL_DIR}/scripts/ppt_agent.py plan <project_path> --source <source_file_or_url> ...` 或 `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files...> --move` |
| 用户直接在对话里提供文本 | 无需导入——内容已经在上下文中，后续步骤可直接引用 |

> ⚠️ **必须使用 `--move`**：所有源文件（原始 PDF / MD / 图片）都必须**移动**而不是复制进 `sources/` 做归档。
> - 第 1 步生成的 Markdown、原始 PDF、原始 MD —— **都必须**通过 `import-sources --move` 移入项目
> - 中间产物（例如 `_files/` 目录）由 `import-sources` 自动处理
> - 执行后，原路径下的源文件将不再保留

**✅ 检查点——确认项目结构已创建成功，`sources/` 中包含所有源文件，转换材料已就绪。进入 Step 3。**

---

### Step 3：模板选择

🚧 **GATE**：Step 2 已完成；项目目录结构已准备好。

⛔ **BLOCKING**：如果用户还没有明确表示是否使用模板，你必须先给出选项，并**等待用户明确回复**后才能继续。如果用户之前已经说过“不使用模板”或已指定具体模板，则跳过本提示，直接进入下一步。

**⚡ 早退出**：如果用户在此前任意位置已经明确表示“no template” / “不使用模板” / “自由设计”等同义意思，**不要查询 `layouts_index.json`**，直接跳到 Step 4，以避免不必要的 token 消耗。

**模板推荐流程**（仅当用户还未做出选择时）：
查询 `${SKILL_DIR}/templates/layouts/layouts_index.json`，列出可用模板及其风格说明。
**在给出选项时，必须结合当前 PPT 主题和内容给出专业推荐**（推荐某个具体模板或自由设计，并说明原因），然后向用户发问：

> 💡 **AI 推荐**：根据你的内容主题（简要概述），我建议使用 **[具体模板 / 自由设计]**，因为……
>
> 你更希望采用哪种方式？
> **A）使用现有模板**（请指定模板名或风格偏好）
> **B）不使用模板** —— 自由设计

> **模板选择原则**：默认仍由用户决定是否使用模板以及使用哪个模板。本 skill 不会强行锁死为单模板系统；但如果用户选择带有 `stabilityProfile` / `qa_profile.md` 的模板（例如展示名为“长亭通用墨绿色”、模板 ID 为 `chaitin`），则必须保留该模板的固定骨架元素，同时允许正文内容区继续灵活编排，不得为了追求统一而把所有页都做成单一版式。

当用户确认选项 A 后，把模板文件复制到项目目录：
```bash
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.svg <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/design_spec.md <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.md <project_path>/templates/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.png <project_path>/images/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.jpg <project_path>/images/ 2>/dev/null || true
cp -R ${SKILL_DIR}/templates/layouts/<template_name>/images <project_path>/ 2>/dev/null || true
cp -r ${SKILL_DIR}/templates/layouts/<template_name>/images/icons <project_path>/images/ 2>/dev/null || true
```

当用户确认选项 B 后，直接进入 Step 4。

> 若需创建新的全局模板，请阅读 `workflows/create-template.md`

**✅ 检查点——用户已完成模板选择；如选择模板，模板文件已复制完成。进入 Step 4。**

---

### Step 4：Strategist 阶段（强制，不能跳过）

🚧 **GATE**：Step 3 已完成；用户已确认模板选择。

首先读取角色定义：
```
Read references/strategist.md
```

若项目目录中已存在以下文件，则在开始八项确认前还必须先读取：

```text
Read <project_path>/project_brief.md
Read <project_path>/notes/template_domain_recommendation.md
Read <project_path>/notes/storyline.md
Read <project_path>/notes/page_outline.md
```

> **项目级前置规划规则（强制）**：对新建 PPT 项目，`project_brief.md`、`notes/storyline.md`、`notes/page_outline.md` 不再只是“可参考文件”，而是 Strategist 的正式上游输入。写 `design_spec.md` 时，必须显式继承这些文件中的受众、目标、优先级、章节推进和逐页意图，而不是重新另起一套逻辑。

**必须完成“八项确认”**（模板结构参考 `templates/design_spec_reference.md`）：

⛔ **BLOCKING**：八项确认必须作为一组建议统一呈现给用户，且在输出设计规格与内容大纲之前，**必须等待用户确认或修改**。这是整个工作流中仅有的两个核心确认点之一（另一个是模板选择）。一旦用户确认，后续脚本执行与幻灯片生成应自动连续推进。

1. 画布格式
2. 页数范围
3. 目标受众
4. 风格目标
5. 配色方案
6. 图标使用方式
7. 字体方案
8. 图片使用方式

如果用户提供了图片，在输出设计规格之前必须先运行分析脚本（**不要直接读取/打开图片文件，只能使用脚本输出结果**）：
```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> ⚠️ **图片处理规则**：AI **不得**直接读取、打开或查看图片文件（`.jpg`、`.png` 等）。所有图片信息都必须来自 `analyze_images.py` 的输出或设计规格中的“图片资源列表”。

**输出**：`<project_path>/design_spec.md`

> **模板本地文档读取**：八项确认完成后，如果使用了模板，**必须**读取所选模板目录下的所有 markdown 文档（特别是 `templates/design_spec.md`、`qa_profile.md`、`ppt_logic_reference.md`、`text_prompt_snippets.md`、`generation_checklist.md`、Section X「Template Local Assets」和 Section XI「Content Page Selection Guide」），以及其他模板参考文档。这些文档包含：
> - 模板本地图标的使用方式（通过 `<image>` 而非 `<use data-icon>`）
> - 内容页模板与内容类型的映射关系
> - 模板固定骨架、保护区和高风险页的修复策略
> - 该类 PPT 的编辑逻辑与写作风格指南
> - 模板特有的正文文本提炼规则、术语黑白名单、复杂页 prompt 片段
> - 模板生成前与导出前的检查清单
> - 高级正文页的文本逻辑、图形逻辑、呈现效果与文图协同规则
> - 对 `security_service`，还应把 `sample_grade_content_system.md` 作为案例级复杂正文补充基线，用于约束论证主线、证据锚点、文本压缩和跨页推进
> - 若模板目录存在 `soft_content_qa_framework.md`，则还必须把它作为软性内容 QA 基线，用于拦截“有其表、无其实”的逻辑混乱页
> - 若模板目录还存在 `soft_content_rewrite_strategies.md`，则命中软性内容问题后，必须按其中的页面级重写顺序修正标题、模块、证据与页尾收束，而不能只做局部润色
>
> 这些信息将整合进项目的 `design_spec.md`，确保后续 Executor 阶段能够正确调用模板资产。

> **行业包读取（新增强制）**：若 Step 0 已经识别出可匹配的行业包（位于 `${SKILL_DIR}/domain_packs/<domain>/`），则在写 `design_spec.md` 前，还必须同步读取该行业包中的规则文件，至少包括：
> - `domain_profile.md`
> - `story_patterns.md`
> - `page_logic.md`
> - `diagram_logic.md`
> - `terminology_rules.md`
> - `qa_rules.md`
> - `rewrite_rules.md`
>
> 行业包用于补充模板之外的“行业怎么讲、复杂页怎么建、术语怎么控、软问题怎么修”。这些规则应与模板文档一起整合进 `design_spec.md` 与后续页面规划，而不是只在生成后再补救。

> **长亭安服选页门禁（强制）**：若命中 `security_service`，`design_spec.md` 的 Section IX「内容大纲」里，除封面 / 目录 / 章节 / 结束页外，每个正文页都必须显式写出：
> - `页面意图`
> - `证明目标`
> - `高级正文模式`（填写 `layered_system_map` / `timeline_roadmap` / `attack_case_chain` / `operation_loop` / `swimlane_collaboration` / `matrix_defense_map` / `maturity_model` / `evidence_wall` 之一，或填 `无`）
> - `优先页型`
> - 若 `优先页型` 为 `03_content.svg` 或 `11_list.svg`，必须额外写 `回退原因`
> - 若 `高级正文模式` 不为 `无`，还必须额外写：
>   - `页面角色`（`概览页` / `推进页` / `证明页` / `收束页` 四选一）
>   - `与上一页关系`
>   - `与下一页关系`
>
> 写完 `design_spec.md` 后，进入 Executor 前必须先运行：
>
> ```bash
> python3 ${SKILL_DIR}/scripts/design_spec_validator.py <project_path>/design_spec.md
> ```
>
> 若校验提示 `security_service` 选页字段缺失或回退理由缺失，必须先修正 `design_spec.md`，不得直接继续生成 SVG。
>
> **复杂度服从内容规则（强制）**：命中 `security_service` 时，是否使用高级正文模式，必须由源文档内容的真实结构决定，而不能为了“做得更高级”而强上复杂页。只有当文档本身存在明显的链路、分层、矩阵、闭环、协同、证据挂载、成熟度或多维映射关系时，才应命中高级正文模式。若页面核心信息本质上是单一结论、简单说明、轻量建议或普通过渡，则应优先使用更简洁但更准确的表达方式。任何复杂页都必须在 `design_spec.md` 中能回答：**为什么这页必须复杂、为什么复杂结构比简单结构更能服务文档表达**；若回答不成立，应回退为更清晰的普通页型。

> **长亭双模板差异化规则（强制）**：若命中 `chaitin` 或 `security_service`，必须把它们视为两套不同的正文生成逻辑，而不是同一套版式换皮肤。
> - `chaitin`（长亭通用墨绿色）：定位是**品牌通用表达底盘**。Strategist 应优先规划概览、方法、模块、对比、案例、建议等混合型内容结构；Executor 在正文区可灵活采用卡片、流程、时间线、图文混排、takeaway 等形式，但仍须保持品牌骨架稳定。
> - `security_service`（长亭安服）：定位是**安服专项解决方案 / 能力证明型胶片**。Strategist 应优先规划“体系总览 → 分域能力 → 结果案例 → 可信背书”的章节节奏；Executor 每页都应先回答“这页要证明什么”，优先使用能力地图、证明链、证据墙、结果导向案例等打法。
> - 禁止把 `security_service` 退化成普通通用汇报，也禁止把 `chaitin` 强行写成安服证明型胶片。

**✅ 检查点——本阶段交付完成，自动进入下一步**：
```markdown
## ✅ Strategist 阶段完成
- [x] 八项确认完成（用户已确认）
- [x] 设计规格与内容大纲已生成
- [ ] **下一步**：自动进入 [Image_Generator / Executor] 阶段
```

---

### Step 5：Image_Generator 阶段（条件触发）

🚧 **GATE**：Step 4 已完成；设计规格与内容大纲已生成并获得用户确认。

> **触发条件**：图片方案包含“AI 生成”。若未触发，直接跳到 Step 6（但 Step 6 的前置条件仍必须满足）。

读取 `references/image-generator.md`

1. 从设计规格中提取所有状态为“pending generation”的图片
2. 生成提示词文档 → `<project_path>/images/image_prompts.md`
3. 生成图片（推荐使用 CLI 工具）：
   ```bash
   python3 ${SKILL_DIR}/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
   ```

**✅ 检查点——确认所有图片已准备好，进入 Step 6**：
```markdown
## ✅ Image_Generator 阶段完成
- [x] 提示词文档已创建
- [x] 所有图片已保存到 images/
```

---

### Step 6：Executor 阶段

🚧 **GATE**：Step 4（以及如有触发则 Step 5）已完成；所有前置交付物已准备好。

根据选定风格读取对应角色定义：
```
Read references/executor-base.md          # 必读：通用执行规则
Read references/executor-visual-review.md # 必读：逐页视觉复核门
Read references/executor-general.md       # 通用灵活风格
Read references/executor-consultant.md    # 咨询风格
Read references/executor-consultant-top.md # 顶级咨询风格（MBB 级）
```

> 必须读取 executor-base + executor-visual-review + 一个风格文件。

若项目目录中已存在以下规划文件，则在生成第 1 页 SVG 前还必须先读取：

```text
Read <project_path>/project_brief.md
Read <project_path>/notes/template_domain_recommendation.md
Read <project_path>/notes/storyline.md
Read <project_path>/notes/page_outline.md
```

**设计参数确认（强制）**：在生成第一页 SVG 之前，Executor 必须回顾并输出设计规格中的关键设计参数（画布尺寸、配色方案、字体方案、正文基准字号），以确保执行严格遵循设计规格。详见 `executor-base.md` 第 2 节。

> ⚠️ **仅限主代理规则**：第 6 步中的 SVG 生成必须由当前主代理完成，因为页面设计依赖完整上游上下文（源内容、设计规格、模板映射、图片决策以及跨页一致性）。禁止把任何幻灯片 SVG 生成委托给子代理。
> ⚠️ **生成节奏规则**：确认全局设计参数后，Executor 必须在同一连续主上下文中按页码顺序逐页生成。禁止把第 6 步拆成“每次 5 页”这样的分批生成。
> ⚠️ **逐页复核门（强制）**：每生成一页草稿，Executor 都必须立刻执行 `references/executor-visual-review.md` 中定义的视觉复核，然后才能继续下一页。复核项包括：中文断句/可读性、边距与拥挤感、卡片溢出风险、页脚/Logo/页码冲突、takeaway 与正文层级分离、信息密度、是否需要精简/重排、以及同类页一致性。这些检查必须发生在**生成过程中**，而不是全部做完后的集中清理。
> ⚠️ **模板固定骨架规则（强制）**：如果模板目录中提供了 `qa_profile.md` 或在模板设计规格中声明了 fixed skeleton / protected zones，则这些骨架元素（如目录页数字-标题关系、Logo 区、页码区、底部装饰条、模板遮罩层）视为不可随意重画的稳定结构。允许灵活发挥的范围是正文内容区、图表、卡片编排与信息组织，而不是把固定骨架挪位。
> ⚠️ **长亭品牌规则（强制）**：命中长亭相关模板（如 `chaitin`、`security_service`）时，品牌元素必须固定保留。Logo 可以按模板设计规格在批准版本中切换，但**不能缺失、不能乱用、不能自行加白底/描边/底板**。如果模板提供了 `data-brand-required` / `data-brand-assets` / `data-logo-safe-zone`，这些语义必须保留到生成页中，供 QA 脚本做强制校验。
> ⚠️ **长亭模板正文逻辑分流（强制）**：命中 `chaitin` 时，重点检查“主题是否讲清楚、结构是否丰富、版式是否保持品牌节奏”；命中 `security_service` 时，重点检查“这页是否真正证明一个能力 / 结果 / 证据点、是否仍符合安服历史胶片逻辑”。两者的正文表达和页型判断标准不得混用。
> ⚠️ **项目级页面规划规则（新增强制）**：若项目存在 `notes/page_outline.md`，Executor 必须按其逐页定义生成页面。每个正文页在开始绘制前，都应能回答：这页对应哪个 outline 条目、页面意图是什么、证明目标是什么、是否应命中复杂页。若对应不上，必须先修复规划层，而不是直接画图。
> ⚠️ **模板文本治理规则（强制）**：若模板目录中存在 `text_prompt_snippets.md` 或 `generation_checklist.md`，Executor 在生成正文页前必须先读取并执行其中的模板专属文本提炼规则、术语规则和生成检查清单。若模板目录中同时存在 `qa_profile.md`，则三者共同构成模板级内容 QA 基线，不能只做版式检查而忽略文本逻辑检查。若模板目录还存在 `soft_content_qa_framework.md`，则必须额外按其中的软性问题分类检查标题-模块-证据-页尾判断是否统一；若命中软问题，且模板目录存在 `soft_content_rewrite_strategies.md`，则必须按其中的页面级重写顺序修正，而不是只微调措辞。
> ⚠️ **行业包治理规则（新增强制）**：若当前项目在 Step 0 已匹配行业包，则 Executor 在生成正文页前还必须读取该行业包中的 `story_patterns.md`、`page_logic.md`、`diagram_logic.md`、`terminology_rules.md`、`qa_rules.md`、`rewrite_rules.md`。模板负责骨架，行业包负责“行业怎么讲、复杂页如何命中、术语如何控、软问题如何修”，两者不能缺一。
> ⚠️ **复杂页建模规则（强制）**：若页面在项目级 `design_spec.md` 中已标注 `高级正文模式`，或模板本地文档（如 `advanced_page_patterns.md`、`complex_graph_semantics.md`、`complex_case_chain_modeling.md`）表明该页属于复杂页，则 Executor **不得直接开始画 SVG**。必须先完成该页的“节点 / 关系 / 证据 / 主判断”建模中间层，再进入 SVG 生成。若这一步缺失，则视为 Executor 尚未准备完成。
> ⚠️ **内容优先复杂度规则（强制）**：复杂页的目标是压缩和组织复杂信息，而不是制造“高级感”。若某页内容并不存在跨层关系、因果链、映射关系、闭环机制或证据链，则不得为了追求视觉复杂度而硬做复杂结构。Executor 在落图前必须再次判断：当前复杂结构是否让读者更快理解文档主线；如果没有，必须收敛为更简单、更稳、更准确的页面表达。

**Step 6.0 —— 复杂页建模（命中复杂页时强制）**

当页面属于以下任一情况时，必须先执行本子步骤：

- `高级正文模式` 不为 `无`
- 页面意图属于攻击链、复杂案例链、证据证明页、治理矩阵页、闭环机制页、攻击树、泳道协同图等复杂内容
- 模板本地文档明确要求该类页面先做语义建模

复杂页建模中间层至少应输出：

1. `页面角色`（概览页 / 推进页 / 证明页 / 收束页）
2. `页面意图`
3. `证明目标`
4. `主判断`
5. `分判断`（最多 3 个）
6. `论证主线`
   - 现象 / 入口
   - 放大机制 / 关键条件
   - 结果 / 影响
   - 管理判断 / 动作要求
7. `主结构类型`（链路 / 分层 / 矩阵 / 闭环 / 泳道 / 证据挂载 / 混合结构）
8. `结构选择理由`
9. `为什么不用其他结构`
10. `关键节点`
   - 入口节点
   - 动作节点
   - 放大条件
   - 结果节点
   - 证据节点
   - 判断节点 / 控制节点（如适用）
11. `关键关系`
   - 因果
   - 依赖
   - 放大
   - 并行 / 汇聚
   - 反馈 / 闭环（如适用）
12. `证据挂载计划`
   - 哪个证据挂在哪个节点
   - 每个证据证明什么
13. `证据分级`
   - 直接证据
   - 结果证据
   - 旁证 / 背景证据
14. `文本压缩计划`
   - 标题句
   - 节点文案
   - 证据说明句
   - 页尾收束句
15. `视觉焦点排序`
    - 第一眼看什么
    - 第二眼看什么
    - 第三眼看什么
16. `页面收束方式`
   - 管理判断
   - 风险判断
   - 整改或闭环建议

> **落盘要求（强制）**：命中复杂页后，不允许只在对话里临时想一遍。必须把复杂页建模结果写入 `<project_path>/notes/complex_page_models.md`，并按页面标题分块保存，推荐格式为：
>
> ```markdown
> #### 页面标题
> - 页面角色：
> - 页面意图：
> - 证明目标：
> ...
> ```
>
> 同一项目中的所有复杂页，统一写入这一份文件，供后续校验与修复闭环复用。

> 对 `security_service`，若模板目录存在 `complex_graph_semantics.md`、`complex_case_chain_modeling.md`、`complex_page_logic_qa_checklist.md`，则命中复杂页时必须先读取这些文档并据此完成建模中间层。
> 若模板目录还存在 `complex_page_reasoning_template.md`、`evidence_grading_rules.md`、`complex_deck_orchestration.md`、`complex_svg_blueprints.md`、`sample_grade_content_system.md`，则命中复杂页时也必须同步读取，并以这些文档为复杂页建模、重型页骨架选择、案例级论证语言与跨页编排的执行基线。

> **建模粒度要求**：
> - 不能粗到只有“入口 → 结果”
> - 也不能细到把每一个操作动作都拆成碎步骤
> - 推荐控制在：3-5 个主节点、1-3 个放大条件、1-3 个结果节点、2-4 个关键证据

> **通过标准**：只有当这一页已经能说清：
> - 它在整套 deck 中承担什么角色
> - 这页要证明什么
> - 为什么这条链/结构成立
> - 为什么选这个结构、而不用其他结构
> - 证据挂在哪里、分别证明什么
> - 读者第一眼应该先看到什么
> - 最后应该得出什么判断
>
> 才允许进入下一步 SVG 生成。

> **建模校验门（强制）**：在开始复杂页 SVG 生成之前，必须先运行：
>
> ```bash
> python3 ${SKILL_DIR}/scripts/check_complex_page_model.py <project_path>
> ```
>
> 若脚本提示缺页、字段缺失、页面标题对不上或复杂页建模文件不存在，必须先补齐 `<project_path>/notes/complex_page_models.md`，不得直接继续画复杂页。

**视觉构建阶段**：
- 按页码顺序连续逐页生成 SVG 页面 → `<project_path>/svg_output/`
- 每一页都执行：`（如命中复杂页则先做 Step 6.0 建模）→ 生成草稿 → 立即复核 → 有问题就修 → 标记通过 → 继续下一页`
- 长亭相关模板每一页额外强制检查：Logo 是否存在、是否使用批准版本、是否与标题/正文/页脚冲突
- 当所有页面通过逐页复核后，再做一次整套 deck 的一致性复核
  - 强制检查项：目录页结构一致性、同类页面结构一致性、takeaway/正文分离规则一致性、信息密度异常页、相似内容页之间的版式节奏漂移
  - 新增强制检查项：顶部页型标签是否压到第一层表头/模块、标题组（主标题/判断句/装饰线）是否互相打架、章节页说明文案是否侵入大号章节数字保护区
- 在宣布 SVG 初稿阶段完成之前，必须运行：
  ```bash
  python3 ${SKILL_DIR}/scripts/check_svg_text_fit.py <project_path>/svg_output
  ```
  若脚本报错，必须先修正对应 SVG 页面，再继续后续阶段

**逻辑构建阶段**：
- 只有当**所有页面都通过逐页复核，并完成整套 deck 一致性复核后**，才生成讲稿 → `<project_path>/notes/total.md`

**✅ 检查点——确认 SVG 和讲稿已全部生成完成，直接进入 Step 7 后处理**：
```markdown
## ✅ Executor 阶段完成
- [x] 所有 SVG 已生成到 svg_output/
- [x] 每一页都通过了过程内视觉复核
- [x] 整套 deck 一致性复核已完成
- [x] 讲稿已生成到 notes/total.md
```

---

### Step 7：后处理与导出

🚧 **GATE**：Step 6 已完成；所有 SVG 已生成到 `svg_output/`；每页都通过过程内视觉复核；整套 deck 一致性复核已完成；讲稿 `notes/total.md` 已生成。

先读取导出后成品复核定义：
```
Read references/exported-ppt-review.md
Read references/output-qa-checklist.md
```

> ⚠️ 以下子步骤必须**逐个单独执行**。每一步命令或复核都必须完成并确认成功后，才能进行下一步。
> ❌ **禁止**把它们打包成一条 shell 命令执行，也禁止在未完成复核门时直接把导出结果视为最终成品。

**Step 7.1** —— 拆分讲稿：
```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

**Step 7.2** —— SVG 后处理（图标嵌入 / 图片裁切与嵌入 / 文本扁平化 / 圆角矩形转 Path）：
```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

**Step 7.3** —— SVG 审核（必须关注 warning，不只是 error）：
```bash
python3 ${SKILL_DIR}/scripts/svg_quality_checker.py <project_path> --format <format>
```

- 对带有 fixed skeleton / `qa_profile.md` / `data-brand-required` 的模板，`svg_quality_checker.py` 中命中的阻塞级 warning 也视为**未通过**
- 重点阻塞项包括：中文断句与可读性、贴边/拥挤、卡片视觉溢出、Logo 安全区冲突、Takeaway 与正文分层冲突、目录结构不一致、信息密度超载、品牌资产缺失或误用
- 对长亭相关模板，以下视觉层级冲突也必须视为阻塞：顶部标签压表头、标题组内部碰撞、章节页动态说明侵入大号章节数字保护区

**Step 7.4** —— SVG 文本适配复核（强制）：
```bash
python3 ${SKILL_DIR}/scripts/check_svg_text_fit.py <project_path>/svg_final
```

**Step 7.5** —— SVG 渲染图抽检（强制）：
```bash
python3 ${SKILL_DIR}/scripts/render_svg_pages.py <project_path> -s final
```

- 至少检查 4 类页面：目录页、普通内容页、密集内容页、图片重页面
- 对于带 `qa_profile.md` 的模板，必须额外按模板本地 QA 清单抽检其高风险页
- 长亭相关模板必须把章节页、高级正文页、矩阵/治理页列为高风险页；发现标题组塌陷、标签与表头打架、装饰数字与正文冲突时不得继续交付

**Step 7.6** —— 导出 PPTX（默认嵌入讲稿）：
```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
# 默认生成两个文件——原生可编辑形状版 (.pptx) + SVG 参考版 (_svg.pptx)
# 可用 --only native 跳过 SVG 参考版
# 可用 --only legacy 仅生成 SVG 图像版
```

**Step 7.7** —— 导出后成品 PPT 复核门（强制）：

- 必须检查**实际导出的 PPT 外观**，不能只看 SVG 文件
- 必检项目：
  - 导出后的文本断句 / 可读性
  - 文字是否贴边 / 是否显得拥挤
  - 卡片文字是否裁切或视觉溢出
  - takeaway 与正文是否碰撞、上下层模块是否打架
  - Logo / 页码 / 底部装饰是否冲突
  - 信息密度是否合适
  - 目录页结构是否一致
  - 同类页面在整套 deck 中是否保持一致
- 以 `references/exported-ppt-review.md` 和 `references/output-qa-checklist.md` 作为检查清单
- 导出后必须运行：
  ```bash
  python3 ${SKILL_DIR}/scripts/check_pptx_fonts.py <project_path>
  python3 ${SKILL_DIR}/scripts/write_qa_manifest.py <project_path> --format <format>
  ```
  若字体检查报错，或 QA manifest 中任一强制项（含 `complex_page_model`、SVG 质量、文本适配、视觉抽检、字体检查）显示未通过，则不得交付

**Step 7.8** —— 如发现问题，进入修复闭环：

- 回到 `svg_output/` 修正对应源 SVG 页面
- 重新执行 Step 7.2 → Step 7.7，直到 SVG 审核、文本适配、渲染抽检、导出后成品 PPT 复核都通过
- 在此闭环完成之前，**不得**将该 deck 视为最终成品

> ❌ **绝对不要**用 `cp` 代替 `finalize_svg.py` —— 它承担了多项关键处理步骤
> ❌ **绝对不要**直接从 `svg_output/` 导出 —— 必须使用 `-s final` 从 `svg_final/` 导出
> ❌ **绝对不要**额外添加 `--only` 之类的标志
> ❌ **绝对不要**把第一次导出的 PPT 当作最终交付，除非已经完成 Step 7.5，且如有需要已完成 Step 7.6

---

## 角色切换协议

在切换角色之前，**必须先读取**对应参考文件——禁止跳过。输出标记格式：

```markdown
## [角色切换：<Role Name>]
📖 正在读取角色定义：references/<filename>.md
📋 当前任务：<简要描述>
```

---

## 参考资源

| 资源 | 路径 |
|----------|------|
| 通用技术约束 | `references/shared-standards.md` |
| 画布格式说明 | `references/canvas-formats.md` |
| 图片布局规范 | `references/image-layout-spec.md` |
| SVG 图片嵌入说明 | `references/svg-image-embedding.md` |

---

## 备注

- 后处理命令默认不要额外加 `--only` 等参数——按原样执行即可
- 本地预览：`python3 -m http.server -d <project_path>/svg_final 8000`
