# Google Login Integration

- Date: 2026-05-22
- Scope: Web login page Google OAuth entry point
- Plan: `docs/plans/2026-05-22-google-login-design.md`, `docs/plans/2026-05-22-google-login.md`

## What Changed

- Added `django-allauth` and required Google provider runtime dependencies to `requirements.txt`.
- Registered allauth, socialaccount, sites, and the Google provider in `lifeDiary/settings/dev.py`.
- Added allauth account middleware and authentication backend after the existing Django model backend.
- Configured Google OAuth credentials through `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`.
- Mounted allauth URLs under `/accounts/` after existing `apps.users.urls`.
- Added a "Google로 계속하기" action to the existing login page.
- Added focused tests for the login page Google entry point and allauth provider/settings registration.

## Verification Evidence

Fresh verification run on 2026-05-22:

```bash
conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py::test_login_page_has_google_continue_link --tb=short
# 1 passed, 1 warning in 2.26s

conda run -n knou-life-diary pytest apps/users/test_google_login_settings.py --tb=short
# 4 passed in 0.22s

conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py apps/users/test_google_login_settings.py --tb=short
# 8 passed, 4 warnings in 1.46s

conda run -n knou-life-diary python manage.py check
# System check identified no issues (0 silenced).

git diff --check
# exit 0
```

The broader auth regression command was also run:

```bash
conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py apps/users/test_google_login_settings.py apps/users/tests.py --tb=short
# 2 failed, 14 passed
```

The failures were both existing axes lockout assertions in `apps/users/tests.py`. The same two failures were observed in the clean worktree baseline before the Google login implementation, so they are not counted as introduced by this task.

## Not Verified

- Real Google OAuth browser round trip was not verified because Google OAuth client credentials and Google Console redirect URI setup were not available in this session.
- Production deployment behavior was not verified.
- Desktop app behavior was not verified because desktop Google login is out of scope.

## Operational Notes

Before production use, configure these environment variables:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

Google Console redirect URIs should include:

- `http://127.0.0.1:8000/accounts/google/login/callback/`
- `https://lifediary.onrender.com/accounts/google/login/callback/`

Run allauth migrations before production use because the integration adds `django.contrib.sites`, `allauth.account`, and `allauth.socialaccount` database tables.

## Deferred Refactoring Note

- Topic: Existing password-account linking for matching Google email addresses
- Why it is not part of the current scope: The approved scope was adding the basic "Google로 계속하기" entry point and allauth integration.
- Why it may be needed later: Existing users may expect Google login to attach to their current LifeDiary account instead of creating a separate social account path.
- Trigger condition: Duplicate account creation, account-linking support requests, or a product decision to require verified email ownership before linking.
- Expected change location: `apps/users/`, allauth adapter configuration, auth templates.
- Related tests: social login account linking, duplicate email handling, login rendering.
