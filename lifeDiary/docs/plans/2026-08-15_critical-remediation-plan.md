# Critical Correctness, Security, and Account Lifecycle Remediation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore trustworthy statistics, remove the stored DOM-XSS boundary,
make dashboard delete state truthful, and give local and Google users the same
registration and account-deletion lifecycle.

**Architecture:** Keep the Django monolith and current app ownership. Stats uses
stable internal tag keys and subscribes to owner-app post-commit signals;
dashboard and tags remain the only writers of slot/tag state; users owns
registration and deletion orchestration. Frontend user data is rendered through
DOM text nodes, never reconstructed as HTML.

**Tech Stack:** Django 5.2, pytest/pytest-django, django-allauth 65.17,
vanilla JavaScript, Bootstrap, Chart.js, Django cache framework, SQLite in
development and the configured production database.

---

## Document Status

- Design approval: user approved on 2026-08-15.
- Implementation approval: not implied by this document; execute one Lane only
  after the user selects it.
- Source design: `docs/plans/2026-08-15_critical-remediation-design.md`.
- Supersedes: unresolved implementation scope in
  `docs/plans/2026-08-10_comprehensive-review-follow-up-plan.md`.
- Git actions: the agent must not commit, push, merge, or open a PR. At a user
  checkpoint, provide copy-ready commands and commit messages only.

## Approved Scope

### Lane A — statistics and record integrity

- Collision-proof real-tag and synthetic-unclassified identity in daily,
  weekly, monthly, analysis, and hourly chart data.
- Sleep policy by category slug rather than editable translated tag name.
- Delete-without-destination removes source TimeBlocks and memo data.
- Remove legacy tagless rows and require a tag for every future TimeBlock.
- Per-user stats cache generation rotated after committed slot, tag, goal, or
  note mutations.

### Lane B — dashboard security and core interaction

- Remove tag/memo data from `innerHTML` paths.
- Remove implicit global `event` use during tag selection.
- Separate HTTP delete failure from post-commit UI/event failure.
- Send the actual deleted slot list in the success event.

### Lane C — account lifecycle

- Re-request deletion after a prior cancellation.
- Atomic local and Google account bootstrap.
- Explicit legal consent before Google account creation.
- Seed tags for Google-created users.
- Cancel pending deletion through an already-linked Google identity only within
  the grace period.
- Preserve purge cascade and audit behavior; specify but do not choose the
  production scheduler without a separate provider approval.

## Explicit Exclusions

- Desktop boot/auth/packaging/offline remediation.
- General dashboard/stats accessibility and responsive-layout findings.
- SMTP, reCAPTCHA, axes threshold, shared atomic throttle backend.
- Slot payload uniqueness, tag-name API length, broad API error translation.
- New queue, Celery, service split, or event-bus framework.
- Full CSP nonce migration.
- Provider-specific scheduler file before the user chooses the provider.

## Activated Roles

- Product Scope Owner — approved destructive meaning of “기록까지 함께 삭제”.
- Domain Architecture Reviewer — stable identity, dependency direction, cache
  generation, signal, and transaction boundaries.
- Backend TDD Coach — one next-smallest backend behavior at a time.
- Backend & Integration Engineer — backend, migrations, tests, settings, and
  general documentation.
- Security & Resilience Reviewer — XSS, social identity, lifecycle and purge
  failure modes.
- Deployment & Operations Reviewer — irreversible migration, backup, scheduler,
  and rollout gates.
- Web Experience Designer — social-consent screen and post-delete status copy.
- Browser Interaction Reviewer — XSS, selection, success/failure, event, focus,
  and console behavior.
- Frontend Implementation Engineer — approved template and JavaScript files.
- Quality Verification Lead — evidence matrix and final completion verdict.

### Not Activated

- AI Automation Architect — no LLM, classifier, prompt, or model evaluation.

## Domain Boundary and Dependency Direction

```text
dashboard use cases -> dashboard repository -> TimeBlock
       │
       └─ on_commit(time_blocks_changed)

tags use cases -> Tag + dashboard repository maintenance methods
       │
       └─ on_commit(tags_changed)

users use cases/forms/adapters -> User lifecycle + tags seed service
       │
       ├─ on_commit(goals_changed)
       └─ on_commit(notes_changed)

stats receivers -> dashboard/tags/users signals -> rotate stats generation
stats aggregation -> dashboard/users read repositories
```

- No owner app imports `apps.stats`.
- Stats may import the public signal objects of apps it reads.
- Tags continues to own deletion policy; dashboard owns TimeBlock persistence.
- Users owns auth/lifecycle orchestration and calls the existing tags bootstrap
  service only at registration boundaries.
- `apps/dashboard/test_domain_boundaries.py` must continue to reject
  dashboard-to-stats imports.

## Coupling and Cohesion Review

- A small `apps/stats/aggregation/identity.py` is preferred over repeating
  `tag:<id>` construction in four aggregators.
- Cache generation functions stay in `apps/stats/use_cases.py`; do not create a
  repository or service class for two cache operations.
- Signals carry only `user_id` and domain-relevant metadata. They do not carry
  ORM objects or precomputed stats payloads.
- Do not connect broad model `post_save` handlers. Only approved use cases emit
  events so imports, migrations, fixtures, and admin maintenance do not create
  surprising cache work. The TimeBlock FK invariant protects out-of-band tag
  deletion separately.
- Social form and adapter stay in `apps.users`; do not put account lifecycle in
  tags or core.
- Keep the existing Django monolith. This remediation does not justify a new
  command bus, generic Unit of Work, or shared domain-events package.

## Pythonic Code Design

- Use small module-level functions for tag keys and cache generation.
- Use immutable strings for identity keys and a random token rather than a
  mutable global counter.
- Capture values in `transaction.on_commit()` callbacks with keyword/default
  arguments so later mutation cannot change the emitted user/date.
- Keep public result dicts explicit. Do not use magic tuple positions.
- Use `select_for_update()` only around the existing deletion-request row and
  due purge rows; do not lock unrelated users.
- Prefer `replaceChildren()` and named DOM construction helpers to large nested
  HTML template literals.
- Failure injection may mock `create_seed_tags` or a browser event listener;
  ordinary behavior tests must assert persisted/public results rather than
  internal call counts.

## Acceptance Criteria

| ID | Acceptance criterion |
|---|---|
| AC-STAT-1 | Korean and English user tags matching the unclassified display name remain separate from synthetic unrecorded time in daily, weekly, monthly, analysis, and hourly chart data. |
| AC-STAT-2 | A sleep-category tag contributes the same active-week result before and after a name/language change. |
| AC-TAG-1 | Delete-without-destination removes the source tag, its TimeBlocks, and their memos; delete-with-destination preserves records and memos under the destination. |
| AC-TAG-2 | No valid TimeBlock can be stored without a tag after migration; legacy tagless rows are removed with a documented backup-only rollback. |
| AC-CACHE-1 | A committed slot, tag, goal, or note change invalidates every cached stats date/language for that user. |
| AC-CACHE-2 | A rolled-back mutation does not invalidate the previously valid cache generation. |
| AC-FE-1 | HTML-like memo/tag text is displayed literally and creates no DOM element or event handler. |
| AC-FE-2 | Tag selection works without `window.event`. |
| AC-FE-3 | Only HTTP DELETE failure restores the old snapshot; success remains success if rendering or event consumption fails. |
| AC-ACC-1 | A cancelled deletion can be requested again with a new 15-day deadline. |
| AC-ACC-2 | Local and Google signup both require consent, create seed tags, and roll back the user if bootstrap fails. |
| AC-ACC-3 | An already-linked Google login cancels deletion before, but not at or after, the deadline. |
| AC-OPS-1 | Production purge automation is not marked complete until a provider, schedule, overlap protection, alert, overdue signal, and recovery command are verified. |

## Backend Test List

Every `Pending` entry starts as exactly one failing test. The Backend TDD Coach
must approve its Red reason before production changes for that scenario.

### Statistics identity

| Scenario ID | Business behavior | Given | When | Then | Boundary / rationale | Test name | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| STAT-ID-01 | A real tag named like the translated unclassified label keeps only its recorded daily time. | A user has one 10-minute block tagged `미분류` or `Unclassified`. | Daily statistics are calculated in the matching locale. | The real tag has 10 minutes and the synthetic entry has 1,430 minutes, with distinct keys. | domain; DB is required to prove persisted tag identity through the real aggregation boundary. | `test_user_tag_named_unclassified_stays_separate_in_daily_statistics` with `ko`/`en` ids | Green | Red 2026-08-15: `pytest apps/stats/aggregation/test_tag_identity.py::test_user_tag_named_unclassified_stays_separate_in_daily_statistics -q` -> `2 failed` (`key` 필드 부재로 실제 entry 조회 실패, en 출력에서 합성 143블록/실제 1블록 분리 없음 확인). Green: 같은 노드 + `apps/stats/tests.py` -> 12 passed; `node --check apps/stats/static/stats/js/stats.js` exit 0. |
| STAT-ID-02 | The same-name real tag does not become a full-month record. | The same one-block record exists in a 31-day month. | Monthly statistics are calculated. | The real tag total is 0.2 hours and active days is 1; it is not merged with empty time. | domain; monthly aggregation is a distinct observable result. | `test_user_tag_named_unclassified_stays_separate_in_monthly_statistics` with `ko`/`en` ids | Green | Red 2026-08-15: targeted -q -> `2 failed` (월간 entry에 key 부재, ko는 병합). Green: targeted + `apps/stats/tests.py` + `apps/stats/aggregation/test_weekly_summary.py` -> 25 passed. |
| STAT-ID-03 | Weekly tag totals keep real and synthetic unclassified rows separate. | One matching-name block exists in a selected week. | Weekly statistics are calculated. | The real tag has 10 minutes and synthetic time remains separately marked `is_unclassified`. | domain; weekly aggregation owns a separate output contract. | `test_user_tag_named_unclassified_stays_separate_in_weekly_statistics` with `ko`/`en` ids | Green | Red 2026-08-15: targeted -q -> `2 failed` (tag_weekly_stats entry에 key 부재). Green: targeted + `apps/stats/tests.py` -> 12 passed. |
| STAT-ID-04 | Monthly analysis never attributes empty time to a matching-name real tag. | One matching-name block exists in the month. | Tag analysis is calculated. | The real tag reports 0.2 hours rather than the month’s empty hours. | domain; analysis filters synthetic rows independently of monthly charts. | `test_user_tag_named_unclassified_stays_separate_in_tag_analysis` with `ko`/`en` ids | Green | Red 2026-08-15: targeted -q -> `2 failed` (analysis entry에 key 부재, ko 병합). Green: targeted -> 2 passed; 회귀 `apps/stats/aggregation apps/stats/tests.py apps/stats/test_stats_perf.py -q` -> 124 passed(쿼리 예산 유지); `node --check` exit 0. |
| STAT-WEEK-01 | Active-week totals use category semantics, not an editable name. | A sleep-category tag has either `수면`, `Sleep`, or a custom name and one block. | Weekly statistics are calculated. | Active total and active-day count are identical for all names and exclude that sleep block. | domain; category slug is persisted and the aggregate is user-visible. | `test_sleep_category_is_excluded_from_active_week_totals_after_rename` with name ids | Green | Red 2026-08-15: targeted -q -> `수면` 통과·`Sleep`/`낮잠자기` `2 failed` (이름 기반 제외). Green: targeted -> 3 passed; 회귀 `apps/stats/aggregation apps/stats/tests.py apps/stats/test_stats_perf.py -q` -> 127 passed. get_tag_info에 category_slug 추가, N+1 방지를 위해 find_by_date/find_by_month에 tag__category join 확장(쿼리 수 불변, perf 계약으로 검증). SLEEP_TAG_NAME 상수 제거. |

### Tag deletion and migration

| Scenario ID | Business behavior | Given | When | Then | Boundary / rationale | Test name | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| TAG-DEL-01 | “기록까지 함께 삭제” removes the diary rows and memos attached to the tag. | A source tag owns three TimeBlocks including a private memo. | The user deletes it without a destination. | The source tag and all three rows/memos are absent; unrelated tags remain. | domain; DB cascade and privacy result require persistence. | `test_deleting_a_used_tag_removes_its_time_blocks_and_memos` | Green | Red 2026-08-15: targeted -q -> `1 failed` (SET_NULL로 tagless 행 3개 잔존). Green: `apps/tags/test_tag_migration.py apps/tags/test_personal_tags.py -q` -> 17 passed (이동 보존·소유자 격리 유지). tags signals.py는 CACHE-TAG-01(Task 8)의 Red가 요구할 때 작성. |
| TAG-MIG-01 | Legacy tagless rows do not survive the required-tag migration. | Migration state 0006 contains a TimeBlock with `tag_id=NULL`. | Migration 0007 is applied. | The orphan row is deleted and the current field is non-null with CASCADE deletion. | contract/slow; migration behavior cannot be proven by the current model alone. | `test_required_tag_migration_removes_legacy_tagless_time_blocks` | Green | Red 2026-08-15: targeted -q -> `NodeNotFoundError: ('dashboard', '0007_...')` (예상 이유). Green: `apps/dashboard/test_required_tag_migration.py apps/tags/test_tag_migration.py -q` -> 9 passed; `makemigrations --check --dry-run` -> No changes detected. 데이터 삭제 reverse는 `RunPython.noop`이며 rollback은 배포 전 backup 복원뿐. production DB 미적용(Deployment hold 유지). |

### Cache invalidation

| Scenario ID | Business behavior | Given | When | Then | Boundary / rationale | Test name | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| CACHE-SLOT-01 | A past slot edit refreshes a cached selected-date context that depends on it. | August 15 stats are cached and include the whole month; August 1 is initially empty. | A TimeBlock is committed on August 1. | The next August 15 request recomputes and contains the new monthly value. | domain with LocMemCache; exact-date cache deletion cannot prove this cross-date rule. | `test_past_slot_change_refreshes_cached_selected_month` | Green | Red 2026-08-15: targeted -q -> `assert 0 == 0.2` (8/15 캐시가 8/1 커밋 후에도 잔존). Green: targeted + `apps/stats/test_receivers.py` + `apps/dashboard/test_use_cases.py` -> 11 passed. 무작위 generation token(v3 key), receiver는 rotate만, 대시보드 use case 3곳 on_commit 발행. 구 `invalidate_stats_cache` 제거, receiver 테스트를 LocMemCache 세대 회전 관찰로 교체. |
| CACHE-TAG-01 | A tag edit refreshes cached statistics using its name/category/color. | Stats are cached for a recorded tag. | The owner commits a tag update. | The next request contains the updated tag data. | domain with LocMemCache; proves tag input dependency. | `test_tag_change_refreshes_cached_statistics` | Green | Red 2026-08-15: targeted -q -> 캐시가 옛 이름 `집중` 서빙. Green: targeted -> 1 passed; 회귀 `apps/tags apps/stats/test_cache_invalidation.py apps/stats/test_receivers.py -q` -> 99 passed. tags signals.py 신설, Create/Update/Delete atomic + on_commit 발행(Delete 발행은 계획 지시 — 미발행 시 기록 삭제 후 stale 캐시), stats receiver 구독. |
| CACHE-GOAL-01 | A goal change refreshes cached summary and goal observations. | Stats are cached before a goal exists or changes. | The owner commits a goal save. | The next request contains the new goal result. | domain with LocMemCache; goals enter stats through users repositories. | `test_goal_change_refreshes_cached_statistics` | Green | Red 2026-08-15: targeted -q -> 캐시된 `summary.goal=None` 잔존. Green: targeted -> 1 passed. users signals.py 신설(goals_changed), SaveGoal/DeleteGoal on_commit 발행, stats 구독. |
| CACHE-NOTE-01 | A note change refreshes the latest note in cached context. | Stats are cached with an old latest note. | The owner commits a note save. | The next request exposes the new latest note. | domain with LocMemCache; note is a separate input and core When. | `test_note_change_refreshes_cached_statistics` | Green | Red 2026-08-15: targeted -q -> 캐시가 옛 메모 서빙. Green: targeted -> 1 passed; 회귀 `apps/stats/test_cache_invalidation.py apps/stats/test_receivers.py apps/users/test_use_cases.py apps/tags/test_tag_migration.py -q` -> 19 passed. notes_changed 발행(SaveNote/DeleteNote) + stats 구독. |
| CACHE-TX-01 | A rolled-back mutation keeps the valid cache generation. | A stats context and generation are cached inside a transaction. | The mutation raises and the transaction rolls back. | The generation and cached context remain unchanged. | contract; `on_commit` timing is itself the consistency contract. | `test_rolled_back_mutation_does_not_rotate_stats_cache_generation` | Green | Discovered Green 2026-08-15: Task 6이 발행을 on_commit으로 옮긴 뒤라 첫 실행 통과 (`1 passed`, 가짜 Red 미생성). 회귀 `apps/dashboard/test_use_cases.py apps/dashboard/test_restore_use_case.py apps/stats/test_cache_invalidation.py apps/stats/test_receivers.py -q` -> 20 passed. |

### Account lifecycle

| Scenario ID | Business behavior | Given | When | Then | Boundary / rationale | Test name | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| ACC-REQ-01 | A user can request deletion again after cancelling an earlier request. | A prior request was cancelled and the user is active. | The user requests deletion at a later time. | The same OneToOne row has a new request/deadline, cleared cancellation, and the user is inactive. | domain; persisted lifecycle state is the contract. | `test_new_deletion_request_after_cancellation_reuses_request_with_new_deadline` | Green | Red 2026-08-16: targeted -q -> `IntegrityError: UNIQUE constraint failed: users_accountdeletionrequest.user_id` (예상 이유). Green: `apps/users/test_account_deletion.py -q` -> 15 passed (활성 요청 idempotency 유지). select_for_update로 행 잠근 뒤 취소된 행의 4개 시각 필드 재설정. |
| ACC-LOCAL-01 | Local signup never leaves a user without bootstrap tags. | Seed creation is forced to fail. | A valid local signup is submitted. | The request fails and neither the user nor partial seed state remains. | web with failure injection; the HTTP registration transaction is the boundary. | `test_local_signup_rolls_back_user_when_seed_tags_fail` | Green | Red 2026-08-16: targeted -> seed RuntimeError 후 `User newcomer` 잔존(`assert not True`). Green: `apps/users/test_signup_consent.py` + `apps/tags/test_seed_tags.py::TestSignupSeedsTags` -> 5 passed. signup_view의 form.save+create_seed_tags를 transaction.atomic으로 묶음. |
| ACC-SOC-01 | Google signup requires the same legal consent as local signup. | A new provider-authenticated identity reaches social signup. | The form is submitted without consent. | The form is invalid and no User/SocialAccount is saved. | contract; no external Google network is needed to prove the allauth form boundary. | `test_google_signup_requires_legal_consent` | Green | Red 2026-08-16: `ImportError: cannot import name 'SocialSignupForm'` (예상 이유). Green: `apps/users/test_social_signup.py` + `test_signup_consent.py` -> 5 passed. 공유 상수(CONSENT_LABEL/CONSENT_REQUIRED_ERROR)로 로컬 form과 문구 일치. |
| ACC-SOC-CONFIG-01 | Google signup cannot bypass the project consent form. | Web settings load with Google auth enabled. | The allauth social-signup contract is inspected. | Auto signup is disabled and the project social signup form is configured. | contract; settings wiring is independently required in addition to form behavior. | `test_google_signup_requires_project_consent_form` | Green | Red 2026-08-16: `SOCIALACCOUNT_AUTO_SIGNUP is True` AssertionError. Green: `apps/users/test_google_login_settings.py -q` -> 5 passed. dev.py에 AUTO_SIGNUP=False + SOCIALACCOUNT_FORMS 등록. |
| ACC-SOC-02 | Consented Google signup creates a complete account with seed tags. | A valid new SocialLogin and consented form exist. | The social signup form saves. | User and SocialAccount exist and the user owns the full seed-tag set. | contract with DB; proves current allauth integration without provider network. | `test_google_signup_creates_seed_tags_atomically` | Green | Red 2026-08-16: User/SocialAccount 저장, seed 태그 0/11. Green: targeted + 모듈 -> 2 passed. `SocialSignupForm.save(request)` atomic override + create_seed_tags. |
| ACC-SOC-03 | Google bootstrap failure leaves no partial account. | Seed creation is forced to fail during social form save. | The form attempts to save. | User, SocialAccount, and partial tags are absent. | contract with failure injection; atomicity is an allowed interaction contract. | `test_google_signup_rolls_back_user_when_seed_tags_fail` | Green | Discovered Green 2026-08-16: ACC-SOC-02의 atomic override가 이미 rollback을 보장, 첫 실행 `1 passed`(가짜 Red 미생성). User/SocialAccount/Tag 전부 부재 검증. |
| ACC-SOC-04 | A linked Google identity can cancel deletion within the grace period. | An existing linked SocialAccount user is inactive with a due date in the future. | `pre_social_login` runs after provider authentication. | The deletion request is cancelled and the user is active. | contract; adapter hook is the trusted provider integration boundary. | `test_google_login_within_grace_period_cancels_deletion_request` | Green | Discovered Green 2026-08-16: adapter 클래스·hook이 ACC-SOC-CONFIG-02의 Green과 한 일관 변경으로 구현되어 첫 실행 통과(`2 passed`). 연결된 SocialAccount + 미래 deadline에서 취소·재활성 확인. |
| ACC-SOC-05 | Google login cannot cancel deletion at or after the deadline. | The same linked user has reached the deadline. | `pre_social_login` runs. | The request remains pending and user remains inactive. | contract; verifies the security boundary value. | `test_google_login_after_grace_period_keeps_account_inactive` | Green | Discovered Green 2026-08-16 (계획서가 예상한 경우): `cancel_account_deletion()`이 기한 경과 요청을 거부하므로 adapter에 deadline 로직을 중복하지 않고 첫 실행 통과. 회귀 4개 모듈 -> 30 passed. |
| ACC-SOC-CONFIG-02 | Google login routes through the pending-deletion lifecycle adapter. | Web settings load with Google auth enabled. | The allauth adapter contract is inspected. | The configured adapter is `LifeDiarySocialAccountAdapter`. | contract; a correct adapter class that is not configured provides no behavior. | `test_google_login_uses_pending_deletion_lifecycle_adapter` | Green | Red 2026-08-16: `AttributeError: SOCIALACCOUNT_ADAPTER` (미설정). Green: `apps/users/test_google_login_settings.py -q` -> 6 passed. `apps/users/adapters.py` 신설 + dev.py 등록. hook 구현이 함께 들어가 ACC-SOC-04/05는 discovered Green. |
| ACC-OPS-01 | Due deletion requests run automatically with monitored recovery. | An approved production scheduler and due account exist. | The scheduled job runs or misses a run. | Due data is purged once; failure alerts and overdue recovery are observable. | provider contract/slow; repository code cannot prove external scheduling. | Provider-specific after user approval | Deferred | Scheduler provider not selected |

## Existing Regression Mapping

These tests already protect retained behavior. Do not rename, merge, or delete
them without first preserving their Scenario mapping.

| Existing pytest node | Protected behavior | Mapping |
|---|---|---|
| `apps/tags/test_tag_migration.py::TestDeleteWithMigration::test_blocks_move_to_the_destination_tag` | Delete-with-destination preserves block count under destination. | AC-TAG-1 retained Green guard |
| `apps/tags/test_tag_migration.py::TestDeleteWithMigration::test_other_tags_are_untouched` | Unrelated tags and records are not deleted. | TAG-DEL-01 regression guard |
| `apps/users/test_account_deletion.py::TestAccountDeletionService::test_request_is_idempotent_for_active_request` | Repeated active deletion request keeps its first deadline. | ACC-REQ-01 regression guard |
| `apps/users/test_account_deletion.py::TestAccountDeletionService::test_purge_due_account_deletes_user_data_and_keeps_masked_audit_record` | Purge cascade and minimal audit content. | AC-OPS-1 retained Green guard |
| `apps/users/test_account_deletion.py::TestPurgeDeletedAccountsCommand::test_command_purges_due_accounts` | Management command invokes due purge successfully. | ACC-OPS-01 local command guard |
| `apps/tags/test_seed_tags.py::TestSignupSeedsTags::test_signup_gives_the_new_user_personal_tags` | Local successful signup gets seed tags. | ACC-LOCAL-01 success guard |

The obsolete
`TestDeleteWithoutMigration::test_deleting_a_used_tag_turns_its_blocks_unlogged`
must be replaced by TAG-DEL-01. Its old assertion is the confirmed defect, not a
supported contract.

## Frontend Browser Scenario List

Frontend policy forbids tests that grep JavaScript source, assert HTML strings,
or mirror CSS. These scenarios require source review plus a real browser.

| Scenario ID | Given | When | Then | Viewports / input | Status |
|---|---|---|---|---|---|
| FE-XSS-01 | A saved memo is `<img src=x onerror="window.__memoXss=1">`. | The slot is selected. | The exact text is visible; no `img` is created and `window.__memoXss` is unset. | 375 and 1024; pointer + keyboard | Pending |
| FE-XSS-02 | A tag name contains HTML-like text and quotes. | SSR loads and a later partial row render occurs. | Both render paths show the same literal text and create no extra element. | 375 and 1024 | Pending |
| FE-TAG-01 | `window.event` is absent. | A tag button is clicked after selecting a slot. | The clicked button becomes selected and Save enables without console error. | Chrome plus a browser without implicit global event | Pending |
| FE-DEL-01 | A recorded slot is selected and DELETE returns success. | The user confirms deletion. | The slot remains deleted, snackbar appears, event detail contains the deleted indexes, and no failure notification appears. | 375 and 1024; pointer + keyboard | Pending |
| FE-DEL-02 | A `time-blocks-saved` listener deliberately throws after server success. | The user deletes a slot. | The error is logged without restoring the old row or reporting HTTP delete failure. | 1024 devtools-assisted | Pending |
| FE-SOC-01 | A new Google identity is returned to the project signup step. | The user submits without checking consent, then checks it and retries. | The first attempt stays on the form with an announced error; the second completes and enters the normal welcome flow. | 375 and 1024; keyboard-only and pointer | Pending |

## Frontend Review Evidence Required Before Editing

### Web Experience Designer specification

- Information hierarchy and existing labels remain unchanged; only unsafe DOM
  construction changes.
- HTML-like text must remain readable as literal user content.
- The social signup page must show Google identity context, consent checkbox,
  links to Terms/Privacy, validation error, and a clear cancel/back path.
- A post-commit UI refresh failure must say that deletion succeeded but the
  screen could not refresh; it must never say the deletion itself failed.
- New user-facing copy ships in ko/en catalogs.

### Browser Interaction Reviewer criteria

- No user-controlled value reaches `innerHTML`, `insertAdjacentHTML`, inline
  event attributes, or executable URL attributes.
- SSR and `buildBlock()` expose the same dataset fields.
- Delete button listeners survive repeated `showSlotInfo()` rerenders without
  duplicate calls.
- Network/HTTP failure restores the snapshot exactly once.
- Post-success render/event failure never restores it.
- Tag selection passes the clicked element explicitly.
- Social signup validation returns focus to the invalid consent control or
  exposes the error through the existing form pattern.

## Implementation Tasks

### Task 0: Freeze and verify the implementation baseline

**Files:** Read only. No project files change.

**Step 1: Record the branch and preserve unrelated work**

Run:

```bash
git status -sb
git diff --name-only
```

Expected: only user-owned pre-existing changes are reported. Do not stage,
move, or modify `월간_소비시간_기록_시트.xlsx`.

**Step 2: Run the full backend baseline**

Run:

```bash
conda run -n knou-life-diary pytest --tb=short
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
```

Expected: the suite is green, Django reports no issues, and no migration drift
exists. If the count differs from 501 because user work landed, record the new
count rather than editing tests to recover an old number.

**Step 3: Record frontend and catalog baselines**

Run:

```bash
node --check apps/dashboard/static/dashboard/js/dashboard.js
node --check apps/stats/static/stats/js/stats.js
msgfmt --check-format -o /dev/null locale/ko/LC_MESSAGES/django.po
msgfmt --check-format -o /dev/null locale/en/LC_MESSAGES/django.po
msgfmt --check-format -o /dev/null locale/ko/LC_MESSAGES/djangojs.po
msgfmt --check-format -o /dev/null locale/en/LC_MESSAGES/djangojs.po
```

Expected: all commands exit 0.

### Task 1: Separate daily real-tag identity from synthetic unclassified time

**Files:**

- Create: `apps/stats/aggregation/identity.py`
- Create: `apps/stats/aggregation/test_tag_identity.py`
- Modify: `apps/stats/aggregation/calculator.py`
- Modify: `apps/stats/aggregation/daily.py`
- Modify: `apps/stats/services.py`
- Modify: `apps/stats/static/stats/js/stats.js`

**Step 1: Write only STAT-ID-01**

Create the Korean/English parametrized test using persisted `Category`, `Tag`,
and one `TimeBlock`. Call `get_daily_stats_data()` through a real
`StatsCalculator`; assert by `entry["key"]`, not list order or query order.

**Step 2: Run it and confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation/test_tag_identity.py::test_user_tag_named_unclassified_stays_separate_in_daily_statistics -q
```

Expected Red: the real entry receives 1,440 minutes/144 blocks or the synthetic
entry is absent because both use the translated display name as a dict key.

**Step 3: Implement the smallest collision-proof daily contract**

`identity.py` owns only these concepts:

```python
UNCLASSIFIED_KEY = "unclassified"


def real_tag_key(tag_id: int) -> str:
    return f"tag:{tag_id}"
```

Extend `StatsCalculator.get_tag_info()` with `key`, `tag_id`, and
`category_slug`. Extend every unclassified builder with
`key=UNCLASSIFIED_KEY` and `tag_id=None`. In `daily.py`, index `tag_stats` and
`hourly_stats` by `tag_info["key"]`; keep display name/color in each value.

Update `renderHourlyBarChart()` to read minutes by `tag.key` while using
`tag.name` as the visible dataset label:

```javascript
const datasets = tagStats.map(tag => ({
    label: tag.name,
    data: hourlyStats.map(hour => hour[tag.key] || 0),
    backgroundColor: tag.color,
}));
```

Do not reserve or reject the names `미분류` or `Unclassified`.

**Step 4: Verify Green and syntax**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation/test_tag_identity.py::test_user_tag_named_unclassified_stays_separate_in_daily_statistics apps/stats/tests.py -q
node --check apps/stats/static/stats/js/stats.js
```

Expected: tests pass and JavaScript syntax exits 0.

### Task 2: Extend stable identity through monthly, weekly, and analysis output

**Files:**

- Modify: `apps/stats/aggregation/test_tag_identity.py`
- Modify: `apps/stats/aggregation/monthly.py`
- Modify: `apps/stats/aggregation/weekly.py`
- Modify: `apps/stats/aggregation/analysis.py`
- Modify: `apps/stats/aggregation/calculator.py`
- Modify if required: `apps/stats/aggregation/weekly_summary.py`

Take these scenarios one at a time. Do not write all three tests before the
first Red/Green cycle.

**Step 1: STAT-ID-02 Red/Green**

Run after writing only the monthly test:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation/test_tag_identity.py::test_user_tag_named_unclassified_stays_separate_in_monthly_statistics -q
```

Expected Red: 0.2 recorded hours are merged with the month’s empty hours.
Change monthly maps to use stable keys and return their value entries.

**Step 2: STAT-ID-03 Red/Green**

Run after writing only the weekly test:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation/test_tag_identity.py::test_user_tag_named_unclassified_stays_separate_in_weekly_statistics -q
```

Expected Red: real and synthetic rows share one name key. Change both
`daily_tag_stats` and `tag_weekly_stats` to stable keys.

**Step 3: STAT-ID-04 Red/Green**

Run after writing only the analysis test:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation/test_tag_identity.py::test_user_tag_named_unclassified_stays_separate_in_tag_analysis -q
```

Expected Red: the real tag includes empty-month minutes. Change analysis maps
to stable keys and filter only entries carrying `is_unclassified=True`.

**Step 4: Run the aggregation regression slice**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation apps/stats/tests.py apps/stats/test_stats_perf.py -q
node --check apps/stats/static/stats/js/stats.js
```

Expected: all pass; existing query-count budgets stay green.

### Task 3: Make weekly sleep policy independent of tag name and language

**Files:**

- Modify: `apps/stats/aggregation/test_tag_identity.py`
- Modify: `apps/stats/aggregation/weekly.py`
- Modify: `apps/core/utils.py` only to remove `SLEEP_TAG_NAME` after all uses are gone

**Step 1: Write STAT-WEEK-01**

Parametrize the same persisted sleep-category block with `수면`, `Sleep`, and a
custom name. Assert active week hours and active days, not a private helper.

**Step 2: Confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation/test_tag_identity.py::test_sleep_category_is_excluded_from_active_week_totals_after_rename -q
```

Expected Red: only the Korean name is excluded.

**Step 3: Implement minimum Green**

Use the already selected `block.tag.category.slug` from
`TimeBlockRepository.find_by_date_range()`:

```python
is_sleep = tag_info["category_slug"] == "sleep"
if not is_sleep:
    active_blocks_count += 1
    active_minutes += MINUTES_PER_SLOT
```

Do not translate or compare tag names for policy.

**Step 4: Verify**

Run the targeted test and `apps/stats/aggregation` regression. Expected: pass.

### Task 4: Make delete-without-destination actually remove records and memos

**Files:**

- Modify: `apps/tags/test_tag_migration.py`
- Modify: `apps/tags/use_cases.py`
- Modify: `apps/dashboard/repositories.py`
- Create: `apps/tags/signals.py`

**Step 1: Replace the obsolete test with TAG-DEL-01**

The test body must create a memo-bearing source row and an unrelated tag/row,
execute `DeleteTagUseCase().execute(..., move_to_id=None)`, then directly assert
source rows are absent and the unrelated row remains.

**Step 2: Confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/tags/test_tag_migration.py::TestDeleteWithoutMigration::test_deleting_a_used_tag_removes_its_time_blocks_and_memos -q
```

Expected Red: three TimeBlocks remain with `tag_id=NULL`.

**Step 3: Implement minimum Green in one transaction**

Add a narrowly named dashboard repository operation:

```python
def delete_blocks_for_tag(self, tag) -> int:
    deleted, _ = TimeBlock.objects.filter(tag=tag).delete()
    return deleted
```

When no destination is supplied, call it before deleting the tag. When a
destination exists, preserve the existing move behavior. Schedule a
`tags_changed` signal with `user_id` through `transaction.on_commit()` after a
successful create/update/delete transaction; do not import stats here.

**Step 4: Verify retained behavior**

Run:

```bash
conda run -n knou-life-diary pytest apps/tags/test_tag_migration.py apps/tags/test_personal_tags.py -q
```

Expected: delete-without-destination removes rows; migration-to-destination and
owner isolation remain green.

### Task 5: Remove legacy tagless rows and enforce the TimeBlock tag invariant

**Files:**

- Create: `apps/dashboard/test_required_tag_migration.py`
- Modify: `apps/dashboard/models.py`
- Create: `apps/dashboard/migrations/0007_delete_tagless_blocks_and_require_tag.py`
- Modify: `apps/dashboard/admin.py` if its null fallback becomes unreachable

**Step 1: Write only TAG-MIG-01 using MigrationExecutor**

Migrate the test database to `dashboard.0006`, create a valid user/category/tag
and a legacy TimeBlock whose tag is null, then migrate to `dashboard.0007`.
Assert the row is gone. Restore the executor to the leaf migration in teardown
so later tests do not inherit historical app state.

**Step 2: Confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/test_required_tag_migration.py::test_required_tag_migration_removes_legacy_tagless_time_blocks -q
```

Expected Red: migration node `0007` does not exist.

**Step 3: Implement migration and model state**

Migration order:

1. `RunPython` deletes `TimeBlock` rows whose historical `tag_id` is null.
2. `AlterField` sets `null=False` and `on_delete=CASCADE`.

The reverse for data deletion is `RunPython.noop`; the plan and work log must
state that only a pre-deploy backup restores deleted legacy rows.

**Step 4: Verify migration and domain behavior**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/test_required_tag_migration.py apps/tags/test_tag_migration.py -q
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
```

Expected: tests pass and no untracked migration drift remains.

**Deployment hold:** Do not apply this migration to production until the user
confirms a current DB backup and a read-only count of legacy tagless rows.

### Task 6: Introduce cache generation and post-commit TimeBlock invalidation

**Files:**

- Modify: `apps/stats/use_cases.py`
- Modify: `apps/stats/receivers.py`
- Modify: `apps/stats/test_receivers.py`
- Create: `apps/stats/test_cache_invalidation.py`
- Modify: `apps/dashboard/use_cases.py`

**Step 1: Add an explicit LocMemCache fixture local to the new test module**

Do not remove the global DummyCache fixture in `conftest.py` during this task.
The module fixture must override only its tests with a unique LocMemCache
location and clear it before/after each test.

**Step 2: Write only CACHE-SLOT-01**

Cache August 15 through `GetStatsContextUseCase.execute()`, commit a real August
1 slot through `UpsertTimeBlocksUseCase` inside
`django_capture_on_commit_callbacks(execute=True)`, and request August 15 again.
Assert the public monthly result changed. Do not assert `cache.delete()` calls
or a specific key string.

**Step 3: Confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_cache_invalidation.py::test_past_slot_change_refreshes_cached_selected_month -q
```

Expected Red: the second context is the cached pre-mutation result because only
the August 1 date key is deleted.

**Step 4: Implement a random per-user generation**

Use `secrets.token_urlsafe()` or `uuid.uuid4().hex`; do not use cache `incr()`.
The public behavior is:

```python
def get_stats_generation(user_id: int) -> str:
    key = f"stats-generation:{user_id}"
    token = cache.get(key)
    if token is None:
        token = secrets.token_urlsafe(12)
        cache.set(key, token, timeout=None)
    return token


def rotate_stats_generation(user_id: int) -> None:
    cache.set(
        f"stats-generation:{user_id}",
        secrets.token_urlsafe(12),
        timeout=None,
    )
```

Include the token in `_cache_key()`. `on_time_blocks_changed()` rotates once for
the user; it no longer tries to enumerate dates/languages.

In all three dashboard mutation use cases, replace immediate signal send with:

```python
transaction.on_commit(
    lambda user_id=cmd.user_id, target_date=cmd.target_date:
        time_blocks_changed.send(
            sender=type(self), user_id=user_id, target_date=target_date
        )
)
```

Use project formatting; the snippet fixes the value-capture requirement, not a
mandatory line layout.

**Step 5: Verify targeted Green**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_cache_invalidation.py::test_past_slot_change_refreshes_cached_selected_month apps/stats/test_receivers.py apps/dashboard/test_use_cases.py -q
```

Expected: pass. Update the old receiver test to use LocMemCache and assert a
generation change or public recomputation; a DummyCache assertion is invalid.

### Task 7: Prove rollback safety for cache invalidation

**Files:**

- Modify: `apps/stats/test_cache_invalidation.py`
- Modify only if Green requires it: `apps/dashboard/use_cases.py`

**Step 1: Write CACHE-TX-01**

Use `django_capture_on_commit_callbacks(execute=False)` or an equivalent real
transaction boundary. Force the surrounding transaction to roll back after the
dashboard use case schedules its event. Assert no callback is executed and the
cached public context remains valid.

**Step 2: Confirm Red for the expected reason**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_cache_invalidation.py::test_rolled_back_mutation_does_not_rotate_stats_cache_generation -q
```

Expected Red before Task 6 Green would be immediate generation rotation. If it
already passes because Task 6 correctly moved all sends to `on_commit`, record
it as newly discovered Green evidence and do not manufacture a failure or add
implementation-detail assertions.

**Step 3: Run dashboard/cache regression**

Run:

```bash
conda run -n knou-life-diary pytest apps/dashboard/test_use_cases.py apps/dashboard/test_restore_use_case.py apps/stats/test_cache_invalidation.py apps/stats/test_receivers.py -q
```

Expected: pass.

### Task 8: Invalidate stats after committed tag changes

**Files:**

- Modify: `apps/stats/test_cache_invalidation.py`
- Modify: `apps/tags/signals.py`
- Modify: `apps/tags/use_cases.py`
- Modify: `apps/stats/receivers.py`

**Step 1: Write CACHE-TAG-01**

Cache stats for a recorded tag, update the tag name/category/color through
`UpdateTagUseCase` inside
`django_capture_on_commit_callbacks(execute=True)`, and assert the next public
stats context reflects the update. Use LocMemCache and real DB rows.

**Step 2: Confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_cache_invalidation.py::test_tag_change_refreshes_cached_statistics -q
```

Expected Red: cached old tag data remains.

**Step 3: Implement minimum Green**

Make Create/Update/Delete tag use cases atomic where necessary. After a
successful commit, emit `tags_changed(user_id=...)`. Subscribe from stats and
rotate the same per-user generation. Do not send both `tags_changed` and a
dashboard-specific signal for one tag-delete transaction.

**Step 4: Verify**

Run the targeted test plus `apps/tags` and stats cache tests. Expected: pass.

### Task 9: Invalidate stats after committed goal and note changes

**Files:**

- Create: `apps/users/signals.py`
- Modify: `apps/users/use_cases.py`
- Modify: `apps/stats/receivers.py`
- Modify: `apps/stats/test_cache_invalidation.py`

Take one scenario at a time.

**Step 1: CACHE-GOAL-01 Red/Green**

Run after writing only the goal test:

```bash
conda run -n knou-life-diary pytest apps/stats/test_cache_invalidation.py::test_goal_change_refreshes_cached_statistics -q
```

Expected Red: cached goal summary remains. Emit `goals_changed(user_id=...)`
from Save/Delete goal use cases through `on_commit`, then subscribe from stats.
Execute the mutation in the test with
`django_capture_on_commit_callbacks(execute=True)`.

**Step 2: CACHE-NOTE-01 Red/Green**

Run after writing only the note test:

```bash
conda run -n knou-life-diary pytest apps/stats/test_cache_invalidation.py::test_note_change_refreshes_cached_statistics -q
```

Expected Red: cached `user_note` remains old. Emit `notes_changed(user_id=...)`
from Save/Delete note use cases through `on_commit`.
Execute the mutation in the test with
`django_capture_on_commit_callbacks(execute=True)`.

**Step 3: Verify all cache inputs**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/test_cache_invalidation.py apps/stats/test_receivers.py apps/users/test_use_cases.py apps/tags/test_tag_migration.py -q
```

Expected: all pass with real LocMemCache in the cache modules only.

### Task 10: Remove the stored DOM-XSS rendering boundary

**Files:**

- Modify: `apps/dashboard/templates/dashboard/_day_row.html`
- Modify: `apps/dashboard/static/dashboard/js/dashboard.js`
- Modify if new copy is added: `locale/ko/LC_MESSAGES/djangojs.po`
- Modify if new copy is added: `locale/en/LC_MESSAGES/djangojs.po`
- Later log: `docs/frontend/2026-08-15-dashboard-security-interaction.md`

**Step 1: Record the pre-edit dual-review findings**

The Web Experience Designer and Browser Interaction Reviewer must confirm the
criteria already stated in this plan against current line numbers. This is a
read-only checkpoint.

**Step 2: Give SSR and partial rows the same inert data fields**

In `_day_row.html`, add escaped dataset values for filled blocks:

```django
data-tag-name="{{ run.tag.name }}"
data-memo="{{ run.memo }}"
```

Keep `title` only as a tooltip/accessibility fallback; never parse it as state.
In `buildBlock(run)`, set `block.dataset.tagName` and `block.dataset.memo` from
the JSON response.

**Step 3: Replace HTML assembly with DOM construction**

`slotTagInfo()` reads dataset values. `showSlotInfo()` clears the target with
`replaceChildren()` and constructs all text using `textContent`. Create the
delete button with `document.createElement("button")` and
`addEventListener("click", deleteSlot)`; do not use inline `onclick`.

Static empty prompts may also use text nodes. Do not leave a second branch that
interpolates memo/tag name into `innerHTML`.

**Step 4: Run static verification**

Run:

```bash
node --check apps/dashboard/static/dashboard/js/dashboard.js
msgfmt --check-format -o /dev/null locale/ko/LC_MESSAGES/djangojs.po
msgfmt --check-format -o /dev/null locale/en/LC_MESSAGES/djangojs.po
```

Expected: exit 0. Do not add source-grep pytest tests as proof of XSS safety.

**Step 5: Run FE-XSS-01 and FE-XSS-02 in a browser**

Use a disposable pytest-created user/data fixture or rollback-safe local setup.
At 375 and 1024 CSS pixels inspect DOM, console, and `window.__memoXss`.
Expected: literal text, no injected node, no console error.

### Task 11: Make tag selection and delete success state deterministic

**Files:**

- Modify: `apps/dashboard/static/dashboard/js/dashboard.js`
- Modify: `locale/ko/LC_MESSAGES/djangojs.po`
- Modify: `locale/en/LC_MESSAGES/djangojs.po`
- Continue log: `docs/frontend/2026-08-15-dashboard-security-interaction.md`

**Step 1: Pass the clicked element explicitly**

Change the public local function shape to:

```javascript
const selectTag = (targetBtn, tagId, tagColor, tagName) => {
    document.querySelectorAll('.tag-btn').forEach(btn => btn.classList.remove('active'));
    if (targetBtn) targetBtn.classList.add('active');
    selectedTag = { id: tagId, color: tagColor, name: tagName };
    updateButtons();
};
```

The delegation handler passes its `el`. No function reads global `event`.

**Step 2: Restrict snapshot restoration to request failure**

Refactor DELETE into explicit phases:

```javascript
let result;
try {
    result = await apiCall(/* DELETE */);
} catch (error) {
    restoreRows(affectedRows);
    showNotification(/* true HTTP failure */);
    return;
}

try {
    // render committed result, clear selection, snackbar
} catch (error) {
    showNotification(gettext('삭제되었지만 화면을 새로 고치지 못했습니다. 페이지를 새로고침해주세요.'), 'warning');
    console.error('Delete render error:', error);
    return;
}

try {
    document.dispatchEvent(new CustomEvent('time-blocks-saved', {
        detail: { date, slotIndexes: filledSlots },
    }));
} catch (error) {
    console.error('Delete success event error:', error);
}
```

Do not restore `affectedRows` after HTTP success.

**Step 3: Update both catalogs and run syntax/catalog checks**

Run `node --check` and both djangojs `msgfmt --check-format` commands. Expected:
exit 0 and fuzzy/untranslated counts remain zero.

**Step 4: Run FE-TAG-01, FE-DEL-01, and FE-DEL-02**

Expected: selection works without implicit event; deletion stays committed;
the custom event contains `filledSlots`; an event-consumer exception does not
show a false delete failure.

### Task 12: Allow a fresh deletion request after cancellation

**Files:**

- Modify: `apps/users/test_account_deletion.py`
- Modify: `apps/users/account_deletion.py`

**Step 1: Write ACC-REQ-01**

Arrange request -> cancel -> later request. Assert one row remains, its ID is
unchanged, timestamps are refreshed, cancellation is cleared, and the user is
inactive.

**Step 2: Confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_account_deletion.py::TestAccountDeletionService::test_new_deletion_request_after_cancellation_reuses_request_with_new_deadline -q
```

Expected Red: `UNIQUE constraint failed: users_accountdeletionrequest.user_id`.

**Step 3: Implement row reuse under lock**

Inside the existing atomic function, lock any request for the user. Return an
active request unchanged; if cancelled, reset the four lifecycle timestamps to
a new request state and disable the user. Do not create an append-only history
model in this scope.

**Step 4: Verify account deletion service regression**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_account_deletion.py -q
```

Expected: all current and new lifecycle tests pass.

### Task 13: Make local signup bootstrap atomic

**Files:**

- Modify: `apps/users/test_signup_consent.py`
- Modify: `apps/users/views.py`
- Modify if a helper is justified: `apps/users/registration.py`

**Step 1: Write ACC-LOCAL-01**

Inject failure at the external bootstrap boundary `create_seed_tags`. Submit a
valid local signup through the Django client and catch the expected exception.
Assert the username/email does not exist afterward. Do not assert a private
helper was called.

**Step 2: Confirm Red**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_signup_consent.py::TestSignupConsent::test_local_signup_rolls_back_user_when_seed_tags_fail -q
```

Expected Red: the User remains after seed creation raises.

**Step 3: Implement minimum Green**

Wrap form save and seed creation in one explicit transaction. A small helper is
allowed only if it makes the transaction boundary clearer:

```python
@transaction.atomic
def save_local_signup(form):
    user = form.save()
    create_seed_tags(user)
    return user
```

The view logs in only after this function returns. Keep the existing welcome
redirect and consent validation.

**Step 4: Verify local signup**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_signup_consent.py apps/tags/test_seed_tags.py::TestSignupSeedsTags -q
```

Expected: failure rolls back and successful signup still gets seed tags.

### Task 14: Require consent and atomic bootstrap for Google signup

**Files:**

- Modify: `apps/users/forms.py`
- Modify: `apps/users/test_google_login_settings.py`
- Create: `apps/users/test_social_signup.py`
- Create: `apps/users/templates/socialaccount/signup.html`
- Modify: `lifeDiary/settings/dev.py`
- Modify: `locale/ko/LC_MESSAGES/django.po`
- Modify: `locale/en/LC_MESSAGES/django.po`

Take the config and behavior tests one at a time.

**Step 1: ACC-SOC-CONFIG-01 Red/Green**

Add the settings contract and run:

```bash
conda run -n knou-life-diary pytest apps/users/test_google_login_settings.py::test_google_signup_requires_project_consent_form -q
```

Expected Red: `SOCIALACCOUNT_AUTO_SIGNUP` is true and no project form is set.
Configure:

```python
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_FORMS = {
    "signup": "apps.users.forms.SocialSignupForm",
}
```

**Step 2: ACC-SOC-01 Red/Green**

Create a real allauth `SocialLogin` with an unsaved User/SocialAccount and
instantiate the project form without consent. Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_social_signup.py::test_google_signup_requires_legal_consent -q
```

Expected Red: `SocialSignupForm` or its consent field does not exist.

Implement `SocialSignupForm` as a subclass of
`allauth.socialaccount.forms.SignupForm` with the same required translated
consent label/error as local `SignupForm`. Avoid copy drift by defining shared
label/error constants in `forms.py`, not a new generic form framework.

**Step 3: ACC-SOC-02 Red/Green**

Run after adding the successful save test:

```bash
conda run -n knou-life-diary pytest apps/users/test_social_signup.py::test_google_signup_creates_seed_tags_atomically -q
```

Expected Red: the User/SocialAccount saves but no seed tags exist. Override
`SocialSignupForm.save(request)` with `transaction.atomic`, call `super()`, then
`create_seed_tags(user)`, and return the user.

**Step 4: ACC-SOC-03 Red/Green**

Run after adding failure injection:

```bash
conda run -n knou-life-diary pytest apps/users/test_social_signup.py::test_google_signup_rolls_back_user_when_seed_tags_fail -q
```

Expected Red before the atomic override: partial User/SocialAccount persists.
If Step 3 already makes it Green, record it as a discovered Green scenario and
do not manufacture a failure.

**Step 5: Implement the project social signup template**

Create `socialaccount/signup.html` using existing auth panel/form field/error
partials. It must include CSRF, provider context, consent, Terms and Privacy
links, submit and cancel/back action, and translated copy. Do not add Google
network code.

**Step 6: Verify form, settings, i18n, and render**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_google_login_settings.py apps/users/test_social_signup.py apps/users/test_signup_consent.py apps/tags/test_seed_tags.py -q
msgfmt --check-format -o /dev/null locale/ko/LC_MESSAGES/django.po
msgfmt --check-format -o /dev/null locale/en/LC_MESSAGES/django.po
```

Expected: pass, fuzzy 0, untranslated 0. Execute FE-SOC-01 in a real browser;
the actual Google OAuth round trip remains separately unverified without valid
provider credentials.

### Task 15: Integrate Google login with deletion-grace cancellation

**Files:**

- Create: `apps/users/adapters.py`
- Modify: `apps/users/test_social_signup.py`
- Modify: `apps/users/test_google_login_settings.py`
- Modify: `lifeDiary/settings/dev.py`

**Step 1: ACC-SOC-CONFIG-02 Red/Green**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_google_login_settings.py::test_google_login_uses_pending_deletion_lifecycle_adapter -q
```

Expected Red: no project social adapter is configured. Add:

```python
SOCIALACCOUNT_ADAPTER = "apps.users.adapters.LifeDiarySocialAccountAdapter"
```

**Step 2: ACC-SOC-04 Red/Green**

Create a saved User and Google SocialAccount, request deletion with a future
deadline, build a `SocialLogin` for that existing linked user, and invoke the
configured adapter hook. Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_social_signup.py::test_google_login_within_grace_period_cancels_deletion_request -q
```

Expected Red: adapter class/hook is absent and the user remains inactive.

Implement only:

```python
class LifeDiarySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        super().pre_social_login(request, sociallogin)
        if sociallogin.is_existing and not sociallogin.user.is_active:
            cancel_account_deletion(sociallogin.user)
```

Do not locate accounts by unverified email and do not reactivate a new social
identity.

**Step 3: ACC-SOC-05 Red/Green**

Run after writing the deadline-boundary test:

```bash
conda run -n knou-life-diary pytest apps/users/test_social_signup.py::test_google_login_after_grace_period_keeps_account_inactive -q
```

Expected: the test may already be Green because
`cancel_account_deletion()` rejects `scheduled_delete_at <= now`. Record the
evidence; do not duplicate deadline logic in the adapter.

**Step 4: Verify auth lifecycle regression**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_social_signup.py apps/users/test_google_login_settings.py apps/users/test_account_deletion.py apps/users/test_signup_consent.py -q
```

Expected: local and Google lifecycle contracts pass.

### Task 16: Scheduler provider approval and purge rollout contract

**Files:** No provider file changes until the user approves one option.

**Step 1: Present provider choices with concrete trade-offs**

The Deployment & Operations Reviewer must compare:

1. managed cron at the deployment provider;
2. GitHub Actions `schedule` with production DB secrets;
3. separately managed cron.

Required comparison fields: secret exposure, cost, timing guarantees, overlap
control, logs, alerts, manual rerun, and repository-verifiable evidence.

**Step 2: Obtain explicit user approval**

Until approval, keep ACC-OPS-01 `Deferred`. Do not claim the 15-day deletion
contract is operationally complete.

**Step 3: After approval, add a provider-specific plan amendment**

The amendment must identify exact files and include:

- at least daily execution of `purge_deleted_accounts`;
- concurrency/overlap protection;
- nonzero exit and alert on failure;
- an overdue request count that excludes cancelled requests;
- a copy-ready missed-run recovery command;
- least-privilege secrets;
- staging/dry-run verification before production.

Do not silently choose GitHub Actions merely because workflow files already
exist.

### Task 16 Amendment — GitHub Actions scheduler (user approved 2026-08-16)

The user compared Render Cron Job (paid), GitHub Actions schedule (free), and
a separately managed cron, and approved **GitHub Actions schedule**.

**Files:**

- Create: `../.github/workflows/purge-deleted-accounts.yml` (repository root
  `.github/`, same repo)
- Modify: `apps/users/account_deletion.py` (overdue count query)
- Modify: `apps/users/management/commands/purge_deleted_accounts.py`
  (`--check` option)
- Modify: `apps/users/test_account_deletion.py` (ACC-OPS-02/03)

**Contract mapping:**

- Daily execution: `schedule: cron "47 18 * * *"` (UTC; KST 03:47). Purge
  processes every due request per run, so missed runs self-heal on the next
  run.
- Overlap protection: `concurrency: group: purge-deleted-accounts,
  cancel-in-progress: false`.
- Nonzero exit + alert: command exceptions already exit nonzero; a post-purge
  `--check` step fails the workflow if overdue requests remain; GitHub sends
  failure notification e-mail for scheduled workflows.
- Overdue count excluding cancelled: new `--check` reports
  due & uncancelled & unpurged count; nonzero count raises `CommandError`.
- Missed-run recovery (copy-ready): `workflow_dispatch` manual run, or
  locally `DJANGO_SETTINGS_MODULE=lifeDiary.settings.prod DB_...=... conda
  run -n knou-life-diary python manage.py purge_deleted_accounts`.
- Least-privilege secrets: real values only for `DB_NAME/DB_USER/DB_PASSWORD/
  DB_HOST`. `DJANGO_SECRET_KEY` is a **separate random value** (the purge job
  never signs sessions/tokens — do not copy the web key), `RESEND_API_KEY`
  and `DEFAULT_FROM_EMAIL` are dummies (purge sends no mail).
- Staging/dry-run: before trusting the schedule, run `workflow_dispatch` once
  and confirm `Purged N account(s).` + `Overdue deletion requests: 0`; the
  scheduled workflow runs from the default branch's workflow file and checks
  out `production` for code.

**Scenario additions:**

| Scenario ID | Business behavior | Given | When | Then | Boundary / rationale | Test name | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| ACC-OPS-02 | The check mode fails loudly with the overdue count and purges nothing. | One overdue active request and one overdue cancelled request exist. | `purge_deleted_accounts --check` runs. | `CommandError` reports 1 overdue (cancelled excluded); users and requests remain untouched. | domain; command boundary is the scheduler's alert contract. | `test_check_reports_overdue_requests_excluding_cancelled_without_purging` | Green | Red 2026-08-16: `TypeError: Unknown option(s) ... check` (옵션 부재). Green: targeted 1 passed, `apps/users/test_account_deletion.py` 17 passed. `count_overdue_deletion_requests()` + `--check`(잔량 시 CommandError). |
| ACC-OPS-03 | The check mode passes quietly when nothing is overdue. | Only a cancelled overdue request exists. | `--check` runs. | Command exits normally reporting 0. | domain; success path of the same contract. | `test_check_passes_quietly_when_no_overdue_requests` | Green | Discovered Green 2026-08-16: ACC-OPS-02의 최소 구현이 0 분기를 포함해 첫 실행 통과(`1 passed`). "Overdue deletion requests: 0" 출력 확인. |

ACC-OPS-01 stays `Deferred` until the user registers the secrets and a real
scheduled run + failure alert are observed on GitHub.

### Task 17: Full verification, browser verdicts, and documentation

**Files:**

- Create: `docs/refactoring/2026-08-15_critical-backend-remediation.md`
- Create: `docs/frontend/2026-08-15-dashboard-security-interaction.md`
- Modify: `docs/project-status.md`
- Modify: this plan's Test List status/evidence fields

**Step 1: Run focused Lane regressions**

Run:

```bash
conda run -n knou-life-diary pytest apps/stats/aggregation apps/stats/test_cache_invalidation.py apps/stats/test_receivers.py apps/tags/test_tag_migration.py apps/dashboard/test_required_tag_migration.py apps/users/test_account_deletion.py apps/users/test_social_signup.py apps/users/test_signup_consent.py apps/users/test_google_login_settings.py --tb=short
```

Expected: all pass with no unexpected skip.

**Step 2: Run full backend and configuration gates**

Run:

```bash
conda run -n knou-life-diary pytest --tb=short
conda run -n knou-life-diary python manage.py check
conda run -n knou-life-diary python manage.py makemigrations --check --dry-run
```

For the production deploy check, provide explicit non-secret dummy environment
values required by current settings and run:

```bash
conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
```

Expected: exit 0. Record the exact test count and duration rather than copying
the 501-test baseline.

**Step 3: Run all static and i18n checks**

Run:

```bash
node --check apps/dashboard/static/dashboard/js/dashboard.js
node --check apps/stats/static/stats/js/stats.js
msgfmt --check-format -o /dev/null locale/ko/LC_MESSAGES/django.po
msgfmt --check-format -o /dev/null locale/en/LC_MESSAGES/django.po
msgfmt --check-format -o /dev/null locale/ko/LC_MESSAGES/djangojs.po
msgfmt --check-format -o /dev/null locale/en/LC_MESSAGES/djangojs.po
```

Expected: all exit 0, fuzzy 0, untranslated 0.

**Step 4: Execute all frontend browser scenarios**

At minimum run 375 and 1024 CSS-pixel viewports, keyboard-only selection, the
two XSS payloads, successful/failed delete, throwing success listener, and
social consent validation. Capture console state and screenshots where they
materially prove behavior.

The two frontend reviewers independently return `Conforms`, `Deviates`, or
`Unverified`. A source-only review cannot mark browser scenarios Conforms.

**Step 5: Verify migration rollout prerequisites**

Before production migration:

- current backup timestamp and restore path are recorded;
- tagless TimeBlock count is recorded read-only;
- migration duration is measured on a representative copy if count is material;
- rollback is explicitly “restore backup,” not reverse migration;
- scheduler remains Deferred unless Task 16 has its own approved evidence.

**Step 6: Write work logs and update status**

Backend log records every Scenario's Red command/reason and fresh Green command.
Frontend log records source diff, browser matrix, screenshots, console results,
and both reviewer verdicts. `docs/project-status.md` must distinguish completed,
failed, Deferred, and unverified items.

**Step 7: Final clean-tree evidence**

Run:

```bash
git diff --check
git diff --name-only
git status -sb
```

Expected: no whitespace errors; only approved files and preserved user-owned
changes appear. The agent does not perform Git actions. Provide the user with
copy-ready `git add` paths and suggested commit messages per completed Lane.

## TDD Checkpoints

For every Pending backend Scenario:

1. Backend TDD Coach selects exactly one next Scenario.
2. Backend & Integration Engineer writes only that test.
3. Run the exact node and record Red for the expected business reason.
4. If setup or fixture failure occurs, repair the test before production code.
5. Implement the minimum Green behavior.
6. Run the exact node and the listed focused regression slice.
7. Coach records Green evidence and decides whether refactoring is allowed.
8. Only then advance to the next Scenario.
9. If a later planned Scenario turns Green due to an earlier coherent change,
   record “discovered Green”; do not force a fake Red or weaken implementation.
10. Update this document's Status/Evidence fields during execution, not after
    all work is finished.

## Quality Verification Matrix

| Acceptance | Required evidence | Completion rule |
|---|---|---|
| AC-STAT-1 | STAT-ID-01 through 04, stats aggregation regression, hourly browser chart | All pass; same-name real/synthetic entries visibly separate |
| AC-STAT-2 | STAT-WEEK-01 | All parametrized names produce identical category-based result |
| AC-TAG-1 | TAG-DEL-01 plus existing migration-to-destination tests | Rows/memos deleted only on delete-without-destination |
| AC-TAG-2 | TAG-MIG-01, migration drift check, backup evidence | Test Green and rollout prerequisite recorded |
| AC-CACHE-1 | CACHE-SLOT/TAG/GOAL/NOTE tests with LocMemCache | All next requests show committed values |
| AC-CACHE-2 | CACHE-TX-01 | Rollback preserves generation/context |
| AC-FE-1 | FE-XSS-01/02 browser DOM+console evidence | No injected element/handler in SSR or partial render |
| AC-FE-2 | FE-TAG-01 | Tag select/save works without implicit event |
| AC-FE-3 | FE-DEL-01/02 and explicit HTTP failure case | Snapshot restore occurs only for request failure |
| AC-ACC-1 | ACC-REQ-01 plus existing active-request idempotency | New deadline after cancellation, original deadline during active repeat |
| AC-ACC-2 | ACC-LOCAL-01, ACC-SOC-01/02/03, settings contracts, FE-SOC-01 | Both paths consented, atomic, and seeded |
| AC-ACC-3 | ACC-SOC-04/05 and adapter settings contract | Before deadline active; at/after deadline inactive |
| AC-OPS-1 | Provider-specific scheduler evidence | Remains Deferred until external schedule/alert/recovery are observed |

## Deferred Refactoring Notes

```text
- Topic: Full dashboard/tags writer-port extraction
- Why deferred: Current tags -> dashboard repository orchestration already exists;
  restore the deletion invariant before introducing another abstraction.
- Trigger: A second cross-app tag maintenance workflow or alternate TimeBlock store.
```

```text
- Topic: Shared atomic cache backend for security and stats
- Why deferred: Random stats generation works with the current cache contract;
  axes/throttle atomicity is a separate security/operations decision.
- Trigger: Production Redis/shared-cache approval.
```

```text
- Topic: General frontend accessibility remediation
- Why deferred: Chart alternatives, slot roving tabindex, mobile sheet inert/focus,
  and 768-991px layout are material but not dependencies of this critical scope.
- Trigger: Completion or explicit deferral of Lane B.
```

```text
- Topic: Desktop boot and release readiness
- Why deferred: Desktop auth surface, offline assets, packaging, backup, and release
  workflow require their own integrated plan in the mandated execution order.
- Trigger: Web critical regression is Green.
```

## Suggested User Git Checkpoints

The agent does not execute these. After each Lane is independently complete and
verified, the user may choose equivalent commits:

```text
fix(stats): separate tag identity and refresh committed statistics
fix(dashboard): remove unsafe slot info rendering and preserve delete truth
fix(users): align local and Google account lifecycle
docs: record critical remediation evidence
```

Do not combine the irreversible TimeBlock migration with unverified scheduler
or desktop work in one release decision.
