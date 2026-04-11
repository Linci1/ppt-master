# 中国电建现代模板 - 设计规格

> 适用于重大工程、国际业务展示与科技创新发布。
> **v2.0 特性**：融合现代工程美学与国际化视角，强调结构感、通透感与数字化表达。

---

## 一、模板总览

| 属性 | 说明                                                      |
| -------------- | ---------------------------------------------------------------- |
| **模板名称** | 中国电建_现代（中国电建现代模板） |
| **适用场景** | 重大工程汇报、国际业务展示、科技创新发布 |
| **设计调性** | 宏大叙事、现代精工、数字科技、国际视野 |
| **主题模式** | 深蓝科技渐变主题（精密网格纹理） |

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

### 主色（升级版）

| 角色           | 颜色值 | 渐变（SVG defs）            | 说明                              |
| -------------- | ----------- | ------------------------------ | ---------------------------------- |
| **POWERCHINA Blue** | `#00418D` | `#00418D` -> `#072C61`       | Brand core color for main 背景, title bars |
| **Tech Blue**  | `#0066CC`  | `#0066CC` -> `#0088FF`         | Highlight color for charts, accent borders |
| **Deep Sea Blue** | `#001F45` | N/A                           | Page base color for a deep, immersive feel |
| **Engineering White** | `#FFFFFF` | N/A                        | 标题 text, inverted icons         |

### 辅助色（国家力量感）

| 角色           | 颜色值 | 用途                              |
| -------------- | ----------- | ---------------------------------- |
| **China Red**  | `#C41E3A`  | Key data emphasis, progress bar indicators |
| **Architectural Gray** | `#E2E8F0` | Grid lines, secondary text      |
| **Glorious Gold** | `#FFD700` | Honors, milestone highlights (Opacity 20%) |

---

## 四、字体系统

### 字体栈

**主字体栈**：`"Microsoft YaHei", "PingFang SC", "Heiti SC", "Segoe UI", Arial, sans-serif`

### 字号层级（增强对比）

| Level | 用途              | Size  | Weight  | Color      |
| ----- | ------------------ | ----- | ------- | ---------- |
| H1    | 封面主标题   | 60px  | 粗体    | #FFFFFF    |
| H2    | 页面标题       | 36px  | 粗体    | #00418D    |
| H3    | 分节标题      | 24px  | 粗体    | #1A202C    |
| P     | 正文内容       | 18px  | 常规 | #4A5568    |
| Num   | Giant decorative numbers | 120px | 粗体 | Opacity 5% |

---

## 五、页面结构

### 通用导航条（y=0 到 100）

- **Top Blue Bar**: 8px height, deep blue gradient.
- **Logo Area**: Fixed at upper-right corner with a white backing plate.
- **标题 Group**: Upper-left corner using **"Tag Style"** design, simulating engineering drawing labels.

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)
- **Visual Focus**: **"Foundation"** concept. Heavy deep blue supporting the bottom, transparent top.
- **Background**: Overlaid with precision **"Geo Grid"** (latitude-longitude grid), symbolizing global presence.
- **布局**： Center-symmetric layout, projecting state-owned enterprise gravitas.

### 2. 目录页 (02_toc.svg)
- **布局**： **"Milestones"** style. Horizontal timeline or connected cards, representing project progression.
- **Elements**: Connection lines and node dots, simulating circuits or pipeline networks.

### 3. 章节页 (02_chapter.svg)
- **Background**: Deep blue tech gradient; large whitespace on the right for perspective grid.
- **Numbers**: Giant outlined numbers (Stroke Only) — not just chapter numbers, but part of the architectural structure.

### 4. 内容页 (03_content.svg)
- **布局**： **"Console"** style. Orderly top navigation bar, maximized content area.
- **Details**: **"Corner Marks"** added at all four corners for a precision engineering feel.

### 5. 结束页 (04_ending.svg)
- **Background**: Echoes the cover's "Foundation" structure.
- **Elements**: Reinforces "win-win cooperation" concept with QR code / contact information displayed in zones.

---

## 七、版式模式（推荐）

### 1. Tech Cards
- Cards with subtle borders and a glowing effect.
- Ideal for showcasing key technical indicators or innovation achievements.

### 2. Dashboard
- Combined layout of charts and key data.
- Uses Tech Blue as the primary chart color.

### 3. Blueprint
- Leverages the Geo Grid 背景 to explain complex structures through lines and annotations.

---

## VIII. Spacing Guidelines

| 属性 | 值 | 说明              |
| -------------- | ----- | ------------------------ |
| **Base Unit**  | 4px   | Precision design uses a 4px grid |
| **Module Gap** | 40px  | Generous spacing for breathing room |
| **Card Gap**   | 20px  | Compact yet clear spacing |
| **Inner Padding** | 32px | Distance between content and border |

---

## 九、SVG 技术约束

### Mandatory Rules

1. **Gradients**: Use `<linearGradient>` to create metallic or light/shadow effects.
2. **Grid**: Use `<pattern>` to define precision grid 背景 with opacity controlled at 0.05-0.1.
3. **Opacity**: Strictly use `fill-opacity` / `stroke-opacity`.
4. **Forbidden**: No `clipPath`, `mask`.

### Forbidden Elements (Blacklist)

- `clipPath`, `mask` (clipping/masking)
- `<style>`, `class` (stylesheets; `id` within `<defs>` is allowed)
- `foreignObject` (foreign objects)
- `textPath` (text on path)
- `animate`, `animateTransform`, `set` (animations)

- `rgba()` color format (must use hex + opacity)
- `<g opacity="...">` (分组透明度 — set individually on each element)

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
| `{{CONTENT_AREA}}` | 内容区 identifier |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题    |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`    | Thank-you message     |
| `{{CONTACT_INFO}}` | Contact information   |

---

## 十一、使用说明（推荐）

1. **Logo**: Recommend using white PNG Logo to suit dark 背景.
2. **Background Images**: 封面背景 grid is embedded in SVG; no external images needed.
3. **Fonts**: Prefer sans-serif fonts; Roboto or Arial recommended for English text.
