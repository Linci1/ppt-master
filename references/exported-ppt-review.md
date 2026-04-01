# Exported PPT Review Gate

> This file defines the **post-export final review discipline** for PPT Master. It exists because some layout issues only become obvious after SVG is converted into an actual PPTX. Export is **not** the finish line; export is the start of the final audit gate.

---

## Core Rule

**Exported PPT = Audit → Fix source SVG → Re-export → Pass → Delivery**

The Executor must NOT treat the first exported `.pptx` as final output. If the exported deck reveals any meaningful visual issue, the fix must happen in the source SVG page, followed by a new export cycle.

---

## Review Scope (Mandatory for Every Final Export)

### 1. Exported appearance vs. SVG intent

Check whether:

- The PPT rendering preserves the intended hierarchy from the SVG source
- Text blocks, cards, and decorative elements still align as expected after export
- Any gradient, border, shadow, or conversion artifact changes the visual balance

### 2. Text segmentation and readability in the real deck

Check whether:

- Chinese line breaks still read naturally in the exported PPT
- Dense text became harder to read after export
- Titles, subtitles, and body copy still have clear visual rhythm

### 3. Edge pressure, crowding, and clipping

Check whether:

- Text feels tighter in PPT than it did in SVG
- Card content looks visually jammed even if it still technically fits
- Any card title, bullet, or label appears clipped or pressed against edges

### 4. Takeaway/body conflict and layer separation

Check whether:

- The takeaway strip remains clearly separated from the lower body modules
- Card borders appear to intrude into the summary band after export
- The page reads as two clean layers rather than one compressed stack

### 5. Footer / logo / page-number conflict

Check whether:

- Logo, page number, bottom accent bar, and body content still have breathing room
- Footer-adjacent items became more crowded after export
- Any body element drifts into the footer-protected zone

### 6. Information density and page-family consistency

Check whether:

- The page still behaves like a presentation page, not a report screenshot
- TOC cards use one consistent structure
- Same-family pages use one stable layout logic across the deck
- Any page now feels like an outlier in spacing, rhythm, or module stacking

---

## Must-fix Threshold

The exported PPT fails this gate if any of the following appear:

- Text clipping, clear overflow, or unreadable dense lines
- Takeaway/body collision or upper/lower modules fighting visually
- Footer / logo / page-number conflict
- TOC structure inconsistency
- Same-family layout inconsistency that makes the deck feel unfinished
- Any page that obviously needs trimming or relayout after real PPT inspection

---

## Review Output Pattern

Before declaring the deck final, the Executor should internally complete this checkpoint:

```markdown
[Exported PPT Review]
- Exported appearance vs SVG: pass / fix
- Text readability in PPT: pass / fix
- Edge pressure / clipping: pass / fix
- Takeaway/body separation: pass / fix
- Footer / logo conflict: pass / fix
- Density and consistency: pass / fix
```

If any item is `fix`, repair the source SVG page(s), then repeat the export and the review.

---

## Relationship With Other Gates

This review gate comes **after**:

- in-process page review in `executor-visual-review.md`
- deck-level consistency audit in `executor-base.md`
- technical SVG audit from `svg_quality_checker.py`

Those gates reduce the error rate. This gate catches the remaining issues that only show up in the delivered PPT.
