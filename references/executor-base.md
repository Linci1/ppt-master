# Executor Common Guidelines

> Style-specific content is in the corresponding `executor-{style}.md`. Technical constraints are in shared-standards.md. In-process page review discipline is in `executor-visual-review.md`.

---

## 0. Project-level Planning Inputs (Mandatory Pre-read)

Before generating the first SVG page, the Executor must check whether the project contains the following planning artifacts:

- `project_brief.md`
- `notes/template_domain_recommendation.md`
- `notes/storyline.md`
- `notes/page_outline.md`

If they exist, they are **mandatory execution inputs**.

Required behavior:

- `project_brief.md`: use it to lock audience, goal, priorities, tone, and constraints
- `notes/template_domain_recommendation.md`: use it to confirm template/domain intent before page generation
- `notes/storyline.md`: use it to preserve chapter rhythm and cross-page progression
- `notes/page_outline.md`: use it as the page-level source of truth for intent, proof target, and role

The Executor must not treat these files as optional inspiration. They define the planned deck logic that SVG execution must implement.

### Page-level binding rule

For every non-fixed page, before generating the page draft, the Executor should be able to answer:

- Which entry in `notes/page_outline.md` this page corresponds to
- What the page intent is
- What the proof goal is
- Whether the page is meant to be simple or complex

If that mapping cannot be established, the Executor should pause and repair the planning layer before continuing.

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
- **Template-local QA profiles**: If `templates/qa_profile.md` or the template Design Spec defines fixed skeleton / protected zones, those rules override improvisation. Keep logo/footer/TOC scaffold and other protected elements stable; place creativity inside the allowed content area.

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
- **Follow planning structure**: If `notes/page_outline.md` exists, page generation must follow its page intent / proof goal / role definition instead of improvising a new deck structure on the fly
- **Flexible within fixed skeleton**: Preserve template-stable elements such as logo, footer accents, TOC scaffold, protected masks, and fixed anchor coordinates. Use flexibility for cards, charts, image treatment, emphasis hierarchy, and narrative framing inside the content area
- **Main-agent ownership**: SVG generation must be performed by the current main agent, not delegated to sub-agents, because each page depends on shared upstream context and cross-page visual continuity
- **Generation rhythm**: First lock the global design context, then generate pages sequentially one by one in the same continuous context; grouped page batches (for example, 5 pages at a time) are not allowed
- **Per-page review gate**: After generating each page draft, immediately review it before continuing. Do not postpone readability/layout review until the end of the deck
- **Phased batch generation** (recommended):
  1. **Visual Construction Phase**: Generate all SVG pages continuously in sequential page order, ensuring high consistency in design style and layout coordinates (Visual Consistency)
  2. **Logic Construction Phase**: After all SVGs are finalized, batch-generate speaker notes to ensure narrative coherence (Narrative Continuity)
- **Technical specifications**: See [shared-standards.md](shared-standards.md) for SVG technical constraints and PPT compatibility rules
- **Visual depth**: Use filter shadows, glow effects, gradient fills, dashed strokes, and gradient overlays from shared-standards.md to create layered depth — flat pages without elevation or emphasis look unfinished

### 3.1 In-process Visual Review Gate (Mandatory)

After each page draft is generated, the Executor **must** check the current page against `executor-visual-review.md` before moving on.

In addition, check whether the page still matches its corresponding `notes/page_outline.md` entry:

- page role
- page intent
- proof goal
- expected density / complexity level
- whether the chosen structure still matches the planned page type

Minimum review items:

- Chinese text segmentation and reading rhythm
- Whether text is too close to card edges or canvas edges
- Whether card content is likely to overflow or already looks cramped
- Whether the Chaitin logo, page number, or footer decoration visually conflicts with body content
- Whether takeaway strips / summary bands are clearly separated from lower body modules
- Whether information density is suitable for a presentation page
- Whether the page should be trimmed or relaid out instead of keeping all drafted content
- Whether the page still matches the same-family structure already established elsewhere in the deck

**Important**:

- These checks are part of the generation path itself, not a post-hoc QA pass
- If a page fails review, fix that page immediately in the same context
- Speaker notes generation may begin only after all pages have passed this gate
- During the audit stage, run `svg_quality_checker.py`; its heuristic warnings should be used to catch Chinese readability, edge-pressure, card-overflow, takeaway/body separation, and TOC consistency risks before export

### 3.2 Deck-level Consistency Audit (Mandatory)

After all page drafts have passed the per-page gate, but before the deck is considered ready for export, the Executor **must** perform a cross-page audit across the whole deck.

Minimum deck-level checks:

- TOC structure is consistent across all directory cards
- Same-family pages use one stable structure instead of drifting page by page
- Body-page starting baselines and spacing logic do not visibly jump between adjacent pages
- Pages that share takeaway strips also share a clean separation rule between upper and lower layers
- Pages with excessive density are identified for trimming, splitting, or relayout before export

**Important**:

- This is a deck review, not a single-page review
- A page may individually pass yet still fail this cross-page audit
- Speaker notes generation may begin only after both the per-page gate and the deck-level consistency audit are complete

### SVG File Naming Convention

File naming format: `<number>_<page_name>.svg`

- **Chinese content** → Chinese naming: `01_封面.svg`, `02_目录.svg`, `03_核心优势.svg`
- **English content** → English naming: `01_cover.svg`, `02_agenda.svg`, `03_key_benefits.svg`
- **Number rules**: Two-digit numbers, starting from 01
- **Page name**: Concise and descriptive, matching the page title in the Design Specification & Content Outline

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

**Template-local icons — Image reference method**:

Some templates bundle their own icons in `images/icons/` (e.g., security_service template). These icons are **NOT** in the global icon library and are NOT accessed via `<use data-icon>`. Instead, use the `<image>` tag:

```xml
<image href="../images/icons/icon_shield.svg" x="100" y="200" width="48" height="48"/>
```

> ⚠️ **Template icon rule**: If the project's `design_spec.md` includes Section X「Template Local Assets」or similar template-specific icon documentation, Executor **must** use `<image>` tags with paths like `../images/icons/{name}.svg`. Do NOT use `<use data-icon>` for template-local icons — they are not registered in the global icon index.

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

After **all SVG pages are generated, visually reviewed, deck-audited, and finalized**, enter the "Logic Construction Phase" and generate the complete speaker notes document in `notes/total.md`.

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

> **Auto-continuation**: After Visual Construction Phase (all SVG pages, each having passed the in-process visual review gate and deck-level consistency audit) and Logic Construction Phase (all notes) are complete, the Executor proceeds directly to the post-processing pipeline.

**Post-processing & Export** (see [shared-standards.md](shared-standards.md)):

```bash
# 1. Split speaker notes
python3 scripts/total_md_split.py <project_path>

# 2. SVG post-processing (auto-embed icons, images, etc.)
python3 scripts/finalize_svg.py <project_path>

# 3. SVG audit
python3 scripts/svg_quality_checker.py <project_path> --format <format>

# 4. Export PPTX
python3 scripts/svg_to_pptx.py <project_path> -s final
# Default: generates native shapes (.pptx) + SVG reference (_svg.pptx)
```

After export, the Executor must also run the **Exported PPT Review Gate** defined in `references/exported-ppt-review.md`:

- Review the actual exported PPT appearance, not just the SVG source
- If exported PPT review reveals issues, fix the source SVG files in `svg_output/`
- Re-run post-processing, SVG audit, export, and exported-PPT review until the deck passes
