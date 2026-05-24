# Login reCAPTCHA After Failures

- Date: 2026-05-25
- Scope: Local development login lockout and production repeated-failure challenge
- Plan: `docs/plans/2026-05-25-login-recaptcha-after-failures.md`

## What Changed

- Disabled `django-axes` lockout behavior in local development with `AXES_ENABLED = False`.
- Added production reCAPTCHA settings:
  - `LOGIN_RECAPTCHA_ENABLED = True`
  - `LOGIN_RECAPTCHA_FAILURE_LIMIT = 5`
  - `LOGIN_RECAPTCHA_CACHE_TIMEOUT = 60 * 60`
  - `RECAPTCHA_SITE_KEY`
  - `RECAPTCHA_SECRET_KEY`
- Raised production `AXES_FAILURE_LIMIT` above the reCAPTCHA threshold so axes does not return an account-locked response before the challenge can be completed.
- Added cache-backed login failure counting by client identifier and username.
- Added server-side Google reCAPTCHA verification before allowing challenged logins.
- Updated the login template to render the reCAPTCHA widget only when the challenge is required.

## Code Design Reason

The user-facing production behavior is now challenge-based rather than lockout-based. After repeated failed logins, the user can still log in with the correct password if they complete reCAPTCHA. This avoids the poor UX of a hard account lock while still adding friction for automated login attempts.

Local development disables axes because repeated password mistakes are common while testing and should not block the developer. Production keeps axes enabled for the broader auth stack, but its lockout threshold is intentionally higher than the reCAPTCHA threshold so the reCAPTCHA flow is the first user-facing control.

The reCAPTCHA verification uses Python stdlib `urllib` instead of adding a new package. That keeps the change scoped and avoids another dependency for one POST request.

## Verification Evidence

Fresh verification run on 2026-05-25:

```bash
pytest apps/users/tests.py::TestLoginView::test_local_development_disables_axes apps/users/tests.py::TestLoginRecaptchaChallenge lifeDiary/test_prod_settings.py::test_prod_settings_enable_login_recaptcha_after_failures --tb=short
# RED before implementation: 5 failed
```

```bash
pytest apps/users/tests.py::TestLoginView::test_local_development_disables_axes apps/users/tests.py::TestLoginRecaptchaChallenge lifeDiary/test_prod_settings.py::test_prod_settings_enable_login_recaptcha_after_failures --tb=short
# 5 passed in 16.98s
```

```bash
pytest apps/users/tests.py lifeDiary/test_prod_settings.py --tb=short
# 15 passed in 31.51s
```

```bash
pytest apps/users/test_auth_enhance_render.py apps/users/test_remember_me.py --tb=short
# 8 passed in 4.19s
```

```bash
pytest apps/users/tests.py lifeDiary/test_prod_settings.py apps/users/test_auth_enhance_render.py apps/users/test_remember_me.py --tb=short
# 23 passed in 37.19s
```

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

```bash
DJANGO_SECRET_KEY=prod-recaptcha-check-2026-05-25-with-diverse-characters-ABC123xyz789 DB_NAME=test_db DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost DB_PORT=6543 EMAIL_HOST_USER=test@example.com EMAIL_HOST_PASSWORD=test-password DEFAULT_FROM_EMAIL=test@example.com RECAPTCHA_SITE_KEY=site-key RECAPTCHA_SECRET_KEY=secret-key python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR
# System check identified no issues (0 silenced).
```

```bash
git diff --check
# exit 0
```

## Not Verified

- A real Google reCAPTCHA browser challenge was not manually completed.
- Production deployment environment variables were not verified on Render.

## Deferred Refactoring Note

- Topic: Central authentication risk service
- Why it is not part of the current scope: This task only needed repeated-login-failure challenge behavior.
- Why it may be needed later: Login, recovery, signup validation, and future account alerts may need one place to manage risk counters and user-facing security actions.
- Trigger condition: More than one auth flow requires challenge/risk scoring beyond simple rate limits.
- Expected change location: `apps/users/` auth services or a small `apps/core/security.py`.
- Related tests: login challenge, recovery rate limit, signup validation throttling, and future alert tests.
