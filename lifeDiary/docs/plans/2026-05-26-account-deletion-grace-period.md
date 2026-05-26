# Account Deletion Grace Period Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add account deletion with a 15-day cancellation period, followed by irreversible purge and minimal masked audit retention.

**Architecture:** Keep deletion state in `apps.users` with two small models: one active request model tied to `User`, and one deleted-account audit record without a user FK. Put business rules in a small service module so request, cancellation, purge, and email masking can be tested directly. Integrate cancellation into the existing custom `login_view` without replacing Django authentication globally.

**Tech Stack:** Django ORM, Django auth `User.date_joined`, Django management command, pytest.

---

## Approved Scope

- Add 15-day account deletion grace period.
- Store account deletion request time and scheduled purge time.
- Disable the account during the grace period with `User.is_active = False`.
- Allow cancellation by logging in with the same username/password before the 15-day deadline.
- Fully delete the user and cascading personal records after the deadline.
- Keep a minimal deleted-account audit record after purge:
  - original user id
  - username
  - masked email
  - original `date_joined`
  - deletion requested time
  - purge time
- Use masked email only. Do not retain email plaintext in the deleted-account audit table.
- Add a management command for purge execution.
- Add mypage entry point and confirmation page.

## Non-Scope

- Email notification for deletion request/cancellation/purge.
- Admin UI for deletion records.
- Background scheduler setup in production.
- Self-service data export.
- Separate password re-entry on delete confirmation. This can be added later if needed.

## TDD Boundary

Business logic must be TDD:

- email masking
- deletion request creation
- cancellation before deadline
- rejection after deadline
- purge and audit record creation

Template/UI wiring will be covered by rendering and POST regression tests after the service logic is green.

## Acceptance Criteria

- A logged-in user can request account deletion from mypage.
- Requesting deletion creates one active request, sets `is_active=False`, sets `scheduled_delete_at` to 15 days after request, logs the user out, and shows a message.
- Before `scheduled_delete_at`, a correct username/password login cancels deletion, reactivates the account, records `cancelled_at`, and logs the user in.
- After `scheduled_delete_at`, login does not cancel deletion.
- `purge_deleted_accounts` deletes due users, cascades user-owned records, marks the request purged, and creates `DeletedAccountRecord`.
- `DeletedAccountRecord.masked_email` stores only a masked address.
- Existing `User.date_joined` is preserved in the audit record.

## Data Model

### `AccountDeletionRequest`

- `user = OneToOneField(User, on_delete=CASCADE, related_name="deletion_request")`
- `requested_at = DateTimeField()`
- `scheduled_delete_at = DateTimeField()`
- `cancelled_at = DateTimeField(null=True, blank=True)`
- `purged_at = DateTimeField(null=True, blank=True)`
- indexes on `scheduled_delete_at`, `cancelled_at`, `purged_at`

### `DeletedAccountRecord`

- `original_user_id = PositiveIntegerField()`
- `username = CharField(max_length=150)`
- `masked_email = CharField(max_length=254, blank=True)`
- `date_joined = DateTimeField()`
- `deletion_requested_at = DateTimeField()`
- `purged_at = DateTimeField()`

## Implementation Tasks

### Task 1: Business Service TDD

**Files:**
- Create: `apps/users/test_account_deletion.py`
- Create: `apps/users/account_deletion.py`
- Modify: `apps/users/models.py`

**Steps:**
1. Write RED tests for `mask_email()`.
2. Implement minimal masking.
3. Write RED tests for request/cancel/purge behavior.
4. Add models and service functions.
5. Run focused tests to green.

### Task 2: Migration

**Files:**
- Create: `apps/users/migrations/0002_account_deletion.py`

**Steps:**
1. Generate or write migration for the two models.
2. Run `python manage.py makemigrations --check --dry-run`.

### Task 3: Login Cancellation

**Files:**
- Modify: `apps/users/views.py`
- Test: `apps/users/test_account_deletion.py`

**Steps:**
1. Add RED integration test: inactive pending-deletion user can log in before deadline and cancellation is recorded.
2. Add RED integration test: expired pending-deletion user cannot log in.
3. Implement helper in `login_view` after normal form invalid path.

### Task 4: UI Wiring

**Files:**
- Modify: `apps/users/urls.py`
- Modify: `apps/users/views.py`
- Modify: `apps/users/templates/users/mypage.html`
- Create: `apps/users/templates/users/account_delete_confirm.html`
- Test: `apps/users/test_account_deletion.py`

**Steps:**
1. Add delete confirmation route.
2. Add GET confirmation page and POST deletion request.
3. Add mypage link/section.
4. Add rendering/POST regression tests.

### Task 5: Purge Command

**Files:**
- Create: `apps/users/management/commands/purge_deleted_accounts.py`
- Test: `apps/users/test_account_deletion.py`

**Steps:**
1. Add command that calls `purge_due_deleted_accounts()`.
2. Add command smoke test.

### Task 6: Documentation And Verification

**Files:**
- Create: `docs/refactoring/2026-05-26_account-deletion-grace-period.md`
- Modify: `docs/project-status.md`

**Verification Commands:**

```bash
pytest apps/users/test_account_deletion.py --tb=short
pytest apps/users --tb=short
python manage.py makemigrations --check --dry-run
git diff --check
```

## Deferred Refactoring Note

- Topic: Deletion notification and export workflow.
- Why it is not part of the current scope: The approved scope is account deletion with grace cancellation and audit retention.
- Why it may be needed later: Users may expect email confirmations, deletion reminders, or a data export before purge.
- Trigger condition: Production launch, regulatory requirement, or user support request.
- Expected change location: `apps/users/account_deletion.py`, `apps/users/views.py`, email templates under `apps/users/templates/users/`.
- Related tests: account deletion email delivery, export access, and purge reminder tests.
