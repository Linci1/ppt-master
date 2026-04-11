# 长亭安服模板 - 设计规格

## 一、模板总览

| 字段 | 内容 |
|------|------|
| 模板 ID | `security_service` |
| 模板名称 | 长亭安服 |
| 模板分类 | `scenario` |
| 适用场景 | 长亭安服解决方案、攻防演习总结、安全运营介绍、能力证明型胶片 |
| 风格概述 | 专业技术、证据导向、结论先行 |
| 主题模式 | 浅色主题（白底 + 蓝橙强调） |
| 对齐参考 | `长亭安服主打胶片- v2.2-0427.pptx` |

## 二、历史对齐目标

这个模板**不是**通用安全汇报模板，而是对齐长亭安服历史胶片的表达方式与绘图习惯。

### 推荐叙事顺序

1. 品牌与理念铺垫
2. 安服体系总览
3. `攻` / `防` / `培` / `安全运营` 分域能力展开
4. 结果导向的案例证明
5. 客户、赛事、研究、资质等可信度背书

### 行文规则

- 标题优先结论先行，不只写中性主题名
- 正文优先短句、标签、数据点，不写长段说明
- 生成正文前必须先明确：`页面意图`、`证明目标`、`核心判断`、`支撑证据`
- 案例页必须体现“背景/动作/结果”或“挑战/方案/成效”证明链
- 背书页优先做证据墙、矩阵、能力图，不优先做普通列表页
- 文本必须避免黑话和 AI 自造术语，具体黑白名单见 `qa_profile.md` 与 `text_prompt_snippets.md`

## 三、画布规格

```yaml
viewBox: "0 0 1280 720"
width: 1280
height: 720
ratio: 16:9
```

## 四、配色方案

| 角色 | 名称 | HEX | 用途 |
|------|------|-----|------|
| 主色 | 深蓝 | `#0563C1` | 主标题、页眉条、关键结构 |
| 次色 | 蓝色 | `#4472C4` | 次级标题、模块卡片 |
| 强调色 | 橙色 | `#ED7D31` | 关键指标、结论、结果高亮 |
| 辅助色 | 浅蓝 | `#5B9BD5` | 标签、连接、辅助模块 |
| 正文色 | 深灰 | `#44546A` | 正文文字 |
| 背景色 | 白色 | `#FFFFFF` | 页面背景 |
| 中性色 | 浅灰 | `#E7E6E6` | 分隔线、轻底色 |
| 正向色 | 绿色 | `#70AD47` | 正向指标 |
| 重点色 | 金黄 | `#FFC000` | 特别提醒 |

## 五、字体系统

```yaml
font_plan:
  chinese: "微软雅黑"
  english: "Arial"
  fallback: "Microsoft YaHei, Arial, sans-serif"

font_size_hierarchy:
  cover_title: 52-60px
  chapter_title: 42-48px
  page_title: 28-32px
  section_heading: 20-24px
  body: 13-16px
  caption: 12-14px
  footer: 14px
```

## 六、模板固定骨架

下列元素属于固定骨架，生成时必须保持稳定。

| 元素 | 位置 | 规则 |
|------|------|------|
| 顶部强调条 | y: 0-6px | 固定品牌结构 |
| 左侧竖条 | x: 0-8px | 固定品牌结构 |
| 标题引导条 | x: 60-66px / y: 50-94px | 必须可见，不得被正文压住 |
| 页眉区 | y: 40-105px | 标题安全区 |
| 正文主内容区 | y: 120-620px | 灵活内容区域 |
| 页脚信息区 | y: 650-700px | 仅页码或固定页脚信息可进入 |
| 底部橙色装饰条 | y: 714-720px | 保护装饰区 |
| 封面 Logo 安全区 | x: 1080-1245 / y: 630-690 | 禁止正文侵入 |
| 顶部 Logo 安全区 | x: 1088-1240 / y: 42-94 | 禁止标题、正文、图示侵入 |
| 结束页 Logo 安全区 | x: 1100-1245 / y: 40-95 | 禁止正文侵入 |

### 品牌资产固定规则

- `security_service` 命中后，**所有模板页都必须保留长亭 Logo**
- 只允许使用以下批准资产：
  - `images/logo_green.png`：浅底内容页 / 目录页 / 证据页
  - `images/logo_top_right.png`：深色背景图页、章节页、结束页
  - `images/logo_bottom_right.png`：封面页、大图页
- 不允许：
  - 缺失 Logo
  - 在浅底页继续使用白色 Logo 导致不可见
  - 自行添加白底、描边、底板
  - 用非批准文件替换品牌元素

## 七、页面模板清单

### 核心模板（5 页）

| # | 文件 | 用途 | 主要占位符 |
|---|------|------|-----------|
| 1 | `01_cover.svg` | 封面页 | `{{TITLE}}`, `{{SUBTITLE}}`, `{{DATE}}` |
| 2 | `02_chapter.svg` | 章节页 | `{{CHAPTER_NUM}}`, `{{CHAPTER_TITLE}}`, `{{CHAPTER_DESC}}`, `{{PAGE_NUM}}` |
| 3 | `02_toc.svg` | 目录页 | `{{TOC_ITEM_1_TITLE}}`, `{{TOC_ITEM_1_DESC}}`, `{{TOC_ITEM_2_TITLE}}`, `{{TOC_ITEM_2_DESC}}`, `{{TOC_ITEM_3_TITLE}}`, `{{TOC_ITEM_3_DESC}}`, `{{TOC_ITEM_4_TITLE}}`, `{{TOC_ITEM_4_DESC}}`, `{{PAGE_NUM}}` |
| 4 | `03_content.svg` | 基础兜底内容页 | `{{PAGE_TITLE}}`, `{{CONTENT_AREA}}`, `{{PAGE_NUM}}`, `{{SECTION_NAME}}` |
| 5 | `04_ending.svg` | 结束页 | `{{THANK_YOU}}`, `{{CLOSING_MESSAGE}}`, `{{CONTACT_INFO}}`, `{{COPYRIGHT}}` |

### 叙事模板（15 页）

| # | 文件 | 用途 | 主要占位符 |
|---|------|------|-----------|
| 6 | `05_case.svg` | 通用案例页 | `{{PAGE_TITLE}}`, `{{CASE_BACKGROUND}}`, `{{CASE_SOLUTION}}`, `{{CASE_PROCESS}}`, `{{CASE_RESULTS}}`, `{{CASE_IMAGE}}`, `{{CASE_CLIENT}}`, `{{PAGE_NUM}}` |
| 7 | `06_tactics.svg` | 方法论 / 战术页 | `{{PAGE_TITLE}}`, `{{TACTICS_CATEGORY}}`, `{{TACTIC_POINT_1-6}}`, `{{TACTICS_IMAGE}}`, `{{TACTICS_HIGHLIGHT}}`, `{{PAGE_NUM}}` |
| 8 | `07_data.svg` | 数据证明页 / 结果总览页 | `{{PAGE_TITLE}}`, `{{DATA_VALUE_1-4}}`, `{{DATA_LABEL_1-4}}`, `{{DATA_NOTE_1-3}}`, `{{CHART_AREA}}`, `{{PAGE_NUM}}` |
| 9 | `08_product.svg` | 分层攻击树 / 复杂结构页 | `{{PAGE_TITLE}}`, `{{PRODUCT_NAME}}`, `{{PRODUCT_TAGLINE}}`, `{{PRODUCT_IMAGE}}`, `{{PRODUCT_FEATURE_1-6}}`, `{{PRODUCT_VALUE}}`, `{{PAGE_NUM}}` |
| 10 | `09_comparison.svg` | 多泳道实施链 / 对照页 | `{{PAGE_TITLE}}`, `{{COMPARE_TITLE_A}}`, `{{COMPARE_TITLE_B}}`, `{{COMPARE_CONTENT_A_1-4}}`, `{{COMPARE_CONTENT_B_1-4}}`, `{{COMPARE_RESULT}}`, `{{PAGE_NUM}}` |
| 11 | `10_timeline.svg` | 时间线 / 历程页 | `{{PAGE_TITLE}}`, `{{TIME_NODE_1-5}}`, `{{TIME_DESC_1-5}}`, `{{TIME_SUMMARY_TITLE}}`, `{{TIME_SUMMARY_CONTENT}}`, `{{PAGE_NUM}}` |
| 12 | `11_list.svg` | 结构化列表页 | `{{PAGE_TITLE}}`, `{{LIST_TITLE_1-5}}`, `{{LIST_DESC_1-5}}`, `{{PAGE_NUM}}` |
| 13 | `12_grid.svg` | 栅格 / 矩阵页 | `{{PAGE_TITLE}}`, `{{GRID_CARD_1-6}}`, `{{GRID_DESC_1-6}}`, `{{GRID_SUMMARY}}`, `{{PAGE_NUM}}` |
| 14 | `13_highlight.svg` | 单一重点指标页 | `{{PAGE_TITLE}}`, `{{HIGHLIGHT_VALUE}}`, `{{HIGHLIGHT_UNIT}}`, `{{HIGHLIGHT_DESC}}`, `{{SIDE_STAT_1}}`, `{{SIDE_LABEL_1}}`, `{{SIDE_STAT_2}}`, `{{SIDE_LABEL_2}}`, `{{PAGE_NUM}}` |
| 15 | `14_fullimage.svg` | 全图叠字页 | `{{PAGE_TITLE}}`, `{{FULL_IMAGE}}`, `{{FULL_TITLE}}`, `{{FULL_SUBTITLE}}`, `{{FULL_POINT_1-3}}` |
| 16 | `15_section.svg` | 分节过渡页 | `{{SECTION_NUM}}`, `{{SECTION_TITLE}}`, `{{SECTION_DESC}}`, `{{PAGE_NUM}}` |
| 17 | `16_table.svg` | 控制矩阵 / 治理看板页 | `{{PAGE_TITLE}}`, `{{TABLE_ROW_1-5_COL_1-4}}`, `{{TABLE_INSIGHT_1-3}}`, `{{TABLE_HIGHLIGHT}}`, `{{PAGE_NUM}}` |
| 18 | `17_service_overview.svg` | 安服体系总览页 | `{{PAGE_TITLE}}`, `{{OVERVIEW_LEAD}}`, `{{PLATFORM_NAME}}`, `{{PLATFORM_DESC}}`, `{{DRIVER_TITLE}}`, `{{DRIVER_POINT_1}}`, `{{DRIVER_POINT_2}}`, `{{DOMAIN_ATTACK_TITLE}}`, `{{DOMAIN_ATTACK_DESC}}`, `{{DOMAIN_DEFENSE_TITLE}}`, `{{DOMAIN_DEFENSE_DESC}}`, `{{DOMAIN_TRAINING_TITLE}}`, `{{DOMAIN_TRAINING_DESC}}`, `{{VALUE_1}}`, `{{VALUE_2}}`, `{{VALUE_3}}`, `{{PAGE_NUM}}` |
| 19 | `18_domain_capability_map.svg` | `攻 / 防 / 培 / 运营` 能力地图页 | `{{PAGE_TITLE}}`, `{{DOMAIN_LABEL}}`, `{{SCENE_TITLE}}`, `{{SCENE_POINT_1-3}}`, `{{CAPABILITY_1_TITLE}}`, `{{CAPABILITY_1_DESC}}`, `{{CAPABILITY_2_TITLE}}`, `{{CAPABILITY_2_DESC}}`, `{{CAPABILITY_3_TITLE}}`, `{{CAPABILITY_3_DESC}}`, `{{CAPABILITY_4_TITLE}}`, `{{CAPABILITY_4_DESC}}`, `{{OUTCOME_TITLE}}`, `{{OUTCOME_1-3}}`, `{{METHOD_NOTE}}`, `{{PAGE_NUM}}` |
| 20 | `19_result_leading_case.svg` | 复杂案例链 / 结果导向案例页 | `{{PAGE_TITLE}}`, `{{RESULT_HEADLINE}}`, `{{CLIENT_CONTEXT}}`, `{{CHALLENGE_1-3}}`, `{{ACTION_1-3}}`, `{{RESULT_1-3}}`, `{{KEY_METRIC}}`, `{{KEY_METRIC_LABEL}}`, `{{PAGE_NUM}}` |

## 八、页面选型优先级

当选择该模板时，页面选型应优先贴合历史胶片逻辑，而不是退回通用报告默认值。

### 选页总原则

不是“先看哪页能装下内容”，而是：

```text
先判断这页要证明什么
→ 再判断是否命中高级正文模式
→ 再从对应主承接页型中选 SVG
→ 主承接页型不合适时，才退到次承接页型或兜底页
```

补充原则：

- 高级正文模式只在文档内容本身存在复杂结构关系时启用
- 复杂页必须服务表达效率，而不是服务“高级感”
- 如果简单结构已经能更准确地说明问题，就不应强行升级为复杂页
- 任何命中高级正文模式的页面，都应能解释：为什么简单页不够、为什么当前复杂结构更适合这页内容

| 表达意图 | 优先页型 | 说明 |
|---------|---------|------|
| 品牌与理念 | `17_service_overview.svg`, `12_grid.svg`, `03_content.svg` | 优先体系/理念图，不优先普通列表 |
| 安服体系总览 | `17_service_overview.svg`, `18_domain_capability_map.svg` | 强调“平台 + 服务 + 结果” |
| `攻 / 防 / 培 / 运营` 能力展开 | `18_domain_capability_map.svg`, `06_tactics.svg`, `07_data.svg` | 优先能力地图或方法论图 |
| 案例证明 | `19_result_leading_case.svg`, `05_case.svg`, `07_data.svg` | 必须突出结果与成效 |
| 背书页 | `12_grid.svg`, `16_table.svg`, `07_data.svg` | 做证据墙/矩阵，不做长段正文 |
| 兜底页 | `03_content.svg`, `11_list.svg`, `09_comparison.svg` | 仅在没有更合适页型时使用 |

### 高级正文模式到页型映射

复杂正文页必须结合 `advanced_page_patterns.md` 中的模式选择对应页型。

| 高级正文模式 | 主承接页型 | 次承接页型 | 兜底页型 |
|-------------|-----------|-----------|---------|
| 分层体系图 | `17_service_overview.svg` | `08_product.svg`, `18_domain_capability_map.svg` | `03_content.svg` |
| 阶段演进 / 路线图 | `10_timeline.svg` | `15_section.svg`, `09_comparison.svg` | `03_content.svg` |
| 攻击链 / 案例链路图 | `19_result_leading_case.svg` | `05_case.svg` | `03_content.svg` |
| 闭环运营 / 机制图 | `18_domain_capability_map.svg` | `17_service_overview.svg`, `06_tactics.svg` | `03_content.svg` |
| 泳道协同图 | `05_case.svg` | `10_timeline.svg`, `06_tactics.svg` | `03_content.svg` |
| 矩阵防御 / 映射图 | `12_grid.svg` | `16_table.svg`, `09_comparison.svg` | `03_content.svg` |
| 成熟度模型 / 能力评估图 | `18_domain_capability_map.svg` | `12_grid.svg`, `16_table.svg` | `03_content.svg` |
| 证据墙 / 背书页 2.0 | `12_grid.svg` | `16_table.svg`, `07_data.svg` | `03_content.svg` |
| 多泳道实施链 | `09_comparison.svg` | `05_case.svg`, `10_timeline.svg` | `03_content.svg` |
| 分层攻击树 / 复杂结构图 | `08_product.svg` | `17_service_overview.svg`, `18_domain_capability_map.svg` | `03_content.svg` |
| 数据证明页 / 结果总览 | `07_data.svg` | `19_result_leading_case.svg`, `12_grid.svg` | `03_content.svg` |
| 控制矩阵 / 治理看板 | `16_table.svg` | `12_grid.svg`, `07_data.svg` | `03_content.svg` |
| 复杂案例链 / 证据案例链 | `19_result_leading_case.svg` | `05_case.svg`, `07_data.svg` | `03_content.svg` |

### 禁止的退化选页

以下情况即使“能排下”，也视为选页错误：

- 体系图退化成 `11_list.svg`
- 攻击链退化成普通 `03_content.svg` 三段式卡片
- 闭环机制退化成无循环感的普通流程列表
- 证据墙退化成无分组的 logo / 截图拼贴
- 治理看板退化成普通数据表截图
- 复杂案例链退化成无证据附着的三段并列卡片

### 强制命中信号与回退门禁

当页面出现以下信号时，应先命中对应高级正文模式，再选页；不能直接拿普通内容页兜底。

| 模式 | 典型触发信号 | 应优先页型 | 禁止直接退化 |
|------|-------------|-----------|-------------|
| 分层体系图 | `体系 / 架构 / 平台 + 服务 + 结果 / 多层能力域` | `17_service_overview.svg` | `11_list.svg` |
| 阶段演进 / 路线图 | `阶段 / 路线图 / 里程碑 / 演进 / 建设路径` | `10_timeline.svg` | `03_content.svg` |
| 攻击链 / 案例链路图 | `入侵路径 / 横向移动 / 关键动作 / 中间突破 / 最终影响` | `19_result_leading_case.svg` | `03_content.svg`, `11_list.svg` |
| 闭环运营 / 机制图 | `闭环 / 循环 / 持续优化 / 平战切换 / 输入-处置-验证` | `18_domain_capability_map.svg` | `03_content.svg` |
| 泳道协同图 | `客户侧 / 长亭侧 / 多角色协同 / 战前战中战后联动` | `05_case.svg` | `11_list.svg` |
| 矩阵防御 / 映射图 | `矩阵 / 映射 / 横纵维度 / 风险域 x 控制域` | `12_grid.svg` | `03_content.svg`, `11_list.svg` |
| 成熟度模型 / 能力评估图 | `成熟度 / 等级 / 当前状态 / 目标状态 / 提升路径` | `18_domain_capability_map.svg` | `11_list.svg` |
| 证据墙 / 背书页 2.0 | `客户版图 / 赛事成绩 / 资质认证 / 研究成果 / 人才储备` | `12_grid.svg` | `11_list.svg` |
| 多泳道实施链 | `多角色协同 / 阶段推进 / 交付链 / 客户侧 x 长亭侧` | `09_comparison.svg` | `03_content.svg`, `11_list.svg` |
| 分层攻击树 / 复杂结构图 | `攻击树 / 根因拆解 / 分层结构 / 入口到目标` | `08_product.svg` | `03_content.svg`, `11_list.svg` |
| 数据证明页 / 结果总览 | `KPI + 主证据图 / 指标+结论分层` | `07_data.svg` | `11_list.svg` |
| 控制矩阵 / 治理看板 | `控制矩阵 / 治理看板 / 控制点盘点 / 域-状态-动作` | `16_table.svg` | `03_content.svg`, `11_list.svg` |
| 复杂案例链 / 证据案例链 | `节点证据 / 复杂案例链 / 关键突破 + 结果证明` | `19_result_leading_case.svg` | `03_content.svg`, `11_list.svg` |

## 九、本地规则文档

使用 `security_service` 时，除本文件外，还必须同时读取以下文档：

- `qa_profile.md`：模板级品牌、版式、文本、逻辑 QA 护栏
- `ppt_logic_reference.md`：历史胶片节奏、正文表达与绘图逻辑
- `advanced_page_patterns.md`：复杂正文模式与页型映射
- `text_prompt_snippets.md`：正文文本提炼 prompt 片段
- `generation_checklist.md`：生成前、生成中、导出前检查清单
- `complex_graph_semantics.md`：复杂图形语义与节点/关系规则
- `complex_case_chain_modeling.md`：复杂案例链建模规则
- `complex_page_logic_qa_checklist.md`：复杂页逻辑 QA 清单
- `complex_page_reasoning_template.md`：复杂页推理模板
- `evidence_grading_rules.md`：证据分级与挂载规则
- `complex_deck_orchestration.md`：复杂页在整套 deck 中的编排规则

### 内容大纲输出要求

项目级 `design_spec.md` 中，除封面 / 目录 / 章节 / 结束页外，每个正文页都必须补充：

- `页面意图`
- `证明目标`
- `高级正文模式`
- `优先页型`
- 若 `优先页型` 为 `03_content.svg` 或 `11_list.svg`，补 `回退原因`

若缺失这些字段，视为 Strategist 尚未完成 `security_service` 的选页工作，不允许直接进入 Executor。

若某页的 `高级正文模式` 不为 `无`，则在进入 SVG 生成前，还必须把该页的复杂页建模结果写入 `<project_path>/notes/complex_page_models.md`，并使用 `complex_page_reasoning_template.md` 的字段结构保存。页面标题必须与项目级 `design_spec.md` 中的对应页面标题保持一致，供 `check_complex_page_model.py` 做强制校验。

## 十、标题写法规则

- 能力页优先写成：`"攻"——自动化攻防体系`、`"防"——常态化主防体系`、`"培"——人才培养体系`
- 运营页优先写成：`【安全运营】...` 这类带价值表达的标题
- 案例页优先写成：`案例 X：客户/行业——结果结论`
- 背书页优先用结论式标题，如 `攻防赛事大满贯`、`行业领先的完整资质认证`
- 避免使用 `案例介绍`、`能力说明`、`项目背景` 这种过于中性的标题

## 十一、SVG 技术约束

### 禁用能力

- `clipPath`
- `mask`
- `<style>`
- `class`
- `foreignObject`
- `textPath`
- `@font-face`
- `<animate*>`
- `marker-end`
- `iframe`
- `<symbol> + <use>`

### 颜色与透明度规则

- 使用 `fill-opacity`，不要使用 `rgba()`
- 透明度设置到具体元素上，不要设置到整组 `<g>` 上

## 十二、背景与品牌资源

| 文件 | 用途 |
|------|------|
| `images/背景.jpeg` | 封面、章节/分节页背景 |
| `images/layout_bg.png` | 内容页、证据页背景 |
| `images/logo_green.png` | 浅底页绿色 Logo |
| `images/logo_bottom_right.png` | 封面 Logo |
| `images/logo_top_right.png` | 结束页 Logo |
| `images/logo.jpeg` | 全量 Logo 参考图 |

### 背景图使用规则

| 页面类型 | 背景 | Logo |
|----------|------|------|
| 封面 `01_cover.svg` | `背景.jpeg`（全屏） | `logo_bottom_right.png` |
| 目录 `02_toc.svg` | 无背景图 | `logo_green.png`（右上） |
| 章节 / 分节 `02_chapter.svg`, `15_section.svg` | `背景.jpeg`（全屏） | `logo_top_right.png`（右上） |
| 内容 / 背书 `03_content.svg`, `05-19_*.svg` | `layout_bg.png`（浅底） | `logo_green.png`（右上，`14_fullimage.svg` 除外） |
| 大图页 `14_fullimage.svg` | 主图全屏 | `logo_bottom_right.png` |
| 结束页 `04_ending.svg` | `背景.jpeg`（全屏） | `logo_top_right.png` |

## 十三、模板本地资源说明

这个模板当前只包含背景图与 Logo 资源，**不包含**单独的本地图标包 `images/icons/`。

- 如需图标，请使用全局图标库 `templates/icons/icons_index.json`
- 除非后续明确补入模板私有图标，否则不要引用 `../images/icons/*.svg`

## 十四、质量检查重点

导出前必须同时检查布局稳定性与历史风格一致性。

### 布局检查重点

- 文本断句与中文可读性
- 文本贴边 / 卡片拥挤风险
- 卡片内视觉溢出风险
- 页脚 / 页码 / 底部装饰条冲突
- Logo 安全区冲突
- Logo 版本是否与页面背景匹配，且是否仍在批准资产列表内

### 历史风格检查重点

- 章节推进是否仍符合长亭安服历史胶片逻辑
- 能力页是否优先使用图示，而不是退化成普通列表
- 案例页是否结果导向
- 背书页是否呈现为证据墙，而不是普通总结页

### 逻辑参考

- 生成正文前必须阅读 `ppt_logic_reference.md`
- 生成复杂正文页前必须阅读 `advanced_page_patterns.md`
- 规划 `05_case.svg`、`17_service_overview.svg`、`18_domain_capability_map.svg`、`19_result_leading_case.svg` 时，必须阅读 `svg_semantic_upgrade_plan.md`
- 如需程序化选页，应优先读取 `templates/layouts/layouts_index.json` 中 `security_service.advancedPageStrategy`
- 应把本模板视为“安服解决方案 / 能力证明型胶片”，而不是通用品牌页只换成浅色皮肤
