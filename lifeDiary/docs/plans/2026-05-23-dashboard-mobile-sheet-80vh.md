# Dashboard Mobile Sheet 80vh Plan

- Date: 2026-05-23
- Scope: Dashboard mobile quick input bottom sheet height and viewport containment
- Status: Approved and implemented

## Approved Scope

Change the dashboard mobile "입력정보" bottom sheet so it uses a fixed mobile viewport height of `80vh`. The sheet should stay anchored to the bottom of the viewport and its bottom edge must not extend past the screen.

## Non-Scope

- Redesigning the 144-slot time grid.
- Changing desktop quick input sidebar behavior.
- Changing tag selection, memo, save, or close behavior.
- Reworking mobile gestures.

## Implementation Notes

- Replaced the previous dynamic 01:00 grid-line height cap with CSS-only mobile sizing.
- Mobile `.quick-input-sheet` now uses `height: 80dvh`, `max-height: calc(100dvh - env(safe-area-inset-bottom, 0px))`, `box-sizing: border-box`, `bottom: 0`, and `overflow-y: auto`.
- Removed JavaScript measurement of `[data-slot-index="6"]` and the `--quick-input-sheet-max-height` CSS custom property.
- Kept the existing open/close, backdrop, ARIA, and focus behavior.

## Verification

```bash
conda run -n knou-life-diary pytest apps/dashboard/tests.py::TestDashboardJavaScriptAssets::test_mobile_sheet_no_longer_uses_grid_anchor_for_height apps/dashboard/tests.py::TestDashboardJavaScriptAssets::test_mobile_sheet_css_uses_fixed_viewport_height_cap --tb=short
# 2 passed in 0.03s

node --check apps/dashboard/static/dashboard/js/dashboard.js
# exit 0

git diff --check
# exit 0

conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
# 20 passed in 8.05s
```

## Manual Checks Still Needed

- Mobile viewport: select a slot and confirm the sheet occupies about 80% of screen height.
- Mobile viewport: confirm the sheet bottom stays flush with the viewport bottom.
- Mobile viewport: confirm long tag lists scroll inside the sheet.
- Desktop viewport: confirm the right-side quick input sidebar still behaves normally.

## Deferred Refactoring Note

- Topic: Browser-level mobile sheet layout test
- Why it is not part of the current scope: Current scope is a small CSS/JS behavior change covered by static and Django render tests.
- Why it may be needed later: CSS string assertions cannot prove actual viewport geometry.
- Trigger condition: More mobile sheet layout changes or repeated mobile visual regressions.
- Expected change location: browser test suite, dashboard page CSS/JS.
- Related tests: `apps/dashboard/tests.py`, future Playwright/mobile viewport checks.
