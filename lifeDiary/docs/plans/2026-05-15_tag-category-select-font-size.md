# Tag Category Select Font Size Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the tag modal category select and its option text easier to read.

**Architecture:** Keep the existing shared tag modal and Bootstrap select. Add a scoped class to the category select and a small CSS rule that sets the select and option text size to `1rem`.

**Tech Stack:** Django templates, CSS, pytest.

---

## Task 1: Regression Test

**Files:**
- Modify: `apps/tags/tests.py`

Write a test that verifies `_tag_modal.html` gives `#tagFormCategory` a readable-font class and `style.css` defines `font-size: 1rem` for the select and options.

## Task 2: Implementation

**Files:**
- Modify: `apps/tags/templates/tags/_tag_modal.html`
- Modify: `apps/core/static/core/css/style.css`

Add `tag-category-select` to the category `<select>`, then style `.tag-category-select` and `.tag-category-select option`.

## Task 3: Verification

Run:

```bash
conda run -n knou-life-diary pytest apps/tags/tests.py::TestTagModalTemplate::test_category_select_has_readable_font_size_class --tb=short
conda run -n knou-life-diary pytest apps/tags/tests.py apps/tags/test_i18n_phase3.py --tb=short
conda run -n knou-life-diary pytest --tb=short
git diff --check
```
