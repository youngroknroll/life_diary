# Pytest Compilemessages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ensure pytest compiles Django translation catalogs before tests so English locale tests do not depend on pre-existing `.mo` files.

**Architecture:** Add a pytest startup hook in the existing root `conftest.py`. The hook will call Django's `compilemessages` command before tests run, keeping the behavior local to test execution and avoiding changes to production settings.

**Tech Stack:** Django 5.2, pytest, pytest-django, gettext message catalogs.

---

### Task 1: Add a Regression Test for the Pytest Translation Compiler

**Files:**
- Create: `test_pytest_i18n_compile.py`
- Modify after RED: `conftest.py`

**Step 1: Write the failing test**

Add a test that imports a helper from `conftest.py`, monkeypatches `django.core.management.call_command`, runs the helper, and asserts that `compilemessages` is called with the project locales.

**Step 2: Run test to verify it fails**

Run:

```bash
pytest test_pytest_i18n_compile.py --tb=short
```

Expected RED: import fails because the helper does not exist yet.

**Step 3: Implement the minimal helper and hook**

Add `_compile_test_messages()` to `conftest.py`, then call it from `pytest_sessionstart`. Use `call_command("compilemessages", locale=["en", "ko"], verbosity=0)` so both project locales are compiled before tests.

**Step 4: Run test to verify it passes**

Run:

```bash
pytest test_pytest_i18n_compile.py --tb=short
```

Expected GREEN: the new regression test passes.

### Task 2: Verify Locale Regression and Full Suite

**Files:**
- No production files.

**Step 1: Run the focused locale regression**

Run:

```bash
pytest apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_hero --tb=short
```

Expected: pass with English hero text rendered.

**Step 2: Run the full test suite**

Run:

```bash
pytest --tb=short
```

Expected: full suite passes.

### Task 3: Document the Result

**Files:**
- Create: `docs/refactoring/2026-05-25_pytest-compilemessages.md`
- Modify: `docs/project-status.md`

Record the root cause, implementation, verification commands, and the remaining deployment note that `.mo` files are generated artifacts and not currently tracked.
