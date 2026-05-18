# Project Status

Last updated: 2026-05-18

This document is the single status index for LifeDiary planning, execution, and follow-up documents. It does not replace the detailed documents linked below, and no existing plan or refactoring document should be deleted only because it is listed here.

Status values are based on the repository documents available at the update time. They are not fresh code verification unless a verification command is explicitly listed.

## Status Legend

| Status | Meaning |
|---|---|
| Completed | Execution log or verification evidence exists in project documents. |
| Active Plan | Planned work that appears relevant and not yet documented as completed. |
| Deferred | Intentional later work or out-of-scope item. |
| Superseded | Older planning context replaced by a newer execution log or status document. |
| Reference | Architecture, analysis, or guidance document, not a task backlog item. |
| Unknown | Status cannot be determined from documents alone. |

## Current Product Direction

LifeDiary is a Django-based life logging app. Users record a day in 10-minute slots, classify time with tags, manage goals and notes, and review life patterns through statistics and rule-based feedback.

The project has moved from a web-only portfolio app toward a desktop distribution path:

- local desktop app packaging with `pywebview`, `waitress`, SQLite, and PyInstaller;
- single local user desktop mode;
- GitHub Releases distribution;
- operational visibility and monetization experiments as later phases.

The current codebase direction is conservative: keep the Django monolith, maintain the app-level boundaries, and use the existing `views -> use_cases -> repositories/domain_services -> models` flow where it already exists.

## Completed Or Documented Execution

| Area | Evidence document | Summary | Verification evidence in document |
|---|---|---|---|
| Initial code review fixes | `docs/refactoring/2026-04-08_fix-log.md` | Fixed selected issues from the 2026-04-08 review, including stats/query and settings concerns. | Document lists verification commands and remaining unfixed items. |
| Phase 0 fixes | `docs/refactoring/2026-04-09_phase0-fix-log.md` | Fixed early architecture/review issues before repository extraction. | Document includes verification section. |
| Repository layer | `docs/refactoring/2026-04-09_phase1-repository-log.md` | Introduced repositories for dashboard, tags, users, goals, and notes. | Document includes import checks and verification. |
| Domain services | `docs/refactoring/2026-04-09_phase2-domain-service-log.md` | Introduced `GoalProgressService` and `TagPolicyService`. | Document includes grep checks and tests. |
| Frontend CSS refactor | `docs/frontend/2026-04-11-css-refactor.md` | Consolidated frontend tokens/components and loading overlay styling. | Document includes verification section. |
| Mobile dashboard responsive pass | `docs/frontend/2026-04-12-mobile-responsive.md` | Improved dashboard mobile responsiveness. | Document includes manual verification method. |
| Inline JS extraction | `docs/refactoring/2026-04-15-inline-js-extraction.md` | Extracted inline JS to static files and aligned dashboard/stats UI behavior. | Document records architecture decisions and changed files. |
| Tag contrast and category fixes | `docs/frontend/2026-04-15-tag-contrast-and-fixes.md` | Fixed tag category behavior and automatic contrast handling. | Document records changed files and implementation details. |
| Sidebar UX | `docs/frontend/2026-04-15-sidebar-ux.md` | Improved dashboard sidebar UX after user feedback. | Document records modified files and JS details. |
| Architecture/cost phases 3-4 | `docs/refactoring/2026-04-20_phase3-4-execution-log.md` | Applied cost and architecture changes including use cases, caching, and stats calculator decomposition. | Document records phase results and final structure. |
| Frontend template remediation | `docs/refactoring/2026-04-21_frontend-template-refactor-log.md` | Fixed stats weekday display, extracted partials/tags, renamed AI feedback to life feedback, and consolidated styles. | Document records final test section. |
| Security remediation | `docs/security/2026-04-21_xss-bruteforce-sri-remediation.md` | Fixed stored XSS risk, added brute-force protection with `django-axes`, and added CDN SRI hashes. | Document reports `55 passed / 0 failed` and lists remaining security work. |
| Post-phase architecture snapshot | `docs/refactoring/2026-04-21_post-phase4-state-update.md` | Captured post-Phase4 architecture status and remaining work. | Document reports `55 passed in 5.89s`. |
| Frontend DRY + dashboard UX | `docs/refactoring/2026-04-23_frontend-dry-and-dashboard-ux.md` | Improved global loading, cache invalidation, dashboard overlays, drag behavior, and frontend DRY structure. | Document includes browser manual checklist. |
| Dashboard tag UX + stats tab preserve | `docs/refactoring/2026-04-24_dashboard-tag-ux-and-stats-tab-preserve.md` | Added dashboard tag legend/category UX and preserved active stats tab on date changes. | Document includes final verification section. |
| Dashboard mobile bottom sheet | `docs/plans/2026-05-15_dashboard-mobile-bottom-sheet-design.md`, `docs/plans/2026-05-15_dashboard-mobile-bottom-sheet.md`, `docs/plans/2026-05-15_dashboard-bottom-sheet-01-line-design.md`, `docs/plans/2026-05-15_dashboard-bottom-sheet-01-line.md`, `docs/plans/2026-05-15_dashboard-tag-list-compact-row.md`, `docs/plans/2026-05-15_tag-category-select-font-size.md`, `docs/frontend/2026-05-15-dashboard-mobile-bottom-sheet.md`, `docs/refactoring/2026-05-15_dashboard-mobile-bottom-sheet.md` | Added a mobile-only quick input bottom sheet for the dashboard so selected slots can be tagged without scrolling to the desktop sidebar. Desktop sidebar behavior remains in place. Touch cancellation now guards `event.cancelable` to avoid browser intervention warnings while scrolling. The sheet height is capped from the grid's 01:00 line to the viewport bottom. Quick input category headers now use `-`, tag buttons use a compact wrapping row content-width layout, and the tag modal category select uses readable 1rem text. | Fresh verification: `conda run -n knou-life-diary pytest apps/dashboard/tests.py --tb=short` -> `14 passed in 7.45s`; `conda run -n knou-life-diary pytest apps/tags/tests.py apps/tags/test_i18n_phase3.py --tb=short` -> `33 passed in 13.70s`; `node --check apps/dashboard/static/dashboard/js/dashboard.js` -> exit 0; `git diff --check` -> exit 0; full suite -> `174 passed in 80.43s (0:01:20)`. Manual mobile browser checks remain unverified. |
| Stats life feedback toggle | `docs/plans/2026-05-15_stats-life-feedback-toggle-design.md`, `docs/plans/2026-05-15_stats-life-feedback-toggle.md`, `docs/refactoring/2026-05-15_stats-life-feedback-toggle.md` | Changed the stats page life feedback list from always-visible toast cards to a default-closed Bootstrap collapse section with count badge, accessible toggle attributes, and compact responsive styling. The expanded feedback cards use a horizontal wrapping row without sideways scrolling. Feedback generation and ordering remain unchanged. | Fresh verification: `conda run -n knou-life-diary pytest apps/stats/test_mobile_layout.py::TestLifeFeedbackToggleStructure --tb=short` -> `2 passed in 1.58s`; stats regression bundle -> `22 passed in 8.44s`; `node --check apps/stats/static/stats/js/stats.js` -> exit 0; `git diff --check` -> exit 0; full suite -> `176 passed in 78.74s (0:01:18)`. Manual mobile browser interaction remains unverified. |
| Korean-English i18n | `docs/refactoring/2026-04-28_i18n-phase1-5-execution-log.md` | Completed i18n phases for base/core, dashboard, tags, users, and stats using `LocalizableMessage` and JS catalog. | Document includes verification section and phase commits. |
| pytest migration | `docs/refactoring/2026-04-28_pytest-migration.md` | Converted unittest-style tests to pytest-native style and expanded fixtures. | Document reports `111 passed in 45.02s`. |
| Account recovery and email infrastructure | Code analysis: `apps/users/urls.py`, `apps/users/forms.py`, `apps/users/views.py`, `apps/core/email_backends.py`, `apps/users/templates/users/password/`, `apps/users/templates/users/recovery/` | Implemented password reset, username recovery, signup email capture/validation, and Resend HTTPS email backend. | Fresh verification: `conda run -n knou-life-diary pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_signup_email.py apps/core/test_email_backends.py ... --tb=short` included in a 50-test run, `50 passed in 29.65s`. |
| Production deploy email readiness | `docs/plans/2026-05-15_production-deploy-email-readiness.md`, `docs/refactoring/2026-05-15_production-deploy-email-readiness.md`, `.github/workflows/deploy-pr.yml`, `lifeDiary/settings/prod.py`, `lifeDiary/test_prod_settings.py` | Added a production settings regression test, set production `DEBUG=False`, added deploy PR verification before PR creation/update, and documented that live recovery email delivery is deferred until a sender domain is purchased/configured and verified in Resend. | Fresh verification: `conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short` -> `3 passed`; prod deploy check -> `System check identified no issues`; `ruby ... YAML.load_file(...)` -> `yaml ok`; full suite -> `167 passed in 73.18s`. |
| Footer copyright LogBetter display | `docs/refactoring/2026-05-18_footer-copyright-logbetter.md` | Updated the shared footer copyright notice to use `LogBetter`, with a 2025 service-start year range and localized app names: Korean screens show `라이프 다이어리 © 2025-2026 LogBetter. All rights reserved.`, and English screens show `Life Diary © 2025-2026 LogBetter. All rights reserved.` for the current year. | Fresh verification: targeted RED failed before implementation for the missing footer strings; after implementation `conda run -n knou-life-diary pytest apps/core/tests.py::TestHomePage::test_home_page_renders_korean_footer_copyright apps/core/test_i18n_phase1.py::TestHomePageEnglish::test_home_page_renders_english_footer_copyright --tb=short` -> `2 passed in 0.64s`; focused core/i18n regression `conda run -n knou-life-diary pytest apps/core/tests.py apps/core/test_i18n_phase1.py --tb=short` -> `12 passed in 1.92s`. |
| Auth onboarding and signup UX | Code analysis: `apps/users/views.py`, `apps/users/urls.py`, `apps/users/templates/users/login.html`, `apps/users/templates/users/signup.html`, `apps/users/templates/users/welcome.html`, `apps/users/static/users/js/` | Implemented remember-me session behavior, signup-to-welcome flow, realtime username/email checks, password visibility/strength enhancements, and auth JS i18n catalog wiring. | Fresh verification: auth-related tests included in the same 50-test run, `50 passed in 29.65s`. |
| Stats goal cards and mobile tab structure tests | Code analysis: `apps/stats/templates/stats/life_feedback.html`, `apps/stats/templates/stats/_goal_accordion_item.html`, `apps/stats/test_goal_accordion.py`, `apps/stats/test_mobile_layout.py` | Implemented daily/weekly/monthly goal cards with per-card collapse behavior, weekly default expansion, count badges, and empty-state add links. Stats tab structure regression tests exist. | Fresh verification: stats goal/mobile tests included in the same 50-test run, `50 passed in 29.65s`. |
| Stats UserGoal query consolidation and performance guard | Code analysis: `apps/users/repositories.py`, `apps/stats/logic.py`, `apps/users/test_goal_repository.py`, `apps/stats/test_stats_perf.py` | Implemented `GoalRepository.find_grouped_by_period()` and stats context usage to fetch goals once and split by period; query target is guarded by performance tests. | Fresh verification: `conda run -n knou-life-diary pytest apps/users/test_goal_repository.py apps/stats/test_stats_perf.py --tb=short` -> `7 passed in 8.12s`. |

## Active Plans

| Priority | Document | Scope | Next decision or action |
|---|---|---|---|
| High | `docs/plans/2026-05-07_desktop-auth-single-user-plan.md` | Desktop mode auto-login with one local user; block auth pages only in desktop settings. | Approve or revise scope, then create an integrated implementation plan before code work. |
| High | `docs/plans/2026-05-03_desktop-app-packaging-plan.md` | Package the Django app as macOS `.app` and Windows `.exe` with pywebview, waitress, and PyInstaller. | Partial code exists (`desktop/launcher.py`, `lifeDiary/settings/desktop.py`, `requirements-desktop.txt`), but no PyInstaller spec or release workflow was found in this pass. Confirm scope before continuing. |
| Medium | `docs/plans/2026-05-07_stats-dashboard-mobile-ui-plan.md` | Improve mobile stats/dashboard UX: stacked stats sections, goal accordion, feedback reveal, mobile tag bottom sheet. | Goal cards, dashboard mobile bottom sheet, and default-closed stats feedback reveal are implemented and covered by focused tests. Re-check item #1 expectations before marking complete because current tests preserve tab structure rather than requiring all mobile panes to be stacked. |
| Medium | `docs/plans/2026-04-26_stats-tab-performance-plan.md` | Measure and optimize stats tab backend queries and chart rendering. | Backend query consolidation and query-count guards are implemented and verified. Frontend chart lazy render was not confirmed in this pass. |
| Strategic | `docs/plans/2026-05-06_distribution-and-monetization-plan.md` | Public distribution, operational infrastructure, monetization experiment, portfolio metrics. | Treat as roadmap; each phase requires explicit approval. |

## Code Found But Not Fully Completed

| Area | Files found | Current read |
|---|---|---|
| Desktop packaging foundation | `desktop/launcher.py`, `lifeDiary/settings/desktop.py`, `requirements-desktop.txt` | Basic desktop runtime foundation exists: desktop settings, user data directory, local SQLite path, persisted secret key, axes disabled in desktop auth backends/middleware, waitress server, pywebview launcher, migrate, and local collectstatic. The broader packaging plan still appears incomplete because `desktop/lifediary.spec`, desktop README, and release workflow were not found. |
| Desktop single local user auth | `docs/plans/2026-05-07_desktop-auth-single-user-plan.md`, `lifeDiary/settings/desktop.py`, `desktop/launcher.py` | The desktop settings/launcher exist, but the planned local user bootstrap, desktop auth middleware, context processor, auth-page blocking, and logout hiding were not found in this pass. Keep this as active planned work. |

## Superseded Or Historical Plans

| Document | Current status | Superseded or informed by |
|---|---|---|
| `prompt_plan.md` | Superseded as implementation plan | `docs/refactoring/2026-04-28_i18n-phase1-5-execution-log.md` is the current i18n execution record. |
| `docs/plans/2026-05-01_account-recovery-plan.md` | Completed by code analysis and fresh targeted tests | Password reset, username recovery, signup email validation, and Resend backend are implemented. |
| `docs/plans/2026-04-26_stats-goal-repo-refactor-plan.md` | Completed by code analysis and fresh targeted tests | `GoalRepository.find_grouped_by_period()` and stats context usage are implemented. |
| `docs/plans/2026-04-09_light-ddd-plan.md` | Largely completed / historical | Phase 0-2 logs and later architecture execution logs. |
| `docs/plans/2026-04-11-business-logic-refactor-design.md` | Historical design | Later repository/domain/use case execution logs. |
| `docs/plans/2026-04-11-business-logic-refactor.md` | Historical implementation plan | Later architecture and phase logs. |
| `docs/plans/2026-04-20_architecture-and-cost-plan.md` | Historical plan | `docs/refactoring/2026-04-20_phase3-4-execution-log.md` and `2026-04-21_post-phase4-state-update.md`. |
| `docs/plans/2026-04-21_architecture-and-cost-plan.md` | Snapshot / historical | Use as reference, not the primary active backlog. |
| `docs/plans/2026-04-20_frontend-template-remediation-plan.md` | Completed / historical | `docs/refactoring/2026-04-21_frontend-template-refactor-log.md`. |
| `docs/plans/2026-04-20_review-remediation-plan.md` | Mostly historical | Later architecture, frontend, pytest, and security execution logs cover much of the remediation. |
| `docs/plans/2026-04-11-home-main-ui-design.md` | Historical design | Check current UI before using. |
| `docs/plans/2026-04-11-home-main-ui.md` | Unknown / likely historical | No direct execution log was matched in this pass. |

## Reference Documents

| Document | Purpose |
|---|---|
| `AGENTS.md` | Operating guide for agent roles, project file flow, TDD rules, review gates, and completion reporting. |
| `docs/architecture/2026-04-21_business-logic-and-architecture-guide.md` | Product and architecture guide for LifeDiary's business flow, domain model, and app responsibilities. |
| `docs/refactoring/2026-04-08_code-review.md` | Original 2026-04-08 review findings and action items. |
| `docs/refactoring/2026-04-09_business-logic-analysis.md` | Early business logic analysis and service-layer refactoring direction. |
| `docs/refactoring/2026-04-20_backend-flow-and-improvements.md` | Backend flow and improvement snapshot before later phase completion. |
| `docs/refactoring/2026-04-21_backend-flow-and-improvements.md` | Updated backend flow and remaining improvement snapshot. |

## Deferred Or Later Work

| Area | Source | Deferred work |
|---|---|---|
| i18n | `docs/refactoring/2026-04-28_i18n-phase1-5-execution-log.md` | Japanese support, DRF API behavior, cache key locale split, and Chart.js locale configuration. |
| Security | `docs/security/2026-04-21_xss-bruteforce-sri-remediation.md` | CSP, stronger cookie/security flags, production debug review, and login failure notifications. |
| pytest | `docs/refactoring/2026-04-28_pytest-migration.md` | More locale parametrization, possible `factory_boy`, and optional locale leak guard fixture. |
| Desktop distribution | `docs/plans/2026-05-06_distribution-and-monetization-plan.md` | Code signing, notarization, auto-update, operational metrics, and monetization phases. |
| Account recovery | `docs/plans/2026-05-01_account-recovery-plan.md` | Social login, recovery endpoint rate limiting, email verification, and email backfill policy. |
| Account recovery email delivery | `docs/refactoring/2026-05-15_production-deploy-email-readiness.md` | Live Resend recovery email delivery is deferred until a sender domain is purchased/configured, DNS records are set, and Resend marks the domain as verified. No live delivery verification has been performed. |

## Next Recommended Work

1. Choose one active plan as the next approved scope.
2. Before code work, create an integrated plan document that combines analyst requirements, design, risks, TDD checkpoints, and verification commands.
3. For a small implementation start, consider either:
   - `docs/plans/2026-05-07_desktop-auth-single-user-plan.md`; or
   - the remaining unimplemented items from `docs/plans/2026-05-07_stats-dashboard-mobile-ui-plan.md`.
4. After each completed implementation, update this `docs/project-status.md` file and write the required refactoring document.

## Fresh Verification From This Status Update

Commands run on 2026-05-14:

```bash
conda run -n knou-life-diary pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_signup_email.py apps/core/test_email_backends.py apps/users/test_remember_me.py apps/users/test_realtime_validation.py apps/users/test_welcome.py apps/users/test_auth_enhance_render.py apps/users/test_jsi18n_auth.py apps/stats/test_goal_accordion.py apps/stats/test_mobile_layout.py --tb=short
# 50 passed in 29.65s

conda run -n knou-life-diary pytest apps/users/test_goal_repository.py apps/stats/test_stats_perf.py --tb=short
# 7 passed in 8.12s
```

Commands run on 2026-05-15:

```bash
conda run -n knou-life-diary pytest lifeDiary/test_prod_settings.py apps/core/test_email_backends.py --tb=short
# 3 passed in 0.07s

DJANGO_SECRET_KEY=test-ci-secret-value-for-deploy-readiness-checks-only-1234567890 DB_NAME=test_db DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost DB_PORT=6543 RESEND_API_KEY=re_test_dummy DEFAULT_FROM_EMAIL='LifeDiary <noreply@example.com>' conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
# System check identified no issues (0 silenced).

ruby -e "require 'yaml'; YAML.load_file('/Users/yeongroksong/Desktop/study/project/knou/.github/workflows/deploy-pr.yml'); puts 'yaml ok'"
# yaml ok

conda run -n knou-life-diary pytest --tb=short
# 167 passed in 73.18s
```

The default local `python -m pytest ...` command failed before test collection because the default Python environment did not initialize Django settings/apps correctly. The conda environment used by project documents, `knou-life-diary`, was used for the successful verification runs.
