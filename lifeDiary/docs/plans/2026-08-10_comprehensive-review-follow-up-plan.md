# Design Completion and Comprehensive Review Follow-up Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the active design iteration, re-review its final UI, then fix
the confirmed data-integrity, cache, i18n, accessibility, and operations gaps
without mixing those changes into the design work.

**Architecture:** `dashboard` owns `TimeBlock` writes; `tags` owns tag
policy; `users` owns account lifecycle; and `stats` reads only
owner-scoped data through app query paths. Design-dependent browser findings
are re-evaluated against final templates and JavaScript. Design-independent
release blockers remain required remediation work.

**Tech Stack:** Django 5.2, pytest/pytest-django, GNU gettext, vanilla
browser JavaScript, Bootstrap, Chart.js, GitHub Actions, pywebview/Waitress.

---

## User-approved sequencing

The user chose this order on 2026-08-10:

1. Complete the current design-sian work.
2. Re-review final frontend and browser behavior.
3. Plan and repair the remaining UI issues as one consolidated scope.
4. Plan and repair backend, i18n, and operations issues as separate,
   test-driven scopes.

This plan records that decision and the audit input. It authorizes no code,
settings, infrastructure, dependency, release, or Git change on its own.
Each implementation unit still needs explicit user scope approval and an
integrated execution plan.

### Explicit exclusions

- No application, template, CSS, JavaScript, settings, migration, CI, or
  deployment edits in this documentation task.
- No repeated frontend verdict before the user declares the active design
  iteration complete.
- No scheduler-provider, backup-system, desktop-packaging, or release-workflow
  decision without a separate approval.
- No agent commit, push, merge, or pull request.

## Activated Roles

- Backend & Integration Engineer — documentation ownership.
- Quality Verification Lead — maps findings to future evidence.
- Domain Architecture Reviewer — ownership, dependencies, and cache boundary.
- Security & Resilience Reviewer — privacy, XSS, and account-lifecycle risk.
- Deployment & Operations Reviewer — scheduler, desktop, CI, backup, release.
- Web Experience Designer and Browser Interaction Reviewer — final-design
  dual-review gate.

### Not Activated

- Product Scope Owner — the user explicitly chose the sequence.
- Backend TDD Coach — no backend behavior changes in this task; activate
  before the first approved remediation implementation.
- Frontend Implementation Engineer — no frontend files change here.
- AI Automation Architect — no AI/LLM scope.

## Findings and execution lanes

### Lane A — P0 release blockers, independent of design

| ID | Finding | Source evidence | Required direction |
|---|---|---|---|
| TAG-OWN-01 | Deleting a global default tag can migrate every user's blocks to an administrator's private tag. | `apps/tags/use_cases.py:112-130`; `apps/dashboard/repositories.py:95-96` | Permit global-source migration only to a global/default destination, or reject deletion. |
| TAG-OWN-02 | A superuser editing another user's private tag can transfer that tag's owner. | `apps/tags/repositories.py:41-45`; `apps/tags/use_cases.py:95-99` | Preserve the private-tag owner or disallow the cross-user flow. |
| STATS-CACHE-01 | Cached week/month/rolling statistics and goal/note/tag inputs can remain stale for 24 hours. | `apps/stats/logic.py:29-83`; `apps/stats/use_cases.py:10-34` | Invalidate every affected period/input with a per-user cache version or post-commit events. |
| I18N-01 | GNU gettext cannot compile Korean server or JS catalogs. | `locale/ko/LC_MESSAGES/django.po:347`; `djangojs.po:99` | Correct Korean plural forms and verify with GNU `msgfmt --check`. |
| ACC-OPS-01 | The 15-day account-deletion deadline has no scheduled purge or monitoring. | `apps/users/management/commands/purge_deleted_accounts.py:1-11`; `.github/workflows/deploy-pr.yml:3-42` | Approve scheduler, overdue metric, failure alert, recovery runbook, and desktop policy. |

### Lane B — final-design re-review required

| ID | Review target | Current evidence |
|---|---|---|
| FE-KEY-01 | First Shift+Arrow selection must not throw and must select a valid range. | `apps/dashboard/static/dashboard/js/dashboard.js:417` uses undefined `slotIndex`. |
| FE-FOCUS-01 | A closed mobile quick-input sheet must have no focusable descendant. | `dashboard.js:161-167,253-270`; `apps/core/static/core/css/style.css:1329-1346` |
| FE-XSS-01 | Tag names and memos must not enter inline JavaScript strings or `innerHTML` sinks. | `apps/tags/templates/tags/index.html:84,109`; `dashboard.js:558-593`; `apps/core/static/core/js/utils.js:51` |
| FE-A11Y-01 | Selection state, loading state, close labels, reduced motion, tables, and chart alternatives need final-design evaluation. | 2026-08-10 audit; refresh locations after design completion. |

### Lane C — separately approved architecture and reliability work

- Carry owner-scoped tag identity/color through stats aggregation instead of a
  global tag-name lookup.
- Use `timezone.localdate()` for My Page goal progress.
- Make concurrent slot save/restore idempotent or conflict-safe.
- Resolve `dashboard <-> tags` and `users <-> stats` cycles without a new
  framework or service split.
- Replace the stats receiver's `DummyCache` setup with a retaining cache.
- Verify desktop first run, failed upgrade migration, backup/restore, and
  packaged-app behavior before distribution claims.

## Post-design dual review gate

Run this only after the user declares the design iteration complete and its
final branch/diff is stable.

1. Record the branch and commit; run the baseline commands below.
2. Web Experience Designer reviews hierarchy, responsiveness, static
   accessibility, forms, empty states, and copy.
3. Browser Interaction Reviewer traces keyboard, focus, touch, Escape, async
   success/failure/retry, motion, overlays, and dynamic content.
4. Inspect 375, 768, 1024, and 1440 CSS-pixel widths, keyboard-only use, and
   at least one assistive-technology-oriented state check where practical.
5. Both reviewers return `Conforms`, `Deviates`, or `Unverified`; Quality
   Verification Lead maps verdicts to acceptance criteria.
6. Create a frontend implementation plan only for findings still present.

Required scenarios include quick-input open/close/Tab/focus return,
Shift+Arrow as first slot action, quoted/HTML-like Korean and English tag and
memo values, save/failure/undo/retry, empty state, mobile navigation, and
reduced-motion behavior.

## Future backend Test List

These are Pending. The Backend TDD Coach must take exactly one to Red before
production code changes.

| Scenario ID | Business behavior | Given / When / Then | Boundary | Test name | Status |
|---|---|---|---|---|---|
| TAG-OWN-01 | Global tag cannot migrate records to a private tag. | Given two users use a default tag; when admin selects private destination; then rejection leaves both records valid. | domain | `test_deleting_default_tag_rejects_private_destination` | Pending |
| TAG-OWN-02 | Staff edit does not change private tag ownership. | Given another user's tag; when superuser changes fields; then owner and valid blocks remain unchanged. | domain | `test_staff_update_preserves_private_tag_owner` | Pending |
| STATS-CACHE-01 | Relevant mutations refresh affected statistics views. | Given cached daily/week/month/rolling views; when slot/goal/note/tag changes; then affected entries are invalidated. | domain | `test_stats_input_change_invalidates_affected_periods` | Pending |
| I18N-01 | Korean catalogs compile with GNU gettext. | Given tracked Korean PO files; when GNU check runs; then both exit zero. | contract | `test_korean_catalogs_compile_with_gnu_gettext` or CI check | Pending |
| ACC-OPS-01 | Due deletion requests are purged by the approved schedule. | Given a past-deadline user; when scheduled job runs; then account is purged and telemetry emitted. | contract/slow | provider-specific after approval | Deferred |
| STATS-TZ-01 | Goal progress uses configured local date. | Given KST date differs from UTC date; when My Page loads; then Korean date is used. | domain | `test_my_page_progress_uses_local_date` | Pending |
| STATS-TAG-01 | Top-tag color comes from owning user's tag. | Given same-named tags with different colors; when stats load; then each user sees own color. | domain | `test_top_tag_uses_owner_scoped_tag_color` | Pending |

## Execution tasks after approval

### Task 1: Freeze the review baseline

**Files:** Read final design diff, `docs/plans/2026-08-01_p0-redesign-plan.md`,
and this plan. No files change.

1. Record final branch and commit in the execution plan.
2. Run baseline checks and retain complete output in the work log.
3. Confirm unrelated worktree changes are excluded.

### Task 2: Re-run frontend dual review

**Files:** Read final templates, CSS, JavaScript, and locale catalogs. No files
change in this review step.

1. Deliver review-only Web Experience Designer output.
2. Deliver review-only Browser Interaction Reviewer output.
3. Create a separate frontend plan for remaining issues and browser evidence.

### Task 3: Repair ownership and statistics correctness

**Files:** Modify only after approval: `apps/tags/use_cases.py`,
`apps/tags/repositories.py`, `apps/dashboard/repositories.py`,
`apps/stats/use_cases.py`, `apps/stats/logic.py`, and relevant aggregation
or query-port modules. Test `apps/tags/test_tag_migration.py`,
`apps/stats/test_receivers.py`, and focused domain tests.

1. Write one failing scenario test.
2. Run it and confirm the expected Red failure.
3. Implement the smallest owner-scoped behavior.
4. Run the focused test and relevant app regression slice.
5. Record TDD Coach Green evidence before refactoring.

### Task 4: Repair i18n build correctness

**Files:** Modify only after approval: Korean `django.po`, `djangojs.po`,
and only necessary catalog coverage.

1. Run both GNU `msgfmt --check` commands to capture Red.
2. Correct the smallest plural-form error.
3. Re-run GNU checks and locale regression.

### Task 5: Implement operations remediation after provider decision

**Files:** Modify only after approval: scheduler/release configuration and
deployment/desktop recovery documentation.

1. Choose production scheduler and desktop purge policy with the user.
2. Define idempotency, observability, missed-run recovery, and rollback.
3. Implement and test an isolated overdue-account path.

## Verification commands

```bash
conda run -n knou-life-diary pytest --tb=short
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
msgfmt --check -o /dev/null locale/ko/LC_MESSAGES/django.po
msgfmt --check -o /dev/null locale/ko/LC_MESSAGES/djangojs.po
node --check apps/core/static/core/js/tag.js
node --check apps/dashboard/static/dashboard/js/dashboard.js
node --check apps/stats/static/stats/js/stats.js
```

Completion later requires targeted Red/Green records, focused regressions, full
pytest, clean migration drift, GNU catalog checks, Django checks, and both
post-design browser verdicts. Live scheduler, deployed headers/mail, packaged
desktop, real-device, and screen-reader checks remain unverified until run.

## Deferred Refactoring Note

```text
- Topic: Full dashboard/tags and users/stats boundary decoupling
- Why it is not part of the current scope: Restore ownership and cache
  correctness with the smallest safe boundary change first.
- Trigger condition: Another cross-app workflow needs shared orchestration.
- Expected change location: apps/dashboard/, apps/tags/, apps/users/, apps/stats/
- Related tests: boundary-contract and cache-invalidation suites.
```
