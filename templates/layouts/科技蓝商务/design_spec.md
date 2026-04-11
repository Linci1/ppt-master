# 科技蓝商务模板 - 设计规格

> 适用于企业汇报、产品发布与解决方案提案。

---

## 一、模板总览

| Property         | 说明                                                      |
| ---------------- | ---------------------------------------------------------------- |
| **模板名称** | 科技蓝商务（科技蓝商务模板） |
| **适用场景** | 企业汇报、产品发布、解决方案提案 |
| **设计调性** | 科技商务、专业干净、表达清晰 |
| **主题模式** | 混合主题（深蓝/科技蓝封面 + 浅色内容页） |

---

## 二、画布规格

| 属性 | 值                         |
| ------------------ | ----------------------------- |
| **格式**         | 标准 16:9                 |
| **尺寸**     | 1280 × 720 px                |
| **viewBox**        | `0 0 1280 720`               |
| **安全边距**   | 60px (左右), 50px (上下) |
| **内容区**   | x: 60-1220, y: 140-640       |
| **标题区**     | y: 40-100                    |
| **Grid Baseline**  | 40px                         |

---

## 三、配色方案

### 主色

| 角色               | 数值       | 说明                                    |
| ------------------ | ----------- | ---------------------------------------- |
| **Primary Blue**   | `#0078D7`   | Brand identity, title accents, key elements |
| **Dark Blue**      | `#002E5D`   | 深色背景, footer, important nodes |
| **Accent Cyan**    | `#4CA1E7`   | Gradient pairing, secondary accents      |
| **Alert Red**      | `#E60012`   | Key emphasis, warning information        |

### 中性色

| 角色               | 数值       | 用途                          |
| ------------------ | ----------- | ------------------------------ |
| **Background White**| `#FFFFFF`  | Main 页面背景           |
| **Light Gray BG**  | `#F5F5F7`   | Base color for each page       |
| **Border Gray**    | `#A0C4E3`   | Dashed borders, module dividers |
| **正文文字 Black**| `#333333`   | Standard color for titles and body text |
| **Caption Gray**   | `#666666`   | 副标题, page numbers, annotations |

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "PingFang SC", sans-serif`

### 字号层级

| Level    | 用途              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | 封面主标题   | 64px    | 粗体    |
| H2       | 页面标题         | 36-40px | 粗体    |
| H3       | 章节/卡片标题 | 24-28px | 粗体    |
| P        | 正文内容       | 20-24px | 常规 |
| Caption  | 补充文字 | 14-16px | 常规 |

---

## V. Core Design Principles

### 科技商务风格

1. **Wave Curves**: Multi-layered wave curves at the bottom of cover and transition pages add dynamism and depth.
2. **Dashed Containers**: 内容区s use dashed borders (`stroke-dasharray`) to convey a data-driven, rigorous aesthetic.
3. **Blue-White Simplicity**: Generous white space paired with tech blue creates a professional, crisp visual feel.
4. **Hexagonal 模式**: Cover and chapter pages use hexagonal patterns to evoke a sense of technology and innovation.

### 进阶视觉特性

1. **Gradient Application**: Blue-to-dark-blue linear gradients for 背景 and important graphics.
2. **Opacity Layering**: Waves use varying opacity levels to create a breathing effect.
3. **Rounded Corners**: 内容 containers use `rx="10"` rounded corners to soften the tech coldness and add warmth.
4. **Decorative Triangles**: Small triangle prefixes before titles guide the reader's eye.

---

## 六、页面结构

### 通用布局

| Area         | Position/Height | 说明                            |
| ------------ | --------------- | -------------------------------------- |
| **Top**      | y=0-120         | 标题 area, logo, and decorative lines |
| **内容**  | y=140-640       | 主要内容区 (dashed containers)  |
| **页脚**   | y=680-720       | 页码 and copyright info         |

### 装饰设计

- **Bottom Waves**: Core visual element of cover and ending pages.
- **Top Accent Bar**: Blue color block as title prefix in the upper-left corner.
- **Dashed Frames**: Standard containers for structured content layout.

---

## 七、页面类型

### 1. 封面页 (01_cover.svg)

- **布局**： Asymmetric left-right or overlay layout.
- **Background**: Large blue gradient on the left/top; image container on the right.
- **Decoration**: Dual-layer wave curves at the bottom for dynamism.
- **标题**： Left-aligned, large white text with subtitle 背景 accent.
- **Image**: Full-bleed right-side crop showcasing medical/tech scenes.

### 2. 目录页 (02_toc.svg)

- **布局**： Left-right split.
- **Left Side**: Dark blue/tech blue sidebar with large "内容s" text.
- **Right Side**: List-style entries with bullet points and line guides.
- **Decoration**: Clean line dividers maintaining visual breathing room.

### 3. 章节页 (02_chapter.svg)

- **Background**: Full-screen dark blue gradient (`#0078D7` -> `#002E5D`).
- **Center**: Center-aligned large chapter number + bold title.
- **Decoration**: Minimalist geometric rings or line accents focusing on the theme.

### 4. 内容页 (03_content.svg)

- **Top**: Minimalist title bar with blue rectangle accent in the upper-left.
- **Background**: Pure white.
- **内容**: Default includes a rounded dashed container (`stroke-dasharray="8,8"`).
- **页脚**: Small gray text for page number and confidentiality label.

### 5. 结束页 (04_ending.svg)

- **Background**: Dark blue gradient echoing the chapter page.
- **Center**: "Thank You" message and Q&A.
- **Decoration**: Bottom wave curves for visual bookending.

---

## VIII. Common Components

### Dashed 内容 Container

```xml
<!-- Rounded dashed content frame -->
<rect x="60" y="140" width="1160" height="500" fill="none" stroke="#A0C4E3" stroke-width="2" stroke-dasharray="8,8" rx="10" />
```

### 标题 Prefix Decoration

```xml
<!-- Blue rectangle decoration -->
<rect x="40" y="40" width="10" height="40" fill="#0078D7" />
```

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (**`<foreignObject>` is strictly prohibited**)
4. Use `fill-opacity` / `stroke-opacity` for transparency
5. Prohibited: `clipPath` (avoid unless needed for image cropping), `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`
7. Define gradients in `<defs>`

---

## 十、占位符规范

| 占位符 | 说明 |
| ----------------------------- | -------------------------- |
| `{{TITLE}}`                   | 主标题                 |
| `{{SUBTITLE}}`                | 副标题                   |
| `{{AUTHOR}}`                  | Speaker/Author             |
| `{{DATE}}`                    | Date                       |
| `{{PAGE_TITLE}}`              | 页面标题                 |
| `{{CONTENT_AREA}}`            | 内容区 prompt text   |
| `{{CHAPTER_NUM}}`             | Chapter number (01)        |
| `{{CHAPTER_TITLE}}`           | 章节标题              |
| `{{CHAPTER_DESC}}`            | 章节说明        |
| `{{PAGE_NUM}}`                | 页码                |
| `{{TOC_ITEM_1_TITLE}}`        | TOC item 1 title           |
| `{{THANK_YOU}}`               | Thank-you message          |
| `{{ENDING_SUBTITLE}}`         | 结束页副标题            |
| `{{CLOSING_MESSAGE}}`         | Closing message            |
| `{{CONTACT_INFO}}`            | Primary contact info       |

---

## 十一、使用说明

1. This template is a universal tech blue business style, suitable for various corporate business scenarios.
2. 内容 pages include dashed frames by default; these can be removed or resized based on content volume.
3. Wave elements and hexagonal patterns are decorative SVG paths; modifications should maintain the original style.
4. The color scheme is primarily blue-based and can be fine-tuned to match corporate brand colors.
