# Dashboard Tag List Compact Row Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make quick input tag buttons use content-sized widths while flowing in a compact wrapping row.

**Architecture:** Keep the existing dashboard template and tag buttons. Replace the full-width grid layout classes with a scoped compact tag-list class, then add CSS that lays tag buttons out as a wrapping row with `align-items: flex-start` and `max-width: 100%`.

**Tech Stack:** Django templates, CSS, pytest.

---

## Task 1: Add Rendering Regression Test

**Files:**
- Modify: `apps/dashboard/tests.py`

**Step 1: Write the failing test**

Assert that the quick input tag list renders with the compact class, no longer uses `d-grid` on the category tag-list wrappers, and uses a wrapping row layout.

**Step 2: Verify RED**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py::TestDashboardIndexRendering::test_sidebar_tag_list_uses_compact_wrapping_row_layout --tb=short
```

Expected: fail before the template class is changed.

## Task 2: Implement Compact Wrapping Row Layout

**Files:**
- Modify: `apps/dashboard/templates/dashboard/index.html`
- Modify: `apps/core/static/core/css/style.css`

**Step 1: Template**

Replace the tag list wrapper classes inside `#tagContainer` with `quick-input-tag-list`.

**Step 2: CSS**

Add CSS for `.quick-input-tag-list` and `.quick-input-tag-list .tag-btn` so buttons flow horizontally, wrap when needed, and size to their contents, with `max-width: 100%` for long names.

**Step 3: Verify GREEN**

Run the targeted test and dashboard test file.

## Task 3: Documentation and Final Verification

**Files:**
- Modify: `docs/frontend/2026-05-15-dashboard-mobile-bottom-sheet.md`
- Modify: `docs/refactoring/2026-05-15_dashboard-mobile-bottom-sheet.md`
- Modify: `docs/project-status.md`

Run:

```bash
node --check apps/dashboard/static/dashboard/js/dashboard.js
conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
conda run -n knou-life-diary pytest --tb=short
git diff --check
```
