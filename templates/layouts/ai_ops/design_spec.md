# 企业数字智能模板 - 设计规格

> 适用于运营商 AI 运维架构、IT 系统总览、数字化转型方案等高信息密度场景。

> **风格参考**：参见 `reference_style.svg`（运营商 AI 运维架构总览），该文件展示了本模板的核心视觉语言。

---

## 一、模板总览

| 属性 | 说明                                                                    |
| ------------------ | ------------------------------------------------------------------------------ |
| **模板名称** | ai_ops（企业数字智能模板） |
| **适用场景** | 运营商 AI 运维架构、IT 系统总览、数字化转型方案、智慧基础设施汇报 |
| **设计调性** | 信息密度高、结构清晰、模块化布局、运营商/政企风格 |
| **主题模式** | 浅色主题（白底 + 红蓝强调 + 暖灰面板） |
| **信息密度** | 高密度——单页可容纳 6-10 个信息模块，符合运营商常见汇报习惯 |

---

## 二、画布规格

| 属性 | 值                            |
| ------------------ | -------------------------------- |
| **格式**         | 标准 16:9                    |
| **尺寸**     | 1280 × 720 px                   |
| **viewBox**        | `0 0 1280 720`                  |
| **页面边距**   | Left/right 30-50px, top 20px, bottom 40px |
| **内容安全区** | x: 30-1250, y: 80-680        |
| **标题区**     | y: 20-80                        |
| **网格基线** | 20px（高密度布局需要更细的网格） |

> **说明**：本模板的边距比标准模板更窄（30px 对比 60px），以适配运营商场景常见的高信息密度汇报风格。

---

## 三、配色方案

### 主色

| 角色               | 数值       | 说明                                        |
| ------------------ | ----------- | -------------------------------------------- |
| **Primary Red**    | `#C00000`   | Brand identity, title vertical bar, number badges, target bars |
| **Accent Blue**    | `#2E75B6`   | Scenario labels, category headers, bottom accent bars |
| **Light Blue**     | `#5B9BD5`   | Feature module cards, sub-item labels        |

### 功能色

| 角色               | 数值       | 用途                              |
| ------------------ | ----------- | ---------------------------------- |
| **Warm Gray BG**   | `#FDF3EB`   | Overview panel, open platform panel 背景 |
| **Warm Orange Border** | `#F8CBAD` | Panel borders, decorative dividers |
| **Light Gray BG**  | `#F2F2F2`   | 副标题 bar, metric card 背景 |
| **Card Gray BG**   | `#E7E6E6`   | Sub-module cards, capability base cards |
| **Card Border**    | `#D9D9D9`   | Card strokes                       |

### 文字颜色

| 角色               | 数值       | 用途                          |
| ------------------ | ----------- | ------------------------------ |
| **正文黑**     | `#000000`   | 标题, standard body text     |
| **White Text**     | `#FFFFFF`   | 深色块上的文字      |
| **Secondary Text** | `#666666`   | 副标题、注释         |
| **Light Secondary**| `#999999`   | 页码、来源标注 |
| **Data Emphasis**  | `#C00000`   | KPI values, key metrics        |

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", "SimHei", Arial, sans-serif`

### 字号层级

| Level    | 用途                  | Size    | Weight  |
| -------- | ---------------------- | ------- | ------- |
| H1       | 封面主标题       | 36-48px | 粗体    |
| H2       | 页面标题             | 32-36px | 粗体    |
| H3       | 模块标题/副标题  | 18-20px | 粗体    |
| P        | 正文内容           | 14-16px | 常规 |
| Caption  | 补充说明/脚注 | 12-14px | 常规 |
| Data     | KPI 数值/指标强调 | 24-36px | 粗体 |

> **Note**: Body font size is smaller than usual (14-16px vs standard 18-20px) to accommodate high information density per page.

---

## V. Core Design Principles

### 运营商高信息密度风格

This template emulates the visual language of telecom technical reports. The core characteristics are "**modular zoning + high information density + red-blue dual-color hierarchy**".

1. **Left Red Vertical Bar**: A red rectangle (10×40px) before titles serves as a visual anchor — the most essential title identifier throughout the template.
2. **Number Badges**: Red square badges (30×30px with white numbers) identify key initiatives/capability numbers (e.g., numbers 1-5 in "Five Key Initiatives").
3. **Dashed Zone Frames**: `stroke-dasharray="5 5"` dashed rectangles group content modules, creating a structured, modular visual effect — a common "zone frame" in telecom reports.
4. **Blue Label Bars**: `#2E75B6` blue-filled rectangles (full-width or fixed-width) serve as scenario/category headers carrying scenario names.
5. **Warm Gray Overview Panels**: Panels with `#FDF3EB` 背景 + `#F8CBAD` border carry overviews, summaries, and open platform entries.
6. **Metric Card Groups**: White cards with `#F2F2F2` borders, closely arranged to display KPI metrics; values highlighted in `#C00000` red.
7. **Light Blue Sub-modules**: `#5B9BD5` filled small rectangular cards displaying specific feature items (e.g., "AI One-Click Troubleshooting Assistant").
8. **Gray Capability Base Cards**: Cards with `#E7E6E6` / `#F2F2F2` 背景 for displaying foundational capabilities/platform components.

### 进阶特性

1. **Triangle Decorations**: The top area may use light semi-transparent triangles (`fill-opacity="0.3"`) as visual guides.
2. **Star/Icon Accents**: Simple polygon stars near key achievements enhance visual impact.
3. **Multi-level Nested Zones**: Outer dashed frame > inner label area > specific feature cards, forming a three-layer visual hierarchy.
4. **Compact Line Spacing**: Module spacing compressed to 10-20px to maximize information capacity.

---

## 六、页面结构

### 通用布局

| Area               | Position/Height  | 说明                                          |
| ------------------ | ---------------- | ---------------------------------------------------- |
| **标题区**     | y=20-80          | Red vertical bar + title text + optional subtitle overview bar |
| **Overview Bar**   | y=80-140         | Full-width `#F2F2F2` 背景 bar carrying the page's core summary |
| **内容区**   | y=140-670        | 主要内容区 (densely packed multi-module layout) |
| **页脚**         | y=680-720        | Red narrow bar with page number + chapter name + source citation |

### 导航条设计

- **标题 Vertical Bar**: Red rectangle `#C00000`, 10×40px, positioned left of the title text
- **标题 Text**: 10px from the vertical bar, 36px font size, `#C00000` or `#000000`
- **Overview Bar**: Full-width light gray rectangle (h=60px), centered 16px body text carrying the page overview/introduction

### 装饰元素

- **Number Badges**: 30×30px red squares + white numbers (centered)
- **Blue Labels**: Fixed-width blue rectangles + white text (e.g., "Fault Boundary Identification")
- **Dashed Zone Frames**: `stroke="#C00000"` or `stroke="#E7E6E6"`, `stroke-dasharray="5 5"`
- **Warm Gray Panels**: `fill="#FDF3EB"` + `stroke="#F8CBAD"` + `stroke-width="2"`
- **Light Blue Feature Cards**: `fill="#5B9BD5"` rectangles + white text

---

## 七、页面类型

### 1. 封面页 (01_cover.svg)

- **Background**: White `#FFFFFF`
- **Left Decoration**: Full-height red-blue dual-color vertical bar (red upper half + blue lower half), width 60px
- **标题 Area**: Centered large title `{{TITLE}}` (red), with subtitle `{{SUBTITLE}}` inside a light gray overview bar below
- **Middle Decoration**: Number badges (1-5) + blue scenario labels showcasing core capabilities/scenarios
- **Bottom 信息**: Speaker `{{AUTHOR}}` + date `{{DATE}}`
- **Bottom Decoration**: Warm gray narrow bar + blue full-width bottom bar

### 2. Chapter Page (02_chapter.svg)

- **Background**: White `#FFFFFF`
- **左右 Decoration**: Left red vertical bar + right blue vertical bar (echoing the cover dual-color scheme)
- **Center**: Red number badge (80×80px large) `{{CHAPTER_NUM}}` + watermark number (160px light gray)
- **标题**： Centered `{{CHAPTER_TITLE}}` (48px 粗体)
- **Decorative Line**: Red-blue dual lines (thick red line + thin blue line)
- **说明**: `{{CHAPTER_DESC}}` in gray text

### 3. 内容 Page (03_content.svg)

- **Top**: 4px red top bar + white title bar (80px height)
- **标题 Identifier**: Red vertical bar (8×40px) + 32px 粗体 title `{{PAGE_TITLE}}`
- **内容 Area**: Dashed frame (`stroke-dasharray="5 5"`) marking content area `{{CONTENT_AREA}}`
- **页脚**: Light gray bottom bar, left red vertical bar + chapter name `{{SECTION_NAME}}`, right red square page number `{{PAGE_NUM}}`
- **Source Citation**: 页脚居中 `{{SOURCE}}`
- **TOC**: Use canonical indexed placeholders such as `{{TOC_ITEM_1_TITLE}}`

### 4. Ending Page (04_ending.svg)

- **布局**： Mirrors the cover — left red-blue dual-color vertical bar, bottom blue bar
- **Central Panel**: Warm gray panel (`#FDF3EB` + `#F8CBAD` border) carrying the thank-you message
- **内容**: `{{THANK_YOU}}` (red 64px 粗体) + `{{ENDING_SUBTITLE}}` (blue 22px)
- **Contact 信息**: `{{CONTACT_INFO}}` + `{{COPYRIGHT}}`
- **Bottom Decoration**: Number badges + blue labels, echoing the cover

---

## VIII. 版式模式

| 模式 | 适用场景 |
| ------------------------------ | ------------------------------------------------- |
| **Architecture Overview**      | AI operations overview, system architecture panorama |
| **Metrics Dashboard**          | KPI display, performance reports, data dashboards |
| **Multi-Module Zoning**        | Capability lists, scenario matrices, domain displays |
| **Process/时间轴**           | 实施路线图、部署计划、演进路径 |
| **上下分栏**           | Objectives+results (top), scenarios+capabilities (bottom) |
| **Left-Right Split (3:7)**     | Left navigation labels + right content area       |
| **Card Matrix (2x3/3x3)**     | Capability modules, team assignments, project lists |
| **Table**                      | Metric comparisons, progress tracking             |

> **Recommended**: Telecom reports commonly use the "**Architecture Overview**" pattern — a single page presenting the complete architecture from objectives → results → scenarios → orchestration → foundational capabilities, unfolding top to bottom.

---

## IX. Common Components

### 标题 Vertical Bar Decoration

```xml
<!-- Red vertical bar + title -->
<rect x="30" y="20" width="10" height="40" fill="#C00000" />
<text x="50" y="55" font-family="Microsoft YaHei, sans-serif" font-size="36" font-weight="bold" fill="#C00000">Page 标题</text>
```

### Number Badge

```xml
<!-- Red square number badge -->
<rect x="80" y="560" width="30" height="30" fill="#C00000" />
<text x="95" y="582" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#FFFFFF" text-anchor="middle">1</text>
```

### Blue Scenario Label

```xml
<!-- Blue label bar -->
<rect x="120" y="310" width="220" height="40" fill="#2E75B6" />
<text x="230" y="336" font-family="Microsoft YaHei, sans-serif" font-size="16" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Fault Boundary Identification</text>
```

### Metric Card

```xml
<!-- White metric card (values highlighted in red) -->
<rect x="120" y="215" width="140" height="35" fill="#FFFFFF" stroke="#F2F2F2" stroke-width="2" />
<text x="190" y="239" font-family="Microsoft YaHei, sans-serif" font-size="14" font-weight="bold" fill="#000000" text-anchor="middle">Fault tickets reduced by<tspan fill="#C00000">30%</tspan></text>
```

### Dashed Zone Frame

```xml
<!-- Dashed content zone -->
<rect x="120" y="390" width="940" height="150" fill="none" stroke="#C00000" stroke-width="2" stroke-dasharray="5 5" />
```

### Warm Gray Overview Bar

```xml
<!-- Full-width warm gray overview/summary bar -->
<rect x="30" y="80" width="1220" height="60" fill="#F2F2F2" />
<text x="640" y="115" font-family="Microsoft YaHei, sans-serif" font-size="16" fill="#000000" text-anchor="middle">Overview text content...</text>
```

### Warm Gray Panel

```xml
<!-- Warm gray panel (open platform/summary area) -->
<rect x="1080" y="390" width="160" height="300" fill="#FDF3EB" stroke="#F8CBAD" stroke-width="2" />
```

### Light Blue Feature Card

```xml
<!-- Feature module card -->
<rect x="160" y="450" width="240" height="30" fill="#5B9BD5" />
<text x="280" y="471" font-family="Microsoft YaHei, sans-serif" font-size="14" fill="#FFFFFF" text-anchor="middle">AI One-Click Troubleshooting Assistant</text>
```

### Gray Capability Base Card

```xml
<!-- Foundational capability card -->
<rect x="120" y="630" width="80" height="40" fill="#F2F2F2" stroke="#D9D9D9" stroke-width="1" />
<text x="160" y="655" font-family="Microsoft YaHei, sans-serif" font-size="14" fill="#000000" text-anchor="middle">Core Network</text>
```

---

## X. Spacing Specification

| Element                        | 数值     |
| ------------------------------ | --------- |
| 页面左右边距        | 30-50px   |
| 页面上下边距        | 20-40px   |
| 标题 area height              | 60px      |
| Overview bar height            | 60px      |
| 标题与摘要条间距  | 0px       |
| Overview bar to content spacing | 10-20px  |
| Module spacing                 | 10-20px   |
| Card spacing                   | 10px      |
| Card inner padding             | 15-20px   |
| Badge to label spacing         | 5-10px    |
| 页脚 height                  | 40px      |

> **Compact Principle**: The telecom style pursues maximum information per page; spacing is generally 30-50% smaller than standard templates.

---

## 十一、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (**`<foreignObject>` is strictly prohibited**)
4. Use `fill-opacity` / `stroke-opacity` for transparency; `rgba()` is prohibited
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject` (`id` inside `<defs>` is allowed)
6. Prohibited: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Prohibited: `<symbol>+<use>`, `<iframe>`, `@font-face`
8. Prohibited: `<g opacity="...">` (分组透明度) — set opacity on each child element individually
9. Use `<polygon>` triangles instead of `<marker>` for arrows
10. Use only system fonts and inline styles

### PPT 兼容性规则

- Use overlay layers instead of image opacity
- Define gradients using `<linearGradient>` inside `<defs>`
- Use `rx`/`ry` attributes for rounded rectangles (post-processing converts to Path)

---

## 十二、占位符说明

The template uses `{{PLACEHOLDER}}` format placeholders:

| 占位符 | 说明 | 适用模板 |
| ------------------- | ------------------------ | ------------------- |
| `{{TITLE}}`         | 主标题               | Cover               |
| `{{SUBTITLE}}`      | 副标题/overview        | Cover               |
| `{{AUTHOR}}`        | Speaker/organization     | Cover               |
| `{{DATE}}`          | Date                     | Cover               |
| `{{CHAPTER_NUM}}`   | Chapter number           | Chapter page        |
| `{{CHAPTER_TITLE}}` | 章节标题            | Chapter page        |
| `{{CHAPTER_DESC}}`  | 章节说明      | Chapter page        |
| `{{PAGE_TITLE}}`    | 页面标题               | 内容 page        |
| `{{CONTENT_AREA}}`  | 内容区 identifier  | 内容 page        |
| `{{SECTION_NAME}}`  | 章节名称 (footer)    | 内容 page        |
| `{{SOURCE}}`        | Data source (footer)     | 内容 page        |
| `{{PAGE_NUM}}`      | 页码              | 内容/ending page |
| `{{THANK_YOU}}`     | Thank-you message        | Ending page         |
| `{{ENDING_SUBTITLE}}` | Slogan/tagline         | Ending page         |
| `{{CONTACT_INFO}}`  | Contact information      | Ending page         |
| `{{COPYRIGHT}}`     | Copyright                | Ending page         |

---

## 十三、使用说明

1. Copy this template directory to the project `templates/` directory
2. Review `reference_style.svg` to understand the core visual style
3. Select appropriate page templates based on content needs
4. Mark content to be replaced using placeholders
5. Generate final SVG through the Executor role
6. For high-information-density pages, refer to the multi-module zoning layout in `reference_style.svg`

---

## XIV. Design Highlights

- **Telecom DNA**: Derived from real telecom AI operations architecture reports, naturally suited for telecom/enterprise presentation styles
- **High 信息 Density**: A single page can accommodate a complete architecture view (objectives → results → scenarios → orchestration → foundational capabilities)
- **Red-Blue Dual-Color Hierarchy**: Red = core/emphasis/objectives, Blue = scenarios/modules/capabilities — clear visual hierarchy
- **Number Badge System**: Red square numbers throughout create a "N Key Initiatives" visual narrative
- **Three-Level Nested Zoning**: Dashed outer frame → category labels → feature cards for structured expression of complex architectures
- **Metric Card Groups**: Compactly arranged KPI metrics with red-highlighted values for instant readability
