> Merged from standalone skill: ppt-template-productization (2026-04-26)

# PPT Template Productization

Use this when the user does **not** just want to fix one deck, but wants to make a PPT/template system reusable across similar documents.

Typical triggers: "make this template generic", "not just this project", "reverse-engineer this deck into reusable rules", "build a page-type system / routing rules / copy rules".

Do **not** use for simple slide polishing or one-off PPT edits.

## Goal

Turn a mature reference deck into a reusable specification that can drive generation for a document family.

## Core idea

A reusable PPT template is **not** one shell page reused everywhere. It should be modeled as:
1. Brand framework
2. Page-type system
3. Component contracts
4. Copy contracts
5. Rhythm/composition rules
6. Quality acceptance rules

## Recommended workflow

### 1. Reverse-engineer the mature PPT first

Inspect the mature reference deck and extract: chapter rhythm, page families, title patterns, evidence/case density, backing/credibility section patterns, heavy vs light page alternation.

Focus on why the deck feels mature: fewer visible template/protocol artifacts, richer page-family variation, more evidence/case/backing density, better chapter transitions, stronger business-language titles.

### 2. Produce a page-family map

Classify into page families: cover, toc, chapter opener, overview/judgment, scope/target, attack chain / path, issue breakdown, case/evidence, governance/remediation, backing/credentials, ending.

Identify **reading role**, not just visual style.

### 3. Build a page_type_registry

Define each reusable page type with: `page_type`, `role`, `applicable_when`, `required_slots`, `optional_slots`, `forbidden_slots`, `default_layout_family`, `copy_rules`, `visual_rules`, `acceptance_rules`.

High-value page types for security/service-report decks: cover_page, toc_page, chapter_page, overview_page, scope_target_page, attack_chain_page, path_analysis_page, issue_breakdown_page, impact_summary_page, evidence_case_page, evidence_gallery_page, governance_overview_page, remediation_action_page, timeline_roadmap_page, owner_matrix_page, capability_backing_page, ending_page.

### 4. Build routing_rules

Use a two-layer routing model:
1. First classify content block into semantic class: opening, overview, scope, path, issue, evidence_case, governance, backing
2. Then resolve into concrete `page_type`

Good routing signals: title keywords, body keywords, stage/step structure, evidence/screenshots, case/story-like, owner/timeline/remediation oriented, chapter position.

Important priority lessons:
- Case beats issue when there is real story structure
- Path beats overview when there is clear multi-stage flow
- Governance overview beats single action when content is multi-phase/multi-owner
- Evidence gallery beats narrative case when screenshots are primary
- Specific backing subtypes beat generic backing pages

### 4.5 Audit source-material consumption

Before blaming prompt quality, verify whether the generated deck is actually consuming source materials (especially screenshots/evidence images).

Recommended audit sequence:
- count image references in normalized source markdown
- inventory extracted source images
- inspect final SVG for actual page-level image references
- map each source image back to its nearest section heading
- compare `page -> expected semantic role -> available image pool -> actual consumption`

Strong heuristic: attack/path pages should usually be strong-bound evidence pages, not optional-image text pages.

### 5. Build copy_contracts

Define: title rules, module naming rules, closure rules, forbidden protocol words, page-type-specific sentence patterns.

Strong rules:
- Remove protocol/internal terms from visible slides
- Prefer business-facing labels over internal slot names
- One page = one judgment
- Closure should advance to action/management meaning, not restate the title
- Titles should be viewpoint-driven when possible

Recommended module vocabulary: 核心判断, 关键发现, 演练范围, 目标说明, 攻击入口, 关键路径, 核心问题, 主要原因, 业务影响, 实施动作, 运营成效, 整改目标, 关键动作, 责任分工, 预期效果.

### 6. Build rhythm_profiles

Typical modes: executive short, standard review, case-heavy, capability-pitch.

Composition rules: every major chapter gets a chapter opener; each major theme should have overview -> breakdown -> case/evidence; avoid long runs of identical page types; alternate heavy and light pages.

### 7. Define quality acceptance

3-layer model:
- L1 technical pass: no overflow/cropping/resource/footer issues
- L2 productized pass: no protocol words, no obvious template smell
- L3 mature-deck pass: chapter rhythm, evidence density, backing credibility, page-family variation

## Concrete PPTX-to-Layout Extraction Workflow

### Step A: Analyze PPTX structure with python-pptx

```python
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

prs = Presentation("target.pptx")
for i, slide in enumerate(prs.slides):
    for shape in slide.shapes:
        # Classify: PICTURE, GROUP, TEXTBOX, AUTO_SHAPE, PLACEHOLDER
        # Record: shape.left, shape.top, shape.width, shape.height (EMU)
```

Page type heuristics:
- Cover: first slide, large background + centered bold title
- TOC: second slide, numbered items
- Chapter dividers: dark background + large chapter number
- Content pages: high shape count, white background
- Ending: last slide, dark background + "Thanks"

### Step B: Extract images

Compare background images across slides with MD5 — many PPTs reuse the same dark background. Extract two logo variants: dark-text logo for white pages, light-text logo for dark pages.

### Step C: Convert EMU to SVG pixels

```
SVG canvas: 1280 x 720 (ppt169 format)
Scale: 1280 / 12192000 ≈ 0.000105 per EMU
```

> **CRITICAL** — Geometric Parameters Are Layout-Specific, Not Reusable
>
> When adapting an extracted SVG variant to a different layout, **never copy the source's geometric parameters** (XS array, column widths, row Y coordinates, card dimensions).
>
> Correct approach: treat every layout adaptation as a fresh design:
> 1. Determine target layout structure
> 2. Calculate XS, YS, CARD_W, CARD_H, GAP_X, GAP_Y from scratch
> 3. Preserve only: color scheme, content framework, and general visual style

### Step D: Identify the color scheme

Extract from: title text runs, accent/decorative shapes, background fills, theme colors.

### Step E: Build the layout directory

Standard structure:
```
chaitin_anfu/
├── design_spec.md
├── 01_cover.svg
├── 02_toc.svg
├── 02_chapter.svg
├── 03_content.svg
├── 04_ending.svg
├── bg_dark_tech.jpeg
├── chaitin_logo_dark.png
└── chaitin_logo_light.png
```

### Step F: Register in layouts_index.json

Update: categories, quickLookup, layouts entry, meta.total.

### Step G: Validate

Checklist: all standardFiles present, asset files exist, placeholders match design_spec, content pages have brand_locked/body_safe_region markers, valid JSON, layout name in all three sections.

## Recommended implementation batches

### Batch 1 — Freeze the abstraction layer
Build: page_type_registry, slot_contracts, copy_contracts, quality_acceptance, naming separation.

### Batch 2 — Semantic chunking and routing
Build: document_chunker, routing_rules, page_router.
Pass: core blocks route reliably; overview_page is not catch-all sink.

### Batch 3 — Slot building and copy cleaning
Build: slot_builder, title_rewriter, module_label_rewriter, closure_rewriter, protocol_leakage_cleaner.
Pass: no protocol words visible; titles read like business/judgment titles.

### Batch 4 — Page-family realization and rhythm composition
Build: core layout_family implementations, rhythm_profiles, rhythm_composer.
Pass: page types visually distinct; full decks have chapter rhythm.

### Batch 5 — Acceptance automation
Build: L1 technical checker, L2 product checker, deck-level checker, acceptance_report, rework rules.

### Batch 6 — Multi-sample validation
Validate on multiple document types. Pass: several types reach stable L2 quality.

## Pitfalls

- Do not confuse a polished one-off deck with a reusable template system
- Do not keep protocol vocabulary visible in final slides
- Do not let overview pages swallow everything
- Do not copy geometric parameters from an extracted SVG variant when adapting to different layout
