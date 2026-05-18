# Footer Copyright Log

Date: 2026-05-18

## Scope

Updated the shared footer copyright notice to use `LogBetter` and a service-start year range that begins in 2025. The app name stays localized: Korean screens show `라이프 다이어리`, and English screens show `Life Diary`.

## Changed Files

- `templates/base.html`
- `locale/en/LC_MESSAGES/django.po`
- `locale/en/LC_MESSAGES/django.mo`
- `locale/ko/LC_MESSAGES/django.po`
- `apps/core/tests.py`
- `apps/core/test_i18n_phase1.py`

## Verification

- RED: `conda run -n knou-life-diary pytest apps/core/tests.py::TestHomePage::test_home_page_renders_korean_footer_copyright apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_footer_copyright --tb=short` failed with the expected missing footer strings before implementation.
- GREEN: same command passed with `2 passed in 0.64s` after implementation.
- Final focused regression: `conda run -n knou-life-diary pytest apps/core/tests.py apps/core/test_i18n_phase1.py --tb=short` passed with `12 passed in 1.92s`.

## Remaining Risk

No legal ownership validation was performed. This change only updates the product footer display and project translations.

## Deferred Refactoring Note

- Topic: Centralized copyright year helper
- Why it is not part of the current scope: The current requirement only affects one shared footer template.
- Why it may be needed later: More pages or generated documents may need the same year range.
- Trigger condition: Another runtime surface needs the same `2025-current year` copyright string.
- Expected change location: A context processor or template tag under `apps/core/`.
- Related tests: Footer rendering tests in `apps/core/tests.py` and `apps/core/test_i18n_phase1.py`.
