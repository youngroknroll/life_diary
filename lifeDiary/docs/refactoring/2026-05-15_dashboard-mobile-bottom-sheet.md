# Dashboard Mobile Bottom Sheet Completion Log

## What Changed

- Added a mobile-only quick input bottom sheet to the dashboard.
- Reused the existing dashboard quick input controls so desktop behavior keeps the right-side sidebar.
- Added mobile open/close behavior, backdrop handling, ARIA state updates, and focus return after closing.
- Preserved vertical touch movement as page scroll instead of forcing slot selection.
- Guarded `touchmove` cancellation with `event.cancelable` to avoid browser intervention warnings after scrolling starts.
- Capped the mobile sheet height to the space from the grid's 01:00 line to the viewport bottom.
- Replaced quick input category header color dots with a plain `-` separator while preserving individual tag color markers.
- Changed quick input tag lists to a compact wrapping row layout where buttons size to their contents.
- Added a scoped readable font-size rule for the shared tag modal category select.
- Added a dashboard rendering test for the bottom sheet structure.
- Added a dashboard JavaScript asset regression test for guarded touch cancellation.
- Added regression checks for the 01:00 line height cap.
- Added a rendering regression check for category header separators.
- Added a rendering regression check for the compact tag list layout.
- Added a tag modal regression check for the category select font-size class and CSS rule.

## Verification

Fresh verification for the final state:

```bash
node --check apps/dashboard/static/dashboard/js/dashboard.js
# exit 0

git diff --check
# exit 0

conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short
# 14 passed in 7.45s

conda run -n knou-life-diary pytest --tb=short
# 174 passed in 80.43s (0:01:20)
```

## Remaining Risks

- Manual mobile browser checks were not performed in this session.
- The behavior depends on the existing dashboard grid and tag controls; this task did not redesign those flows.

## Deferred Refactoring Note

- Topic: Broader mobile dashboard interaction redesign
- Why it is not part of the current scope: The approved scope was a focused mobile bottom sheet for quick tag assignment.
- Why it may be needed later: The 144-slot grid, tag management controls, and help/category modals may need a more complete mobile interaction model.
- Trigger condition: Mobile usability testing shows repeated friction beyond the selected-slot-to-tag path.
- Expected change location: `apps/dashboard/templates/dashboard/index.html`, `apps/dashboard/static/dashboard/js/dashboard.js`, `apps/core/static/core/css/style.css`
- Related tests: `apps/dashboard/tests.py` plus future browser-level mobile interaction checks
