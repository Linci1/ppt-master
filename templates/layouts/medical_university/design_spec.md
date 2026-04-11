# 医院/医学院模板 - 设计规格

> 适用于医学汇报、病例讨论与科研展示。

---

## 一、模板总览

| Property         | 说明                                                          |
| ---------------- | -------------------------------------------------------------------- |
| **模板名称** | medical_university（医院/医学院模板） |
| **适用场景** | 医学汇报、病例讨论、科研展示、学术会议 |
| **设计调性** | 专业严谨、生命关怀、科技感强、可信赖 |
| **主题模式** | 浅色主题（白底 + 医学蓝标题栏 + 生命绿强调） |
| **Target Institutions** | All types of medical institutions (hospitals, medical universities, affiliated hospitals, medical research institutes) |

---

## 二、画布规格

| 属性 | 值                        |
| ------------------ | ---------------------------- |
| **格式**         | 标准 16:9                |
| **尺寸**     | 1280 × 720 px               |
| **viewBox**        | `0 0 1280 720`              |
| **页面边距**   | Left/right 40px, top 0px, bottom 35px |
| **内容安全区** | x: 40-1240, y: 70-665    |

---

## 三、配色方案

### 主色

| 角色               | 数值     | 说明                                    |
| ------------------ | --------- | ---------------------------------------- |
| **Primary Medical Blue** | `#0066B3` | 页眉 背景, chapter titles, main titles |
| **Deep Medical Blue** | `#004080` | Chapter 页面背景, key emphasis   |
| **Accent Green**   | `#00A86B` | 卡片边框, life/health-related content, icons |
| **Emphasis Orange** | `#FF6B35` | Key highlights, critical data, left accent bars |
| **Light Blue BG**  | `#E6F3FA` | Key message 背景 bar, card inner blocks |
| **Light Green BG** | `#E8F5EE` | Medical-related cards, health data blocks |
| **Background White** | `#FFFFFF` | Main 页面背景                   |

### 文字颜色

| 角色             | 数值     | 用途                      |
| ---------------- | --------- | -------------------------- |
| **White Text**   | `#FFFFFF` | 深色背景上的文字   |
| **Primary Text** | `#333333` | 正文内容               |
| **Secondary Text** | `#666666` | 图注、标注    |
| **Muted Gray**   | `#999999` | 页脚, supplementary info |

### 中性色

| 角色           | 数值     | 用途                        |
| -------------- | --------- | ---------------------------- |
| **Card Gray**  | `#F5F7FA` | Card inner 背景, info blocks |
| **Border Gray**| `#D0D7E0` | 卡片边框、分隔线  |

### 功能色

| 用途        | 数值     | 说明                    |
| ------------ | --------- | ------------------------------ |
| **Success**  | `#28A745` | Positive indicators, recovery data |
| **Warning**  | `#FFC107` | Precautions, reminders         |
| **Danger**   | `#DC3545` | Critical values, risk alerts   |
| **信息**     | `#17A2B8` | 信息 tips, reference data      |

### 配色变体方案

To adapt to other medical institution branding, replace the corresponding values in the primary color system:

| 机构类型 | 主色 | 强调色 | 重点色 | 适用场景 |
| ------------------- | --------- | --------- | --------- | ----------------------------- |
| Default Medical Blue | `#0066B3` | `#00A86B` | `#FF6B35` | General hospitals, medical universities |
| Children's Hospital | `#0099CC` | `#66CC99` | `#FF9933` | Children's hospitals, pediatric specialties |
| TCM Hospital        | `#8B4513` | `#228B22` | `#DAA520` | TCM hospitals, TCM research institutes |
| Maternal & Child Health | `#E91E8C` | `#9C27B0` | `#FF5722` | Maternal & child health centers, OB/GYN |

> **Usage**: Perform a global find-and-replace of the primary color values across all SVG template files to quickly switch color schemes.

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", Arial, sans-serif`

### 字号层级

| Level | 用途            | Size | Weight  |
| ----- | ---------------- | ---- | ------- |
| H1    | 封面主标题 | 52px | 粗体    |
| H2    | 页面标题       | 28px | 粗体    |
| H3    | 章节标题    | 52px | 粗体    |
| H4    | 卡片标题       | 24px | 粗体    |
| P     | 正文内容     | 18px | 常规 |
| High  | 强调数据  | 36px | 粗体    |
| Sub   | 说明/来源    | 14px | 常规 |
| XS    | 页码/版权 | 12px | 常规 |

---

## 五、页面结构

### 通用布局

| Area              | Position/Height  | 说明                                  |
| ----------------- | ---------------- | -------------------------------------------- |
| **页眉**        | y=0, h=70px      | Medical blue 背景 + orange left vertical bar + page title |
| **Key Message Bar** | y=70, h=50px   | Core message/summary area (light blue 背景) |
| **内容区**  | y=135, h=515px   | 主要内容区                            |
| **页脚**        | y=665, h=55px    | Data source, institution name, page number   |

### 装饰设计

- **Left Orange Vertical Bar**: Emphasis orange (`#FF6B35`), width 6px, used for header and card decoration
- **Medical Blue Border**: Primary blue (`#0066B3`), used for card borders
- **Green Accents**: Accent green (`#00A86B`), used for health/life-related elements
- **Cross/ECG Decorations**: Medical-themed geometric decorative elements

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- 白色背景
- Medical blue top horizontal bar + orange left vertical bar decoration
- Upper-right logo/emblem placeholder area
- Centered main title + subtitle
- Decorative divider line (blue + green dots)
- Presenter information area (name, department/advisor, institution)
- Bottom gray info area (date)

### 2. 目录页 (02_toc.svg)

- 白色背景
- Standard header (medical blue + orange vertical bar)
- Card-style TOC layout (2 columns)
- Light blue/light green 背景 cards + left colored vertical bar
- Optional items use dashed borders

### 3. 章节页 (02_chapter.svg)

- Deep medical blue full-screen 背景 (`#004080`)
- Right-side geometric decorations (medical theme)
- Left orange vertical bar decoration
- Large semi-transparent 背景 chapter number
- Prominent white chapter title
- Light blue chapter description

### 4. 内容页 (03_content.svg)

- 白色背景
- Standard header (medical blue + orange vertical bar)
- Key message bar (light blue 背景 + blue left vertical bar)
- 可灵活编排的内容区
- 页脚: 数据来源、机构名称、页码

### 5. 结束页 (04_ending.svg)

- 白色背景
- Medical blue top horizontal bar
- Centered thank-you message
- Department/contact information
- Institution logo area

---

## 七、版式模式（推荐）

### 常用布局s for Medical Reports

| 版式名称 | 适用场景 | 特征 |
| --------------------- | -------------------------------- | ------------------------------ |
| **单列居中** | 案例概览、主要结论 | 突出关键点，层级清晰 |
| **Dual Column Comparison** | Before/after treatment, plan comparison | Symmetrical, easy to compare |
| **Image-Text Mixed**  | Imaging materials, pathology images | Images with text 描述文字 |
| **Data Cards**        | Lab results, vital signs         | Multiple metrics side by side  |
| **时间轴**          | Disease progression, treatment course | Clear chronological order    |
| **Flowchart**         | Clinical pathways, procedure standards | Clear steps, logical flow   |

---

## 八、间距规范

| Spacing Type       | 数值 | 用途                            |
| ------------------ | ----- | -------------------------------- |
| **页面边距**   | 40px  | Distance from content to page edge |
| **Card Spacing**   | 24px  | Spacing between cards            |
| **Element Spacing** | 16px | Spacing between elements within cards |
| **行高**    | 1.5   | 正文字进行高倍数 |
| **Paragraph Spacing** | 20px | Spacing between paragraphs     |

---

## 九、SVG 技术约束

### Mandatory Rules

- viewBox fixed at `0 0 1280 720`
- 背景统一使用 `<rect>` 元素
- Use `<tspan>` for text wrapping
- All colors in HEX format (no rgba)
- Use `fill-opacity` / `stroke-opacity` for transparency

### 禁止元素（与 PPT 不兼容）

| Prohibited Item      | Alternative                    |
| -------------------- | ------------------------------ |
| `clipPath`           | Do not use clipping            |
| `mask`               | Do not use masking             |
| `<style>`            | Use inline styles              |
| `class`              | Use inline attributes (`id` inside `<defs>` is allowed) |
| `foreignObject`      | Use `<tspan>` for wrapping     |
| `textPath`           | Use standard `<text>`          |
| `animate*` / `set`   | Do not use animations          |
| `marker-end`         | Use `<polygon>` for arrows     |
| `<g opacity>`        | Set opacity on each element individually |

---

## 十、占位符规范

| 占位符 | 用途 |
| ------------------- | ---------------------------- |
| `{{LOGO}}`          | Emblem/institution logo      |
| `{{TITLE}}`         | 主标题                   |
| `{{SUBTITLE}}`      | 副标题                     |
| `{{AUTHOR}}`        | Presenter name               |
| `{{DEPARTMENT}}`    | Department/school            |
| `{{ADVISOR}}`       | Thesis advisor               |
| `{{INSTITUTION}}`   | Institution name             |
| `{{DATE}}`          | Date                         |
| `{{CHAPTER_NUM}}`   | Chapter number               |
| `{{CHAPTER_TITLE}}` | 章节标题                |
| `{{CHAPTER_DESC}}`  | 章节说明          |
| `{{PAGE_TITLE}}`    | 页面标题                   |
| `{{KEY_MESSAGE}}`   | Key message                  |
| `{{CONTENT_AREA}}`  | 内容区                 |
| `{{SOURCE}}`        | Data source                  |
| `{{PAGE_NUM}}`      | 页码                  |
| `{{SECTION_NAME}}`  | 章节名称 (footer)        |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题 (N=1..n)   |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 (N=1..n) |
| `{{THANK_YOU}}`     | Thank-you message            |
| `{{ENDING_SUBTITLE}}` | 结束页副标题/tagline    |

---

## 十一、使用说明

### 1. Copy Template to Project

```bash
cp templates/layouts/medical_university/* projects/<project>/templates/
```

### 2. Logo 放置规范

- Cover page: Upper-right corner, approx. 160×50px
- 内容 page: Upper-right within header, approx. 120×35px
- Ending page: Can be enlarged, centered or paired with contact info

---

## XII. Medical 内容-Specific Components

### Data Card (Vital Signs)

```xml
<rect x="x" y="y" width="180" height="100" fill="#E8F5EE" rx="8"/>
<text x="x+90" y="y+35" text-anchor="middle" fill="#333333" font-size="14">Temperature</text>
<text x="x+90" y="y+70" text-anchor="middle" fill="#00A86B" font-size="28" font-weight="bold">36.5°C</text>
```

### 警示标签

```xml
<rect x="x" y="y" width="80" height="28" fill="#FFC107" rx="4"/>
<text x="x+40" y="y+19" text-anchor="middle" fill="#333333" font-size="14">Caution</text>
```

### Critical Value Label

```xml
<rect x="x" y="y" width="80" height="28" fill="#DC3545" rx="4"/>
<text x="x+40" y="y+19" text-anchor="middle" fill="#FFFFFF" font-size="14">Critical</text>
```
