# Dashboard Mobile Bottom Sheet

## Scope

Implemented the dashboard mobile bottom sheet from the mobile UI plan.

Changed behavior:

- Mobile users can select a time slot and immediately get the quick input controls in a bottom sheet.
- Desktop keeps the existing right-side quick input card.
- The sheet includes selected-slot info, tag selection, memo, save action, and a close button.
- Vertical touch movement is treated as page scroll rather than forced slot selection.
- The mobile sheet height is capped from the grid's 01:00 line (`data-slot-index="6"`) to the viewport bottom.
- Tag category headers in the quick input area use a plain `-` separator instead of a color dot; individual tag buttons keep their color markers.
- Tag buttons in each quick input category flow in a compact wrapping row and size to their color marker plus label instead of filling the full row.
- The shared tag modal category select uses a scoped readable font-size rule for the select and option text.

## Changed Files

- `apps/dashboard/templates/dashboard/index.html`
- `apps/dashboard/static/dashboard/js/dashboard.js`
- `apps/core/static/core/css/style.css`
- `apps/dashboard/tests.py`

## Verification

Fresh verification for this work:

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
# 14 passed in 7.45s

node --check apps/dashboard/static/dashboard/js/dashboard.js
# exit 0

git diff --check
# exit 0

conda run -n knou-life-diary pytest --tb=short
# 174 passed in 80.43s (0:01:20)
```

## Manual Checks Still Needed

- Mobile viewport at 360px/375px: select a slot and confirm the sheet opens without scrolling.
- Mobile viewport: vertical swipe over the grid should scroll the page.
- Mobile viewport: tap backdrop and close button to dismiss the sheet.
- Desktop viewport: confirm the existing sidebar layout and tag save flow still behave normally.

## Deferred

- Redesigning the 144-slot grid.
- Reworking tag management/category explanation modals.
- Adding advanced mobile gestures such as long-press or pinch.
