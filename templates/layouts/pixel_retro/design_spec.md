# 像素复古模板 - 设计规格

> 适用于技术分享、复古游戏主题与极客风内容。

---

## 一、模板总览

| 属性 | 说明                                                |
| -------------- | ---------------------------------------------------------- |
| **模板名称** | pixel_retro（像素复古模板） |
| **适用场景** | 技术分享、复古游戏主题、极客风展示 |
| **设计调性** | 复古游戏、霓虹赛博、极客科技、8 位风格 |
| **主题模式** | 深色主题（深空黑底 + 霓虹强调） |

---

## 二、画布规格

| 属性 | 值                         |
| -------------- | ----------------------------- |
| **格式**     | 标准 16:9                 |
| **尺寸** | 1280 × 720 px                |
| **viewBox**    | `0 0 1280 720`                |
| **页面边距** | 左右 60px, Top 50px, Bottom 40px |
| **安全区**  | x: 60-1220, y: 50-680         |

---

## 三、配色方案

### 背景色

| 角色           | 数值       | 说明                            |
| -------------- | ----------- | -------------------------------- |
| **Deep Space Black** | `#0D1117` | Main 背景 color          |
| **Starry Night Blue** | `#161B22` | Card/block 背景         |
| **Dark Border** | `#30363D`  | Borders/dividers                 |

### 强调色（霓虹系列）

| 角色           | 数值       | 用途                            |
| -------------- | ----------- | -------------------------------- |
| **Neon Green** | `#39FF14`   | Primary accent, success, save points, Git |
| **Cyber Pink** | `#FF2E97`   | Secondary accent, warnings, contrast, GitHub |
| **Electric Blue** | `#00D4FF` | Tertiary accent, links, info, flows |
| **Gold Yellow** | `#FFD700`  | Quaternary accent, history, timelines, highlights |

### 辅助色

| 角色           | 数值       | 用途                            |
| -------------- | ----------- | -------------------------------- |
| **Dark Green** | `#238636`   | Muted version of success state   |
| **Dark Pink**  | `#8B2252`   | Muted pink                       |
| **Dark Blue**  | `#1F6FEB`   | Muted blue                       |

### 文字颜色

| 角色           | 数值       | 用途                  |
| -------------- | ----------- | ---------------------- |
| **Moonlight White** | `#E6EDF3` | Primary text         |
| **Mist Gray**  | `#8B949E`   | Secondary descriptive text |
| **Pure White** | `#FFFFFF`   | Emphasized titles      |

---

## 四、字体系统

### 字体栈

**标题 Font**: `"Consolas", "Monaco", "Courier New", monospace` - Pixel/code aesthetic

**正文字体**: `-apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif`

**Code Font**: `"Cascadia Code", "Fira Code", "Consolas", monospace`

### 字号层级

| Level | 用途              | Size | Weight  |
| ----- | ------------------ | ---- | ------- |
| H1    | 封面主标题   | 52px | 粗体    |
| H2    | 页面标题       | 36px | 粗体    |
| H3    | 分节标题/副标题 | 22px | 600  |
| P     | 正文内容       | 18px | 常规 |
| High  | 高亮数据   | 48px | 粗体    |
| Sub   | 补充文字 | 14px | 常规 |
| Code  | 代码文字          | 16px | 常规 |

---

## 五、页面结构

### 通用布局

| Area       | Position/Height | 说明                            |
| ---------- | --------------- | -------------------------------------- |
| **Top**    | y=0, h=4-6px    | Neon green decoration line (dual-line effect) |
| **标题区** | y=50, h=70px | 页面标题 + 英文副标题         |
| **内容区** | y=130, h=510px | 主要内容区                  |
| **页脚** | y=680, h=40px   | 页码, decoration line, progress indicator |

### 装饰元素

- **Top Decoration Line**: Neon green dual lines (main line 4px + auxiliary line 2px)
- **Bottom Decoration Line**: Neon green dual lines (auxiliary line 4px + main line 4px)
- **Pixel Blocks**: Corner decorations with decreasing opacity (100% → 60% → 30%)
- **Scanline Grid**: Optional low-opacity 背景 grid lines

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- Deep space black 背景
- Top/bottom neon decoration lines
- Pixel-style console graphic (optional)
- 主标题 (neon green glow effect)
- 副标题 (moonlight white)
- Function button group (horizontal layout)
- Bottom prompt text (e.g., "PRESS START")

### 2. 目录页 (02_toc.svg)

- Deep space black 背景
- Standard top decoration
- Chapter list (with importance labels)
  - Red: Essential / Must-learn
  - Yellow: Recommended
  - Green: Optional
- Pixel-style list design

### 3. 章节页 (02_chapter.svg)

- Deep space black 背景
- Full-screen neon effect
- Large chapter number (glow effect)
- 章节标题 + 英文副标题
- Pixel-style decorative frame

### 4. 内容页 (03_content.svg)

- Deep space black 背景
- Standard top decoration
- 页面标题 (neon green + glow)
- 英文副标题 (mist gray)
- **Fully open content area** (y=140 to y=670, width 1160px)
- 底部页码

> **Design Principle**: The content page template only provides the page frame (title area + footer). The content area is freely designed by the Executor based on actual content. Available layouts include but are not limited to: cards, progress bars, tables, timelines, comparison charts, etc.

### 5. 结束页 (04_ending.svg)

- Deep space black 背景
- Neon glow main title
- Summary card group
- "GAME SAVED" visual effect
- Progress button group

---

## 七、布局模式

| 模式 | 适用场景 |
| ------------------ | ------------------------------ |
| **单列居中** | 封面、结束页、关键观点 |
| **双栏（5:5）** | 对比展示 (e.g., Git vs GitHub) |
| **Dual-Column Cards** | Feature lists, trait comparisons |
| **三列卡片** | Key takeaways, project lists |
| **Progress Bar Display** | Data statistics, usage rates |
| **时间轴**       | 历史、流程、工作流  |

---

## VIII. Spacing Guidelines

| Element          | 数值  |
| ---------------- | ------ |
| Card spacing     | 20-30px |
| 内容 block spacing | 30px |
| Card padding     | 20-24px |
| 卡片圆角 | 0px (blocky feel) or 4px |
| Border width     | 2-3px  |
| 图标与文字间距 | 12px   |

---

## IX. Visual Effects

### Pixel Style Characteristics

- Blocky icons and decorations
- Use block characters such as: full block, dark shade, light shade, upper half, lower half, small black/white squares for decoration
- Progress bars filled with blocks
- Borders use double lines or dotted patterns
- Card corners with pixel decoration blocks

### Neon Glow Effect

Apply glow filters to key text/elements:

```xml
<defs>
  <filter id="glowGreen" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="3-4" result="blur" />
    <feMerge>
      <feMergeNode in="blur" />
      <feMergeNode in="SourceGraphic" />
    </feMerge>
  </filter>
</defs>

<!-- Usage -->
<text filter="url(#glowGreen)" fill="#39FF14">Glowing Text</text>
```

> **Note**: `filter` effects are typically ignored in PPT, but render well in SVG-compatible viewers.

### Emoji Usage

- 🎮 Game/Save
- 💾 Save
- 🔀 Branch/Merge
- 📁 Folder
- 📝 Document
- 🚀 Release
- ⏪ Revert
- 👾 Developer
- 🌐 Network/Cloud
- ✅ Confirm/Success
- 🎯 Target/Key Point
- 🤔 Question/Thinking

---

## 十、SVG 技术约束

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
- `filter` effects serve as enhancements (allowed) and do not affect baseline display

---

## 十一、占位符说明

Templates use `{{PLACEHOLDER}}` format placeholders. Common placeholders:

| 占位符 | 说明 |
| ------------------ | ------------------ |
| `{{TITLE}}`        | 主标题         |
| `{{SUBTITLE}}`     | 副标题           |
| `{{AUTHOR}}`       | Author/Organization |
| `{{PAGE_TITLE}}`   | 页面标题         |
| `{{PAGE_TITLE_EN}}`| 页面标题 (English) |
| `{{CONTENT_AREA}}` | 可灵活编排的内容区 |
| `{{CHAPTER_NUM}}`  | Chapter number     |
| `{{PAGE_NUM}}`     | 页码        |
| `{{TOTAL_PAGES}}`  | Total page count   |
| `{{VERSION}}`      | Version number     |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题 |
| `{{THANK_YOU}}`    | Thank-you message  |
| `{{CONTACT_INFO}}` | Primary contact info |

---

## 十二、使用说明

1. Copy the template to the project `templates/` directory
2. Select the appropriate page template based on content requirements
3. Mark content to be replaced using placeholders
4. 由 Executor 角色生成最终 SVG
5. Define glow effects using `filter` (within `<defs>`)
6. Maintain consistency of the neon color scheme

---

## XIII. Color Quick Reference

```
Background Layer:
  Main 背景    #0D1117  Deep Space Black
  卡片背景    #161B22  Starry Night Blue
  Borders            #30363D  Dark Border

Accent Colors (use in order):
  Primary accent     #39FF14  Neon Green
  Secondary accent   #FF2E97  Cyber Pink
  Tertiary accent    #00D4FF  Electric Blue
  Quaternary accent  #FFD700  Gold Yellow

Text:
  Primary text       #E6EDF3  Moonlight White
  Secondary text     #8B949E  Mist Gray
  Emphasis text      #FFFFFF  Pure White
```
