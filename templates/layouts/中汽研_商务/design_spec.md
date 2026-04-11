# 中汽研商务模板 - 设计规格

> 适用于认证展示、高端商务汇报与技术交流。
> **v2.0 更新**：整体升级为现代科技商务风，加入渐变、柔和发光与几何装饰元素。

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | 中汽研_商务（中汽研商务模板） |
| **适用场景** | 认证展示、高端商务汇报、技术交流 |
| **设计调性** | 现代科技、权威专业、沉稳大气 |
| **主题模式** | 深蓝科技渐变主题（白色内容页） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`               |
| **页面边距** | 左右 60px, Top 90px, Bottom 50px |
| **安全区**  | x: 60-1220, y: 90-670        |

---

## 三、配色方案

### 核心色板

| 角色           | 颜色值 | 渐变（SVG defs）            | 说明                            |
| -------------- | ----------- | ------------------------------ | -------------------------------- |
| **Primary Deep Blue** | `#003366` | `#003366` -> `#001F4D`      | Brand primary tone               |
| **Tech Bright Blue**  | `#0050B3` | `#0050B3` -> `#007ACC`      | Highlight decoration, gradient bright end |
| **Auxiliary Cool Gray** | `#F0F2F5` | N/A                        | Background blocks, card base     |
| **Vibrant Red** | `#D32F2F` | N/A                            | Accent, emphasis, alerts         |
| **Pure White**  | `#FFFFFF`  | N/A                            | Text, inverted icons             |

### 文字颜色

| 角色           | 颜色值 | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Headings/Body** | `#1F2937` | Dark gray for body text on white 背景 |
| **Secondary Text** | `#6B7280` | 用于说明文字的浅灰色 |
| **Inverted Text** | `#FFFFFF` | 深色背景上的文字 |
| **Watermark Text** | `#E5E7EB` | Very light gray for 背景 text |

---

## 四、字体系统

### 字体栈

**主字体栈**：`"Microsoft YaHei", "PingFang SC", "Heiti SC", "Segoe UI", Arial, sans-serif`

### 字号层级（优化对比）

| Level | 用途              | Size | Weight  | Color      |
| ----- | ------------------ | ---- | ------- | ---------- |
| H1    | 封面主标题   | 56px | 粗体    | #FFFFFF    |
| H2    | 页面标题       | 32px | 粗体    | #003366    |
| H3    | 分节标题      | 24px | 粗体    | #333333    |
| P     | 正文内容       | 18px | 常规 | #4B5563    |
| Num   | 装饰性数字 | 80px+| 粗体    | Opacity 10%|

---

## 五、页面结构

### 通用导航条（y=0 到 90）

- **Top Color Bar**: Gradient blue bar, 6px height.
- **Logo Area**: Fixed at upper-right corner.
- **标题 Group**: Upper-left corner, includes chapter number (with colored block 背景) and page title.
- **Decorative Line**: Light gray thin line below the title for visual breathing room.

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)
- **Visual Focus**: Large whitespace or image on the left, dark tech-styled cutout on the right/bottom.
- **Decoration**: Dynamic geometric lines (Tech Lines), simulating light beam effects.
- **内容 布局**: 标题 left-aligned or centered floating card style for enhanced hierarchy.

### 2. 目录页 (02_toc.svg)
- **布局**： Card-style list. Each chapter as a horizontal card with simulated subtle shadow.
- **Numbers**: Extra-large semi-transparent numbers in the 背景 (01, 02...) for added design appeal.

### 3. 章节页 (02_chapter.svg)
- **Background**: Full-screen deep blue radial gradient for an immersive feel.
- **Elements**: Center-focused typography with radiating lines or ring decorations.

### 4. 内容页 (03_content.svg)
- **布局**： Clean white 背景, maximizing content display area.
- **Auxiliary**: Very faint Logo watermark in the lower-right corner.

### 5. 结束页 (04_ending.svg)
- **Background**: Echoes the cover's dark tone.
- **Elements**: Centered thank-you message with refined contact information layout.

---

## 七、版式模式（推荐）

### 1. Card List
- Wide cards arranged vertically, suitable for table of contents or key points.
- Use shadow simulation (e.g., semi-transparent black rectangles) for a floating effect.

### 2. Contrast 布局
- Left-right split: left dark / right light, or left image / right text, emphasizing contrast.

### 3. Radial 布局
- Core concept centered with surrounding explanations, suitable for chapter or summary pages.

---

## VIII. Spacing Guidelines

| 属性 | 值 | 说明              |
| -------------- | ----- | ------------------------ |
| **Base Unit**  | 8px   | 8px grid system          |
| **Module Gap** | 32px  | Comfortable reading gap  |
| **Card Gap**   | 16px  | Compact with cohesion    |

---

## 九、SVG 技术约束

### Mandatory Rules

1. **Gradient Support**: Use `<linearGradient>` and `<radialGradient>` defined within `<defs>`.
2. **Shadow Simulation**: PPT does not support SVG filter shadows. Use **semi-transparent black rectangles (`fill="#000000" fill-opacity="0.1"`)** with offset stacking to simulate card shadows.
3. **Opacity**: Strictly use `fill-opacity` / `stroke-opacity`.
4. **Forbidden**: No `clipPath`, `mask`.

---

## 十、占位符规范

| 占位符 | 说明 |
| ------------------ | --------------------- |
| `{{TITLE}}`        | Presentation main title |
| `{{SUBTITLE}}`     | 副标题              |
| `{{AUTHOR}}`       | Presenter / Department |
| `{{DATE}}`         | Date                  |
| `{{PAGE_TITLE}}`   | 内容 page title    |
| `{{CHAPTER_NUM}}`  | Chapter number (01, 02) |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题    |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`    | Thank-you message     |
| `{{CONTACT_INFO}}` | Contact information   |
| `{{LOGO_LARGE}}`   | Cover/back page large Logo |
| `{{LOGO_HEADER}}`  | Navigation bar small Logo |

---

## 十一、使用说明（推荐）

1. **Shadow Handling**: All card shadows are simulated via vector rectangles, ensuring good compatibility and lossless scaling.
2. **Gradients**: To modify gradient colors, adjust `stop-color` values in the `<defs>` section.
3. **Logo**: Recommend using transparent PNG. Use inverted (white) Logo for dark 背景 pages.
