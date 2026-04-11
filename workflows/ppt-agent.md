# PPT Agent 总控工作流

> 用途：把 `ppt-master` 从“文档转 PPT 工具”升级为“会先澄清需求、再吸收案例、再生成、再复盘沉淀”的总控 Agent。

---

## 一、总控目标

`ppt-master` 在 Agent 模式下，不应一上来就直接生成 PPT，而应先判断当前任务属于哪一种模式，再进入对应流程。

支持 6 种模式：

- `learn`：吸收历史优秀 PPT 素材案例
- `plan`：澄清需求、行业、客户要求与展示重点
- `produce`：生成进入正式执行前的生产包、复杂页骨架与 design_spec 草案
- `execute`：补齐项目级 `design_spec.md` 首稿，并生成执行交接与校验结果
- `run`：自动执行 execute 后的修补与角色调度入口生成
- `improve`：复盘本次项目问题，并沉淀回规则库

默认规则：

- 如果用户给的是历史 PPT 素材，优先进入 `learn`
- 如果用户要做新 PPT，优先进入 `plan`
- 如果用户已经有产出并要求检查、修复、总结经验，优先进入 `improve`

---

## 二、六种模式的输入输出

### 2.1 `learn` 模式

**输入**

- 一个或多个历史优秀 `.pptx`
- 可选：行业、场景、模板归属、用户评价

**动作**

1. 用 `scripts/ingest_reference_ppt.py` 建案例目录
2. 生成案例拆解结果
3. 用 `scripts/distill_case_patterns.py` 提炼跨案例共性
4. 给出“建议写回模板 / 建议写回行业包 / 仅保留为案例模式”的分类结果

**输出**

- `case_library/<domain>/<case_name>/`
- 结构化案例分析文件
- 合并建议文件 `merge_suggestions.md`

### 2.2 `plan` 模式

**输入**

- 用户对本次 PPT 的目标描述
- 源文档、历史案例、品牌要求、客户约束

**动作**

1. 读取 `references/plan-question-bank.md`
2. 引导用户补齐关键信息
3. 用 `scripts/build_project_brief.py` 生成标准 brief
4. 用 `scripts/select_template_and_domain.py` 给出模板、行业包与案例建议

**输出**

- `project_brief.md`
- 若项目较复杂，可再拆分为：
  - `customer_requirements.md`
  - `content_priorities.md`
  - `delivery_constraints.md`
- 在 brief 未就绪前，还应先输出：
  - `notes/plan_answers.json`
  - `notes/plan_questions.md`
  - `notes/plan_readiness.md`
  - `notes/plan_agent_state.json`
  - `notes/plan_next_turn.md`

其中 `plan_next_turn.md` 应尽量把下一轮追问收敛为 1-3 个高价值问题，而不是一次性把整张问卷抛给用户。

如果要让 `/plan` 更接近真实 Agent，还应额外维护：

- `notes/plan_rounds.json`：轮次级状态快照
- `notes/plan_dialogue.md`：人类可读的追问历史
- `notes/plan_session_status.md`：当前轮次的会话状态面板

### 2.3 `produce` 模式

**输入**

- `project_brief.md`
- 源文档
- 模板资产
- 行业包
- 可复用案例模式

**动作**

1. 刷新 `storyline.md` / `page_outline.md`
2. 生成 `production_readiness.md`、`production_packet.md`
3. 生成 `strategist_packet.md`、`complex_page_models.md`
4. 生成 `design_spec_scaffold.md`、`design_spec_draft.md`

**输出**

- `notes/production_readiness.md`
- `notes/production_packet.md`
- `notes/strategist_packet.md`
- `notes/complex_page_models.md`
- `notes/design_spec_scaffold.md`
- `notes/design_spec_draft.md`

### 2.4 `execute` 模式

**输入**

- 已通过 `produce` 的项目
- `notes/design_spec_draft.md`
- `notes/complex_page_models.md`
- 模板与行业包规则

**动作**

1. 生成或保留项目根目录 `design_spec.md`
2. 输出 `notes/execution_readiness.md`
3. 输出 `notes/execution_runbook.md`
4. 自动执行 `design_spec_validator.py`
5. 自动执行 `check_complex_page_model.py`
6. 如需要，可自动修补 design_spec / complex_page_models 的 warning 类问题

**输出**

- `design_spec.md`
- `notes/execution_readiness.md`
- `notes/execution_runbook.md`
- design_spec 校验结果
- 复杂页模型校验结果

### 2.5 `run` 模式

**输入**

- 已通过 `produce` 的项目
- `execute` 阶段输出

**动作**

1. 自动触发 execute 所需的设计稿生成与校验
2. 自动执行 `auto_repair_execution_artifacts.py`
3. 输出 `notes/strategist_handoff.md`
4. 输出 `notes/executor_handoff.md`
5. 输出 `notes/agent_run_status.md`
6. 输出 `notes/svg_execution_queue.md`、`notes/svg_generation_status.md`、`notes/svg_postprocess_plan.md`
7. 为逐页 SVG 生成补出 `notes/page_briefs/`

**输出**

- `notes/strategist_handoff.md`
- `notes/executor_handoff.md`
- `notes/agent_run_status.md`
- `notes/auto_repair_report.md`
- `notes/svg_execution_queue.md`
- `notes/svg_generation_status.md`
- `notes/svg_execution_state.json`
- `notes/svg_current_task.md`
- `notes/svg_current_prompt.md`
- `notes/svg_current_context_pack.md`
- `notes/svg_current_review.md`
- `notes/svg_execution_log.md`
- `notes/svg_postprocess_plan.md`
- `notes/page_briefs/`

其中若希望把“当前页 SVG 先由脚本直接写出来”，可在 `run` 后额外调用：

```bash
python3 scripts/ppt_agent.py svg-exec render <project_path> --page <页码或SVG名>
```

它会生成当前页 starter SVG，并输出即时 QA 快照，作为主代理后续细修的起点。

### 2.6 `improve` 模式

**输入**

- 已生成项目
- QA 结果
- 用户指出的问题
- 导出后成品复核意见

**动作**

1. 问题分类：模板问题 / 内容问题 / 复杂页问题 / QA 漏检问题
2. 用 `scripts/update_learning_registry.py` 输出结构化复盘，并自动吸收 `qa_manifest.json` 与 `notes/page_execution/*.json` 的修复轨迹
3. 标注哪些应写入模板，哪些应写入行业包，哪些只保留为项目特例

**输出**

- `notes/review_findings.md`
- `notes/learning_update.md`
- 可供人工确认的规则更新建议

---

## 三、启动时的默认执行顺序

当用户明确要“做 PPT”时，Agent 默认按下面顺序执行：

1. 判断是否已有足够清晰的 brief
2. 若没有，进入 `plan`
3. `plan` 通过后，输出模板建议与叙事建议，等待确认
4. 确认后进入 `produce`
5. `produce` 通过后进入 `execute`
6. `execute` 通过后进入 `run`
7. `run` 生成角色交接文件后，再进入正式 SVG / PPT 生成
8. 项目收尾后进入 `improve`

也就是说，**默认链路不是“文档 -> PPT”，而是“需求澄清 -> 内容规划 -> 生成 -> QA -> 经验沉淀”**。

---

## 四、Plan 阶段的强制要求

当任务进入 `plan` 时，Agent 必须至少澄清以下内容：

- 行业与业务场景
- 受众类型
- 目标动作与展示重点
- 品牌 / 模板 / 历史风格要求
- 页数与时长约束
- 材料情况
- 必须避免的表达或风格

如果这些内容不清晰，**不得直接进入 SVG 生成**。

---

## 五、案例持续吸收机制

后续如果用户持续提供新的 PPT 素材案例，Agent 必须具备“先入库，再蒸馏，再合并”的能力。

### 5.1 原则

- 不直接把单个案例写死进模板
- 先进入 `case_library/`
- 再判断属于：
  - `case pattern`（单案例技巧）
  - `domain rule`（行业表达规律）
  - `template rule`（固定品牌骨架或模板规则）

### 5.2 吸收标准

只有当同类规律在多个案例中重复出现时，才建议升级为长期规则。

### 5.3 合并方向

- 品牌骨架问题 -> 回写模板目录
- 行业表达、图文逻辑、复杂页打法 -> 回写 `domain_packs/`
- 通用 QA 与重写策略 -> 回写总 skill / 通用 reference

---

## 六、推荐目录落点

- `case_library/`：案例资产与蒸馏结果
- `domain_packs/`：行业级表达、页型、图形与 QA 规则
- `references/`：/plan 提问题库与中间产物模板
- `scripts/`：案例吸收、brief 生成、模板选择、故事线构建、学习回写脚本

---

## 七、和现有主链路的关系

`ppt-agent.md` 不替代 `SKILL.md`，而是作为其前置总控层。

关系如下：

- `ppt-agent.md`：决定进入哪种模式、是否先 `/plan`、是否先吸收案例
- `SKILL.md`：在进入正式生成后，继续执行严格串行的 Strategist / Executor / QA 主链路

因此，Agent 的推荐读取顺序为：

1. `workflows/ppt-agent.md`
2. `references/plan-question-bank.md`
3. `references/project-brief-template.md`
4. `SKILL.md`
5. 具体模板目录文档

---

## 八、当前 Agent 的标准使用方式

如果把 `ppt-master` 当成一个可持续进化的 PPT Agent 来使用，当前推荐链路是：

1. `new` / `plan`：建立项目，先做 `/plan` 收集
2. 补齐 `notes/plan_questions.md` 中缺失信息
3. 等待系统生成 `project_brief.md`、模板推荐、`storyline.md`、`page_outline.md`
4. 执行 `produce`，形成生产包和复杂页建模骨架
5. 执行 `execute`，生成项目根目录 `design_spec.md` 并做执行前校验
6. 执行 `run`，生成 Strategist / Executor 的执行交接包和逐页 brief
7. 再进入 `SKILL.md` 中的正式 SVG / PPT 主链路
8. 项目结束后执行 `improve`

可以把它理解为：

- 需求与规划层：`new / plan / produce`
- 执行准备层：`execute / run`
- 正式生成层：Strategist / Executor / QA / Export

### 8.1 用户需要明确给指令的节点

当前不是每一步都需要用户再说一次“继续”，但下面几个节点最好明确确认：

- 立项时：行业、场景、受众、目标、展示重点
- `/plan` 追问后：补齐缺失信息
- 模板推荐出来后：确认模板、品牌要求、页数、复杂页比例
- 正式生成前：确认是否偏“高级复杂页”还是偏“稳妥标准页”
- 成品复盘时：把发现的问题作为 `improve` 输入回灌

### 8.2 哪些阶段可以连续自动推进

在前置条件满足时，下面几段可以连续推进，不需要额外等待用户逐步放行：

- `new/plan` 完成后，到 `project_brief.md` / 模板推荐 / 故事线生成
- `produce` 内部的生产包、复杂页骨架、`design_spec` 草案生成
- `execute` 内部的 `design_spec.md` 生成、校验、可选 auto-repair
- `run` 内部的执行交接包、逐页 brief、SVG 执行队列生成

但进入正式 SVG 主链路前，仍建议让用户至少确认一次模板方向、信息密度和复杂页占比。

### 8.3 当前仍存在的差距

和理想中的“完整对话式 PPT Agent”相比，目前还存在三类差距：

- `/plan` 已能产出结构化问题与 readiness 报告，但距离真正的全对话式多轮追问还差一层交互编排
- `run` 已能补齐执行交接与 SVG 队列，但正式 SVG 逐页执行的状态回写还不是完全自动化闭环
- 软性质量问题已经进入 QA 与规则层，但复杂页的文本-图形深耦合仍需要主代理在正式生成时做最后把关

因此，当前最准确的定位是：`ppt-master` 已经是一个“可用的半自动 PPT Agent”，而不是完全黑盒的一键成品机。
