# 中国电建常规模板 - 设计规格

> 适用于工程建设、电力能源与国央企汇报。

---

## 一、模板总览

| 属性 | 说明                                                      |
| -------------- | ---------------------------------------------------------------- |
| **模板名称** | 中国电建_常规（中国电建常规模板） |
| **适用场景** | 工程建设、电力能源、国央企汇报 |
| **设计调性** | 专业稳重、国际化、国企工程风格 |
| **主题模式** | 浅色主题（白底 + 电建蓝强调） |

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

### 主色 (POWERCHINA Brand Colors)

| 角色           | 颜色值 | 说明                              |
| -------------- | ----------- | ---------------------------------- |
| **POWERCHINA Blue** | `#00418D` | Primary color for title bars, accent blocks, decorative bars |
| **Deep Blue**  | `#002B5C`  | Chapter 页面背景, gradient dark end |
| **Vibrant Blue** | `#0066CC` | Secondary accent, chart colors     |
| **Sky Blue**   | `#4A90D9`  | Decorative accents, tertiary emphasis |
| **Background White** | `#FFFFFF` | Main 页面背景              |
| **Auxiliary Light Gray** | `#F4F6F8` | Secondary content 背景 blocks |

### 辅助色 (China Red Accents)

| 角色           | 颜色值 | 说明                              |
| -------------- | ----------- | ---------------------------------- |
| **China Red**  | `#C41E3A`  | Key data emphasis, decorative accents |
| **Gold**       | `#C9A227`  | Honors, achievements display       |

### 文字颜色

| 角色           | 颜色值 | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Primary Text** | `#1A1A1A` | 正文文字、标题    |
| **White Text** | `#FFFFFF`  | 深色背景上的文字 |
| **Secondary Text** | `#4A5568` | Dimmed chapters, auxiliary 描述文字 |
| **Light Auxiliary** | `#718096` | Annotations, page numbers, hints |

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", "SimHei", Arial, sans-serif`

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
| **Top**    | y=0, h=6px      | POWERCHINA blue gradient bar spanning full width |
| **标题 Bar** | y=30, h=50px | Chapter number block + 标题 text + Top-right Logo |
| **内容** | y=100, h=560px | 主要内容区                     |
| **页脚** | y=680, h=40px   | 页码, company name, bottom decorative line |

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- 深蓝渐变背景 + engineering-style diagonal line texture
- Left-side brand blue decorative bar
- 主标题 + subtitle (white)
- Company English name POWERCHINA
- Bottom red decorative bar

### 2. 目录页 (02_toc.svg)

- 白色背景 + left-side blue decorative area
- Supports up to 5 chapters
- Numbered items + vertical line separator design
- Right side can display corporate data

### 3. 章节页 (02_chapter.svg)

- 深蓝渐变背景
- Large chapter number
- 章节标题 + 英文副标题
- Geometric grid decoration

### 4. 内容页 (03_content.svg)

- 白色背景
- Standard navigation bar
- 可灵活编排的内容区
- Supports multiple layout patterns

### 5. 结束页 (04_ending.svg)

- 深蓝渐变背景
- 企业 Logo 区域
- Thank-you message (Chinese & English)
- Corporate information

---

## 七、版式模式（推荐）

### 1. Split Column
- Classic image-text mixed layout: left text / right image, or left image / right text.
- Recommended split ratio: 1:1 or 2:3.

### 2. Card Grid
- 3-column or 4-column card layout for showcasing project cases or qualifications.
- 卡片背景 recommended: auxiliary light gray `#F4F6F8`.

### 3. Process Flow
- Horizontal timeline or flowchart for displaying project progress.
- POWERCHINA blue as the main axis color, China Red for key milestone markers.

---

## VIII. Spacing Guidelines

| 属性 | 值 | 说明              |
| -------------- | ----- | ------------------------ |
| **Base Unit**  | 8px   | All spacing should be multiples of 8px |
| **Module Gap** | 32px  | Standard gap between major modules |
| **Card Gap**   | 24px  | Gap between cards        |
| **Inner Padding** | 24px | Padding inside cards    |
| **行高** | 1.5  | Standard body line height |

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox fixed at `0 0 1280 720`
2. Background must include a full-screen `<rect>`
3. Text wrapping via `<tspan>`
4. Opacity must use `fill-opacity` / `stroke-opacity`
5. Arrows must use `<polygon>`, no `marker`

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
| -------------------- | ------------------ |
| `{{TITLE}}`          | 主标题         |
| `{{SUBTITLE}}`       | 副标题           |
| `{{AUTHOR}}`         | Presenting organization |
| `{{PRESENTER}}`      | Presenter          |
| `{{CHAPTER_NUM}}`    | Chapter number     |
| `{{PAGE_NUM}}`       | 页码        |
| `{{DATE}}`           | Date               |
| `{{CHAPTER_TITLE}}`  | 章节标题      |
| `{{PAGE_TITLE}}`     | 页面标题         |
| `{{CONTENT_AREA}}`   | 内容区 identifier |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题   |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`      | Thank-you message  |
| `{{CONTACT_INFO}}`   | Contact information |

---

## 十一、使用说明（推荐）

1. **Logo Adaptation**: Cover and ending pages use inverted (white) Logo; content page upper-right uses color or inverted Logo.
2. **Image Assets**: Ensure the `images/` folder under the template directory contains necessary Logo files.
3. **Fonts**: Recommend installing "Microsoft YaHei" for optimal display.
