# Password Reset Request Host

- Date: 2026-05-24
- Scope: Development password reset email link host
- Plan: `docs/plans/2026-05-24-password-reset-request-host.md`

## What Changed

- Updated `RateLimitedPasswordResetView.form_valid()` to pass `domain_override=self.request.get_host()` when saving the reset form.
- Added a regression test that posts a password reset request with `HTTP_HOST="127.0.0.1:8000"` and verifies the email link uses that host instead of `example.com`.

## Code Design Reason

Django's default password reset form uses `get_current_site(request)` when `domain_override` is not provided. Because this project enables `django.contrib.sites` with `SITE_ID = 1`, a development database with the default Site row can produce reset links under `example.com`.

Passing `domain_override` keeps the existing Django reset flow, token generation, templates, and rate limiting intact while making links follow the actual request host. This also matches the existing username recovery email behavior, which already uses `request.get_host()`.

## Verification Evidence

Fresh verification run on 2026-05-24:

```bash
pytest apps/users/test_password_reset.py::TestPasswordReset::test_reset_email_uses_request_host_not_default_site_domain --tb=short
# RED before implementation: email body contained http://example.com/...
```

```bash
pytest apps/users/test_password_reset.py::TestPasswordReset::test_reset_email_uses_request_host_not_default_site_domain --tb=short
# 1 passed in 1.69s
```

```bash
pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py --tb=short
# 14 passed in 14.66s
```

```bash
git diff --check
# exit 0
```

## Not Verified

- A real browser click from a development email was not manually verified in this session.
- Production email links were not tested against the deployed service.

## Deferred Refactoring Note

- Topic: Central recovery email URL/domain policy
- Why it is not part of the current scope: The immediate bug only affects password reset links generated through Django's default Site lookup.
- Why it may be needed later: More recovery or notification emails may need consistent host/protocol handling across web, desktop, and production settings.
- Trigger condition: Another email flow starts generating incorrect absolute URLs or requires canonical host control.
- Expected change location: `apps/users/views.py`, email helper functions, or a small recovery email service.
- Related tests: password reset, username recovery, and any future account email URL tests.
