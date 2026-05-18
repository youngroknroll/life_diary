# Header Utility Controls Execution Log

Date: 2026-05-19

## Scope

Implemented the approved header utility controls and dashboard drag polish from:

- `docs/plans/2026-05-19-header-utility-controls-design.md`
- `docs/plans/2026-05-19-header-utility-controls.md`

## Changed Files

- `templates/base.html`
- `apps/core/static/core/css/style.css`
- `apps/core/tests.py`
- `apps/core/test_i18n_phase1.py`
- `apps/dashboard/tests.py`
- `locale/en/LC_MESSAGES/django.po`
- `locale/en/LC_MESSAGES/django.mo`
- `locale/ko/LC_MESSAGES/django.po`

## What Changed

- Added a `navbar-utility-controls` row immediately beside the Life Diary brand.
- Moved the language selector and theme toggle into that row so they stay together outside the collapsed nav content.
- Changed the theme toggle from icon-only markup to localized text:
  - Korean: `다크` / `라이트`
  - English: `Dark` / `Light`
- Updated theme toggle JavaScript to manage text, `aria-label`, and `aria-pressed`.
- Added compact responsive source CSS for the header utility row.
- Added scoped `user-select: none` CSS to the dashboard time-grid/time-slot area to prevent slot text selection during drag.

## Verification

- RED: `conda run -n knou-life-diary pytest apps/core/tests.py::TestHomePage::test_home_page_renders_header_utility_controls apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_header_theme_text apps/dashboard/tests.py::TestDashboardJavaScriptAssets::test_time_grid_prevents_text_selection --tb=short` failed with `3 failed` before implementation.
- GREEN: same targeted command passed with `3 passed in 0.75s` after implementation.
- Focused regression: `conda run -n knou-life-diary pytest apps/core/tests.py apps/core/test_i18n_phase1.py apps/dashboard/tests.py --tb=short` passed with `29 passed in 8.74s`.

## Not Verified

- Manual browser checks at 320px, 375px, 390px, and desktop widths were not run.
- Actual pointer drag behavior was not manually checked in a browser.

## Remaining Risk

- Inline template JavaScript is covered by render tests but not by a dedicated JavaScript syntax checker.
- Very narrow viewport behavior still needs manual browser confirmation.

## Deferred Refactoring Note

- Topic: Extract shared header JavaScript from `templates/base.html`.
- Why it is not part of the current scope: The approved task only required header control layout and theme toggle text behavior.
- Why it may be needed later: Inline JavaScript is harder to lint and test directly.
- Trigger condition: More header interactions are added or theme behavior needs richer test coverage.
- Expected change location: `apps/core/static/core/js/` and `templates/base.html`.
- Related tests: `apps/core/tests.py`, `apps/core/test_i18n_phase1.py`.
