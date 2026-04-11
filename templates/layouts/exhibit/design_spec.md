# Exhibit 风格模板 - 设计规格

> 适用于数据驱动型战略汇报与高管演示，采用结论先行与 takeaway 条结构。

---

## 一、模板总览

| 属性 | 说明                                            |
| -------------- | ------------------------------------------------------ |
| **模板名称** | exhibit（Exhibit 风格模板） |
| **适用场景** | 战略规划、高管汇报、投资分析、董事会演示 |
| **设计调性** | 高级精致、权威克制、数据驱动、结论先行 |
| **主题模式** | 深色主题（深底 + 渐变强调 + 金色高亮） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **页面边距** | 左右 40px, Top 20px, Bottom 40px |
| **安全区**  | x: 40-1240, y: 40-680        |

---

## 三、配色方案

### 主色

| 角色           | 数值       | 说明                            |
| -------------- | ----------- | -------------------------------- |
| **Primary Dark** | `#0D1117` | Cover, chapter, ending 页面背景 |
| **内容 White** | `#FFFFFF` | 内容 page main 背景     |
| **Gradient Start Blue** | `#1E40AF` | Top gradient bar start point |
| **Gradient End Purple** | `#7C3AED` | Top gradient bar end point   |
| **Gold Accent** | `#D4AF37`  | 分隔线, highlight decorations  |
| **Purple-Blue Accent** | `#6366F1` | Chapter numbers, secondary accents |

### 文字颜色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **White Text** | `#FFFFFF`   | Primary text on dark 背景 |
| **Light Gray Text** | `#9CA3AF` | 说明s, subtitles |
| **Tertiary Text** | `#6B7280` | 页脚、时间戳     |
| **正文黑** | `#111827`   | 浅色背景上的正文文字 |

### 中性色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Card Background** | `#1F2937` | Dark card 背景 |
| **Divider**    | `#E5E7EB`   | 分隔线 on light 背景 |
| **Border Gray** | `#374151`  | Borders on dark 背景 |

---

## 四、字体系统

### 字体栈

**字体栈**： `Arial, "Helvetica Neue", sans-serif`

### 字号层级

| Level | 用途            | Size | Weight  | Letter Spacing |
| ----- | ---------------- | ---- | ------- | -------------- |
| H1    | 封面主标题 | 56px | 粗体    | 2px            |
| H2    | 页面主标题  | 28px | 粗体    | 1px            |
| H3    | 分节标题    | 48px | 粗体    | 2px            |
| H4    | 卡片标题       | 18px | 粗体    | 1px            |
| P     | 正文内容     | 14px | 常规 | -              |
| High  | 高亮数据 | 40px | 粗体    | -              |
| Sub   | 辅助文字   | 12px | 常规 | -              |

---

## 五、页面结构

### 通用布局

| Area           | Position/Height | 说明                            |
| -------------- | --------------- | -------------------------------------- |
| **Top**        | y=0, h=6px      | Gradient decorative bar (blue-purple gradient) |
| **页眉**     | y=20, h=60px    | Key message / page title               |
| **内容区** | y=100, h=520px | 主要内容区                    |
| **页脚**     | y=660, h=60px   | 数据来源、保密标识、页码 |

### 装饰元素

- **Top Gradient Bar**: Blue-purple gradient (`#1E40AF` → `#7C3AED`), height 4-6px
- **Left Gold Line**: Gold (`#D4AF37`), width 4px, used for chapter page decoration
- **Grid Decoration**: Low-opacity line grid for a data/precision feel

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- 深色背景 (`#0D1117`)
- Top gradient decorative bar
- Left gold vertical line decoration
- 主标题 + subtitle + project ID
- Right-side grid decoration
- Bottom date, confidential label, author info

### 2. 目录页 (02_toc.svg)

- 深色背景
- Top gradient bar
- Double vertical line separator `||` design (gold)
- Chapter numbers in purple-blue
- Right-side grid decoration
- Confidential label

### 3. 章节页 (02_chapter.svg)

- 深色背景
- Top gradient bar
- Left gold vertical line
- Large semi-transparent 背景 number
- 章节标题 + description
- Right-side grid decoration

### 4. 内容页 (03_content.svg)

- 白色背景
- Top gradient thin bar
- Dark key message bar (gold left decoration)
- 可灵活编排的内容区
- 页脚: 数据来源、保密标识、页码

### 5. 结束页 (04_ending.svg)

- 深色背景
- Top gradient bar
- Grid decoration 背景
- Centered thank-you message
- Gold divider
- Contact info card
- Confidential label + copyright

---

## VII. 版式模式

| 模式 | 适用场景 |
| ------------------ | ------------------------------ |
| **单列居中** | 封面、结束页            |
| **Left-Right Split (5:5)** | Data comparison         |
| **Left-Right Split (3:7)** | 图表 + text            |
| **Matrix Grid**    | Multi-dimensional analysis     |
| **Waterfall 图表** | Financial analysis            |
| **Table**          | Data summary                   |

---

## VIII. Spacing Guidelines

| Element            | 数值  |
| ------------------ | ------ |
| Card gap           | 20px   |
| 内容 block gap  | 24px   |
| Card padding       | 24px   |
| 卡片圆角 | 8px    |
| 图标与文字间距   | 10px   |

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; no `rgba()`
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Use `<polygon>` triangles for arrows instead of `<marker>`
8. Define gradients using `<defs>` with `<linearGradient>`

### PPT 兼容性规则

- No `<g opacity="...">` (分组透明度); set opacity on each child element individually
- Use overlay layers for image transparency
- Inline styles only; no external CSS or `@font-face`

---

## 十、占位符规范

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| 占位符 | 说明 |
| ------------------ | ------------------ |
| `{{TITLE}}`        | 主标题         |
| `{{SUBTITLE}}`     | 副标题           |
| `{{PROJECT_ID}}`   | Project ID         |
| `{{AUTHOR}}`       | Author             |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | 页面标题         |
| `{{KEY_MESSAGE}}`  | Key message (Exhibit) |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| 章节标题      |
| `{{PAGE_NUM}}`     | 页码        |
| `{{SOURCE}}`       | Data source        |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题 |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{CONTACT_NAME}}` | Contact person name |
| `{{CONTACT_INFO}}` | Contact information |
| `{{COPYRIGHT}}`    | Copyright info     |
| `{{LOGO}}`         | Logo 文字          |

---

## XI. Signature Design Elements

### Confidential Label

All pages display a centered `CONFIDENTIAL` label at the bottom in gold text.

### Exhibit 标题 Bar

内容 pages feature a dark 背景 + gold left decoration key message bar at the top, similar to the "Exhibit" style used by consulting firms.

### Grid Background

Chapter and ending pages use low-opacity grid line decoration to create a professional data analysis atmosphere.

---

## 十二、使用说明

1. Copy the template to the project directory
2. Select the appropriate page template based on content needs
3. Use placeholders to mark content that needs replacement
4. Ensure the confidential label displays correctly
5. 由 Executor 角色生成最终 SVG
