# Business Logic Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Lower coupling in the Python business-logic layer by extracting repeated constants, factories, and branching logic while preserving existing behavior.

**Architecture:** Introduce small helper modules near the current apps instead of broad file moves. Keep public view and stats entry points stable, then shift repeated logic behind those boundaries. Add focused unit tests first so the refactor is guarded.

**Tech Stack:** Django, Django TestCase, Python helper modules in `apps/stats`, `apps/dashboard`, `apps/users`, and `apps/tags`.

---

### Task 1: Add Failing Unit Tests For Extracted Logic

**Files:**
- Create: `apps/stats/tests.py`
- Create: `apps/dashboard/tests.py`
- Create: `apps/users/tests.py`
- Create: `apps/tags/tests.py`

**Step 1: Write tests for repeated stats data shapes**

Cover:
- unclassified daily data shape
- unclassified weekly data shape
- unclassified analysis data shape
- monthly hour increment behavior

**Step 2: Write tests for dashboard helper logic**

Cover:
- slot header generation
- valid slot index list
- invalid slot indexes outside the allowed range

**Step 3: Write tests for domain services**

Cover:
- goal progress lookup for `daily`, `weekly`, `monthly`
- shared tag manage policy for default and non-default tags

**Step 4: Run tests and confirm failure**

Run:
`DJANGO_SECRET_KEY=test ./.venv/bin/python manage.py test apps.stats.tests apps.dashboard.tests apps.users.tests apps.tags.tests -v 2`

Expected:
Tests fail because the new helper modules or helper methods do not exist yet.

### Task 2: Extract Stats Helper Functions

**Files:**
- Create: `apps/stats/services.py`
- Modify: `apps/stats/logic.py`

**Step 1: Add helper builders**

Add functions for:
- unclassified daily entry
- unclassified weekly entry
- unclassified monthly entry
- unclassified analysis entry
- repeated hours/minutes conversions

**Step 2: Update stats logic to use helpers**

Replace inline repeated dictionary creation and repeated conversions with helper calls.

**Step 3: Keep public output stable**

Do not change the keys returned by:
- `get_daily_stats_data`
- `get_weekly_stats_data`
- `get_monthly_stats_data`
- `get_tag_analysis_data`
- `get_stats_context`

### Task 3: Extract Dashboard Business Helpers

**Files:**
- Create: `apps/dashboard/services.py`
- Modify: `apps/dashboard/views.py`

**Step 1: Add slot-header helper**

Move the repeated slot-header construction into a helper function.

**Step 2: Add slot-index validation helper**

Move the slot index list validation into a helper function that returns a boolean or raises a simple exception.

**Step 3: Update the view**

Use the new helpers while keeping the HTTP response contract unchanged.

### Task 4: Reduce Domain-Service Duplication

**Files:**
- Modify: `apps/users/domain_services.py`
- Modify: `apps/tags/domain_services.py`

**Step 1: Refactor goal progress lookup**

Replace repeated period branching with a stable internal extractor mapping.

**Step 2: Refactor tag policy duplication**

Introduce one shared internal authorization helper for edit/delete checks.

### Task 5: Verify Behavior

**Files:**
- Read: changed Python modules

**Step 1: Run focused tests**

Run:
`DJANGO_SECRET_KEY=test ./.venv/bin/python manage.py test apps.stats.tests apps.dashboard.tests apps.users.tests apps.tags.tests -v 2`

Expected:
All targeted unit tests pass.

**Step 2: Run full test suite**

Run:
`DJANGO_SECRET_KEY=test ./.venv/bin/python manage.py test -v 2`

Expected:
All project tests pass.

**Step 3: Run Django checks**

Run:
`DJANGO_SECRET_KEY=test ./.venv/bin/python manage.py check`

Expected:
`System check identified no issues`.

**Step 4: Verify diff hygiene**

Run:
`git diff --check -- apps/stats apps/dashboard apps/users apps/tags`

Expected:
No whitespace or patch formatting issues.
