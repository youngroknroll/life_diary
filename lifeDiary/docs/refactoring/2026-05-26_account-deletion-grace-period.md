# Account Deletion Grace Period Execution Log

## Context

The site needed account deletion with a reversible grace period rather than immediate deletion. The approved policy is a 15-day grace period, cancellation by logging in again, permanent deletion after the deadline, and minimal audit retention with masked email only.

## Changed

- Added `AccountDeletionRequest` to track active/cancelled/purged deletion requests.
- Added `DeletedAccountRecord` to retain minimal post-purge audit data without a user FK.
- Added `apps.users.account_deletion` business service:
  - `mask_email()`
  - `request_account_deletion()`
  - `cancel_account_deletion()`
  - `purge_due_deleted_accounts()`
- Added migration `apps/users/migrations/0003_account_deletion.py`.
- Added `purge_deleted_accounts` management command.
- Added account deletion confirmation route and template.
- Added mypage account deletion section.
- Integrated login cancellation for inactive pending-deletion accounts inside the existing `login_view`.
- Added Korean and English UI/messages for account deletion.
- Added focused business, view, management command, and i18n tests.

## Design Reasoning

Django's default `User.date_joined` already stores signup time, so no separate signup-date field was added. Active deletion state remains tied to the user through `AccountDeletionRequest`; after purge, only `DeletedAccountRecord` remains so the user and personal records can be deleted through existing cascade relationships. Login cancellation is handled narrowly in `login_view` after the normal `AuthenticationForm` path fails, avoiding a broader authentication backend change for this one recovery case.

## Verification

- RED account deletion test run:
  - `pytest apps/users/test_account_deletion.py --tb=short`
  - Result: failed with `ModuleNotFoundError: No module named 'apps.users.account_deletion'`
- RED English deletion i18n run:
  - `pytest apps/users/test_i18n_phase4.py::TestAccountDeletionEnglish apps/users/test_i18n_phase4.py::TestMypageEnglish::test_mypage_renders_english --tb=short`
  - Result: `3 failed` because English account deletion strings were not translated yet.
- GREEN focused account deletion:
  - `pytest apps/users/test_account_deletion.py --tb=short`
  - Result: `14 passed in 12.59s`
- GREEN account deletion + users i18n:
  - `pytest apps/users/test_account_deletion.py apps/users/test_i18n_phase4.py --tb=short`
  - Result: `24 passed in 21.15s`
- Users regression:
  - `pytest apps/users --tb=short`
  - Result: `101 passed in 81.95s`
- Migration check:
  - `python manage.py makemigrations --check --dry-run`
  - Result: `No changes detected`
- Whitespace check:
  - `git diff --check`
  - Result: exit 0

## Not Verified

- Production scheduler/cron setup for `purge_deleted_accounts` was not configured.
- Manual browser inspection was not performed.
- Email notifications for deletion request/cancellation/purge were not implemented.

## Deferred Refactoring Note

- Topic: Deletion notification and data export workflow.
- Why it is not part of the current scope: The approved scope is account deletion with grace cancellation and audit retention.
- Why it may be needed later: Users may expect email confirmations, deletion reminders, or data export before purge.
- Trigger condition: Production launch, regulatory requirement, or user support request.
- Expected change location: `apps/users/account_deletion.py`, `apps/users/views.py`, email templates under `apps/users/templates/users/`.
- Related tests: account deletion email delivery, export access, purge reminder, and scheduler integration tests.
