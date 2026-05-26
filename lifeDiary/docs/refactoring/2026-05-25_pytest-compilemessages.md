# Pytest Compilemessages Execution Log

## Context

Full pytest failed with English locale tests rendering Korean text. The request middleware selected English (`Content-Language: en`), but Django rendered untranslated Korean strings because `locale/en/LC_MESSAGES/*.mo` files were missing locally.

## Changed

- Added a pytest startup hook in `conftest.py`.
- The hook runs `compilemessages` for `en` and `ko` before test collection when `msgfmt` is available.
- When `msgfmt` is not on `PATH`, the hook now compiles the project `.po` files to `.mo` with a small Python-only writer instead of skipping.
- Added ignore patterns for `.venv`, `.worktrees`, and `staticfiles` so generated or external locale folders are not scanned during tests.
- Added focused regression tests for both the `msgfmt` path and the Python fallback.

## Design Reason

The failure came from test environment setup, not from individual view logic. Keeping the fix in pytest startup makes every local or CI pytest run self-contained without requiring GNU gettext to be installed on the host.

## Verification

```bash
conda run -n knou-life-diary python -m pytest test_pytest_i18n_compile.py --tb=short
# 2 passed in 0.03s

conda run -n knou-life-diary python -m pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short
# 5 passed in 0.04s

PATH=/usr/bin:/bin /Users/yeongroksong/opt/anaconda3/envs/knou-life-diary/bin/python -m pytest apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_hero --tb=short
# 1 passed in 1.77s

PATH=/usr/bin:/bin /Users/yeongroksong/opt/anaconda3/envs/knou-life-diary/bin/python -m pytest test_pytest_i18n_compile.py --tb=short
# 1 passed, 1 failed before the fallback fix; now 2 passed in 0.03s
```

## Remaining Notes

- `.mo` files remain generated artifacts and are not tracked.
- If a future CI job wants to force catalog regeneration, it can still run `python manage.py compilemessages` when GNU gettext is installed, but the test suite no longer depends on that being available.
