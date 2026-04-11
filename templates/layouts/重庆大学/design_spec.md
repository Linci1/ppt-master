# 重庆大学模板 - 设计规格

> 适用于学术答辩、研究展示与校园学术交流。

---

## 一、模板总览

| 属性 | 说明                                                          |
| ------------------ | -------------------------------------------------------------------- |
| **模板名称** | 重庆大学（重庆大学模板） |
| **适用场景** | 学术答辩、研究展示、校园学术交流 |
| **设计调性** | 学术沉稳、山城气质、现代简洁 |
| **设计灵感** | 山城层叠地貌 + 历史校园建筑的厚重感 + 现代学术专业气质 |

### 设计特征

1. **层叠几何**：通过斜切色块模拟山城台地地貌，打破传统矩形排布。
2. **非对称美学**：通过偏左的视觉重心引导阅读焦点。
3. **渐变色带**：由深到浅的变化象征从厚重历史走向明亮未来。
4. **波纹图案**：抽象化表达长江 / 嘉陵江水纹意象。

---

## 二、画布规格

| 属性 | 值                         |
| ------------------ | ----------------------------- |
| **格式**         | 标准 16:9                 |
| **尺寸**     | 1280 × 720 px                |
| **viewBox**        | `0 0 1280 720`               |
| **页面边距**   | Left/right 60px, 上下 40px |
| **内容安全区** | x: 60-1220, y: 100-660    |

---

## 三、配色方案

### 主色（从 Logo 提取）

| 角色               | 数值       | 说明                                        |
| ------------------ | ----------- | -------------------------------------------- |
| **CQU Blue**       | `#006BB7`   | Emblem primary color; header, titles, main elements |
| **Deep Blue**      | `#004A82`   | Chapter 页面背景, emphasis areas      |
| **Sky Blue**       | `#3A9BD9`   | Accent color, gradient endpoint              |
| **Cloud Blue**     | `#E3F2FD`   | Light 背景, card base color            |
| **Dawn Gold**      | `#D4A84B`   | Decorative accents, highlights (symbolizing brightness) |
| **Background White**| `#FAFCFF`  | Subtly blue-tinted pure white                |

### 文字颜色

| 角色               | 数值       | 用途                    |
| ------------------ | ----------- | ------------------------ |
| **Dark Ink Text**  | `#1A2E44`   | 主标题, heading text |
| **Primary Text**   | `#333D4A`   | 正文内容             |
| **Secondary Text** | `#6B7B8C`   | 图注、标注    |
| **White Text**     | `#FFFFFF`   | 深色背景上的文字 |

### 渐变方案

```
Primary gradient: #004A82 → #006BB7 → #3A9BD9 (deep → light, used for 背景 diagonal cuts)
Gold gradient: #C49A3D → #D4A84B → #E8C675 (decorative use)
```

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", "PingFang SC", Arial, sans-serif`

### 字号层级

| Level | 用途              | Size | Weight  | 说明              |
| ----- | ------------------ | ---- | ------- | ------------------ |
| H1    | 封面主标题   | 48px | 粗体    | Grand and dignified |
| H2    | 页面标题         | 26px | 粗体    |                    |
| H3    | 章节标题      | 44px | 粗体    |                    |
| H4    | 卡片标题         | 22px | 粗体    |                    |
| P     | 正文内容       | 17px | 常规 |                    |
| High  | 强调数据    | 32px | 粗体    |                    |
| Sub   | 说明/来源      | 13px | 常规 |                    |
| XS    | 页码/版权 | 11px | 常规 |                 |

---

## V. Core Visual Elements

### 1. Diagonal Color Blocks (Mountain City Layers)

The template's signature design uses diagonally divided color blocks to simulate the layered terrain of the Mountain City:

```
Cover: Large deep-blue diagonal block in the lower-left corner (approx. 40% of area)
Chapter page: Full-screen deep blue + light diagonal accent in the upper-right
内容 page: Small diagonal accent strip at the top
```

### 2. Wave 模式 (Two Rivers Imagery)

Abstract curves symbolizing the Yangtze and Jialing Rivers:

```xml
<path d="M0,700 Q320,680 640,700 T1280,680 L1280,720 L0,720 Z"
      fill="#006BB7" fill-opacity="0.08"/>
```

### 3. Light Dot Decorations (City Lights)

Small circle elements representing the nighttime lights of the Mountain City:

```xml
<circle cx="x" cy="y" r="3" fill="#D4A84B" fill-opacity="0.6"/>
```

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

**布局 Structure**:
- Upper-right area: Logo (using logo.png)
- Center-left: 主标题 + subtitle
- Lower-left corner: Large diagonal deep-blue color block (extending from lower-left to upper-right)
- Bottom: Presenter info, date
- Decorations: Wave patterns + gold light dots

### 2. Chapter Page (02_chapter.svg)

**布局 Structure**:
- Full-screen deep blue 背景
- Upper-right: Diagonal light area (sky blue gradient)
- Left: Large chapter number (semi-transparent)
- Center-left: 章节标题 (white)
- Bottom: Gold decorative line + Logo (white version)

### 3. 内容 Page (03_content.svg)

**布局 Structure**:
- Top: Diagonal blue accent strip (approx. 80px height, higher on left, lower on right)
- On the accent strip: 页面标题 + Logo
- Body: White content area (flexible layout)
- Left: Thin gold decorative line
- Bottom: Clean footer + wave pattern

### 4. Ending Page (04_ending.svg)

**布局 Structure**:
- Center: Large-sized Logo
- Below logo: Thank-you message
- Bottom diagonal blue area: Contact information
- Decorations: Wave patterns + gold light dots

### 5. Table of 内容s (02_toc.svg)

**布局 Structure**:
- Top diagonal accent strip + title
- Left: Large numeric indices (vertically arranged, with gold accents)
- Right: TOC item text
- Bottom: Wave decoration

---

## VII. Logo Usage Guidelines

| File | Applicable Context | 说明 |
|------|-------------------|-------|
| `重庆大学logo.png` | Light/white 背景 | Blue version |
| `重庆大学logo2.png` | Dark/blue 背景 | White version |

**Recommended Logo Sizes**:
- Cover page: Width 280-320px
- 内容 page header: Width 160-200px
- Ending page: Width 320-400px

---

## 八、间距规范

| Element              | 数值      |
| -------------------- | ---------- |
| 页面边距         | 60px       |
| 内容 block spacing | 28px      |
| Card inner padding   | 24px       |
| Card border radius   | 12px       |
| Diagonal cut angle   | Approx. 8-12° |

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. Define gradients using `<linearGradient>` inside `<defs>`
3. Use `fill-opacity` / `stroke-opacity` for transparency
4. Use `<tspan>` for text wrapping
5. Use Base64 inline or `<image>` reference for logos

### Prohibited Elements

- `clipPath`, `mask`, `<style>`, `class`
- `foreignObject`, `textPath`, `animate*`
- `rgba()` color format
- `<g opacity="...">` (分组透明度)

---

## 十、占位符规范

| 占位符 | 说明 |
| -------------------- | ---------------------- |
| `{{TITLE}}`          | 主标题             |
| `{{SUBTITLE}}`       | 副标题               |
| `{{AUTHOR}}`         | Presenter name         |
| `{{ADVISOR}}`        | Thesis advisor         |
| `{{INSTITUTION}}`    | College/Institution    |
| `{{DATE}}`           | Date                   |
| `{{PAGE_TITLE}}`     | 页面标题             |
| `{{CHAPTER_NUM}}`    | Chapter number         |
| `{{CHAPTER_TITLE}}`  | 章节标题          |
| `{{CHAPTER_DESC}}`   | 章节说明    |
| `{{KEY_MESSAGE}}`    | Key message            |
| `{{CONTENT_AREA}}`   | 内容区           |
| `{{PAGE_NUM}}`       | 页码            |
| `{{THANK_YOU}}`      | Thank-you message      |
| `{{CONTACT_INFO}}`   | Contact information    |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题       |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明  |

---

## XI. 设计检查清单

- [ ] viewBox = `0 0 1280 720`
- [ ] Diagonal block angles are consistent (8-12°)
- [ ] Logo version matches 背景
- [ ] 颜色符合设计规格ification
- [ ] Wave decorations are correctly positioned
- [ ] Text is readable (>=11px)
