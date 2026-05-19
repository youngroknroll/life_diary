# Auth Cookie Login Security Execution Log

Date: 2026-05-19

## Scope

Implemented the approved web-only auth hardening from:

- `docs/plans/2026-05-19_auth-cookie-login-security-plan.md`
- `docs/plans/2026-05-19_auth-cookie-login-security-implementation-plan.md`

## Changed Files

- `apps/users/views.py`
- `apps/users/urls.py`
- `apps/users/test_remember_me.py`
- `apps/users/test_password_reset.py`
- `apps/users/test_username_recovery.py`
- `apps/users/test_realtime_validation.py`
- `apps/users/test_prod_settings.py`
- `apps/users/tests.py`
- `lifeDiary/settings/prod.py`
- `docs/plans/2026-05-19_auth-cookie-login-security-plan.md`
- `docs/plans/2026-05-19_auth-cookie-login-security-implementation-plan.md`
- `docs/project-status.md`

## What Changed

- Reduced `remember_me` session lifetime from 30 days to 14 days while keeping unchecked logins as browser-session only.
- Made the production cookie contract explicit with:
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = "Lax"`
  - `CSRF_COOKIE_SAMESITE = "Lax"`
- Added `PASSWORD_RESET_TIMEOUT = 3 hours` to production settings.
- Added cache-based fixed-window rate limiting for:
  - `password reset`
  - `username recovery`
  - `check-email`
  - `check-username`
- Preserved endpoint response contracts:
  - password reset and username recovery still redirect to the same done pages when throttled
  - realtime validation endpoints still return `200` JSON and switch to a generic unavailable response when throttled
- Added password reset UX tests for invalid, expired, and reused tokens.
- Added `django-axes` behavior tests for lockout, cooloff recovery, and reset-on-success.

## Verification

- Baseline regression before changes:
  - `conda run -n knou-life-diary pytest apps/users/test_signup_email.py apps/users/test_welcome.py apps/users/test_remember_me.py apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_realtime_validation.py apps/users/test_auth_enhance_render.py apps/users/test_jsi18n_auth.py apps/users/test_i18n_phase4.py apps/users/tests.py --tb=short`
  - `52 passed in 34.01s`
- RED 1:
  - `conda run -n knou-life-diary pytest apps/users/test_remember_me.py --tb=short`
  - failed with `1 failed, 2 passed` because the implementation still used 30 days
- GREEN 1:
  - same targeted command passed with `3 passed in 3.90s`
- RED 2:
  - `conda run -n knou-life-diary pytest apps/users/test_prod_settings.py --tb=short`
  - failed first for missing `SESSION_COOKIE_HTTPONLY`, then for missing `PASSWORD_RESET_TIMEOUT`
- GREEN 2:
  - same targeted command passed with `2 passed in 0.05s`
- RED 3/4:
  - `conda run -n knou-life-diary pytest apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_realtime_validation.py --tb=short`
  - failed with `4 failed, 20 passed` before rate limiting was active in test conditions
- GREEN 3/4:
  - same targeted command passed with `24 passed in 17.25s`
- RED 5:
  - `conda run -n knou-life-diary pytest apps/users/test_password_reset.py --tb=short`
  - initially failed because the expired-token test itself used the wrong time context
- GREEN 5:
  - same targeted command passed with `7 passed in 8.35s`
- RED 6:
  - `conda run -n knou-life-diary pytest apps/users/tests.py --tb=short`
  - first failed from an invalid `override_settings` test structure, then from an incorrect lockout expectation
- GREEN 6:
  - same targeted command passed with `8 passed in 15.92s`
- Final focused regression:
  - `conda run -n knou-life-diary pytest apps/users/test_remember_me.py apps/users/test_prod_settings.py apps/users/test_password_reset.py apps/users/test_username_recovery.py apps/users/test_realtime_validation.py apps/users/tests.py --tb=short`
  - `40 passed in 35.83s`
- Deploy-oriented settings check:
  - `DJANGO_SECRET_KEY=test-ci-secret-value-for-deploy-readiness-checks-only-1234567890 DB_NAME=test_db DB_USER=test_user DB_PASSWORD=test_password DB_HOST=localhost DB_PORT=6543 RESEND_API_KEY=re_test_dummy DEFAULT_FROM_EMAIL='LifeDiary <noreply@example.com>' conda run -n knou-life-diary python manage.py check --settings=lifeDiary.settings.prod --deploy --fail-level ERROR`
  - `System check identified no issues (0 silenced).`
- Diff hygiene:
  - `git diff --check`
  - exit 0

## Not Verified

- Full repository test suite was not run after this change.
- Live Resend delivery and sender-domain verification remain unverified.
- Real browser `Set-Cookie` headers were not manually inspected in a deployed environment.

## Remaining Risk

- The new rate limiter uses the default Django cache backend, so runtime behavior depends on the deployed cache configuration.
- Production proxy-related security settings such as `SECURE_PROXY_SSL_HEADER` and `CSRF_TRUSTED_ORIGINS` remain deferred.
- Signup still treats an unverified email address as the recovery channel.

## Deferred Refactoring Note

- Topic: Move public endpoint throttling into a dedicated auth/security utility module.
- Why it is not part of the current scope: The approved task required low-interference hardening without broader auth refactoring.
- Why it may be needed later: Additional public endpoints or differentiated throttle policies will make the inline view helper harder to maintain.
- Trigger condition: More auth abuse controls are added or cache-key policy needs central governance.
- Expected change location: `apps/users/` or `apps/core/security/`.
- Related tests: `apps/users/test_password_reset.py`, `apps/users/test_username_recovery.py`, `apps/users/test_realtime_validation.py`, `apps/users/tests.py`.
