# Dashboard Mobile Bottom Sheet Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a mobile-only dashboard bottom sheet so selected time slots can be tagged without scrolling to the sidebar.

**Architecture:** Keep the existing desktop sidebar and reuse its input controls inside a mobile sheet wrapper. Add focused template/CSS/JS behavior and guard it with dashboard rendering tests. Avoid backend changes.

**Tech Stack:** Django templates, Bootstrap-style markup, vanilla JavaScript, CSS media queries, pytest-django.

---

## Task 1: Template Structure Test

**Files:**
- Modify: `apps/dashboard/tests.py`
- Test: `apps/dashboard/tests.py`

**Step 1: Write failing test**

Add a dashboard rendering test that asserts:

- `id="quickInputSheet"` exists.
- `id="quickInputSheetBackdrop"` exists.
- `aria-labelledby="quickInputSheetTitle"` exists.
- the sheet has a close button with `data-dashboard-sheet-close`.

**Step 2: Verify RED**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py::TestDashboardIndexRendering::test_dashboard_renders_mobile_bottom_sheet_structure --tb=short
```

Expected: fail because the sheet markup does not exist.

## Task 2: Add Mobile Sheet Markup

**Files:**
- Modify: `apps/dashboard/templates/dashboard/index.html`

**Step 1: Implement minimal markup**

Wrap the existing quick input card in a mobile sheet/backdrop structure while preserving the existing `#quickInputSidebar` and form control IDs.

**Step 2: Verify GREEN**

Run the targeted test again. Expected: pass.

## Task 3: CSS Mobile Sheet Behavior

**Files:**
- Modify: `apps/core/static/core/css/style.css`

**Step 1: Add mobile-only styles**

Add rules for:

- `.quick-input-sheet-backdrop`
- `.quick-input-sheet`
- `.quick-input-sheet.is-open`
- 44px touch targets for sheet tag buttons/actions.

Desktop should render the card normally.

**Step 2: Verify static checks**

Run dashboard tests and `git diff --check`.

## Task 4: JS Open/Close Behavior

**Files:**
- Modify: `apps/dashboard/static/dashboard/js/dashboard.js`

**Step 1: Add behavior**

- Open sheet after slot selection/drag end on mobile.
- Close on close button or backdrop click.
- Keep desktop unchanged.
- Set `aria-hidden` and `document.body` class consistently.

**Step 2: Verify tests**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
```

## Task 5: Documentation

**Files:**
- Create: `docs/frontend/2026-05-15-dashboard-mobile-bottom-sheet.md`
- Modify: `docs/project-status.md`

**Step 1: Record changes and verification**

Document the mobile bottom sheet behavior, verification commands, and unverified manual browser/device checks.

## Final Verification

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
conda run -n knou-life-diary pytest --tb=short
git diff --check
```
