# 智慧红橙商务模板 - 设计规格

> 适用于科技公司介绍、教育解决方案与活力型商务展示。

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | smart_red（智慧红橙商务模板） |
| **适用场景** | 科技公司介绍、教育解决方案、商务展示 |
| **设计调性** | 现代鲜明、专业有活力、几何感强 |
| **主题模式** | 混合主题（深色/彩色封面 + 浅色内容页） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **安全边距** | 60px (左右), 50px (上下) |
| **内容区** | x: 60-1220, y: 100-670      |
| **标题区** | y: 50-100                     |
| **Grid Baseline** | 40px                       |

---

## 三、配色方案

### 主色

| 角色             | 数值       | 说明                            |
| ---------------- | ----------- | -------------------------------- |
| **Primary Red**  | `#DE3545`   | Brand identity, title decoration, geometric cutouts |
| **Auxiliary Orange** | `#F0964D` | Geometric accents, gradient pairing |
| **Dark Background** | `#333333` | 封面背景, geometric cutouts, dark footer |

### 中性色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Light Gray Background** | `#F5F5F7` | 页面背景  |
| **Border Gray** | `#E0E0E0`  | Section dividers, card borders |
| **正文黑** | `#333333`   | Standard color for titles and body text |
| **说明 Gray** | `#666666` | 副标题, annotation text |
| **Pure White** | `#FFFFFF`   | 卡片背景        |

---

## 四、字体系统

### 字体栈

**字体栈**： `Arial, "Helvetica Neue", "Microsoft YaHei", sans-serif`

### 字号层级

| Level    | 用途              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | 封面主标题   | 60-80px | 粗体    |
| H2       | 页面标题         | 32-40px | 粗体    |
| H3       | 小节/卡片标题 | 24-28px | 粗体 |
| P        | 正文内容       | 18-20px | 常规 |
| Caption  | 补充文字 | 14-16px | 常规 |

---

## V. Core Design Principles

### 几何商务风格

1. **Geometric Cutouts**: Cover, table of contents, and transition pages use large triangular cutout designs.
2. **Red-Black Contrast**: Red primary color paired with dark gray blocks creates a professional and impactful visual.
3. **Card-Based 布局**: 内容 pages use white cards to hold content, with light gray 背景 for added depth.
4. **Whitespace**: Maintain adequate whitespace to avoid information overload.

### 进阶打磨特性（v2.0）

1. **Multi-Layer Geometric Overlay**: Main triangles paired with semi-transparent smaller triangles for visual depth.
2. **Shadow Effects**: Text shadows, card shadows, and circle shadows for a 3D feel.
3. **Dual-Line Decoration**: Decorative lines use dual-line styles (thick + thin) for enhanced design appeal.
4. **Subtle Glow**: Ultra-faint color glow behind content areas for a premium feel.
5. **Texture Accents**: Panels with very faint diagonal line textures for added tactile quality.
6. **Circle Shadows**: Table of contents numbering circles with shadows to suggest interactivity.

---

## 六、页面结构

### 通用布局

| Area       | Position/Height | 说明                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0-80          | Navigation bar / 标题 area            |
| **内容区** | y=100-660 | 主要内容区 (cards/diagrams)     |
| **页脚** | y=680           | 页码 and copyright information  |

### 装饰设计

- **Triangular Cutouts**: Core visual element of cover and back pages.
- **Sidebar**: Left-side red polygonal panel unique to the table of contents page.
- **Top Decoration Bar**: Red cutout decoration at the top of content pages.

---

## 七、页面类型

### 1. 封面页 (01_cover.svg)

- **Background**: Light gray 背景 `#F5F5F7`
- **Top-Left**: Red large triangular cutout (0,0 -> 350,0 -> 0,350)
- **Bottom-Left**: Dark gray triangular cutout (0,720 -> 300,720 -> 0,420)
- **Bottom-Right**: Red large triangular cutout (1280,720 -> 1280,320 -> 880,720)
- **标题 Area**: 主标题 `{{TITLE}}` and subtitle `{{SUBTITLE}}` displayed center-right
- **信息 Area**: Presenter `{{AUTHOR}}` and date `{{DATE}}` displayed at bottom

### 2. 目录页 (02_toc.svg)

- **Background**: Light gray 背景 `#F5F5F7`
- **Left Side**: Full-height red polygonal panel + large "内容s" text
- **Right Side**: 内容 list area
- **TOC Items**: Vertically arranged with circular number indices (01, 02...)

### 3. 章节页 (02_chapter.svg)

- **Decoration**: Red triangles echoing the cover (top-left / bottom-right)
- **Center**: Large chapter number `{{CHAPTER_NUM}}` + chapter title `{{CHAPTER_TITLE}}`
- **Style**: Clean and impactful, vivid colors

### 4. 内容页 (03_content.svg)

- **Top**: White navigation bar + top-right red cutout decoration + title dual-triangle decoration
- **Background**: Light gray 背景 `#F5F5F7`
- **标题**： 页面标题 `{{PAGE_TITLE}}` displayed left-aligned
- **内容**: `{{CONTENT_AREA}}` uses white card style (rounded corners + border)
- **页脚**: Includes copyright information and page number

### 5. 结束页 (04_ending.svg)

- **布局**： Triangular layout fully echoing the cover (top-left red, bottom-left gray, bottom-right red)
- **Center**: Thank-you message displayed
- **Bottom**: Whitespace reserved for contact information

---

## VIII. Common Components

### Card Style

```xml
<!-- White content card -->
<rect x="60" y="110" width="1160" height="540" rx="4" ry="4" fill="#FFFFFF" stroke="#E0E0E0" stroke-width="1" />
```

### TOC Circular Numbering

```xml
<circle cx="40" cy="40" r="30" fill="#FFFFFF" stroke="#DE3545" stroke-width="2" />
<text x="40" y="50" text-anchor="middle" font-family="Arial" font-size="28" font-weight="bold" fill="#DE3545">01</text>
```

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (**strictly no** `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`
7. Define gradients using `<defs>`

---

## 十、占位符规范

| 占位符 | 说明 |
| ------------------ | ------------------ |
| `{{TITLE}}`        | 主标题         |
| `{{SUBTITLE}}`     | 副标题           |
| `{{AUTHOR}}`       | Presenter/Author   |
| `{{DATE}}`         | Date               |
| `{{PAGE_TITLE}}`   | 页面标题         |
| `{{CONTENT_AREA}}` | 内容区 identifier |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{CHAPTER_TITLE}}`| 章节标题      |
| `{{PAGE_NUM}}`     | 页码        |
| `{{TOC_ITEM_1_TITLE}}` | 目录项标题 |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{ENDING_SUBTITLE}}` | 结束页副标题 |
| `{{CONTACT_INFO}}` | Primary contact info |
| `{{CLOSING_MESSAGE}}`| Closing message  |

---

## 十一、使用说明

1. Copy this directory to the project directory.
2. Select the appropriate page template based on content requirements.
3. Modify the text content in the SVG files or replace images.
4. Use the `ppt-master` tool to generate the PPTX file.
