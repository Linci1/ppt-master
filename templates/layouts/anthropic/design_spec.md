# Anthropic 风格模板 - 设计规格

> 适用于 AI/LLM 技术分享、开发者大会、技术培训与产品发布。

---

## 一、模板总览

| 属性 | 说明                                            |
| -------------- | ------------------------------------------------------ |
| **模板名称** | anthropic（Anthropic 风格模板） |
| **适用场景** | AI/LLM 技术分享、开发者大会、技术培训、产品发布 |
| **设计调性** | 科技前沿、专业现代、结论先行 |
| **主题模式** | 混合主题（深色封面/章节页 + 浅色内容页） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **安全边距** | 60px (左右), 50px (上下) |
| **内容区** | x: 60-1220, y: 100-670     |
| **标题区** | y: 50-100                     |
| **网格基线**  | 40px                          |

---

## 三、配色方案

### 主色

| 角色             | 数值       | 说明                            |
| ---------------- | ----------- | -------------------------------- |
| **Anthropic Orange** | `#D97757` | Brand identity, title emphasis, key data |
| **Deep Space Gray** | `#1A1A2E` | 封面背景, body text, chart base |
| **Tech Blue**    | `#4A90D9`   | Flowcharts, links, interactive elements |
| **Mint Green**   | `#10B981`   | Recommended options, positive indicators, success states |
| **Coral Red**    | `#EF4444`   | Risks, cautions, warnings        |

### 中性色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Cloud White** | `#F8FAFC`  | 卡片背景        |
| **Border Gray** | `#E2E8F0`  | 卡片边框, dividers |
| **Slate Gray** | `#64748B`   | Secondary text, chart labels |
| **Pure White** | `#FFFFFF`   | 页面背景        |

---

## 四、字体系统

### 字体栈

**字体栈**： `Arial, "Helvetica Neue", "Segoe UI", sans-serif`

### 字号层级

| Level    | 用途            | Size   | Weight  |
| -------- | ---------------- | ------ | ------- |
| H1       | 封面主标题 | 56px   | 粗体    |
| H2       | 页面标题       | 32-36px| 粗体    |
| H3       | 副标题/章节 | 24-28px| 半粗体|
| H4       | 卡片标题       | 20-22px| 粗体    |
| P        | 正文内容     | 16-18px| 常规 |
| Data     | 高亮数据 | 40-48px| 粗体    |
| Label    | Label text       | 14px   | 500     |
| Sub      | 图表标签/脚注 | 12-14px | 常规 |

---

## V. Core Design Principles

### 顶级咨询风格

1. **Conclusion First (Pyramid Principle)**: Each page title is the core takeaway
2. **Data Contextualization**: Comparisons, trends, benchmarks — never present data in isolation
3. **SCQA Framework**: Situation → Complication → Question → Answer
4. **MECE Principle**: Mutually Exclusive, Collectively Exhaustive
5. **Professional Whitespace**: 内容 ratio < 65%, let information "breathe"

---

## 六、页面结构

### 通用布局

| Area           | Position/Height | 说明                            |
| -------------- | --------------- | -------------------------------------- |
| **Top**        | y=0, h=6-8px    | Anthropic Orange decorative bar        |
| **Label**      | y=50-70         | 页面类型标签 (uppercase, orange)    |
| **标题区** | y=80-140        | 页面标题 (core takeaway)             |
| **内容区** | y=160-620     | 主要内容区                      |
| **页脚**     | y=680           | 页码 (centered)                 |

### 装饰元素

- **Top Orange Bar**: Anthropic Orange (`#D97757`), height 6px
- **Left Gradient Bar**: Orange gradient (`#D97757` → `#E8956F`)
- **Card Border**: Light gray (`#E2E8F0`)
- **Card Shadow**: Soft shadow effect
- **Grid Decoration Lines**: White low-opacity grid on dark covers

---

## 七、页面类型

### 1. 封面页 (01_cover.svg)

- 深色渐变背景 (`#1A1A2E` → `#16213E` → `#0F0F1A`)
- Grid decoration lines (white, 3% opacity)
- Orange and blue glow effects
- Neural network-style connection lines and nodes
- Centered main title (white) + subtitle
- Orange decorative short line
- Bottom date and source info

### 2. 目录页 (02_toc.svg)

- 白色背景
- Left orange gradient decorative bar (8px)
- Orange circular numbers + chapter titles
- Right-side complexity progression illustration

### 3. 章节页 (02_chapter.svg)

- 深色渐变背景
- Grid decoration
- Centered large chapter title
- Orange decorative line

### 4. 内容页 (03_content.svg)

- 白色背景
- Top orange decorative bar
- 页面类型标签 (orange uppercase)
- 标题 as core takeaway
- Three-column card layout (colored top borders)
- 带居中页码的页脚

### 5. 结束页 (04_ending.svg)

- 深色渐变背景
- Neural network decoration
- Centered thank-you message
- Contact information

---

## VIII. Common Components

### Card Style

```xml
<!-- Card with shadow -->
<g filter="url(#cardShadow)">
    <path fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"
          d="M72,180 H408 A12,12 0 0 1 420,192 V588 A12,12 0 0 1 408,600 H72 A12,12 0 0 1 60,588 V192 A12,12 0 0 1 72,180 Z"/>
</g>
<!-- Top colored decorative bar -->
<rect x="60" y="180" width="360" height="6" fill="#10B981"/>
```

### Circular Number

```xml
<circle cx="90" cy="200" r="24" fill="#D97757"/>
<text x="90" y="207" font-size="18" font-weight="bold" fill="#FFFFFF" text-anchor="middle">1</text>
```

### 图标背景圆

```xml
<circle cx="130" cy="250" r="35" fill="#10B981" fill-opacity="0.1"/>
```

---

## IX. Spacing Guidelines

| Element          | 数值  |
| ---------------- | ------ |
| Safe margin      | 60px   |
| Card gap         | 30-40px|
| 卡片圆角 | 8-12px |
| Card padding     | 30px   |
| Grid base        | 40px   |

---

## 十、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (**strictly no** `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`
7. Define gradients using `<defs>`

### PPT 兼容性规则

- No `<g opacity="...">` (分组透明度)
- Inline styles only

---

## 十一、占位符说明

| 占位符 | 说明 |
| ------------------ | ------------------ |
| `{{TITLE}}`        | 主标题         |
| `{{SUBTITLE}}`     | 副标题           |
| `{{COVER_QUOTE}}`  | 封面引语        |
| `{{SOURCE}}`       | 来源信息        |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | 页面标题 (core takeaway) |
| `{{PAGE_LABEL}}`   | 页面类型标签    |
| `{{CONTENT_AREA}}` | Flexible content anchor |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| 章节标题      |
| `{{PAGE_NUM}}`     | 页码        |
| `{{TOTAL_PAGES}}`  | Total pages        |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题 |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{CONTACT_INFO}}` | Primary contact info |

---

## 十二、使用说明

1. Copy the template to the project directory
2. Select the appropriate page template based on content needs
3. **标题 is the core takeaway** — ensure each page has a clear conclusion
4. Use three accent colors to differentiate content types (green = recommended, blue = process, orange = emphasis)
5. 由 Executor 角色生成最终 SVG
