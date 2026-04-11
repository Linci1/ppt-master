# 心理疗愈模板 - 设计规格

> 适用于心理治疗培训、咨询课程与关系主题讲解。

---

## 一、模板总览

| Property         | 说明                                                  |
| ---------------- | ------------------------------------------------------------ |
| **模板名称** | psychology_attachment（心理疗愈模板） |
| **适用场景** | 心理治疗培训、咨询课程、关系主题讲解 |
| **设计调性** | 专业温和、疗愈可信、关系感强 |
| **主题模式** | 浅色主题（云白底 + 蓝绿渐变 + 多语义色） |

### 核心视觉隐喻

The design adopts "**Secure Base**" as the core visual metaphor:

- **Structural Stability**: Page layout resembles a secure attachment relationship with clear boundaries and predictable patterns
- **Clear Hierarchy**: 信息 levels mirror the organization of the attachment system — from biological instinct to higher-order reflection
- **Warm Professionalism**: Colors convey both professional authority and healing warmth

---

## 二、画布规格

| 属性 | 值                           |
| ------------------ | ------------------------------- |
| **格式**         | 标准 16:9                   |
| **尺寸**     | 1280 × 720 px                  |
| **viewBox**        | `0 0 1280 720`                 |
| **页面边距**   | Left/right 40px, top 60px, bottom 40px |
| **内容安全区** | x: 40-1240, y: 60-680       |

### 页面分区

| Zone             | Y-Range   | Height | 用途                      |
| ---------------- | --------- | ------ | -------------------------- |
| Top 标题 Area   | 60-120    | 60px   | 页面标题, chapter labels |
| Main 内容     | 130-640   | 510px  | Core content display       |
| Bottom 信息 Area | 650-680   | 30px   | 页码, chapter nav   |

---

## 三、配色方案

### 主色

| Semantic Role     | Color Name    | HEX       | RGB         | 用途                              |
| ----------------- | ------------- | --------- | ----------- | ---------------------------------- |
| **Dominant**      | Secure Blue   | `#2E5C8E` | 46,92,142   | 标题, key frameworks, secure attachment |
| **Background**    | Cloud White   | `#F8FAFC` | 248,250,252 | 页面背景                    |
| **Accent A**      | Warm Orange   | `#E07843` | 224,120,67  | Activation, emotion, anxious type  |
| **Accent B**      | Healing Green | `#3D8B7A` | 61,139,122  | Growth, integration, secure type   |
| **Accent C**      | Cool Gray-Blue| `#64748B` | 100,116,139 | Avoidant type, dismissive type     |
| **Warning**       | Trauma Red    | `#B54545` | 181,69,69   | Disorganized type, unresolved trauma |

### 依恋类型配色分配

| Attachment Type              | Primary   | Secondary | Symbolism              |
| ---------------------------- | --------- | --------- | ---------------------- |
| Secure / Autonomous          | `#3D8B7A` | `#D4EDDA` | Growth, coherence      |
| Avoidant / Dismissive        | `#64748B` | `#E2E8F0` | Detachment, suppression |
| Anxious-Ambivalent / Preoccupied | `#E07843` | `#FED7AA` | Anxiety, amplification |
| Disorganized / Unresolved    | `#B54545` | `#FECACA` | Trauma, fragmentation  |

### 文字颜色

| 角色              | 数值     | 用途                              |
| ----------------- | --------- | ---------------------------------- |
| **Main 标题**    | `#1E293B` | Dark ink blue, 封面/页面标题   |
| **副标题**      | `#2E5C8E` | Secure blue, emphasized subtitles  |
| **正文文字**     | `#374151` | Dark gray, body content            |
| **Helper Text**   | `#6B7280` | Medium gray, annotations           |
| **Secondary Text**| `#64748B` | Gray-blue, page numbers etc.       |
| **White Text**    | `#FFFFFF` | 深色背景上的文字           |
| **Light Text**    | `#E5E7EB` | Secondary text on dark 背景 |
| **English Gray**  | `#94A3B8` | 英文副标题                  |

### Gradients

| Name             | Start     | Middle    | End       | 用途                  |
| ---------------- | --------- | --------- | --------- | ---------------------- |
| Cover Gradient   | `#1E3A5F` | `#2E5C8E` | `#3D8B7A` | Cover/chapter page BG  |
| Ending Gradient  | `#1E3A5F` | `#2E5C8E` | `#3D8B7A` | Ending 页面背景 |

---

## 四、字体系统

### 字体栈

**Chinese Font Stack**: `"PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif`

**English Font Stack**: `system-ui, -apple-system, sans-serif`

### 字号层级

| Level | 用途            | Size | Weight   | 行高 |
| ----- | ---------------- | ---- | -------- | ----------- |
| H1    | 封面主标题 | 52px | 粗体     | 1.2         |
| H2    | 页面主标题  | 32px | 粗体     | 1.3         |
| H3    | Section subtitle | 24px | 半粗体 | 1.3         |
| H4    | 卡片标题       | 20px | 半粗体 | 1.4         |
| Body  | 正文内容     | 18px | 常规  | 1.5         |
| Small | Annotations      | 14px | 常规  | 1.4         |

### 间距系统

| 用途              | 数值                     |
| ------------------ | ------------------------- |
| Base unit          | 8px                       |
| Element spacing    | 16px / 24px / 32px / 48px |
| Paragraph spacing  | 24px                      |
| List item spacing  | 12px                      |
| Card inner padding | 24px                      |

---

## 五、页面结构

### 通用布局

| Area              | Position/Height | 说明                          |
| ----------------- | --------------- | ------------------------------------ |
| **Left Accent**   | x=0, w=8px      | Dominant color vertical bar (content pages) |
| **Top**           | y=60-120        | 页面标题 + 英文副标题        |
| **Divider**       | y=125-130       | Decorative divider line              |
| **内容区**  | y=130-640       | 主要内容区 (510px height)     |
| **页脚**        | y=650-700       | 页码, chapter info            |

### 装饰设计

- **Left Accent Bar**: Dominant color (`#2E5C8E`), width 8px, spanning the full page height
- **Divider Line**: Light gray (`#E5E7EB`), width 1-2px
- **Circle Decorations**: Low-opacity circles for chapter page/cover 背景

---

## 六、页面类型

### 1. 封面页 (01_cover.svg)

- **Background**: Blue-green gradient (`#1E3A5F` → `#2E5C8E` → `#3D8B7A`)
- **Decoration**: Optional 背景 image (opacity=0.25)
- **标题 Area**: Centered, main title 52px + subtitle 28px
- **English 标题**: Light gray, 24px
- **Decorative Line**: Warm orange thin line, 200px wide
- **Bottom**: Quote card (semi-transparent 背景 + healing green left border)
- **Tags**: Keyword tags (semi-transparent capsules)
- **Page Number**: Bottom-right, 14px

### 2. 目录页 (02_toc.svg)

- **Background**: Cloud white (`#F8FAFC`)
- **Left Accent**: Dominant color 8px vertical bar
- **标题**： "内容s Overview"
- **Left Side**: Five-chapter list (colored number blocks + title + description)
  - Chapter 1: Dominant blue `#2E5C8E`
  - Chapter 2: Healing green `#3D8B7A`
  - Chapter 3: Warm orange `#E07843`
  - Chapter 4: Cool gray-blue `#64748B`
  - Chapter 5: Trauma red `#B54545`
- **Right Side**: Learning objectives card
- **Center**: Dashed divider

### 3. 章节页 (02_chapter.svg)

- **Background**: Blue-green gradient
- **Decoration**: Multiple low-opacity concentric circles, diagonal line accents
- **Large Number**: 120px, semi-transparent white, centered
- **Chapter Label**: Capsule shape "CHAPTER X"
- **标题**： 48px white bold
- **副标题**: 24px light gray English
- **Decorative Line**: Warm orange thin line, 200px
- **Quote**: Semi-transparent quote card
- **Keywords**: Bottom tag group
- **Page Number**: Bottom-right

### 4. 内容页 (03_content.svg)

- **Background**: Cloud white
- **Left Accent**: Dominant blue 8px vertical bar
- **标题 Area**: 主标题 28px + 英文副标题 16px
- **Divider**: Decorative line below title
- **内容 Area**: Flexible layout (three-column / left-right split / single column)
- **Card Styles**:
  - 白色背景 + light gray border
  - Border radius 12-16px
  - Colored top bar / colored left border
- **Bottom Tip**: Light gray 背景 tip bar (optional)
- **Page Number**: Bottom-right

### 5. 结束页 (04_ending.svg)

- **Background**: Blue-green gradient
- **Decoration**: Network connection graph (dots + lines)
- **标题**： 主标题 56px + subtitle 28px
- **English**: Light gray English title
- **Decorative Line**: Warm orange thin line, 300px
- **信息 Area**: Semi-transparent info card
- **Bottom**: Copyright information

---

## VII. 版式模式

### 7.1 三列并排布局（对比 / 发现）

```
[Card 1: 360px] [Gap: 40px] [Card 2: 360px] [Gap: 40px] [Card 3: 360px]
```

- Each card: Colored top bar + icon + number + title + content + bottom tag
- Suitable for: Three findings, three-type comparisons

### 7.2 Left-Right Split

```
[Left Column: 560px] [Gap: 60px] [Right Column: 580px]
```

- Left side: Concepts/theory
- Right side: Application/practice
- Suitable for: Concept explanations, therapeutic relationships

### 7.3 Vertical Stack (Hierarchical Structure)

```
┌─────────────────────────────────┐
│       Top Layer: Metacognition   │
├─────────────────────────────────┤
│       Representation Layer       │
├─────────────────────────────────┤
│       Affective Layer            │
├─────────────────────────────────┤
│       Somatic Layer              │
└─────────────────────────────────┘
```

- Suitable for: Self-development hierarchy, theoretical frameworks

### 7.4 Attachment Type Quadrant

| Secure (Green) | Avoidant (Gray-Blue) |
| Anxious-Ambivalent (Orange) | Disorganized (Red) |

- Each card uses the corresponding attachment type color scheme

---

## VIII. Visual Element Specifications

### 8.1 Card Styles

```xml
<!-- Standard info card -->
<rect rx="12" fill="#FFFFFF" stroke="#E5E7EB" stroke-width="1"/>

<!-- Emphasis card (with left border) -->
<rect rx="12" fill="#FFFFFF"/>
<rect x="0" width="4" fill="#2E5C8E" rx="2"/>

<!-- Colored top card -->
<rect rx="16" fill="#FFFFFF" stroke="#E5E7EB" stroke-width="1"/>
<rect rx="16" width="100%" height="80" fill="#2E5C8E"/>  <!-- Top color block -->
```

### 8.2 Number Blocks

```xml
<path fill="#2E5C8E" d="M8,0 H42 A8,8 0 0 1 50,8 V42 A8,8 0 0 1 42,50 H8 A8,8 0 0 1 0,42 V8 A8,8 0 0 1 8,0 Z"/>
<text x="25" y="33" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">1</text>
```

### 8.3 Tag Styles

```xml
<!-- Capsule tag -->
<path fill="#E0F2FE" d="M33,0 H107 A13,13 0 0 1 120,13 V13 A13,13 0 0 1 107,26 H33 A13,13 0 0 1 20,13 V13 A13,13 0 0 1 33,0 Z"/>
<text x="70" y="18" font-size="13" fill="#2E5C8E" text-anchor="middle">Tag Text</text>
```

### 8.4 Quote Cards

```xml
<!-- Semi-transparent quote card -->
<path fill="#FFFFFF" fill-opacity="0.1" d="..."/>
<path fill="#3D8B7A" d="..." rx="2"/>  <!-- Left accent bar -->
<text font-style="italic" fill="#E5E7EB">Quote content</text>
```

### 8.5 Divider Lines

```xml
<line x1="60" y1="Y" x2="1240" y2="Y" stroke="#E5E7EB" stroke-width="2"/>
```

---

## 九、图标使用

### 占位符格式

```xml
<use data-icon="icon-name" x="X" y="Y" width="32" height="32" fill="COLOR"/>
```

### 常用图标映射

| Concept              | Icons                     |
| -------------------- | ------------------------- |
| Attachment/Bonding   | `heart`, `link`           |
| Secure Base          | `home`, `shield-check`    |
| Mentalization        | `brain`, `lightbulb`      |
| Affect Regulation    | `activity`, `sliders`     |
| Awareness            | `eye`, `compass`          |
| Trauma               | `alert-triangle`, `zap`   |
| Repair               | `refresh-cw`, `tool`      |
| Development          | `trending-up`, `layers`   |

---

## 十、SVG 技术约束

### viewBox Specification

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
```

### Prohibited Features (Blocklist)

| Category           | Prohibited Items                        |
| ------------------ | --------------------------------------- |
| **Clipping/Masking** | `clipPath`, `mask`                    |
| **Style System**   | `<style>`, `class` (`id` inside `<defs>` is allowed) |
| **Structure/Nesting** | `<foreignObject>`                   |
| **Text/Font**      | `textPath`, `@font-face`               |
| **Animation/Interaction** | `<animate*>`, `<set>`, `on*`    |
| **Markers/Arrows** | `marker`, `marker-end`                  |

### PPT 兼容性规则

| Prohibited                         | Correct Alternative                                    |
| ---------------------------------- | ------------------------------------------------------ |
| `fill="rgba(255,255,255,0.1)"`     | `fill="#FFFFFF" fill-opacity="0.1"`                    |
| `stroke="rgba(0,0,0,0.5)"`        | `stroke="#000000" stroke-opacity="0.5"`                |
| `<g opacity="0.2">...</g>`        | Set `opacity` / `fill-opacity` on each child element individually |

---

## 十一、占位符说明

| 占位符 | 用途 |
| -------------------- | -------------------- |
| `{{TITLE}}`          | 主标题           |
| `{{SUBTITLE}}`       | 副标题             |
| `{{TITLE_EN}}`       | English title        |
| `{{PAGE_TITLE}}`     | 内容 page title   |
| `{{CONTENT_AREA}}`   | 可灵活编排的内容区 |
| `{{CHAPTER_NUM}}`    | Chapter number       |
| `{{CHAPTER_TITLE}}`  | 章节标题        |
| `{{CHAPTER_EN}}`     | Chapter English title |
| `{{QUOTE}}`          | Quote content        |
| `{{QUOTE_AUTHOR}}`   | Quote author         |
| `{{PAGE_NUM}}`       | 页码          |
| `{{COVER_BG_IMAGE}}` | 封面背景 image path |
| `{{TOC_ITEM_N_TITLE}}` | 目录项标题     |
| `{{TOC_ITEM_N_DESC}}`  | 目录项说明 |
| `{{THANK_YOU}}`      | Thank-you message    |
| `{{CONTACT_INFO}}`   | Primary contact info |

---

## 十二、使用说明

### Template Usage Steps

1. **Copy Template**: Copy template files to the project `templates/` directory
2. **Replace Placeholders**: Replace `{{}}` placeholders with actual content
3. **Adjust Colors**: Fine-tune the color scheme based on the theme
4. **Generate 内容**: Use the Executor role to generate specific pages
5. **Post-process**: Run `finalize_svg.py` to complete image embedding

### Applicable Topics

- Psychotherapy and counseling
- Attachment theory research
- Developmental psychology
- Clinical case analysis
- Academic training lectures
- Psychology course instruction
