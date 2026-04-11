# 政务红模板 - 设计规格

> 适用于政务工作汇报与党建类场景。

---

## 一、模板总览

| 属性 | 说明                                                  |
| -------------- | ------------------------------------------------------------ |
| **模板名称** | government_red（政务红模板） |
| **适用场景** | 政务工作汇报、党建展示、主题活动汇报 |
| **设计调性** | 权威庄重、专业规范、现代政务风格 |
| **主题模式** | 浅色主题（白底 + 政务红蓝强调） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **页面边距** | 左右 60px, Top 80px, Bottom 40px |
| **安全区**  | x: 60-1220, y: 80-680         |

---

## 三、配色方案

### 主色

| 角色           | 数值       | 说明                              |
| -------------- | ----------- | ---------------------------------- |
| **Government Red** | `#8B0000` | Primary color, title bar, accent blocks, decoration bars |
| **Government Blue** | `#003366` | Secondary accent, chapter 页面背景 |
| **Background White** | `#FFFFFF` | Main 页面背景            |
| **Auxiliary Light Gray** | `#F5F7FA` | Non-critical content 背景 blocks |
| **Border Gray** | `#E4E7EB`  | 分隔线, borders                  |
| **Gold Accent** | `#DAA520`  | Decorative accents, important data highlights |

### 文字颜色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Primary Text** | `#1A1A1A` | 正文文字、标题      |
| **White Text** | `#FFFFFF`   | 深色背景上的文字 |
| **Secondary Text** | `#4A5568` | Dimmed sections, supplementary notes |
| **Light Auxiliary** | `#718096` | Annotations, page numbers, hints |

### 功能色

| 用途    | 数值       | 说明    |
| -------- | ----------- | -------------- |
| **正向色** | `#38A169` | Completed/On target |
| **警示色** | `#E53E3E` | Attention/Alert |
| **信息**    | `#3182CE` | General information |

---

## 四、字体系统

### 字体栈

**字体栈**： `"Microsoft YaHei", "微软雅黑", "SimHei", "Source Han Sans SC", Arial, sans-serif`

### 字号层级

| Level | 用途              | Size | Weight  |
| ----- | ------------------ | ---- | ------- |
| H1    | 封面主标题   | 48px | 粗体    |
| H2    | 页面标题       | 28px | 粗体    |
| H3    | 分节标题/副标题 | 24px | 粗体 |
| P     | 正文内容       | 18px | 常规 |
| High  | 高亮数据   | 36px | 粗体    |
| Sub   | 补充文字 | 14px | 常规 |

---

## 五、页面结构

### 通用布局

| Area       | Position/Height | 说明                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=6px      | Dual-color gradient bar (red + blue), full width |
| **标题 Bar** | y=30, h=50px | 章节序号 block + title text + top-right logo |
| **内容区** | y=100, h=560px | 主要内容区                 |
| **页脚** | y=680, h=40px   | 页码, organization name, bottom decoration line |

### 导航条设计

- **Top Decoration Line**: Dual-color gradient (`#8B0000` → `#003366`), height 6px, full width
- **Bottom Decoration Line**: Government red (`#8B0000`), height 4px, y=716
- **标题 Bar** (y=30):
  - 章节序号 block: Government red square (50×50px), white number centered
  - 标题 text: 20px from number block, 28px font size, `#1A1A1A`
  - Top-right logo: Fixed at x=1107, dimensions 113×50px

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- 深色渐变背景 (primarily government blue)
- Top gold decoration line
- 主标题 + subtitle (centered, white)
- 机构名称
- Bottom date area

### 2. 目录页 (02_toc.svg)

- 白色背景 + left-side red vertical bar decoration
- Supports up to 5 chapters
- Numbering uses red square blocks + white numbers
- Optional data display area on the right

### 3. 章节页 (02_chapter.svg)

- 深蓝渐变背景
- Large chapter number (semi-transparent decoration)
- 章节标题 + 英文副标题
- Geometric decorative elements

### 4. 内容页 (03_content.svg)

- 白色背景
- Standard navigation bar (red number block)
- 可灵活编排的内容区
- Supports multiple layout modes

### 5. 结束页 (04_ending.svg)

- Deep blue 背景
- Centered thank-you message
- Full organization name
- Contact/Address information

---

## 七、布局模式

| 模式 | 适用场景 |
| ------------------ | ------------------------------ |
| **单列居中** | 封面、结束页、关键观点 |
| **双栏（5:5）** | 对比展示         |
| **双栏（4:6）** | 图文混排ed layout     |
| **上下分栏** | 流程说明、政策列表 |
| **三列卡片** | Project lists, data display |
| **Matrix Grid**    | Category display               |
| **Table**          | Data comparison, specification lists |

---

## VIII. Spacing Guidelines

| Element          | 数值  |
| ---------------- | ------ |
| Card spacing     | 24px   |
| 内容 block spacing | 32px |
| Card padding     | 24px   |
| 卡片圆角 | 8px  |
| 图标与文字间距 | 12px   |

---

## 九、SVG 技术约束

### Mandatory Rules

1. viewBox: `0 0 1280 720`
2. 背景统一使用 `<rect>` 元素
3. Use `<tspan>` for text wrapping (no `<foreignObject>`)
4. Use `fill-opacity` / `stroke-opacity` for transparency; `rgba()` is prohibited
5. Prohibited: `clipPath`, `mask`, `<style>`, `class`, `foreignObject`
6. Prohibited: `textPath`, `animate*`, `script`, `marker`/`marker-end`
7. Use `<polygon>` triangles instead of `<marker>` for arrows

### PPT 兼容性规则

- No `<g opacity="...">` (分组透明度); set opacity on each child element individually
- Use overlay layers instead of image opacity
- Use inline styles only; external CSS and `@font-face` are prohibited

---

## 十、占位符规范

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| 占位符 | 说明 |
| ------------------ | ------------------ |
| `{{TITLE}}`        | 主标题         |
| `{{SUBTITLE}}`     | 副标题           |
| `{{AUTHOR}}`       | 机构名称 (Chinese) |
| `{{AUTHOR_EN}}`    | 机构英文名 |
| `{{PAGE_TITLE}}`   | 页面标题         |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{PAGE_NUM}}`     | 页码        |
| `{{DATE}}`         | Date               |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题 |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{CONTACT_INFO}}` | Contact information |
| `{{LOGO_HEADER}}`  | 页眉 Logo 文件名 |
| `{{COVER_BG_IMAGE}}`| 封面背景图片文件名 |

---

## 十一、使用说明

1. Copy the template to the project directory
2. Replace logo files in the images directory (if applicable)
3. Select the appropriate page template based on content requirements
4. Mark content to be replaced using placeholders
5. 由 Executor 角色生成最终 SVG

---

## XII. Design Highlights

- **Dual-Color Gradient Top Decoration**: Red-blue gradient reflects a government style
- **Gold Accent Elements**: Adds a sense of dignity
- **Geometric Decorative 模式**: Modern government aesthetic
- **Clear Visual Hierarchy**: Ensures efficient information delivery
