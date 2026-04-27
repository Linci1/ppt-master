> Merged from standalone skill: ppt-master-brand-locked-flex-body (2026-04-26)

# Brand-Locked Flex-Body Generation

Use this reference when building or refactoring a PPT generation flow that must balance three constraints:

1. Fixed pages must remain structurally identical to the approved template.
2. Body pages must preserve the brand frame (background, logo, brand band, page number, footer) without inheriting rigid legacy body shells.
3. Content generation must follow page-type semantics and final delivery quality, not merely SVG validity.

## Core principles

- Respect the template on fixed pages.
- Respect the brand frame on body pages.
- Respect page-type semantics for content generation.
- Respect finished PPT quality for final delivery.

The goal is not to generate SVG that merely runs. The goal is to deliver PPT pages that are brand-stable, content-complete, narratively coherent, and ready to ship.

## Required deliverables per run

Every run should leave behind:
- Page classification results
- A page-level intermediate protocol object
- The current template's `frame/slot` constraints
- The generated copy structure
- A validation summary
- Export results
- If the run fails, the failure layer and rollback reason

## Acceptance gate

Do not mark the run deliverable unless all of the following are true:
- Fixed pages only receive field filling; no skeleton drift.
- Body pages preserve background, logo, brand area, page number, and footer.
- Every page has a clear primary judgment and a closing action.
- No prompts, draft text, or planning language appears on the slide.
- No single-character line breaks, hanging headings, or truncated sentences.
- No text collision, clipping, overlap, or crop.
- The exported PPT passes finished-product review, not just SVG technical checks.

## Workflow

### 1. Classify pages before generation

If the project includes a file like `notes/page_execution_contracts.json`, treat it as the first-stop routing artifact.

Split pages into at least: `fixed` (cover, chapter separators, closing) and `body` (semantic content pages).

For each page, record: page id / filename, page type, fixed or body, intended semantic role, primary takeaway, closing or convergence action.

### 2. Build an intermediate protocol object

Define a normalized page protocol: `page_id`, `page_class`, `page_type`, `frame_constraints`, `slot_constraints`, `content_outline`, `main_judgment`, `closing_action`, `validation_targets`, `fallback_plan`.

### 3. Separate frame from body

For body pages, preserve only the brand frame: Background, Logo, Brand band / brand zone, Page number, Footer.

Treat the internal body region as flexible and driven by page-type semantics.

### 4. Keep fixed pages template-locked

Reuse the approved template skeleton. Fill only approved text / asset fields. Do not move or reinterpret decorative structure.

### 5. Generate body pages from semantics

Derive composition from the page's semantic role (scope, target, risk distribution, attack chain, issue overview, remediation overview). Let page type determine layout pattern, hierarchy, and copy density.

### 6. Validate twice

Technical checks (bounds, overflow, protected zones, footer safety, export integrity) + Finished-product checks (readability, narrative completeness, closure, presentation quality).

### 7. Record failure depth and rollback reason

Log the precise layer: classification, protocol assembly, frame locking, slot filling, body composition, copy generation, validation, export.

## Rewiring guidance for legacy hybrid projects

1. Inspect where body-page rendering inherits project-derived layout skeletons.
2. Identify which constraints are truly brand-level versus accidental body-shell coupling.
3. Remove body-shell inheritance while retaining brand frame locks.
4. Route body pages back through native `ppt-master` page-type generation.
5. Rerun export and review against the full acceptance gate.

### Contract vs runtime verification

Do not assume project notes or routing JSON are the actual runtime source of truth.

When rewiring a hybrid deck:
1. Patch the contract or routing metadata first so the intended target state is explicit.
2. Locate the real renderer entrypoint and confirm it consumes that routing.
3. Check for shared helper code that still hardcodes a generic shell.
4. Search both project notes and shared scripts for old shell names.
5. Treat the change as incomplete until runtime routing and actual export output both reflect native page-type composition.

### Runtime reality check

Before claiming a hybrid template has been "wired back to native page-type composition", explicitly inspect the repository's real execution surface.

In executor-driven `ppt-master` projects, be careful not to mislabel support scripts as the native body-page generator:
- `total_md_split.py` may only split or normalize source markdown — not proof of body-page composition.
- `render_svg_pages.py` may only re-render existing SVG into PNG — not proof of regeneration.
- The real body-page composition may be executor-mediated.

Use targeted searches for terms like `page_type`, `layout_family`, `template_family`, `message_contract`, `main_judgment`, `argument_spine`.

If these terms only appear in docs/specs but not in executable scripts, the repo is likely still workflow-driven and executor-mediated rather than code-routed. Record the current state explicitly as: contract layer patched, runtime layer not yet proven.

## Template-contract hardening

When absorbing or repairing a specific template:
1. Align `design_spec.md`, fixed-page SVG placeholders, and `fixed_page_source_map.json` first.
2. Verify fixed pages reflect the source PPT skeleton exactly.
3. For TOC and chapter pages, prefer the absorbed source structure over generic defaults.
4. Normalize chapter asset naming across docs, source maps, and index metadata.
5. If `03_content.svg` remains, document it explicitly as a compatibility anchor.
6. Add machine-checkable fields: `contract_version`, `page_class`, `frame_policy`, `required_brand_elements`, `body_safe_region`, `allowed_native_page_types`, `forbidden_actions`.

## Brand-lock extraction checklist

When converting a derived body shell into a brand-locked native body flow, explicitly separate:
- must keep: white/background policy, logo, page number, top brand line, footer strip, safe region
- must remove from shell lock: card scaffolds, lead/closure blocks, fixed column structures, page-type-specific placeholder groups
- must forbid: swapping back to project-derived content shell, dark-theme regression, footer overlap

## Anti-shell upgrade for maximum body-page flexibility

When the user wants "more flexibility" or the deck still feels `套壳`:

### Diagnose the real failure mode

A deck can already be native-composed and still feel shell-heavy when page semantic classification is too coarse, runtime keeps preferring stable card layouts, copy is adapted to a preselected frame, or the dominant grammar is still `title band + judgment + cards + closure`.

### Introduce an explicit body family system

Practical high-flexibility body families:
- `path-map`: dominant path spine with nodes and directional logic
- `breakthrough-evidence`: staged exploit or entry page with proof anchors
- `blast-radius`: post-entry spread / lateral movement
- `root-cause`: grouped diagnosis or cause synthesis
- `control-gap`: single-topic issue page showing gap -> attacker use -> consequence
- `operating-model`: owner / action / cadence / handoff governance page
- `remediation-roadmap`: 30-60-90 or milestone sequencing page
- `exec-board`: management prioritization or decision board page

### Require page-intent metadata before layout

```yaml
reading_task: path_explain | exploit_prove | spread_explain | diagnose | govern | prioritize | summarize
message_strength: strong | medium
visual_center: flow | network | matrix | board | timeline | evidence | operating_loop
primary_structure: spine | stages | cause_map | gap_chain | owner_model | roadmap | priority_board
copy_density: low | medium | high
must_have: [judgment, evidence, implication]
avoid: [symmetric_cards, generic_closure_bar, repeated_two_column_shell]
```

### Route by reading task

Practical routing table:
- `path_explain` + `flow` + `spine` -> `path-map`
- `exploit_prove` + `evidence` + `stages` -> `breakthrough-evidence`
- `spread_explain` + `network` + `spine/fanout` -> `blast-radius`
- `diagnose` + `cause_map` -> `root-cause`
- `diagnose` + `gap_chain` -> `control-gap`
- `govern` + `operating_loop` -> `operating-model`
- `prioritize` + `timeline` + `roadmap` -> `remediation-roadmap`
- `prioritize` + `board` + `priority_board` -> `exec-board`

### Anti-convergence rules

Reject a candidate layout when:
- three consecutive body pages share the same primary structure
- the same chapter uses only one `visual_center`
- `path-map`, `operating-model`, or `exec-board` falls back to symmetric cards
- closure bar appears on more than roughly one third of body pages

### Change fallback order

1. same family with lower density
2. adjacent family with the same reading task
3. simplified variant inside the same visual center
4. generic shell fallback only if all above fail

## Dense-page copy compression rules

### Attack-chain / path cards

Use phrase-level copy instead of sentence-level prose:
- max 2 short lines per stage card
- prefer `漏洞名 + 动作` or `入口 + 后果`
- avoid leading punctuation on wrapped lines

### Governance / remediation cards

Switch from advisory sentences to directive fragments:
- `收敛外网暴露面`
- `限制高危端口来源`
- `建立高危修复 SLA`

Treat repeated text-fit failures as a content-structure problem, not a kerning problem.

## Checker-driven structural hotfix pattern

1. Confirm the warning is real on `svg_output/` first.
2. If warning repeats across the same page family, assume grammar too fragmented.
3. For attack-chain pages: replace thin closure strip + many tiny stage blocks with wider grouped stage cards.
4. For governance pages: replace badge + heading + multiple lines with one heading + two directive lines.
5. If checker still flags uniformly, remove decorative micro-structure first.

### Do not let acceptance hotfixes become a new shell

Guardrails:
1. Treat checker-green pages as temporary acceptance state, not proof of good design.
2. After batch structural hotfix, compare pages from each family at SVG level.
3. Attack-chain pages should read like path/spread pages, not governance cards.
4. If user says deck still feels shell-heavy, stop text-fit polishing and move to page-intent/family routing.

## Layered acceptance and regression packaging

1. Generate warning inventory from project review summary.
2. Split warning pages into `focused` and `non_focused` tiers.
3. Compute deck gate: Fail / Pass with focused warning / Pass with warning / Pass.
4. Freeze baseline snapshot, diff later runs.
5. Aggregate persistent warnings by `page_type` and `native_structure`.

## Late-stage acceptance hotfix workflow

1. Treat `svg_output/` as source of truth for body-page text fixes.
2. Do NOT rely on manual edits in `svg_final/` alone; they will be overwritten.
3. Run `check_svg_text_fit.py` after edits.
4. After target pages are clean, rerun `finalize_svg.py` then export fresh PPTX.

## Pitfalls

- Passing fixed-page rendering through a generative layout path (skeleton drift)
- Treating brand frame elements as editable body content
- Preserving legacy body shells that block native page semantics
- Declaring success after SVG lint passes without finished PPT review
- Letting notes/prompt residue/planning language leak onto the page
- Ignoring narrative closure on data-heavy pages
