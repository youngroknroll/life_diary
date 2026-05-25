# Pytest Compilemessages Execution Log

## Context

Full pytest failed with English locale tests rendering Korean text. The request middleware selected English (`Content-Language: en`), but Django rendered untranslated Korean strings because `locale/en/LC_MESSAGES/*.mo` files were missing locally.

## Changed

- Added a pytest startup hook in `conftest.py`.
- The hook runs `compilemessages` for `en` and `ko` before test collection.
- Added ignore patterns for `.venv`, `.worktrees`, and `staticfiles` so generated or external locale folders are not scanned during tests.
- Added a focused regression test for the compile helper.

## Design Reason

The failure came from test environment setup, not from individual view logic. Keeping the fix in pytest startup makes every local or CI pytest run self-contained without tracking generated `.mo` files in git.

## Verification

```bash
pytest test_pytest_i18n_compile.py --tb=short
# 1 passed in 0.03s

pytest apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_hero --tb=short
# 1 passed in 0.87s

pytest --tb=short
# 226 passed in 110.00s (0:01:49)
```

## Remaining Notes

- `.mo` files remain generated artifacts and are not tracked.
- If a future CI job runs checks without pytest, that job should run `python manage.py compilemessages` explicitly before any locale-dependent Django command.
