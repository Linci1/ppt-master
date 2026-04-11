# Executor Visual Review Gate

> This file defines the **in-process page review discipline** for PPT Master. It is not an optional final QA pass. The Executor must apply this review **immediately after generating each page draft and before moving to the next page**.

---

## Core Rule

**One page = Generate → Review → Fix → Pass → Next page**

The Executor must NOT generate all pages first and postpone these checks to the end. If a page fails any medium-or-higher issue below, the page must be revised immediately in the same continuous context.

---

## Review Scope (Mandatory for Every Page)

### 1. Text segmentation and Chinese readability

Check whether:

- Long Chinese sentences are split into readable clauses rather than becoming one dense line
- Bullets are short enough to scan at a glance
- Title, subtitle, and body copy have clear reading rhythm
- Consulting-style conclusion sentences are concise and direct, not paragraph-like

**Typical fixes**:

- Split one long sentence into two shorter lines
- Convert prose into 3-5 bullets
- Move evidence/detail from the title area into body cards

### 2. Edge pressure / crowded feeling

Check whether:

- Text sits too close to card borders or canvas edges
- Visual groups are packed with insufficient breathing room
- Adjacent cards, charts, and labels visually collide even if coordinates do not technically overlap

**Typical fixes**:

- Increase card padding
- Reduce bullet count
- Widen column gap
- Move dense blocks upward before footer conflict occurs

### 3. Card text overflow risk

Check whether:

- Card titles are too long for their width
- Body lines are too dense for the card height
- Numeric labels, chart legends, or annotations appear likely to overflow or look cramped

**Typical fixes**:

- Rewrite to shorter labels
- Reduce text levels inside one card
- Split one overloaded card into two cards
- Increase card height only if it does not create downstream crowding

### 4. Footer / logo / page-number conflict

Check whether:

- Main content visually competes with the Chaitin logo
- Bottom accent bar, page number, and annotations feel crowded together
- Content enters the footer-protected zone even if only slightly

**Typical fixes**:

- Move the lowest content group upward
- Remove low-value bottom annotations
- Consolidate footer-adjacent text into a higher takeaway or side note

### 5. Layer separation / takeaway-vs-body conflict

Check whether:

- A takeaway strip, summary band, or top highlight bar visually collides with the body cards below
- Body-card borders appear to intrude into the takeaway band after export
- The page technically fits in SVG coordinates but still reads as "upper and lower modules fighting each other"

**Typical fixes**:

- Move the lower body group downward while keeping internal relationships intact
- Reduce takeaway height slightly if that creates clean separation
- Shorten or simplify the takeaway copy
- Prefer a clear vertical gap over squeezing both layers into the same band

### 6. Information density suitability

Check whether:

- The page contains too many ideas for a single speaking beat
- The user would need to read instead of glance
- The page is more like a document screenshot than a presentation page

**Typical fixes**:

- Keep one page to one main claim
- Move secondary evidence to appendix pages or speaker notes
- Replace raw detail with a summary statement plus 2-3 supporting bullets

### 7. Need for trimming or relayout

Check whether:

- The page technically fits but still feels heavy
- The hierarchy is weak: title, takeaway, and evidence compete equally
- A different layout mode would communicate faster

**Typical fixes**:

- Replace multi-paragraph text with cards, matrix, or two-column structure
- Promote one sentence into a takeaway strip
- Delete nice-to-have details rather than shrinking text

### 8. Same-family consistency

Check whether:

- The current page follows the same structural rule as earlier pages of the same family
- TOC cards use a consistent content structure (for example, either all six cards have a subtitle line or none do)
- Content pages with the same layout pattern share similar top baselines, card rhythm, and spacing logic

**Typical fixes**:

- Normalize repeated page families before continuing
- Align the current page's body start line with earlier same-family pages
- Add or remove repeated subtitle rows so the family uses one consistent structure
- Reuse the established "good page" as the reference instead of improvising a new pattern

---

## Severity Threshold

### Must fix before proceeding

- Text that is hard to parse in one glance
- Content touching or visually pressing against edges
- Card content likely to overflow or already visibly cramped
- Any conflict with logo / page number / footer decorations
- Any upper/lower module collision such as takeaway bars fighting with body cards
- Any obvious same-family inconsistency that makes the deck feel unfinished
- A page whose information density breaks presentation readability

### Can proceed, but tighten if time allows

- Minor rhythm polish
- Slightly verbose subtitles
- Non-critical whitespace imbalance

---

## Review Output Pattern

Before moving to the next page, the Executor should internally complete this checkpoint:

```markdown
[Page Review]
- Brand asset / placement: pass / fix
- Text segmentation: pass / fix
- Edge pressure: pass / fix
- Card overflow risk: pass / fix
- Footer / logo conflict: pass / fix
- Layer separation: pass / fix
- Information density: pass / fix
- Relayout needed: no / yes (fixed)
- Same-family consistency: pass / fix
```

If any item is `fix`, revise the current page first. Only after all eight items pass may the Executor continue to the next page.

---

## Relationship With Technical Validation

This visual review gate complements, but does not replace:

- `svg_quality_checker.py` technical checks
- post-processing checks in `finalize_svg.py`
- export-time PPT compatibility checks

Those tools catch **technical breakage**. This file catches **presentation readability and layout quality**.

Current `svg_quality_checker.py` also provides heuristic audit warnings for:

- Brand presence / approved-logo misuse
- Chinese readability / awkward line breaks
- Text too close to card or canvas edges
- Card text likely to look cramped or overflow
- Takeaway/body separation risk
- TOC card structure inconsistency

These warnings do not replace human judgment, but they should be treated as an automatic review prompt during the audit stage.
