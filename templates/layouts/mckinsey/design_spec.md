# 麦肯锡风格模板 - 设计规格

> 适用于战略咨询、投资分析与高层决策汇报。

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | mckinsey（麦肯锡风格模板） |
| **适用场景** | 战略咨询、投资分析、高层决策汇报 |
| **设计调性** | 数据驱动、结构化思考、留白专业、极简高级 |
| **主题模式** | 浅色主题（白底 + 麦肯锡蓝强调） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **页面边距** | 左右 60px, Top 60px, Bottom 40px |
| **安全区**  | x: 60-1220, y: 60-680         |
| **Grid Baseline** | 40px                       |

---

## 三、配色方案

### 主色

| 角色             | 数值       | 说明                            |
| ---------------- | ----------- | -------------------------------- |
| **McKinsey Blue**| `#005587`   | Primary color, title bar, accent elements |
| **Deep Teal**    | `#004D5C`   | Secondary blue, gradient endpoint |
| **Background White** | `#FFFFFF` | Main 页面背景            |
| **Light Gray Background** | `#ECF0F1` | Separators, secondary 背景 |

### 文字颜色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **标题 Dark Gray** | `#2C3E50` | 主标题, card titles |
| **正文灰**  | `#5D6D7E`   | 正文内容, descriptive text |
| **Auxiliary Gray** | `#7F8C8D` | 标注、来源、页脚 |
| **White Text** | `#FFFFFF`   | Text on blue 背景 |

### Accent Colors

| 用途            | 数值       | 说明            |
| ---------------- | ----------- | ---------------------- |
| **Data Highlight** | `#F5A623` | Amber, key data emphasis |
| **Warning/Issue** | `#E74C3C`  | Coral, problem areas, negative indicators |
| **Success/Positive** | `#27AE60` | Green, positive indicators |
| **信息 Blue**    | `#0076A8`   | 补充信息、图表渐变 |

---

## 四、字体系统

### 字体栈

**字体栈**： `Arial, "Helvetica Neue", "Segoe UI", sans-serif`

### 字号层级

| Level    | 用途              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | 封面主标题   | 52px    | 粗体    |
| H2       | 页面标题         | 36px    | 粗体    |
| H3       | 分节标题      | 22-24px | 粗体    |
| H4       | 卡片标题         | 16-18px | 粗体    |
| P        | 正文内容       | 14-16px | 常规 |
| Data     | 数据高亮     | 44px    | 粗体    |
| Sub      | 图表标签/标注 | 12-14px | 常规 |

---

## V. Core Design Principles

### 麦肯锡风格特征

1. **Data-Driven**: Key data and insights at the core, strengthening argument support
2. **Structured Thinking**: MECE principle, clear logical frameworks
3. **信息 Visualization**: 图表, matrices, and funnel models take priority
4. **Professional Whitespace**: Ample breathing room, content coverage < 65%
5. **网格对齐**: 40px baseline grid, precise alignment
6. **Minimalist Icons**: Geometric shapes, avoiding ornate decoration
7. **Professional Color Palette**: Avoiding flashy gradients, maintaining restraint

---

## 六、页面结构

### 通用布局

| Area       | Position/Height | 说明                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=4px      | McKinsey Blue horizontal bar           |
| **标题区** | y=40, h=60px | 页面标题 (left-aligned, large bold)  |
| **内容区** | y=120, h=520px | 主要内容区                  |
| **页脚** | y=680, h=40px   | 页码 (left), data source/confidential label (right) |

### 装饰设计

- **Left Accent Bar**: McKinsey Blue (`#005587`), width 8px (cover page)
- **Top Decoration Line**: McKinsey Blue (`#005587`), height 4px
- **Card Borders**: Light gray (`#ECF0F1`), width 2px
- **Geometric Decoration**: Low-opacity blue geometric patterns (cover page right side)

---

## 七、页面类型

### 1. 封面页 (01_cover.svg)

- 白色背景
- Left-side blue narrow accent bar (8px)
- Top-left short horizontal line decoration
- 主标题 + subtitle (left-aligned)
- Bottom project code, date
- Right-side low-opacity geometric decoration
- Bottom-right confidential label

### 2. 目录页 (02_toc.svg)

- 白色背景
- Top blue decoration bar
- 标题 area "Agenda" / "内容s"
- Chapter list (number + title)
- Clean line separators

### 3. 章节页 (02_chapter.svg)

- McKinsey Blue full-screen 背景
- Centered large chapter title
- White text
- Minimalist design

### 4. 内容页 (03_content.svg)

- 白色背景
- Top blue decoration bar
- Left-aligned page title
- 可灵活编排的内容区
- 页脚：页码、数据来源

### 5. 结束页 (04_ending.svg)

- 白色背景
- Centered thank-you message
- Contact information
- Confidential label

---

## VIII. 图表规范

### 推荐图表尺寸

| 图表类型       | 推荐尺寸   |
| ---------------- | ------------------ |
| 柱状图        | 500-700 × 400-500px |
| 饼图        | Diameter 300-400px |
| Data card        | 150 × 120px       |
| Matrix           | 240-280px / cell   |
| 漏斗图     | 500 × 400px       |

### 图表色板

- Primary series: `#005587`, `#0076A8`, `#4A90A4`
- Accent: `#F5A623`
- Warning: `#E74C3C`

---

## IX. Spacing Guidelines

| Element          | 数值    |
| ---------------- | -------- |
| 页面边距     | 60px     |
| 标题 area height | 80-100px |
| 图表间距    | 40-60px  |
| Card padding     | 20-24px  |
| Text line height | 1.6      |
| Grid baseline    | 40px     |

---

## 十、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; `rgba()` is prohibited
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Use `<polygon>` triangles instead of `<marker>` for arrows
8. Define gradients using `<linearGradient>` within `<defs>`

### PPT 兼容性规则

- No `<g opacity="...">` (分组透明度); set opacity on each child element individually
- Use overlay layers instead of image opacity
- Use inline styles only; external CSS and `@font-face` are prohibited

---

## 十一、占位符说明

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| 占位符 | 说明 |
| ------------------ | ------------------ |
| `{{TITLE}}`        | 主标题         |
| `{{SUBTITLE}}`     | 副标题           |
| `{{PROJECT_CODE}}` | Project code       |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | 页面标题         |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| 章节标题      |
| `{{PAGE_NUM}}`     | 页码        |
| `{{SOURCE}}`       | Data source        |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题 |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{CONTACT_INFO}}` | Contact information |
| `{{CONFIDENTIAL}}` | Confidential label |

---

## XII. Quality Checklist

### Pre-Generation

- [ ] Each page has a clear core message
- [ ] Sufficient data support
- [ ] Clear logical structure

### Post-Generation

- [ ] viewBox = `0 0 1280 720`
- [ ] McKinsey Blue consistently applied
- [ ] Key data prominently highlighted (Amber/Coral)
- [ ] 图表坐标轴标注完整
- [ ] Text readability is good (contrast ratio > 4.5:1)
- [ ] Elements precisely aligned (grid alignment)
- [ ] 页码s/footer information complete
- [ ] No `<foreignObject>`
- [ ] All text uses `<tspan>` for line breaks

---

## 十三、使用说明

1. Copy the template to the project directory
2. Select the appropriate page template based on briefing content requirements
3. Mark content to be replaced using placeholders
4. Prioritize data charts; keep text concise
5. 由 Executor 角色生成最终 SVG
