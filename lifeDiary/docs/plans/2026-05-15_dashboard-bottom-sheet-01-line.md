# Dashboard Bottom Sheet 01:00 Line Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Cap the mobile dashboard bottom sheet height so the sheet top aligns with the grid's 01:00 line.

**Architecture:** Keep the existing mobile bottom sheet. Add a small JavaScript measurement helper that reads `data-slot-index="6"` and writes a CSS custom property to `#quickInputSheet`. CSS consumes that property as the mobile sheet `max-height`.

**Tech Stack:** Django templates, vanilla JavaScript, CSS media queries, pytest.

---

## Task 1: Add Regression Tests

**Files:**
- Modify: `apps/dashboard/tests.py`

**Step 1: Write failing tests**

Add tests that assert:

- `dashboard.js` uses `data-slot-index="6"` as the mobile sheet anchor.
- `dashboard.js` writes `--quick-input-sheet-max-height`.
- `style.css` uses `var(--quick-input-sheet-max-height, min(82vh, 680px))`.

**Step 2: Verify RED**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py::TestDashboardJavaScriptAssets --tb=short
```

Expected: fail because the anchor sizing logic is not implemented yet.

## Task 2: Implement 01:00 Line Height Cap

**Files:**
- Modify: `apps/dashboard/static/dashboard/js/dashboard.js`
- Modify: `apps/core/static/core/css/style.css`

**Step 1: Implement minimal JS**

- Add a helper that finds `[data-slot-index="6"]`.
- Calculate `window.innerHeight - slot.getBoundingClientRect().top`.
- Set `--quick-input-sheet-max-height` on `#quickInputSheet`.
- Call the helper before opening the sheet and during mobile layout sync.
- Clear the property on desktop.

**Step 2: Implement minimal CSS**

Use the custom property for mobile `.quick-input-sheet` `max-height`, with the current cap as fallback.

**Step 3: Verify GREEN**

Run the targeted test again. Expected: pass.

## Task 3: Final Verification and Documentation

**Files:**
- Modify: `docs/frontend/2026-05-15-dashboard-mobile-bottom-sheet.md`
- Modify: `docs/refactoring/2026-05-15_dashboard-mobile-bottom-sheet.md`
- Modify: `docs/project-status.md`

**Step 1: Run verification**

```bash
node --check apps/dashboard/static/dashboard/js/dashboard.js
conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
conda run -n knou-life-diary pytest --tb=short
git diff --check
```

**Step 2: Update docs**

Record the 01:00 line cap, fresh verification output, and manual mobile browser checks still needed.
