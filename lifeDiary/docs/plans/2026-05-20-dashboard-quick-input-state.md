# Dashboard Quick Input State Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the dashboard quick input form clearer by showing the disabled save button in gray and moving the optional memo label into the textarea placeholder.

**Architecture:** This is a small Django template and CSS change. The dashboard view data flow and save/delete JavaScript behavior remain unchanged; only rendered markup and disabled button styling change.

**Tech Stack:** Django template, Bootstrap-compatible CSS, pytest rendering regression tests.

---

## Approved Scope

- Change the disabled dashboard save button to a gray visual state.
- Show `메모 (선택사항)` only inside the memo textarea as placeholder text.
- Keep existing save behavior, tag selection behavior, mobile bottom sheet behavior, and i18n template usage unchanged.

## Non-Scope

- Redesigning the dashboard input panel.
- Changing save/delete API behavior.
- Changing mobile sheet opening or focus behavior.

## Acceptance Criteria

- Before a time block/tag can be saved, the save button renders disabled and CSS defines a gray disabled style for `#saveBtn`.
- The memo field does not show a visible external `메모 (선택사항)` label in the quick input panel.
- The memo textarea placeholder is `메모 (선택사항)`.
- Existing dashboard tests continue to pass.

## Task 1: Rendering Regression Tests

**Files:**
- Modify: `apps/dashboard/tests.py`

**Step 1: Write the failing tests**

Add tests under `TestDashboardIndexRendering`:

```python
def test_memo_optional_text_is_placeholder_only(self, dash_user_with_tags):
    client, _ = dash_user_with_tags
    resp = client.get("/dashboard/")
    section = _extract_element(resp.content.decode(), "quickInputSheet")

    assert 'placeholder="메모 (선택사항)"' in section
    assert '<label for="memoInput"' not in section

def test_disabled_save_button_has_gray_state_css(self):
    css_path = settings.BASE_DIR / "apps/core/static/core/css/style.css"
    source = css_path.read_text()

    assert "#saveBtn:disabled" in source
    assert "background-color: var(--color-text-muted);" in source
```

**Step 2: Run tests to verify RED**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py::TestDashboardIndexRendering::test_memo_optional_text_is_placeholder_only apps/dashboard/tests.py::TestDashboardIndexRendering::test_disabled_save_button_has_gray_state_css --tb=short
```

Expected: both fail because the old label and old placeholder/CSS are still present.

## Task 2: Minimal UI Implementation

**Files:**
- Modify: `apps/dashboard/templates/dashboard/index.html`
- Modify: `apps/core/static/core/css/style.css`

**Step 1: Update memo markup**

Remove the visible label and set the textarea placeholder:

```html
<textarea class="form-control" id="memoInput" rows="3" placeholder="{% trans '메모 (선택사항)' %}"></textarea>
```

**Step 2: Add disabled save button CSS**

Add scoped CSS near the dashboard quick input styles:

```css
#saveBtn:disabled {
    background-color: var(--color-text-muted);
    border-color: var(--color-text-muted);
    color: white;
    opacity: 1;
}
```

**Step 3: Run focused verification**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
node --check apps/dashboard/static/dashboard/js/dashboard.js
git diff --check
```

Expected: dashboard tests pass, JS syntax check exits 0, whitespace check exits 0.

## Post-Work Documentation

- Create `docs/refactoring/2026-05-20_dashboard-quick-input-state.md`.
- Update `docs/project-status.md` with verification evidence and any unverified manual browser checks.
