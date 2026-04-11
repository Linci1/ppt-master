# Google 风格模板 - 设计规格

> 适用于年报、技术分享、项目展示与数据演示。

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | google_style（Google 风格模板） |
| **适用场景** | 年度汇报、技术分享、项目展示、数据驱动型演示 |
| **设计调性** | 专业现代、干净克制、数据驱动、留白充足 |
| **主题模式** | 浅色主题（白/浅灰底 + Google 品牌色强调） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **页面边距** | 左右 60px, Top 50px, Bottom 50px |
| **安全区**  | x: 60-1220, y: 50-670        |

---

## 三、配色方案

### Google 品牌色

| 角色             | 数值       | 说明                                |
| ---------------- | ----------- | ------------------------------------ |
| **Google Blue**  | `#4285F4`   | Primary titles, key data, main buttons |
| **Google Red**   | `#EA4335`   | Important emphasis, warning info     |
| **Google Yellow**| `#FBBC04`   | Auxiliary icons, secondary emphasis   |
| **Google Green** | `#34A853`   | Success indicators, positive data    |

### 专业配色

| 角色           | 数值       | 用途                                |
| -------------- | ----------- | ------------------------------------ |
| **Deep Blue**  | `#1A237E`   | 标题, core text, dark emphasis     |
| **Deep Blue Gradient Start** | `#1A73E8` | Gradient title start point  |
| **Deep Blue Gradient End** | `#0D47A1` | Gradient title end point      |
| **Main Background White** | `#FFFFFF` | Page main 背景           |
| **Light Gray Background** | `#F8F9FA` | Card inner 背景, auxiliary areas |
| **Light Gray Border** | `#E8EAED` | 分隔线, borders, grid lines     |

### 文字颜色

| 角色           | 数值       | 用途                                |
| -------------- | ----------- | ------------------------------------ |
| **Primary Text** | `#1A237E` | 标题, important text               |
| **正文文字**  | `#5F6368`   | 正文内容, 描述文字           |
| **Secondary Text** | `#9AA0A6` | Annotations, page numbers, tips    |
| **White Text** | `#FFFFFF`   | 深色背景上的文字             |

### 图表配色（按顺序使用）

| 顺序 | 数值       | 说明          |
| ----- | ----------- | -------------- |
| 1     | `#4285F4`   | Google Blue    |
| 2     | `#34A853`   | Google Green   |
| 3     | `#FBBC04`   | Google Yellow  |
| 4     | `#EA4335`   | Google Red     |

---

## 四、字体系统

### 字体栈

**字体栈**： `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

> Uses system UI font stack to ensure cross-platform consistency and optimal rendering.

### 字号层级

| Level  | 用途                | Size   | Weight      |
| ------ | -------------------- | ------ | ----------- |
| H1     | 封面主标题     | 52px   | 700 (粗体)  |
| H2     | 页面主标题      | 46px   | 700 (粗体)  |
| H3     | 模块/章节标题 | 28px   | 600         |
| H4     | 卡片标题/副标题  | 24px   | 600         |
| P      | 正文内容         | 20px   | 400         |
| Data   | 大号数据数字   | 56px   | 700 (粗体)  |
| Label  | Data labels/描述文字 | 16px | 500        |
| Sub    | 辅助文字/页码 | 14px | 400       |

---

## 五、页面结构

### 通用布局

| Area               | Position/Height | 说明                            |
| ------------------ | --------------- | -------------------------------------- |
| **Top Decorative Bar** | y=0, h=6px  | Four-color gradient bar, spanning full width |
| **标题区**     | y=50, h=60px    | 页面标题 + title underline           |
| **内容区**   | y=130, h=500px  | 主要内容区                      |
| **页脚**         | y=660, h=60px   | 四色圆点装饰 + 可选页码 |

### 标志性设计元素

#### 1. Four-Color Gradient Top Bar
```
linearGradient: #4285F4 → #EA4335 → #FBBC04 → #34A853
height: 6px, width: 100%
```

#### 2. 标题 Underline (Four-Color Segments)
```
Blue: 150px → Red: 70px → Yellow: 70px → Green: 170px
stroke-width: 4px, y: 20px below title
```

#### 3. KPI Data Card
```
Size: 280×140px
Border radius: 16px
Border: 3px, using corresponding brand color
Shadow: Subtle shadow for depth
```

#### 4. Four-Color Dot Decoration
```
Used in footer or as dividers
radius: 6-14px (varies)
spacing: 30-50px
```

#### 5. Left Four-Color Vertical Bar
```
Cover page exclusive
width: 10px, 4 segments, 180px each
Color order: Blue → Red → Yellow → Green
```

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- 浅色渐变背景 (white to light blue/light green)
- Left four-color vertical bar decoration
- Centered rounded white content card (with subtle shadow)
- Gradient main title + subtitle
- Four-color segmented divider line
- Speaker info (name, title, date)
- Bottom four-color dot decoration

### 2. 目录页 (02_toc.svg)

- 白色背景 + top four-color gradient bar
- 页面标题 + blue underline
- Chapter list (left brand-color dots + numbers + titles)
- Optional: right-side decorative graphics or data stats

### 3. 章节页 (02_chapter.svg)

- 深色渐变背景 (deep blue to darker blue)
- Large chapter number (gradient or white)
- 章节标题 (white, large font)
- 英文副标题 (white, semi-transparent)
- Four-color decorative elements

### 4. 内容页 (03_content.svg)

- 白色背景
- Top four-color gradient bar
- 页面标题 + blue underline
- 可灵活编排的内容区 (supports multiple layouts)
- Bottom four-color dot decoration

### 5. 结束页 (04_ending.svg)

- 浅色渐变背景
- Centered rounded white content card
- Gradient "Thank You!" title
- Four-color divider line
- Acknowledgment list (brand-color dots + names/items)
- Closing remarks + bottom four-color dots

---

## VII. 版式模式

| 模式 | 适用场景 |
| ---------------------- | ---------------------------------- |
| **Centered Card**      | 封面、结束页, key points          |
| **Left Text Right Image** | Text description + chart/KPI area |
| **KPI Grid (2×2/2×3)** | Data overview, key metrics display |
| **三列卡片** | Project lists, feature introductions |
| **Four Quadrants**     | Category display, SWOT analysis    |
| **上下分栏**   | Two related topics side by side    |
| **时间轴**           | 发展历程、路线图       |
| **Dashboard Style**    | Multi-metric data dashboard        |

---

## VIII. Spacing Guidelines

| Element              | 数值    |
| -------------------- | -------- |
| 页面边距         | 60px     |
| 标题-to-content gap | 30-40px  |
| Module gap           | 60-80px  |
| Card gap             | 20-24px  |
| Card padding         | 20px     |
| Card border radius   | 16px     |
| 图标与文字间距     | 15px     |

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency
5. Define gradients using `<linearGradient>` within `<defs>`

### Prohibited Elements

以下 SVG 特性被禁止使用（与 PPT 不兼容）：

- `clipPath`, `mask`
- `<style>` tag, `class` attribute
- `foreignObject`
- `textPath`
- `animate*` animation elements
- `script`
- `marker`, `marker-end`
- `rgba()` color format (use HEX + opacity instead)

### Shadow Implementation

Since `filter` may affect PPT compatibility:
- Use subtle border color variations to simulate shadows
- Or accept that `filter` may be ignored in older PPT versions, though it works well in newer versions

---

## 十、占位符规范

Templates use `{{PLACEHOLDER}}` format placeholders:

| 占位符 | 说明 |
| ---------------------- | ------------------------ |
| `{{TITLE}}`            | 主标题               |
| `{{SUBTITLE}}`         | 副标题/部门信息 |
| `{{SPEAKER_NAME}}`     | Speaker name             |
| `{{SPEAKER_TITLE}}`    | Speaker title/position   |
| `{{DATE}}`             | Date                     |
| `{{PAGE_TITLE}}`       | 页面标题               |
| `{{CHAPTER_NUM}}`      | Chapter number           |
| `{{CHAPTER_TITLE}}`    | 章节标题            |
| `{{CHAPTER_TITLE_EN}}` | Chapter 英文副标题 |
| `{{PAGE_NUM}}`         | 页码              |
| `{{CONTENT_AREA}}`     | 内容区 placeholder |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题           |
| `{{THANK_YOU}}`        | Thank-you message        |
| `{{CONTACT_INFO}}`     | Primary contact info     |
| `{{ENDING_SUBTITLE}}`  | 结束页副标题          |

---

## XI. Color Application Examples

### KPI Card Color Rules

| Card Order | Border Color | Number Color | Applicable 内容 |
| ---------- | ------------ | ------------ | ------------------ |
| 1st        | `#4285F4`    | `#4285F4`    | Core projects/main metrics |
| 2nd        | `#34A853`    | `#34A853`    | Cost/efficiency metrics |
| 3rd        | `#EA4335`    | `#EA4335`    | Reliability/risk   |
| 4th        | `#FBBC04`    | `#FBBC04`    | Performance/growth |

### List Item Colors

- Use the four brand colors in rotation for list bullet colors
- Keep text in a consistent deep blue `#1A237E`

---

## 十二、使用说明

1. Copy the template to the project directory `templates/`
2. Select the appropriate page type based on content needs
3. Use placeholders to mark content that needs replacement
4. Strictly follow the Google brand four-color scheme
5. Maintain generous whitespace to highlight key information
6. Data-driven: use large numbers + small labels to display KPIs

---

_This specification is based on Google Material Design principles, adapted for PPT Master project requirements_
