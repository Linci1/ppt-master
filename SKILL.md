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
| `${SKILL_DIR}/scripts/project_manager.py` | 项目初始化 / 校验 / 管理 |
| `${SKILL_DIR}/scripts/analyze_images.py` | 图片分析 |
| `${SKILL_DIR}/scripts/image_gen.py` | AI 图片生成（多供应商） |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG 质量检查 |
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

## 独立工作流

| 工作流 | 路径 | 用途 |
|----------|------|---------|
| `create-template` | `workflows/create-template.md` | 独立模板创建工作流 |

---

## 工作流

### Step 1：源内容处理

🚧 **GATE**：用户已经提供源材料（PDF / DOCX / EPUB / URL / Markdown 文件 / 文本描述 / 对话内容——任意一种都可以）。

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
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

格式选项：`ppt169`（默认）、`ppt43`、`xhs`、`story` 等。完整格式列表见 `references/canvas-formats.md`。

导入源内容（按实际情况选择）：

| 场景 | 动作 |
|-----------|--------|
| 有源文件（PDF/MD 等） | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files...> --move` |
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

当用户确认选项 A 后，把模板文件复制到项目目录：
```bash
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.svg <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/design_spec.md <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.png <project_path>/images/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.jpg <project_path>/images/ 2>/dev/null || true
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

**设计参数确认（强制）**：在生成第一页 SVG 之前，Executor 必须回顾并输出设计规格中的关键设计参数（画布尺寸、配色方案、字体方案、正文基准字号），以确保执行严格遵循设计规格。详见 `executor-base.md` 第 2 节。

> ⚠️ **仅限主代理规则**：第 6 步中的 SVG 生成必须由当前主代理完成，因为页面设计依赖完整上游上下文（源内容、设计规格、模板映射、图片决策以及跨页一致性）。禁止把任何幻灯片 SVG 生成委托给子代理。
> ⚠️ **生成节奏规则**：确认全局设计参数后，Executor 必须在同一连续主上下文中按页码顺序逐页生成。禁止把第 6 步拆成“每次 5 页”这样的分批生成。
> ⚠️ **逐页复核门（强制）**：每生成一页草稿，Executor 都必须立刻执行 `references/executor-visual-review.md` 中定义的视觉复核，然后才能继续下一页。复核项包括：中文断句/可读性、边距与拥挤感、卡片溢出风险、页脚/Logo/页码冲突、takeaway 与正文层级分离、信息密度、是否需要精简/重排、以及同类页一致性。这些检查必须发生在**生成过程中**，而不是全部做完后的集中清理。

**视觉构建阶段**：
- 按页码顺序连续逐页生成 SVG 页面 → `<project_path>/svg_output/`
- 每一页都执行：`生成草稿 → 立即复核 → 有问题就修 → 标记通过 → 继续下一页`
- 当所有页面通过逐页复核后，再做一次整套 deck 的一致性复核
  - 强制检查项：目录页结构一致性、同类页面结构一致性、takeaway/正文分离规则一致性、信息密度异常页、相似内容页之间的版式节奏漂移

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

**Step 7.4** —— 导出 PPTX（默认嵌入讲稿）：
```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
# 默认生成两个文件——原生可编辑形状版 (.pptx) + SVG 参考版 (_svg.pptx)
# 可用 --only native 跳过 SVG 参考版
# 可用 --only legacy 仅生成 SVG 图像版
```

**Step 7.5** —— 导出后成品 PPT 复核门（强制）：

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
- 以 `references/exported-ppt-review.md` 作为检查清单

**Step 7.6** —— 如发现问题，进入修复闭环：

- 回到 `svg_output/` 修正对应源 SVG 页面
- 重新执行 Step 7.2 → Step 7.5，直到 SVG 审核和导出后成品 PPT 复核都通过
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
