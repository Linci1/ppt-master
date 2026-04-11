# 招商银行模板 - 设计规格

> 适用于高端金融机构汇报、年报与 VIP 服务展示。

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | 招商银行（招商银行模板） |
| **适用场景** | 高端金融机构汇报、年报展示、VIP 服务介绍 |
| **设计调性** | 极简奢雅、精致层次、现代金融感 |
| **主题模式** | 浅色主题（纹理底 + 招行红金精细装饰） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`               |
| **安全边距** | 40px (左右), 35px (上下) |
| **安全区**  | x: 40-1240, y: 70-665        |
| **网格基线**  | 40px                          |

---

## 三、配色方案

### 核心颜色

| 角色             | 颜色值 | 说明                            |
| ---------------- | ----------- | -------------------------------- |
| **CMB Red**      | `#C41230`   | Brand primary, used for accents, title bars |
| **Auxiliary Gold** | `#C9A962` | Luxury accent for double-line borders, decorations |
| **Dark Red**     | `#9A0E26`   | Deep 背景 color for added depth |
| **Background White** | `#FFFFFF` | Card and highlight area 背景 |
| **Subtle Texture White** | `#FAFAFA` | Very light 背景 to avoid harsh pure white |
| **Warm Gray Accent** | `#F8F6F3` | Bottom decorative bars, card 背景 |

### 安全区锚点（新版极简装饰）

```xml
<!-- Four-corner anchor points (replacing legacy card borders) -->
<path d="M40 140 L50 140 M40 140 L40 150" stroke="#C9A962" stroke-width="1" stroke-opacity="0.5" />
<path d="M1240 140 L1230 140 M1240 140 L1240 150" stroke="#C9A962" stroke-width="1" stroke-opacity="0.5" />
```

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`

### 字号层级

| Level    | 用途              | Size    | Weight  |
| -------- | ------------------ | ------- | ------- |
| H1       | 封面主标题   | 52px    | 粗体    |
| H2       | 页面标题         | 24-28px | 粗体    |
| H3       | 章节标题      | 52px    | 粗体    |
| H4       | 小节 / 卡片标题 | 20-22px | 粗体 |
| P        | 正文内容       | 16-18px | 常规 |
| Caption  | 辅助说明    | 12-14px | 常规 |
| Number   | Chapter number     | 320px   | 粗体 (Low Opacity) |

---

## 五、页面结构

### 常用布局

| Area       | Position/Height | 说明                            |
| ---------- | --------------- | -------------------------------------- |
| **页眉** | y=0-75          | Red 背景 with gold lines, top-left ring decoration |
| **Key Message Bar** | y=95-120 | (内容 pages) Minimalist red line guide + text |
| **内容** | y=140-650      | Open layout with no fixed borders      |
| **页脚** | y=665+          | 页码, copyright, institution name |

### 核心装饰设计（设计 DNA）

1. **Refined Double Lines**: 1px main line + 3px auxiliary line combination, simulating high-end print craftsmanship.
2. **Multi-Layer Concentric Circles**: Abstract representation of CMB's sunflower logo, adding visual depth.
3. **Micro Dot-Matrix Texture**: Arrays of tiny dots for added visual breathing room.
4. **Diamond 分隔线**: Diamond-shaped decorations at title division points for a refined touch.

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- **Background**: White main 背景 + bottom warm gray decorative band.
- **Top**: Red horizontal bar + gold double lines.
- **Decoration**: Multi-layer concentric rings at top-left, vertical decorative lines at right edge.
- **标题 Area**: Centered layout with rounded border and diamond divider line.

### 2. 目录页 (02_toc.svg)

- **页眉**: Fixed "目录 / CONTENTS" title.
- **List**: Left-right dual-column **checklist layout** (no 背景 cards).
- **Design**: Uses "large red number + title + gold underline" combination for strong adaptability.
- **Decoration**: Left side features vertical lines and decorative "Index" text.

### 3. 章节页 (02_chapter.svg)

- **Background**: Full-screen dark red 背景 (`#9A0E26`).
- **Visual Center**: Left-side gold vertical bar with title combination.
- **Right Side**: Complex gold horizontal bar staircase effect + diagonal line texture.
- **Background Text**: Giant semi-transparent chapter numbers.

### 4. 内容页 (03_content.svg)

- **布局**： **Fully open layout**, removing center borders to maximize content display area.
- **Key Message**: Top area presented with minimalist left-side red line + text, reducing visual distraction.
- **Boundary**: Only very faint "safe area anchor points" retained at four corners.
- **页脚**: Contains data source, page number, and chapter name.

### 5. 结束页 (04_ending.svg)

- **Echo**: 布局 closely mirrors the cover page, creating a cohesive bookend.
- **Contact 信息**: Wide contact information card at the bottom.
- **Decoration**: Symmetrical multi-layer gold concentric rings on left and right.

---

## 七、版式模式（推荐）

### 1. Key Message 布局
- Use the top gray message bar to present a one-sentence key conclusion.
- Pair with a single large chart or emphasized text below.

### 2. Card Grid
- Place 2x2 or 3x2 data cards within the white content area.
- Recommended card 背景: `#FDF2F4` (light red) or `#F8F6F3` (warm gray).

### 3. Split Column Comparison
- Left side presents current state / problems; right side presents solutions / results.
- Gold arrows can serve as logical connectors in the middle.

---

## VIII. Spacing Guidelines

| 属性 | 值 | 说明              |
| -------------- | ----- | ------------------------ |
| **Base Unit**  | 4px   | All spacing should be multiples of 4px |
| **Module Gap** | 40px  | Standard gap between major modules |
| **Card Gap**   | 24px  | Gap between cards        |
| **Inner Padding** | 20px | Padding inside cards    |
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
| --------------------- | ------------------ |
| `{{TITLE}}`           | 主标题         |
| `{{SUBTITLE}}`        | 副标题           |
| `{{AUTHOR}}`          | Presenter name     |
| `{{DATE}}`            | Date               |
| `{{CHAPTER_NUM}}`     | Chapter number     |
| `{{CHAPTER_TITLE}}`   | 章节标题      |
| `{{CHAPTER_DESC}}`    | 章节说明 |
| `{{PAGE_TITLE}}`      | 页面标题         |
| `{{KEY_MESSAGE}}`     | Key message        |
| `{{CONTENT_AREA}}`    | 内容区 identifier |
| `{{TOC_ITEM_N_TITLE}}`| 目录项标题 (N=1..n) |
| `{{TOC_ITEM_N_DESC}}` | 目录项说明 (N=1..n) |
| `{{THANK_YOU}}`       | Closing message    |
| `{{ENDING_SUBTITLE}}` | 结束页副标题    |
| `{{CONTACT_INFO}}`    | Contact information |

---

## 十一、使用说明

1. **Logo Adaptation**: Recommend using white inverted Logo.
2. **Font Installation**: Recommend installing "Microsoft YaHei" or an equivalent sans-serif font.
3. **Extended Colors**: If additional colors are needed, maintain the red-gold ratio unchanged.
