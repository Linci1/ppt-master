---
name: chaitin-ppt-master
description: >
  面向公司内部 PPT 生产的 AI 工作流技能。把 PDF/DOCX/URL/Markdown 等源材料
  转成高质量 SVG 页面，并导出为 PPTX。默认优先使用长亭黑绿模板
  black_green_official_2025，除非用户明确要求其他自定义模板或自由设计。
  Use when 用户提出“生成PPT”、“做PPT”、“制作演示文稿”、
  “make presentation”、“create PPT”，或明确提到“长亭模板”、
  “黑绿模板”、“客户运营分析报告”、“启动会PPT”等公司内常见场景。
---

# 长亭 PPT Master 技能

> 一套面向 PPT 生成的 AI 工作流技能：将源材料整理为 SVG 页面，并导出为可编辑 PPTX。

**核心流水线**：`源材料 → 创建项目 → 选择模板 → Strategist → [Image_Generator] → Executor → 后处理 → 导出`

> [!CAUTION]
> ## 🚨 全局执行纪律（强制）
>
> 这是一条**严格串行**的流水线。以下规则优先级最高，违反任意一条都视为执行失败：
>
> 1. **严格串行**：必须按步骤顺序执行。上一步输出就是下一步输入。
> 2. **BLOCKING 必须停下**：标记为 ⛔ 的步骤必须等待用户明确回复，不能替用户做决定。
> 3. **禁止跨阶段打包执行**：不能把多个阶段揉成一步做。尤其是 Step 4 的八项确认，必须整包给建议并等待用户确认。
> 4. **先过 Gate 再进入**：每一步开始前，必须先满足该步骤的 🚧 GATE 前置条件。
> 5. **禁止超前准备**：不能在 Strategist 阶段提前写 SVG，也不能跨阶段偷跑。
> 6. **SVG 生成只能由主代理完成**：Step 6 生成页面 SVG 时，禁止交给子代理。
> 7. **页面必须连续逐页生成**：进入 Step 6 后，必须在同一主上下文里一页一页连续生成，禁止 5 页一批这种分段式生成。

> [!IMPORTANT]
> ## 🌐 语言规则
>
> - **回复语言**：默认跟随用户语言和源材料语言。
> - **显式覆盖**：如果用户明确要求某种语言，则以用户要求为准。
> - **模板格式**：`design_spec.md` 的章节结构与字段名必须保持英文模板格式，内容值可以用中文。

> [!IMPORTANT]
> ## 🔌 与通用编程技能的边界
>
> - `ppt-master` 是仓库级 PPT 生产工作流，不是通用应用脚手架。
> - 不要默认创建 `.worktrees/`、`tests/`、分支工作流等通用工程结构。
> - 如果其他通用编程技能和本技能冲突，以本技能为准，除非用户明确要求别的做法。

## 主流程脚本

| 脚本 | 用途 |
|------|------|
| `${SKILL_DIR}/scripts/pdf_to_md.py` | PDF 转 Markdown |
| `${SKILL_DIR}/scripts/doc_to_md.py` | DOCX/EPUB/HTML/LaTeX/RST 等文档转 Markdown |
| `${SKILL_DIR}/scripts/web_to_md.py` | 普通网页转 Markdown |
| `${SKILL_DIR}/scripts/web_to_md.cjs` | 微信等高限制页面转 Markdown |
| `${SKILL_DIR}/scripts/project_manager.py` | 项目初始化 / 校验 / 管理 |
| `${SKILL_DIR}/scripts/analyze_images.py` | 图片分析 |
| `${SKILL_DIR}/scripts/image_gen.py` | AI 生图 |
| `${SKILL_DIR}/scripts/svg_quality_checker.py` | SVG 质量检查 |
| `${SKILL_DIR}/scripts/check_svg_text_fit.py` | SVG 文本越界检查 |
| `${SKILL_DIR}/scripts/render_svg_pages.py` | SVG 视觉渲染检查 |
| `${SKILL_DIR}/scripts/write_qa_manifest.py` | 交付 QA 记录输出 |
| `${SKILL_DIR}/scripts/check_pptx_fonts.py` | 导出后 PPTX 字体一致性检查 |
| `${SKILL_DIR}/scripts/total_md_split.py` | 讲稿拆分 |
| `${SKILL_DIR}/scripts/finalize_svg.py` | SVG 后处理 |
| `${SKILL_DIR}/scripts/svg_to_pptx.py` | 导出 PPTX |

完整脚本文档见：`${SKILL_DIR}/scripts/README.md`

## 模板索引

| 索引 | 路径 | 用途 |
|------|------|------|
| 布局模板 | `${SKILL_DIR}/templates/layouts/layouts_index.json` | 查询可选页面模板 |
| 图表模板 | `${SKILL_DIR}/templates/charts/charts_index.json` | 查询图表 SVG 模板 |
| 图标库 | `${SKILL_DIR}/templates/icons/icons_index.json` | 查询图标名称与分类 |

## 独立工作流

| 工作流 | 路径 | 用途 |
|--------|------|------|
| `create-template` | `workflows/create-template.md` | 独立创建模板工作流 |

---

## 工作流

### Step 1：源材料处理

🚧 **GATE**：用户已经提供了源材料（PDF / DOCX / EPUB / URL / Markdown / 会话文本等任意一种都可以）。

如果用户提供的不是 Markdown，需要立即转换：

| 用户提供 | 命令 |
|----------|------|
| PDF | `python3 ${SKILL_DIR}/scripts/pdf_to_md.py <file>` |
| DOCX / Word / Office 文档 | `python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| EPUB / HTML / LaTeX / RST / 其他 | `python3 ${SKILL_DIR}/scripts/doc_to_md.py <file>` |
| 网页链接 | `python3 ${SKILL_DIR}/scripts/web_to_md.py <URL>` |
| 微信 / 高限制网页 | `node ${SKILL_DIR}/scripts/web_to_md.cjs <URL>` |
| Markdown | 直接读取 |

**✅ 检查点**：确认源材料已准备完毕，然后进入 Step 2。

---

### Step 2：项目初始化

🚧 **GATE**：Step 1 已完成，源材料已可用。

```bash
python3 ${SKILL_DIR}/scripts/project_manager.py init <project_name> --format <format>
```

格式可选：`ppt169`（默认）、`ppt43`、`xhs`、`story` 等。完整格式见 `references/canvas-formats.md`。

导入源材料：

| 场景 | 动作 |
|------|------|
| 有源文件（PDF/MD/图片等） | `python3 ${SKILL_DIR}/scripts/project_manager.py import-sources <project_path> <source_files...> --move` |
| 用户直接在对话里给文本 | 不需要导入，后续直接使用会话内容 |

> ⚠️ **必须使用 `--move`**：所有原始材料和中间 Markdown 都要归档进 `sources/`，不能只复制不归档。

**✅ 检查点**：确认项目结构创建成功、`sources/` 已归档材料，然后进入 Step 3。

---

### Step 3：模板选择

🚧 **GATE**：Step 2 完成，项目目录已准备好。

⛔ **BLOCKING**：如果用户还没明确说用不用模板，必须先给出建议并等待明确回复。

**⚡ 直接跳过条件**：如果用户已经明确说“不使用模板 / 自由设计”，则不要读取 `layouts_index.json`，直接进入 Step 4。

**推荐模板时必须做的事**：
- 读取 `${SKILL_DIR}/templates/layouts/layouts_index.json`
- 默认优先推荐 **长亭黑绿模板** `black_green_official_2025`
- 除非用户已经明确要求其他模板或自由设计，否则模板选择时要用下面这类话术：

> 💡 **默认模板**：本次默认使用 **长亭黑绿模板** `black_green_official_2025`，它也是当前公司内最稳定、最推荐的默认模板。
>
> 如果你不需要调整，我就按这个模板继续；如果需要，我也可以改成 **其他自定义模板**，或者按你的要求 **不使用模板 / 自由设计**。

如果用户确认继续使用默认黑绿模板，或指定使用其他模板，则复制对应模板文件到项目目录：

```bash
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.svg <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/design_spec.md <project_path>/templates/
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.png <project_path>/images/ 2>/dev/null || true
cp ${SKILL_DIR}/templates/layouts/<template_name>/*.jpg <project_path>/images/ 2>/dev/null || true
```

**源PPT素材分析（强制）**：如果用户提供了参考源PPT（如"按这个PPT的风格来"），必须在复制模板后立即用 python-pptx 逐页提取 shape 结构，记录每个固定页的布局要素（提取脚本见陷阱 8）。

将提取结果保存到 `<project_path>/source_ppt_analysis.md`，后续固定页生成时必须参照此文件，不能凭假设设计。

> ⚠️ **模板保真规则（强制）**：
> - 模板 SVG 是权威骨架，不要随意重画 cover / chapter / toc / content / ending 的框架。
> - 如果模板带了背景图或 logo，必须一并复制到 `<project_path>/images/`，并保持原文件名不变。
> - 如果模板里已经有保护遮罩层或底图修补层，除非底图已确认替换为干净资源，否则不要移除。

如果用户选择 B，则直接进入 Step 4。

如需创建全局模板，读取：`workflows/create-template.md`

**✅ 检查点**：模板选择已确认，模板文件已复制（如适用），进入 Step 4。

---

### Step 4：Strategist 阶段（必做，不能跳过）

🚧 **GATE**：Step 3 完成，用户已确认模板选择。

先读取角色定义：

```text
Read references/strategist.md
```

⛔ **BLOCKING**：必须完成并展示“八项确认”，等待用户确认或修改后，才能继续输出 `design_spec.md`。

八项确认如下：

1. 画布格式
2. 页数范围
3. 目标受众
4. 风格目标
5. 配色方案
6. 图标策略
7. 字体方案
8. 图片策略

如果用户提供了图片，必须先运行：

```bash
python3 ${SKILL_DIR}/scripts/analyze_images.py <project_path>/images
```

> ⚠️ **图片处理规则**：不要直接打开 `.jpg/.png` 文件，所有图片信息必须来自 `analyze_images.py` 输出或设计规格中的资源表。

**源文档图片提取（强制）**：如果源材料是 DOCX/PDF，必须在 Strategist 阶段提取文档中的图片素材并建立用途映射：

```bash
# 提取 DOCX 中的媒体文件
unzip -o <source_file> "word/media/*" -d /tmp/docx_images
# 获取每张图片尺寸
sips -g pixelWidth -g pixelHeight /tmp/docx_images/word/media/*
# 复制到项目 images 目录（重命名为语义化文件名，如 docx_cover.jpeg、docx_diagram.png）
cp /tmp/docx_images/word/media/* <project_path>/images/
```

在 `design_spec.md` 中必须包含 `source_images` 表，明确每张原图的目标页面和用法（格式见陷阱 11）。不能等生成完再补，也不能在无关页面硬塞。

输出文件：`<project_path>/design_spec.md`

**✅ 检查点**：

```markdown
## ✅ Strategist 阶段完成
- [x] 八项确认已完成（用户已确认）
- [x] 设计规格与内容大纲已生成
- [ ] 下一步：自动进入 [Image_Generator / Executor]
```

---

### Step 5：Image_Generator 阶段（条件触发）

🚧 **GATE**：Step 4 完成，且设计规格已确认。

**触发条件**：如果图片策略包含“AI 生成”，则执行本阶段；否则跳过，直接进入 Step 6。

先读取：

```text
Read references/image-generator.md
```

执行流程：

1. 从设计规格中找出所有待生成图片
2. 生成提示词文档到 `<project_path>/images/image_prompts.md`
3. 调用生图脚本：

```bash
python3 ${SKILL_DIR}/scripts/image_gen.py "prompt" --aspect_ratio 16:9 --image_size 1K -o <project_path>/images
```

**✅ 检查点**：

```markdown
## ✅ Image_Generator 阶段完成
- [x] 提示词文档已生成
- [x] 图片已保存到 images/
```

---

### Step 6：Executor 阶段

🚧 **GATE**：Step 4 完成；如果触发生图，则 Step 5 也必须完成。

根据风格读取对应角色定义：

```text
Read references/executor-base.md
Read references/executor-general.md
Read references/executor-consultant.md
Read references/executor-consultant-top.md
```

> 只需要读取 `executor-base.md` + 对应风格文件之一。

**设计参数确认（强制）**：在生成第一页 SVG 之前，必须先输出并确认这些参数：
- 画布尺寸
- 主 / 次 / 强调色
- 字体方案
- 正文字号

**执行前冻结协议（强制）**：在生成第一页之前，必须先冻结并记录本轮页面协议。至少要明确：
- 页面分类结果：区分 `fixed pages` 与 `body pages`
- 页面中间协议对象：为每页记录页型、主判断、信息骨架、风险点、允许调整项、禁止漂移项
- 当前模板的 frame/slot 约束：明确哪些是品牌固定框架，哪些 slot 允许填充、伸缩、删减或换序
- 生成后的文案结构：至少明确标题层、主体层、证据层、收束层
- 对 hybrid brand-locked 模板，必须额外满足 `references/hybrid-page-protocol.md`：每个 `body_page` 在落 SVG 前都要先明确 `page_type`、`template_family`、`frame_policy`、`safe_region`、`native_structure`、`split_strategy` 与 `message_contract`，不得直接从未分型正文文本跳到 `{{CONTENT_AREA}}` 填充

> ⚠️ **主代理专属规则**：SVG 生成只能由当前主代理完成。
> ⚠️ **连续生成规则**：页面必须在同一上下文中一页一页连续生成，禁止分批切割。

**视觉构建阶段**：
- 连续逐页生成 SVG 到 `<project_path>/svg_output/`
- 在宣布 SVG 完成之前，必须运行：

```bash
python3 ${SKILL_DIR}/scripts/check_svg_text_fit.py <project_path>/svg_output
```

如果出现任何问题，必须先修 SVG（如：加 `<tspan>`、放大卡片、拆分内容、缩短文案、放大图示区域），修完才能继续。

**逻辑构建阶段**：
- 生成讲稿到 `<project_path>/notes/total.md`

**✅ 检查点**：

```markdown
## ✅ Executor 阶段完成
- [x] SVG 已生成到 svg_output/
- [x] 讲稿已生成到 notes/total.md
- [x] 页面分类结果已冻结
- [x] 页面中间协议对象已冻结
- [x] frame/slot 约束已冻结
- [x] 生成后的文案结构已记录
```

---

### Step 7：后处理与导出

🚧 **GATE**：Step 6 完成，`svg_output/` 和 `notes/total.md` 已准备好。

> ⚠️ 以下子步骤必须**逐条串行执行**。每一条成功后，才能执行下一条。

#### 最终交付前的模板与输出 QA（强制）

先读取：

```text
Read references/output-qa-checklist.md
```

必须检查：

1. 至少检查 4 类页面：
   - 1 页目录页
   - 1 页普通浅色内容页
   - 1 页密集内容页
   - 1 页图片重页面
2. 确认没有尺寸水印、裁剪框、选区框、截图工具 UI 等底图脏痕迹
3. 确认目录页大号数字不会压住标题
4. 确认中文 / 中英混排页面没有明显字体替换或字体碎裂
5. 确认图片重页面中的核心图示、截图、技术图、图表在当前尺寸下**可读**；如果肉眼看不清主要信息，视为未通过
6. 确认密集内容页即使没有越界，也不存在明显的视觉拥挤、文字互相压迫、卡片内部边框压字等问题；如果存在，视为未通过
7. 如果发现问题，必须先修模板、字体策略、SVG 排版或资源，再重新跑后处理和导出

#### 品牌锁定补充（安服风格固定页）

当用户明确要求“固定页背景和 logo 与参考图一致，不要自己发挥”时，额外执行以下规则：

1. 固定页范围按 6 页锁定：`01_cover.svg`、`02_toc.svg`、`03_chapter_PART_01.svg`、`07_PART_02.svg`、`14_chapter_PART_03.svg`、`26_ending.svg`。
2. 任何 fixed 页改动必须双目录同步：`svg_output/` 与 `svg_final/` 同时更新，避免导出版本不一致。
3. 避免在 fixed 页背景使用 `fill="url(#...)"` 渐变（`svglib/renderPM` 兼容性差，常见告警 `Can't handle color: url(#...)`）；优先使用纯色叠层 + 外部品牌带图片。
4. 如果 Playwright 截图超时，立即回退 `svglib + reportlab` 生成 fixed 页 PNG 回归图；并注明该链路可能出现本机字体替换现象，最终以 PPT 实际打开效果为准。
5. 每轮改稿后必须留痕：落盘 `gap_checklist_runX_YYYYMMDD.md`，记录命令、质检结果、导出文件名与回归图目录，防止会话输出被清理后证据丢失。

1. 至少检查 4 类页面：
   - 1 页目录页
   - 1 页普通浅色内容页
   - 1 页密集内容页
   - 1 页图片重页面
2. 确认没有尺寸水印、裁剪框、选区框、截图工具 UI 等底图脏痕迹
3. 确认目录页大号数字不会压住标题
4. 确认中文 / 中英混排页面没有明显字体替换或字体碎裂
5. 确认图片重页面中的核心图示、截图、技术图、图表在当前尺寸下**可读**；如果肉眼看不清主要信息，视为未通过
6. 确认密集内容页即使没有越界，也不存在明显的视觉拥挤、文字互相压迫、卡片内部边框压字等问题；如果存在，视为未通过
7. 如果发现问题，必须先修模板、字体策略、SVG 排版或资源，再重新跑后处理和导出

#### Step 7.1：拆分讲稿

```bash
python3 ${SKILL_DIR}/scripts/total_md_split.py <project_path>
```

#### Step 7.2：SVG 后处理

```bash
python3 ${SKILL_DIR}/scripts/finalize_svg.py <project_path>
```

#### Step 7.3：视觉渲染检查（强制）

```bash
python3 ${SKILL_DIR}/scripts/render_svg_pages.py <project_path> -s final
```

至少人工查看或由代理读取渲染图中的以下 4 类页面：

- 1 页目录页
- 1 页普通浅色内容页
- 1 页密集内容页
- 1 页图片重页面

如果发现文字碰撞、内容贴边、图片图示太小、页面虽然不越界但肉眼明显过挤，必须回到 SVG 修完，再继续。

#### Step 7.4：导出 PPTX

```bash
python3 ${SKILL_DIR}/scripts/svg_to_pptx.py <project_path> -s final
# 默认生成两个文件：原生可编辑 .pptx + SVG 参考版 _svg.pptx
```

#### Step 7.5：最终输出 QA（强制）

```bash
python3 ${SKILL_DIR}/scripts/check_pptx_fonts.py <project_path>
python3 ${SKILL_DIR}/scripts/write_qa_manifest.py <project_path>
```

如果 `check_pptx_fonts.py` 报出字体碎裂或字体混用警告，或者 `references/output-qa-checklist.md` 中任一项未通过，则禁止交付。

> ❌ 禁止用 `cp` 代替 `finalize_svg.py`
> ❌ 禁止直接从 `svg_output/` 导出，必须使用 `-s final`
> ❌ 禁止在这三步命令中随意加 `--only`

---

## 角色切换协议

切换角色之前，必须先读取对应参考文件，不能跳过。输出格式建议：

```markdown
## [角色切换：<Role Name>]
📖 读取角色定义：references/<filename>.md
📋 当前任务：<brief description>
```

---

## 参考资源

| 资源 | 路径 |
|------|------|
| 通用技术约束 | `references/shared-standards.md` |
| 画布格式说明 | `references/canvas-formats.md` |
| 图片布局说明 | `references/image-layout-spec.md` |
| SVG 图片嵌入规则 | `references/svg-image-embedding.md` |

---

## 实战陷阱（强制阅读）

> 以下陷阱均来自真实执行踩坑，违反会导致生成失败或导出异常。

### 陷阱 1：SVG 写入位置必须是 `svg_output/`

Executor 阶段生成的 SVG **必须直接写入** `<project_path>/svg_output/`，不能写入项目根目录。

后处理脚本（`finalize_svg.py`、`total_md_split.py`、`svg_to_pptx.py`）全部只扫描 `svg_output/` 子目录。如果 SVG 在项目根目录，这些脚本会报 "No SVG files found"。

```
❌ write_file path="<project_path>/01_cover.svg"
✅ write_file path="<project_path>/svg_output/01_cover.svg"
```

### 陷阱 2：SVG 中的图片引用必须用相对路径 `../images/`

SVG 中的 `<image href="..."/>` 引用项目图片时，路径是相对于 SVG 文件所在位置解析的。

- SVG 在 `svg_output/`，图片在 `images/`，所以相对路径是 `../images/xxx.png`
- `finalize_svg.py` 的 `embed-images` 步骤会按此路径查找文件并转为 Base64 嵌入
- 如果路径错误，会报 `[FAIL] xxx.png (NOT FOUND)`，图片不会被嵌入

```
❌ href="logo.png"
❌ href="images/logo.png"
✅ href="../images/logo.png"
```

### 陷阱 3：避免在 SVG 中使用 `fill="url(#gradientId)"` 渐变填充

`svg_to_pptx.py` 导出时**无法处理 SVG 渐变引用**，会输出 `Can't handle color: url(#...)` 并跳过该填充，导致渐变色条/渐变文字在 PPTX 中显示为透明。

替代方案：
- **品牌渐变条**：用纯色替代（取渐变主色），或使用品牌带图片
- **渐变装饰线**：拆为多段纯色矩形模拟渐变效果
- **渐变文字**：改用纯色文字

```
❌ <rect fill="url(#brandGrad)" />
✅ <rect fill="#6BFF85" />
✅ 或者用多段窄矩形模拟：<rect fill="#6BFF85"/><rect fill="#4DE8A0"/><rect fill="#22D3EE"/>
```

### 陷阱 4：内容页 footer 保护区域是 y ≤ 570

`svg_quality_checker.py` 定义 footer 保护区域为 `bottom > 570`（即 y + height > 570）。如果内容元素（卡片、文字、图片）的底部超过 y=570，会被标记为 `Footer zone violation`。

布局时请遵守：
- 内容区域安全范围：y=130 ~ y=560
- 底部品牌元素（logo、页码、装饰条）放在 y=600 以下
- 核心结论/收束条放在 y=550 ~ y=598 之间时需特别注意高度

### 陷阱 5：后处理流水线必须按顺序执行且每步验证

后处理三步必须严格串行，每步成功后再执行下一步：

1. `total_md_split.py` — 拆分讲稿（无讲稿时会跳过，不阻塞）
2. `finalize_svg.py` — SVG 后处理（嵌入图片、裁剪、修圆角等）
3. `svg_quality_checker.py` — 质量检查（可先跑，发现问题后再修 SVG）

如果 `finalize_svg.py` 报 `[FAIL] xxx (NOT FOUND)`，说明图片路径有误，必须先修路径再重跑。

### 陷阱 6：`sips` 替代 `PIL` 获取图片尺寸

在 macOS 上获取图片尺寸，使用 `sips -g pixelWidth -g pixelHeight <file>` 而不是 `python3 -c "from PIL import Image..."`。后者可能被用户环境限制阻止。

### 陷阱 7：深色背景页必须用亮色 logo，浅色背景页用深色 logo

固定页（cover / chapter / toc / ending）如果是深色背景（如深色底图 + overlay），必须使用亮色版本 logo（如 `*_light.png`），否则 logo 会和深色背景重叠不可见。白色/浅色内容页才使用深色版本 logo（如 `*_dark.png`）。

常见错误：所有页面统一用 `*_dark` logo，导致深色背景章节页/尾页的 logo 消失。

```
❌ 深色背景页用 logo_dark（与背景重叠不可见）
✅ 深色背景页用 logo_light；白色内容页用 logo_dark
```

### 陷阱 8：固定页版型必须严格对照源PPT素材，不能自由发挥

固定页（cover / toc / chapter / ending）的版型必须严格参照用户提供的源PPT素材或模板 SVG，不能用通用假设随意设计。

**前置动作（强制）**：在生成任何固定页 SVG 之前，如果用户提供了参考源PPT，必须先用 python-pptx 逐页提取源PPT的 shape 结构（位置、尺寸、文字、颜色），确认每个固定页的真实布局。不能凭"常见PPT格式"假设。提取结果保存到 `<project_path>/source_ppt_analysis.md`。

关键检查点：

1. **TOC页**：源PPT的TOC可能是深色背景+彩色编号+白色标题（右偏列表），也可能是白底居中列表。必须提取确认。
2. **Chapter页**：所有章节页必须使用统一版型。如果源PPT是"左侧大号数字+右侧标题+彩色线"，则所有章节页必须统一为此版型，不能部分用居中标题、部分用左对齐。
3. **Logo位置**：固定页如果源PPT有logo（如右下角），生成时也要加，且深色背景必须用亮色logo。
4. **固定页间版型一致性**：同类固定页（如所有 chapter 页）之间，数字位置、标题字号、装饰线长度、logo位置必须完全一致，不允许出现两套版型混用。

```python
# 源PPT结构提取脚本
from pptx import Presentation
prs = Presentation("source.pptx")
for i, slide in enumerate(prs.slides):
    print(f"Slide {i+1}:")
    for shape in slide.shapes:
        print(f"  {shape.shape_type}: pos=({shape.left},{shape.top}), size=({shape.width},{shape.height})")
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    try:
                        color = str(run.font.color.rgb) if run.font.color.type else 'inherit'
                    except:
                        color = 'inherit'
                    print(f"    '{run.text}' size={run.font.size} color={color}")
```

### 陷阱 9：文档原图素材应在合适页面自然使用，不要硬塞也不要完全忽略

源文档（DOCX/PDF）中的图片素材应提取出来（`unzip -o file.docx "word/media/*"`），然后在内容最相关的页面中自然使用。常见做法：

- 文档封面图 → PPT封面页作为视觉元素
- 流程图/架构图/路径图 → 对应的技术详解页作为主视觉
- 截图/证据图 → 对应的分析页

不要在无关页面硬塞原图（opacity很低也不行），也不要完全忽略文档自带的图片素材。

### 陷阱 10：图表必须尊重相邻面板边界，禁止跨区溢出

当页面包含左右/上下分区的图表布局时（如左柱状图+右环形图），所有图表元素的宽度/高度必须以分区边界为硬上限。

常见错误：水平柱状图的最长一条直接伸入右侧面板区域，导致文字和数值被右侧元素遮挡。

预防规则：
1. 先确定分区分界线坐标（如左区 x=0~650，右区 x=690~1280）
2. 所有柱状条宽度 + 数值标签的 x 坐标，必须严格限制在左区范围内
3. 柱状图最大宽度 = 分界线坐标 - 起始x - 留白(约30px)
4. 如果数据差异导致短bar和长bar差距过大，可以对数缩放或统一缩短，但绝不允许溢出

```
❌ bar width=720，数值标签 x=908（已进入右区680+）
✅ bar width=456，数值标签 x=644（在左区650内）
```

### 陷阱 11：源文档图片素材提取与映射（强制前置步骤）

当源材料是 DOCX/PDF 时，在 Strategist 阶段就必须完成图片提取和用途映射，不能等生成完再补。

**提取步骤**：
```bash
# DOCX: 解压提取媒体文件
unzip -o source.docx "word/media/*" -d /tmp/docx_images
# 用 sips 获取每张图片的尺寸
sips -g pixelWidth -g pixelHeight /tmp/docx_images/word/media/*
# 将图片复制到项目 images/ 目录
cp /tmp/docx_images/word/media/* <project_path>/images/
```

**用途映射**：在 design_spec.md 中必须包含一个 `source_images` 表：

```markdown
| 文件 | 尺寸 | 语义 | 目标页 | 用法 |
|------|------|------|--------|------|
| image1.jpeg | 1829x2405 | 报告封面 | P01_cover | 背景视觉元素 |
| image2.png | 1265x1480 | 流程图 | P13_diagram | 主视觉图示 |
```

**禁止行为**：
- 不要在无关页面以低 opacity 硬塞原图（如 opacity=0.5 的封面图放首页背景）
- 不要完全忽略文档自带的图片，全部用纯SVG重绘
- 图片必须服务于内容表达，不是装饰

---

## 备注

- 后处理命令不要额外乱加 `--only`
- 本地预览：`python3 -m http.server -d <project_path>/svg_final 8000`
