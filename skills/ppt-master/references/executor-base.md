# Executor Common Guidelines

> Style-specific content is in the corresponding `executor-{style}.md`. Technical constraints are in shared-standards.md.

---

## 1. Template Adherence Rules

If template files exist in the project's `templates/` directory, the template structure must be followed:

| Page Type | Corresponding Template | Adherence Rules |
|-----------|----------------------|-----------------|
| Cover | `01_cover.svg` | Inherit background, decorative elements, layout structure; replace placeholder content |
| Chapter | `02_chapter.svg` | Inherit numbering style, title position, decorative elements |
| Content | `03_content.svg` | Inherit header/footer styles; **content area may be freely laid out** |
| Ending | `04_ending.svg` | Inherit background, thank-you message position, contact info layout |
| TOC | `02_toc.svg` | **Optional**: Inherit TOC title, list styles |

### Page-Template Mapping Declaration (Required Output)

Before generating each page, you must explicitly output which template (or "free design") is used:

```
📝 **Template mapping**: `templates/01_cover.svg` (or "None (free design)")
🎯 **Adherence rules / layout strategy**: [specific description]
```

- **Content pages**: Templates only define header and footer; the content area is freely laid out by the Executor
- **No template**: Generate entirely per the Design Specification & Content Outline

---

## 2. Design Parameter Confirmation (Mandatory Step)

> Before generating the first SVG page, you **must review the key design parameters from the Design Specification & Content Outline** to ensure all subsequent generation strictly follows the spec.

Must output confirmation including: canvas dimensions, body font size, color scheme (primary/secondary/accent HEX values), font plan.

**Why is this step mandatory?** Prevents the "spec says one thing, execution does another" disconnect.

---

## 3. Execution Guidelines

- **Proximity principle**: Place related elements close together to form visual groups; increase spacing between unrelated groups to reinforce logical structure
- **Absolute spec adherence**: Strictly follow the color, layout, canvas format, and typography parameters in the spec
- **Follow template structure**: If templates exist, inherit the template's visual framework
- **Main-agent ownership**: SVG generation must be performed by the current main agent, not delegated to sub-agents, because each page depends on shared upstream context and cross-page visual continuity
- **Generation rhythm**: First lock the global design context, then generate pages sequentially one by one in the same continuous context; grouped page batches (for example, 5 pages at a time) are not allowed
- **Phased batch generation** (recommended):
  1. **Visual Construction Phase**: Generate all SVG pages continuously in sequential page order, ensuring high consistency in design style and layout coordinates (Visual Consistency)
  2. **Logic Construction Phase**: After all SVGs are finalized, batch-generate speaker notes to ensure narrative coherence (Narrative Continuity)
- **Technical specifications**: See [shared-standards.md](shared-standards.md) for SVG technical constraints and PPT compatibility rules
- **Visual depth**: Use filter shadows, glow effects, gradient fills, dashed strokes, and gradient overlays from shared-standards.md to create layered depth — flat pages without elevation or emphasis look unfinished

### SVG File Naming Convention

File naming format: `<number>_<page_name>.svg`

- **Chinese content** → Chinese naming: `01_封面.svg`, `02_目录.svg`, `03_核心优势.svg`
- **English content** → English naming: `01_cover.svg`, `02_agenda.svg`, `03_key_benefits.svg`
- **Number rules**: Two-digit numbers, starting from 01
- **Page name**: Concise and descriptive, matching the page title in the Design Specification & Content Outline

---

### 3.2 Text Wrapping & Character Limit Rules (MANDATORY)

**⚠️ SVG does NOT support auto-wrapping** — `<foreignObject>` is FORBIDDEN. All line breaks must be manually calculated.

**Chinese text per-line character limit**:
| Font Size | Approx. Char Width | Max Chars per Line (1000px container) |
|-----------|-------------------|----------------------------------------|
| 16px | ~16px | 55-60 chars |
| 15px | ~15px | 60-65 chars |
| 14px | ~14px | 65-70 chars |
| 13px | ~13px | 70-75 chars |
| 12px | ~12px | 75-80 chars |
| 11px | ~11px | 85-90 chars |

**Rules**:
1. **Measure before placing**: Estimate if text will overflow container width
2. **Pre-split long text**: Break long paragraphs into multiple `<tspan>` lines manually
3. **Use `dy` for line spacing**: `<tspan dy="0">line1</tspan><tspan dy="24">line2</tspan>`
4. **Reserve breathing room**: Keep max chars 10-15% below theoretical limit for safety
5. **Title text**: Keep titles under 20 chars; if longer, split into subtitle + main title

**Example** — Correct:
```xml
<text x="168" y="335" font-size="13">
  <tspan>系统灌装完成，按手册配置，发现实际与手册描述冲突</tspan>
</text>
<!-- Becomes two lines if > 70 chars: -->
<text x="168" y="330" font-size="13">
  <tspan>系统灌装完成，按手册配置，发现实际</tspan>
  <tspan dy="22">与手册描述冲突</tspan>
</text>
```

**Example** — Wrong (will overflow):
```xml
<!-- Single tspan with no width check — LIKELY TO OVERFLOW -->
<tspan>遇到不懂的配置环节，未及时反馈，擅自判断盲目操作，进一步导致配置偏差扩大</tspan>
```

**Special attention for**:
- Bullet point descriptions (sub-text under titles)
- Timeline event details
- Multi-point summary cards
- Any text in narrow columns

---

### 3.3 Card Grid Layout Rules (MANDATORY for Multi-Card Pages)

**⚠️ Grid imbalance and asymmetric spacing make pages look unprofessional.**

When designing multi-card layouts (e.g., 2x3 grid, 2x2 grid), follow these rules strictly:

**Rule 1: Horizontal and Vertical Spacing Must Be Consistent**
```
Formula: card_width = (container_width - margin*2 - gap*(n-1)) / n
Gap between同行卡片间距 must ≈ 上下行间距
If horizontal gap = 29px, vertical gap should also be ~29px (not 20px)
```

**Rule 2: Accent Bar + Number + Title Must Form a Unified Header Block**
```
❌ WRONG — accent bar (6px) feels disconnected from number (y=190):
<rect y="150" height="6" />  ← 6px is too thin
<text y="190">01</text>        ← 40px gap to accent bar

✓ CORRECT — treat as one header module:
<rect y="150" height="50" />  ← taller accent zone
<text y="185">01</text>         ← number inside accent zone
<text y="215">Title</text>         ← title immediately below
```

**Rule 3: Symmetric Left/Right Internal Padding**
```
Card x=56, width=370
If left padding = 20px (text x=76)
Then right padding should also be ~20px
Text max width = 370 - 20 - 20 = 330px
This ensures visual centering of text within card
```

**Rule 4: Vertical Rhythm — Distribute Space Evenly**
```
Card height = 200px
Header zone (accent bar + number + title): ~70px
Content zone: ~80px
Footer breathing room: ~50px
Keep top tight and bottom generous, but not excessive
```

**Rule 5: Multi-Row Cards Must Maintain Grid Alignment**
```
Row 1: 3 cards at x=56, 455, 854
Row 2: 2 cards — do NOT leave right side empty
Use placeholder cards or symmetric layout adjustment:
Option A: Center the 2 cards (x=260, 660)
Option B: Use empty placeholder card to maintain right alignment
Option C: Increase card width to fill space
```

**Rule 6: Content Width Pre-Check**
```
Before placing text, calculate:
available_width = card_width - left_padding - right_padding
For font-size 13px Chinese: ~13 chars per line max in narrow cards
For font-size 12px Chinese: ~15 chars per line max
Always pre-split long descriptions into multiple tspan lines
```

**Visual Checklist Before Finalizing**:
- [ ] All同行间距 equal?
- [ ] All上下间距 equal (or proportionally consistent)?
- [ ] Accent bar, number, title aligned as one block?
- [ ] Left/right padding symmetric within each card?
- [ ] Text does not overflow card boundaries?
- [ ] Multi-row grid maintains right alignment?
- [ ] Vertical space distributed evenly (not top-heavy or bottom-heavy)?
- [ ] **Content does NOT overlap with logo/footer zone?**

---

### 3.4 Footer Zone Protection Rule (MANDATORY)

**⚠️ Content cards must not overlap with logo or bottom accent bar.**

Standard footer zone layout (for 720px height canvas):
```
y=0-150    : Header area (title + underline)
y=150-570  : Content area (cards, text, images)
y=570-640  : Safety margin (NO content here)
y=640      : Bottom accent bar
y=600-635  : Logo position
y=686      : Page number
```

**Content card bottom boundary formula:**
```
card_bottom_y + card_height ≤ 560  (leaves 10px gap before margin)
```

**Logo and footer elements must NOT be covered by content:**
```
Logo y=600, height=32 → logo occupies y=600 to y=632
Content cards must end at y ≤ 560 (before logo area)
Bottom accent bar at y=640 → content should not reach this
```

**If content is too long**, either:
1. Reduce card height
2. Use smaller font
3. Split into multiple cards/pages
4. Use shorter text

**Example — Wrong:**
```xml
<rect y="590" width="..." height="80"/>  ← Overlaps with logo at y=600
```

**Example — Correct:**
```xml
<rect y="550" width="..." height="80"/>  ← Ends at y=630, logo area clear
```


---

## 4. Icon Usage

Four approaches: **A: Emoji** (`<text>🚀</text>`) | **B: AI-generated** (SVG basic shapes) | **C: Built-in library** (`templates/icons/` 640+ icons, recommended) | **D: Custom** (user-specified)

**Built-in icons — Placeholder method (recommended)**:

```xml
<use data-icon="chart-bar" x="100" y="200" width="48" height="48" fill="#005587"/>
```

> No need to manually run `embed_icons.py`; `finalize_svg.py` post-processing tool will auto-embed icons.

**Common icons**: `chart-bar` `arrow-trend-up` `users` `cog` `circle-checkmark` `target` `clock` `file` `dollar` `lightbulb`

> ⚠️ **Icon validation rule**: If the Design Specification includes an icon inventory list, Executor may **only** use icons from that approved list. Using icon names not in the index is FORBIDDEN — verify against `templates/icons/icons_index.json` if uncertain.

Full index: `templates/icons/README.md`

---

## 5. Chart Reference

When the Design Spec includes a **VII. Chart Reference List**, read the referenced SVG templates from `templates/charts/` to understand common chart patterns.

**Adaptation rules**:
- **Must preserve**: Chart type (bar/line/pie etc.) as specified in the Design Spec
- **Must adapt**: Data values, labels, colors (match the project's color scheme), and dimensions to fit the page layout
- **May adjust**: Axis ranges, grid lines, legend position, spacing — as long as the chart remains accurate and readable
- **Must NOT**: Change chart type without Design Spec justification, or remove data points specified in the outline

> Chart templates: `templates/charts/` (33 types). Index: `templates/charts/charts_index.json`

---

## 6. Image Handling

Handle images based on their status in the Design Specification's "Image Resource List":

| Status | Source | Handling |
|--------|--------|----------|
| **Existing** | User-provided | Reference images directly from `../images/` directory |
| **AI-generated** | Generated by Image_Generator | Images already in `../images/`, reference directly |
| **Placeholder** | Not yet prepared | Use dashed border placeholder |

**Reference**: `<image href="../images/xxx.png" ... preserveAspectRatio="xMidYMid slice"/>`

**Placeholder**: Dashed border `<rect stroke-dasharray="8,4" .../>` + description text

---

## 7. Font Usage

Apply corresponding fonts for different text roles based on the font plan in the Design Specification & Content Outline:

| Role | Chinese Recommended | English Recommended |
|------|--------------------|--------------------|
| Title font | Microsoft YaHei / KaiTi / SimHei | Arial / Georgia |
| Body font | Microsoft YaHei / SimSun | Calibri / Times |
| Emphasis font | SimHei | Arial Black / Consolas |
| Annotation font | Microsoft YaHei / SimSun | Arial / Times |

---

## 8. Speaker Notes Generation Framework

### Task 1. Generate Complete Speaker Notes Document

After **all SVG pages are generated and finalized**, enter the "Logic Construction Phase" and generate the complete speaker notes document in `notes/total.md`.

**Why not generate page-by-page?** Batch-writing notes allows planning transitions like a script, ensuring coherent presentation logic.

**Format**: Each page starts with `# <number>_<page_title>`, separated by `---` between pages. Each page includes: script text (2-5 sentences), `Key points: ① ② ③`, `Duration: X minutes`. Except for the first page, each page's text starts with a `[Transition]` phrase.

**Basic stage direction markers** (common to all styles):

| Marker | Purpose |
|--------|---------|
| `[Pause]` | Whitespace after key content, letting the audience absorb |
| `[Transition]` | Standalone paragraph at the start of each page's text, bridging from the previous page |

> Each style may extend with additional markers (`[Interactive]`/`[Data]`/`[Scan Room]`/`[Benchmark]` etc.), see `executor-{style}.md`.

**Language consistency rule**: All structural labels and stage direction markers in speaker notes **MUST match the presentation's content language**. When the presentation content is non-English, localize every label — do NOT mix English labels with non-English content.

| English | 中文 | 日本語 | 한국어 |
|---------|------|--------|--------|
| `[Transition]` | `[过渡]` | `[つなぎ]` | `[전환]` |
| `[Pause]` | `[停顿]` | `[間]` | `[멈춤]` |
| `[Interactive]` | `[互动]` | `[問いかけ]` | `[상호작용]` |
| `[Data]` | `[数据]` | `[データ]` | `[데이터]` |
| `[Scan Room]` | `[观察]` | `[観察]` | `[관찰]` |
| `[Benchmark]` | `[对标]` | `[ベンチマーク]` | `[벤치마크]` |
| `Key points:` | `要点：` | `要点：` | `핵심 포인트:` |
| `Duration:` | `时长：` | `所要時間：` | `소요 시간:` |
| `Flex:` | `弹性：` | `調整：` | `조정:` |

> For languages not listed above, translate each label to the corresponding natural term in that language.

**Requirements**:

- Notes should be conversational and flow naturally
- Highlight each page's core information and presentation key points
- Users can manually edit and override in the `notes/` directory

### Task 2. Split Into Per-Page Note Files

Automatically split `notes/total.md` into individual speaker note files in the `notes/` directory.

**File naming convention**:

- **Recommended**: Match SVG names (e.g., `01_cover.svg` → `notes/01_cover.md`)
- **Compatible**: Also supports `slide01.md` format (backward compatibility)

---

## 9. Next Steps After Completion

> **Auto-continuation**: After Visual Construction Phase (all SVG pages) and Logic Construction Phase (all notes) are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export** (see [shared-standards.md](shared-standards.md)):

```bash
# 1. Split speaker notes
python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (auto-embed icons, images, etc.)
python3 scripts/finalize_svg.py <project_path>

# 3. Export PPTX
python3 scripts/svg_to_pptx.py <project_path> -s final
# Default: generates native shapes (.pptx) + SVG reference (_svg.pptx)
```
