# 中汽研现代模板 - 设计规格

> 适用于前沿科技展示、高端发布与未来感内容表达。
> **v3.0 Update**: Introduces a "Future Tech" design language with deep blue + neon cyan palette, emphasizing spatial depth and flowing light effects.

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | 中汽研_现代（中汽研现代模板） |
| **适用场景** | 前沿科技展示、高端发布、未来感内容表达 |
| **设计调性** | 未来科技、前卫深邃、精致高级 |
| **主题模式** | 沉浸式深色封面/过渡页 + 浅灰内容页 |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`               |
| **页面边距** | 左右 80px, Top 100px, Bottom 60px |
| **安全区**  | x: 80-1200, y: 100-660       |

---

## 三、配色方案

### 核心色板 (Future Tech Palette)

| 角色           | 颜色值 | 渐变（SVG defs）            | 说明                            |
| -------------- | ----------- | ------------------------------ | -------------------------------- |
| **Deep Night Sky** | `#001529` | `#001529` -> `#002B52`        | Cover/transition page main 背景 |
| **Tech Blue**  | `#1890FF`  | `#1890FF` -> `#096DD9`         | Primary visual accent            |
| **Neon Cyan**  | `#00E5FF`  | `#00E5FF` -> `#00B5D8`         | Ultra-bright accent for highlights/data |
| **Polar Gray** | `#F7F9FC`  | N/A                            | 内容 页面背景 (not pure white, easier on eyes) |
| **Dark Night** | `#1F2937`  | N/A                            | Body text                        |

### 文字颜色

| 角色           | 颜色值 | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Heading (Dark BG)** | `#FFFFFF` | 主标题 on dark 背景 |
| **Heading (Light BG)** | `#001529` | 主标题 on light 背景 |
| **正文文字**  | `#374151`  | 内容 page body text  |
| **Secondary Text** | `#6B7280` | Auxiliary 描述文字  |
| **Decorative Text** | `#E5E7EB` | Very light watermark text |

---

## 四、字体系统

### 字体栈

**主字体栈**：`"Roboto", "Helvetica Neue", "Microsoft YaHei", "PingFang SC", sans-serif`
*English and numbers are recommended to use Roboto or Arial for a tech geometric feel.*

### 字号层级

| Level | 用途              | Size  | Weight  | Color      |
| ----- | ------------------ | ----- | ------- | ---------- |
| H1    | 封面主标题   | 64px  | 粗体    | #FFFFFF    |
| H2    | 页面标题       | 36px  | 粗体    | #001529    |
| H3    | 分节标题      | 24px  | 粗体    | #1890FF    |
| P     | 正文内容       | 18px  | 常规 | #374151    |
| Deco  | Decorative large numbers | 120px | 粗体 | Opacity 5% |

---

## 五、页面结构 (Asymmetric Tech 布局)

### 通用导航条（y=0 到 100）

- **Asymmetric Design**: 标题 left-aligned with a geometric decorative bar on the left.
- **Logo**: Floating in the upper-right corner with a subtle glow effect.
- **Decoration**: Top area retains only a splash of bright color line on the right side, breaking visual balance.

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)
- **Visual Focus**: **Deep spatial depth**. Background uses a deep blue radial gradient.
- **Hero Element**: Right side features abstract **"Luminous Flow"** or **"Digital Matrix"** graphics.
- **标题**： Bottom-left aligned, emphasizing bold typography with a neon-colored underline.

### 2. 目录页 (02_toc.svg)
- **布局**： **Split Screen (left dark, right light)**.
- **Left Side**: Dark area containing "CONTENTS" and Logo.
- **Right Side**: Light area with TOC items. Replaces cards with **"时间轴"** or **"Floating List"** style.
- **Numbers**: Highlighted in neon cyan (`#00E5FF`).

### 3. 章节页 (02_chapter.svg)
- **Background**: 深色背景.
- **Special Effect**: Large outlined numbers in the 背景 (Stroke Text).
- **Dynamism**: Added tilted decorative lines to simulate a sense of speed.

### 4. 内容页 (03_content.svg)
- **Background**: Very light gray `#F7F9FC`.
- **页眉**: Floating title bar for enhanced hierarchy.
- **Watermark**: Tech-styled geometric watermark in the lower-right corner.

### 5. 结束页 (04_ending.svg)
- **Background**: Echoes the cover.
- **Center**: Minimalist "Thank You" with surrounding halo ring decoration.

---

## 七、版式模式（推荐）

### 1. Floating 时间轴
- Uses right-side space for time or process display.
- Nodes feature a neon glowing effect.

### 2. HUD Display
- Simulates a heads-up display style using thin wireframes and highlighted numbers for key KPIs.

### 3. Asymmetric Contrast
- Leverages the page's asymmetric structure to create dynamic image-text layouts.

---

## VIII. Spacing Guidelines

| 属性 | 值 | 说明              |
| -------------- | ----- | ------------------------ |
| **Base Unit**  | 8px   | Tech designs typically use an 8px grid |
| **Module Gap** | 48px  | Extra spacious for a modern feel |
| **行高** | 1.6  | Increased line height for readability |

---

## 九、SVG 技术约束

### Mandatory Rules

1. **Blend Modes**: Avoid `mix-blend-mode` wherever possible; use `opacity` as a substitute.
2. **Gradients**: Leverage angled `linearGradient` (e.g., `x1="0%" y1="0%" x2="100%" y2="50%"`) to create light and shadow effects.
3. **Strokes**: Use thin `stroke-width="1"` with low transparency `stroke-opacity="0.2"` to simulate glass edges.

---

## 十、占位符规范

| 占位符 | 说明 |
| ------------------ | --------------------- |
| `{{TITLE}}`        | Presentation main title |
| `{{SUBTITLE}}`     | 副标题              |
| `{{AUTHOR}}`       | Presenting organization |
| `{{PRESENTER}}`    | Presenter             |
| `{{DATE}}`         | Date                  |
| `{{CHAPTER_NUM}}`  | Chapter number (01, 02) |
| `{{PAGE_TITLE}}`   | 内容 page title    |
| `{{STAT_1}}`       | Statistical data 1    |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题    |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`    | Thank-you message     |
| `{{CONTACT_INFO}}` | Contact information   |

---

## 十一、使用说明（推荐）

1. **Light & Shadow Effects**: All light and shadow effects are achieved via SVG gradients, with no dependency on external images.
2. **Fonts**: For optimal tech aesthetics, numbers are recommended to use **Roboto** or **DIN** fonts.
3. **Backgrounds**: 深色背景 look excellent on projectors, but ensure the ambient lighting is as dim as possible.
