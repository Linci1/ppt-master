> Merged from standalone skill: ppt-master-body-layout-variation (2026-04-26)

# Body Layout Variation — Diagnosis and Refactoring

Use this reference when a ppt-master generated deck has many body slides that look nearly identical even though their text differs, especially in security report or attack-summary decks generated from SVG intermediates.

Typical signals:
- Multiple正文页 share the same visual skeleton with only text swapped
- `svg_output/` and `svg_final/` both exist
- `svg_final/` contains namespace changes, line wraps, or text splitting that makes direct parsing brittle

## Core principle

Treat `svg_output/` as the parsing source of truth. Use `svg_final/` only as a write target after regeneration.

Why: `svg_final/` may introduce `svg:` namespaces, split sentences into multiple text nodes, or reflow text differently.

## Workflow

### 1. Identify repeated body-page groups

Inspect a handful of SVGs under `svg_output/`. Group pages by repeated body skeleton rather than title.

Common patterns:
- overview pages: summary block + bullet list + closure strip
- path pages: summary block + 3-step chain + side impact panel
- remediation pages: summary block + 3 action rows/cards + side ownership panel

### 2. Verify the real text-node order before editing

Do not assume all files use the same exact coordinates. Dump ordered `<text>` nodes for representative files. Prefer extracting content by node order within a known group instead of hard-coding one coordinate set.

### 3. Rebuild only the body area

Preserve the brand shell: top green bar, logo image, slide title, divider line, footer accent line, page number. Replace only the content region between the title divider and footer accent.

### 4. Apply distinct layouts per group

- overview group: asymmetric summary-plus-detail composition
- path group: directional timeline/pathway with visible rhythm
- remediation group: roadmap/priority-board or row-based action board

#### 4.1 Second de-homogenization pass

If the first pass still feels samey, run a second pass:
- first pass: split obvious families (overview/path/remediation)
- second pass: split still-repetitive members inside those families

#### 4.2 Make the layout match the page's narrative

Structural difference alone is not enough; aim for page-specific visual semantics:
- attack path page -> exposure chain, hub-and-spoke risk map, or route diagram
- issue overview page -> cause map / theme board
- audit issue page -> observability-gap staircase
- port restriction page -> control gate / chokepoint diagram
- password issue page -> risk amplifier layout
- awareness issue page -> social-engineering chain
- remediation page -> governance board, phased ramp, perimeter gate, operating cadence panel, or role split board

### 5. Write results to both directories

Generate from `svg_output/` data. Write the rebuilt SVG to both `svg_output/` and `svg_final/`.

### 6. Validate structure, not just text

Compare body fingerprints across pages using counts of `rect`, `circle`, `path`, or a body hash. Confirm the brand frame still exists on every rewritten page.

## Recommended extraction approach

Use ordered `<text>` nodes from `svg_output/`:
- read all `<text x="..." y="...">...</text>` in document order
- map indexes to semantic fields for that page group
- avoid fragile regexes that depend on one exact coordinate or on `<tspan>` layout

## Pitfalls

- Do not parse `svg_final/` first if `svg_output/` exists
- Do not assume all overview/path/remediation pages share identical coordinates
- Do not rewrite title/footer shell unless intentionally changing branding
- Do not validate only by eyeballing one slide; compute simple structure fingerprints across the whole group
- If `search_files` is unreliable, fall back to `find`, Python, and direct file reads

## Full-deck audit after body-page cleanup

After obvious正文重复页 are fixed, do a second-pass audit:

What often remains repetitive:
- chapter opener pages that reuse the same dark-background + big-number + wave template
- overview pages that still read as generic summary card
- chain-like issue pages that share too much left-to-right numbered-flow DNA

Recommended prioritization:
1. whole-deck structure scan on all `svg_final/*.svg`
2. identify clusters by body counts/signatures
3. visually sample only the suspicious clusters
4. prioritize: chapter openers first, then high-level overview, then near-duplicate body pages

Judgment rule: if a page still reads like "same template, swapped title", it should be redesigned.

## Export and acceptance follow-up

After SVG rewrites, regenerate fresh PPTX from `svg_final/`:

```bash
python3 /path/to/scripts/svg_to_pptx.py <project_path> -s final
```

Verification pattern:
```bash
python3 - <<'PY'
from zipfile import ZipFile
import re
p='path/to/exported.pptx'
pat=re.compile(r'<a:t>(.*?)</a:t>')
with ZipFile(p) as z:
    for idx in [9,10,20,21,22,23,24]:
        xml=z.read(f'ppt/slides/slide{idx}.xml').decode('utf-8','ignore')
        texts=pat.findall(xml)
        print('slide', idx, 'shapes', xml.count('<p:sp>'), 'texts', len(texts), 'preview', ' / '.join(texts[:10]))
PY
```

## Visual spot-check shortcuts

On macOS:
```bash
qlmanage -t -s 1280 -o /tmp/ppt_svg_check <svg_path>
```

Two-stage acceptance gate:
- stage 1: structural clustering/fingerprints identify suspiciously similar pages
- stage 2: rendered PNG spot-checks verify pages also feel different in composition

## Minimal validation checklist

For each rewritten page, confirm:
- logo still references `assets/chaitin_logo.png`
- title still exists at the top
- footer green accent line still exists
- page number still exists
- body hash differs across pages where content differs
- group-level geometry differs across overview/path/remediation families
