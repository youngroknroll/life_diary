# Stats Life Feedback Toggle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the stats page life feedback list open through a default-closed toggle instead of occupying the page immediately.

**Architecture:** Keep the change in the existing stats life feedback partial. Use Bootstrap collapse markup and the existing shared stylesheet for minimal presentation. Do not change feedback generation, stats context, or chart behavior.

**Tech Stack:** Django templates, Bootstrap collapse, pytest, static CSS.

---

### Task 1: Add Regression Test

**Files:**
- Modify: `apps/stats/test_mobile_layout.py`
- Test: `apps/stats/test_mobile_layout.py`

**Step 1: Write the failing test**

Add a test that requests `stats:index` and verifies:

- a feedback toggle button exists;
- the button has `data-bs-toggle="collapse"`;
- the button targets `#lifeFeedbackCollapse`;
- `aria-expanded="false"` is present by default;
- the collapse body starts with `class="collapse"`;
- a feedback count badge is rendered.

**Step 2: Run test to verify it fails**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py::TestStatsLifeFeedbackToggle::test_feedback_list_uses_default_closed_toggle --tb=short
```

Expected: fail because the current partial renders feedback toast cards directly without a toggle button.

### Task 2: Implement Toggle Markup

**Files:**
- Modify: `apps/stats/templates/stats/life_feedback.html`

**Step 1: Write minimal implementation**

Wrap the existing feedback card list with:

- a `button.life-feedback-toggle`;
- `data-bs-toggle="collapse"`;
- `data-bs-target="#lifeFeedbackCollapse"`;
- `aria-expanded="false"`;
- `aria-controls="lifeFeedbackCollapse"`;
- a badge showing `{{ feedback_list|length }}`;
- a `div#lifeFeedbackCollapse.collapse` containing the existing cards.
- a horizontal wrapping feedback list that continues onto the next row when needed.

**Step 2: Run focused test**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py::TestStatsLifeFeedbackToggle::test_feedback_list_uses_default_closed_toggle --tb=short
```

Expected: pass.

### Task 3: Add Minimal Styling

**Files:**
- Modify: `apps/core/static/core/css/style.css`
- Test: `apps/stats/test_mobile_layout.py`

**Step 1: Extend the test**

Assert the stylesheet contains `.life-feedback-toggle`, a collapsed chevron rule, and a `.life-feedback-list` rule with `display: flex`, `flex-wrap: wrap`, and no `overflow-x: auto`.

**Step 2: Verify RED**

Run the same focused test and confirm it fails on the missing CSS rule.

**Step 3: Implement CSS**

Add compact styling for the feedback toggle and chevron using existing color variables and card conventions.

**Step 4: Verify GREEN**

Run the focused test again.

### Task 4: Documentation and Verification

**Files:**
- Add: `docs/refactoring/2026-05-15_stats-life-feedback-toggle.md`
- Modify: `docs/project-status.md`

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py apps/stats/test_i18n_phase5.py --tb=short
node --check apps/stats/static/stats/js/stats.js
git diff --check
```

If these pass, run the full suite:

```bash
conda run -n knou-life-diary pytest --tb=short
```

Manual browser verification remains unverified unless explicitly performed.
