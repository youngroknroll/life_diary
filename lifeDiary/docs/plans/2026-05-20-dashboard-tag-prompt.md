# Dashboard Tag Prompt Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show a clear next-step prompt after the user selects one or more dashboard time slots.

**Architecture:** Keep the prompt inside the existing `slotInfoInline` state box so desktop sidebar and mobile bottom sheet share the same behavior. Only `showSlotInfo()` changes; no API or save behavior changes are needed.

**Tech Stack:** Django static JavaScript, pytest asset regression test, existing gettext/i18n pattern.

---

## Approved Scope

- After at least one time slot is selected, show `시간을 선택했어요. 원하는 태그를 선택하세요.` inside the existing selected-slot info box.
- Keep the selected time/status/duration information visible.
- Keep current tag selection, save button, and mobile bottom sheet behavior unchanged.

## Task 1: JavaScript Asset Regression Test

**Files:**
- Modify: `apps/dashboard/tests.py`

**Step 1: Write the failing test**

Add a `TestDashboardJavaScriptAssets` test that checks `showSlotInfo()` includes the new gettext prompt after selected slot info is built.

**Step 2: Run RED**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py::TestDashboardJavaScriptAssets::test_selected_slot_info_prompts_tag_selection --tb=short
```

Expected: fail because the prompt is not in `dashboard.js` yet.

## Task 2: Minimal Implementation

**Files:**
- Modify: `apps/dashboard/static/dashboard/js/dashboard.js`

**Step 1: Add the selected prompt**

Inside `showSlotInfo()`, define:

```javascript
const nextActionPrompt = gettext('시간을 선택했어요. 원하는 태그를 선택하세요.');
```

Append it below the selected slot info for both single-slot and multi-slot branches.

**Step 2: Run verification**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
node --check apps/dashboard/static/dashboard/js/dashboard.js
git diff --check
```

Expected: all commands pass.

## Post-Work Documentation

- Update `docs/refactoring/2026-05-20_dashboard-quick-input-state.md` with the tag prompt addition.
- Update `docs/project-status.md` with final verification evidence.
