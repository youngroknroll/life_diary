# Tag Color Recommendations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show a one-line recommended color palette in the tag create/edit modal.

**Architecture:** Keep the existing color picker and HEX input. Add a compact `추천색상:` row below them with 14 swatch buttons: red, orange, yellow, green, blue, navy, and purple, two options each. JavaScript updates the existing color picker and text input when a swatch is clicked.

**Tech Stack:** Django template, shared CSS, browser JavaScript, pytest static/template contract tests, `node --check`.

---

### Task 1: Recommended Color Row

**Files:**
- Modify: `apps/tags/templates/tags/_tag_modal.html`
- Modify: `apps/core/static/core/js/tag.js`
- Modify: `apps/core/static/core/css/style.css`
- Test: `apps/tags/tests.py`

**Step 1: Write the failing tests**

Assert the modal includes `추천색상:`, 14 `data-tag-color-swatch` buttons, and the expected color values. Assert JS listens for swatch clicks and syncs both color inputs.

**Step 2: Run RED**

Run:

```bash
pytest apps/tags/tests.py::TestTagModalTemplate::test_tag_modal_has_one_line_recommended_color_swatches apps/tags/tests.py::TestTagModalTemplate::test_tag_modal_swatch_js_syncs_existing_color_inputs --tb=short
```

Expected: fail because the swatch row and JS behavior do not exist.

**Step 3: Implement**

Add the one-line swatch row under the existing color inputs. Add delegated click handling in `tag.js`. Add compact CSS for wrapping safely on small screens.

**Step 4: Verify**

Run:

```bash
pytest apps/tags/tests.py::TestTagModalTemplate --tb=short
pytest apps/tags/tests.py apps/dashboard/tests.py --tb=short
node --check apps/core/static/core/js/tag.js
git diff --check
```
