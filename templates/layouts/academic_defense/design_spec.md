# 学术答辩模板 - 设计规格

> 适用于学术答辩、科研汇报与项目申报的标准模板。

---

## 一、模板总览

| 属性 | 说明                                            |
| -------------- | ------------------------------------------------------ |
| **模板名称** | academic_defense（学术答辩模板） |
| **适用场景** | 学术答辩、学术汇报、研究进展汇报、项目申报 |
| **设计调性** | 专业严谨、研究导向、层次清晰 |
| **主题模式** | 浅色主题（白底 + 深蓝标题栏） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **页面边距** | 左右 40px, Top 0px, Bottom 35px |
| **安全区**  | x: 40-1240, y: 70-665        |

---

## 三、配色方案

### 主色

| 角色           | 数值       | 说明                            |
| -------------- | ----------- | -------------------------------- |
| **Primary Dark Blue** | `#003366` | 页眉 背景, section titles, main headings |
| **Accent Blue** | `#0066CC` | 卡片边框, icons, secondary decorations |
| **Accent Red** | `#CC0000`  | Key highlights, keyword emphasis, left decorative bar |
| **Light Blue-Gray** | `#E8F4FC` | Key message bar 背景, card inner sections |
| **Background White** | `#FFFFFF` | Page main 背景           |

### 文字颜色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **White Text** | `#FFFFFF`   | 深色背景上的文字 |
| **Primary Text** | `#333333` | 正文内容           |
| **Secondary Text** | `#666666` | 说明文字、注释 |
| **Muted Gray** | `#999999`  | 页脚, auxiliary info |

### 中性色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Card Gray**  | `#F5F7FA`   | Card inner 背景, info blocks |
| **Border Gray** | `#D0D7E0`  | 卡片边框, dividers |

### 功能色

| 用途      | 数值       | 说明    |
| ---------- | ----------- | -------------- |
| **正向色** | `#28A745`  | Positive indicators |
| **警示色** | `#FFA500`  | Alerts         |
| **信息**   | `#17A2B8`   | 信息 tips |

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`

### 字号层级

| Level | 用途            | Size | Weight  |
| ----- | ---------------- | ---- | ------- |
| H1    | 封面主标题 | 56px | 粗体    |
| H2    | 页面标题       | 28px | 粗体    |
| H3    | 分节标题    | 56px | 粗体    |
| H4    | 卡片标题       | 24px | 粗体    |
| P     | 正文内容     | 18px | 常规 |
| High  | 高亮数据 | 36px | 粗体    |
| Sub   | 说明/来源    | 14px | 常规 |
| XS    | 页码/版权 | 12px | 常规 |

---

## 五、页面结构

### 通用布局

| Area           | Position/Height | 说明                            |
| -------------- | --------------- | -------------------------------------- |
| **页眉**     | y=0, h=70px     | Dark blue 背景 + red left bar + page title |
| **Key Message Bar** | y=70, h=50px | Core message/summary area (light blue-gray 背景) |
| **内容区** | y=135, h=515px | 主要内容区                    |
| **页脚**     | y=665, h=55px   | Data source, section name, page number |

### 装饰元素

- **Left Red Bar**: Red (`#CC0000`), width 6px, used for header and card decoration
- **Blue Border**: Accent blue (`#0066CC`), used for card borders
- **Decorative Divider**: Blue (`#0066CC`), paired with decorative dots

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- 白色背景
- Dark blue top bar + red left vertical bar decoration
- Top-right Logo placeholder area
- Centered main title + subtitle
- Decorative divider line (blue + dots)
- Presenter info area (name, advisor, institution)
- Bottom gray info area (date)

### 2. 目录页 (02_toc.svg)

- 白色背景
- Standard header (dark blue + red vertical bar)
- Card-style TOC item layout (2 columns)
- Light blue-gray 背景 cards + left colored vertical bar
- Optional items use dashed borders

### 3. 章节页 (02_chapter.svg)

- Dark blue full-screen 背景 (`#003366`)
- Right-side geometric decorations
- Left red vertical bar decoration
- Large semi-transparent 背景 number
- Prominent white chapter title
- Light blue-gray chapter description
- Red decorative horizontal line

### 4. 内容页 (03_content.svg)

- 白色背景
- Standard header (dark blue + red vertical bar)
- Key message bar (light blue-gray 背景 + blue left vertical bar)
- 可灵活编排的内容区
- 页脚: 数据来源、章节名称、页码

### 5. 结束页 (04_ending.svg)

- 白色背景
- Dark blue top bar
- Centered thank-you message
- Tagline
- Decorative divider line
- Contact info card (gray 背景)
- Bottom gray area (copyright, page number)

---

## VII. 版式模式

| 模式 | 适用场景 |
| ------------------ | ------------------------------ |
| **单列居中** | 封面、结束页, key points |
| **Two-Column Cards** | Table of contents            |
| **Left-Right Split (5:5)** | Comparison display      |
| **Left-Right Split (4:6)** | 图文混排ed layout |
| **Card Grid**      | Research content list           |
| **时间轴**       | 研究进度               |
| **Table**          | Data comparison, experiment results |

---

## VIII. Spacing Guidelines

| Element            | 数值  |
| ------------------ | ------ |
| Card gap           | 20px   |
| 内容 block gap  | 24px   |
| Card padding       | 20px   |
| 卡片圆角 | 8px    |
| 图标与文字间距   | 12px   |

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; no `rgba()`
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Use `<polygon>` triangles for arrows instead of `<marker>`

### PPT 兼容性规则

- No `<g opacity="...">` (分组透明度); set opacity on each child element individually
- Use overlay layers for image transparency
- Inline styles only; no external CSS or `@font-face`

---

## 十、占位符规范

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| 占位符 | 说明 |
| ------------------ | ------------------ |
| `{{TITLE}}`        | Thesis/project main title |
| `{{SUBTITLE}}`     | 副标题           |
| `{{AUTHOR}}`       | Presenter name     |
| `{{ADVISOR}}`      | Advisor            |
| `{{INSTITUTION}}`  | University/institution |
| `{{DATE}}`         | Defense date       |
| `{{PAGE_TITLE}}`   | 页面标题         |
| `{{SECTION_NUM}}`  | 章节序号     |
| `{{CHAPTER_NUM}}`  | Chapter number (large) |
| `{{CHAPTER_TITLE}}`| 章节标题      |
| `{{CHAPTER_DESC}}` | 章节说明 |
| `{{KEY_MESSAGE}}`  | Key message        |
| `{{PAGE_NUM}}`     | 页码        |
| `{{SOURCE}}`       | Data source        |
| `{{SECTION_NAME}}` | 章节名称 (footer) |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题 (N=1..n) |
| `{{TOC_ITEM_N_DESC}}` | 目录项说明 (N=1..n) |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{ENDING_SUBTITLE}}` | 结束页副标题/tagline |
| `{{CONTACT_INFO}}` | Contact information |
| `{{EMAIL}}`        | 邮箱地址      |
| `{{COPYRIGHT}}`    | Copyright info     |
| `{{LOGO}}`         | Logo 文字          |

---

## XI. Component Specifications

### 1. Tag

```xml
<!-- Blue 背景 white text tag -->
<rect x="40" y="150" width="80" height="28" fill="#0066CC" rx="4"/>
<text x="80" y="170" text-anchor="middle" fill="#FFFFFF" font-size="14" font-weight="bold">内容详解</text>

<!-- Red 背景 white text tag (emphasis) -->
<rect x="40" y="150" width="80" height="28" fill="#CC0000" rx="4"/>
<text x="80" y="170" text-anchor="middle" fill="#FFFFFF" font-size="14" font-weight="bold">核心目标</text>
```

### 2. Flow Arrow

```xml
<!-- Horizontal flow arrow -->
<line x1="200" y1="300" x2="350" y2="300" stroke="#0066CC" stroke-width="2"/>
<polygon points="350,295 360,300 350,305" fill="#0066CC"/>
```

### 3. Data Highlight Box

```xml
<!-- Key data block -->
<rect x="40" y="400" width="200" height="80" fill="#FFFFFF" stroke="#CC0000" stroke-width="2" rx="8"/>
<text x="140" y="445" text-anchor="middle" fill="#CC0000" font-size="24" font-weight="bold">30%</text>
<text x="140" y="470" text-anchor="middle" fill="#666666" font-size="12">关键指标</text>
```

---

## 十二、使用说明

1. Copy the template to the project directory
2. Select the appropriate page template based on defense content needs
3. Use placeholders to mark content that needs replacement
4. Ensure presenter info and advisor info are complete
5. 由 Executor 角色生成最终 SVG

---

## XIII. 设计检查清单

### Before Generation

- [ ] Is the content suitable for the current page layout
- [ ] Does the color scheme follow the specification
- [ ] Is the font size hierarchy correct

### After Generation

- [ ] viewBox = `0 0 1280 720`
- [ ] No prohibited elements
- [ ] Text is readable (≥12px)
- [ ] 内容 is within the safe area
- [ ] Elements are properly aligned
- [ ] Style consistency check passed
