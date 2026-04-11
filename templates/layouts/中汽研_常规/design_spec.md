# 中汽研常规模板 - 设计规格

> 适用于认证、检测与评测类展示。

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | 中汽研_常规（中汽研常规模板） |
| **适用场景** | 认证展示、检测汇报、评测场景 |
| **设计调性** | 专业权威、可信稳重、咨询风格 |
| **主题模式** | 浅色主题（白底 + 深蓝强调） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`               |
| **页面边距** | 左右 60px, Top 80px, Bottom 40px |
| **安全区**  | x: 60-1220, y: 80-680        |

---

## 三、配色方案

### 主色

| 角色           | 颜色值 | 说明                            |
| -------------- | ----------- | -------------------------------- |
| **Primary Deep Blue** | `#004098` | 标题 bar, navigation bar, chapter number blocks, decorative bars |
| **Background White** | `#FFFFFF` | Main 页面背景            |
| **Auxiliary Light Gray** | `#F5F5F5` | Secondary content 背景 blocks |
| **Border Gray** | `#E0E0E0` | 分隔线, borders               |
| **Accent Red** | `#CC0000`  | Key information highlight        |

### 文字颜色

| 角色           | 颜色值 | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Primary Text** | `#333333` | 正文文字、标题    |
| **White Text** | `#FFFFFF`  | 深色背景上的文字 |
| **Secondary Text** | `#666666` | Dimmed chapters, auxiliary 描述文字 |
| **Light Auxiliary** | `#999999` | Annotations, page numbers, hints |

### 功能色

| 用途      | 颜色值 | 说明    |
| ---------- | ----------- | -------------- |
| **正向色** | `#4CAF50` | Pass / Certified |
| **警示色** | `#CC0000` | Failed / Attention |

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", "SimHei", Arial, Calibri, sans-serif`

### 字号层级

| Level | 用途              | Size | Weight  |
| ----- | ------------------ | ---- | ------- |
| H1    | 封面主标题   | 48px | 粗体    |
| H2    | 页面标题       | 28px | 粗体    |
| H3    | 分节标题 / 副标题 | 24px | 粗体 |
| P     | 正文内容       | 18px | 常规 |
| High  | 强调数据    | 36px | 粗体    |
| Sub   | 辅助说明    | 14px | 常规 |

---

## 五、页面结构

### 常用布局

| Area       | Position/Height | 说明                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=4px      | Deep blue bar spanning full width      |
| **标题 Bar** | y=30, h=50px | Chapter number block + 标题 text + Top-right Logo |
| **内容** | y=100, h=560px | 主要内容区                     |
| **页脚** | y=680, h=40px   | 页码 (right-aligned), bottom decorative line |

### 导航设计

- **Top Decorative Line**: Deep blue (`#004098`), height 4px, spanning full width
- **Bottom Decorative Line**: Deep blue (`#004098`), height 4px, y=716
- **标题 Bar** (y=30):
  - Chapter number block: Deep blue square (50×50px), white number/text centered
  - 标题 text: 20px from number block, 28px font size, `#333333`
  - Top-right Logo: Fixed at x=1107, size 113×50px

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- Supports 背景 image (AI-generated / user-provided)
- Semi-transparent overlay for text readability
- Large centered Logo
- 主标题 + subtitle
- 机构名称 (Chinese & English)

### 2. 目录页 (02_toc.svg)

- Double vertical line `||` separator design
- Supports up to 5 chapters
- Left decorative vertical line
- Optional statistics display area on the right

### 3. 章节页 (02_chapter.svg)

- 深蓝渐变背景
- Large chapter number
- 章节标题 + 英文副标题

### 4. 内容页 (03_content.svg)

- 白色背景
- Standard navigation bar
- 可灵活编排的内容区
- Supports multiple layout patterns

### 5. 结束页 (04_ending.svg)

- Deep blue solid 背景
- 居中的 Logo
- Thank-you message
- Organization information

---

## 七、版式模式（推荐）

| 模式 | 适用场景 |
| -------------------- | ------------------------------ |
| **单列居中** | 封面、结论、关键观点 |
| **Left-Right Split (5:5)** | Comparison display          |
| **Left-Right Split (4:6)** | 图文混排ed layout     |
| **上下分栏** | Process description, standards list |
| **三列卡片** | Project listings             |
| **Matrix Grid**      | Category display               |
| **Table**            | Data comparison, specification lists |

---

## VIII. Spacing Guidelines

| Element        | 数值  |
| -------------- | ------ |
| Card gap       | 24px   |
| 内容块间距 | 32px |
| Card padding   | 24px   |
| 卡片圆角 | 8px |
| 图标与文字间距 | 12px |

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Text wrapping via `<tspan>` (no `<foreignObject>`)
4. Opacity via `fill-opacity` / `stroke-opacity`, no `rgba()`
5. Forbidden: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Forbidden: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Use `<polygon>` triangles for arrows instead of `<marker>`

### PPT 兼容性规则

- No `<g opacity="...">` (分组透明度) — set opacity on each child element individually
- Use overlay layers for image transparency
- Inline styles only — no external CSS or `@font-face`

---

## 十、占位符规范

Templates use `{{PLACEHOLDER}}` format. Common placeholders:

| 占位符 | 说明 |
| -------------------- | ------------------ |
| `{{TITLE}}`          | 主标题         |
| `{{SUBTITLE}}`       | 副标题           |
| `{{AUTHOR}}`         | Author / Organization (Chinese) |
| `{{AUTHOR_EN}}`      | 作者 / 机构（英文） |
| `{{PAGE_TITLE}}`     | 页面标题         |
| `{{CHAPTER_NUM}}`    | Chapter number     |
| `{{PAGE_NUM}}`       | 页码        |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题   |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`      | Thank-you message  |
| `{{CONTACT_INFO}}`   | Primary contact info |
| `{{LOGO_LARGE}}`     | Large Logo filename |
| `{{LOGO_HEADER}}`    | 页眉 Logo 文件名 |
| `{{COVER_BG_IMAGE}}` | 封面背景图片文件名 |

---

## 十一、使用说明（推荐）

1. **Template Deployment**: Copy the template to your project directory.
2. **Asset Replacement**: Replace `大型 logo.png` (592×238) and `右上角 logo.png` (113×50) in the `images` directory.
3. **内容 Generation**: Select appropriate page templates based on content needs, and replace content using `{{}}` placeholders.
4. **SVG Generation**: Generate final SVG files via automation scripts.
