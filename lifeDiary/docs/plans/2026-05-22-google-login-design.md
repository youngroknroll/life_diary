# Google Login Design

- Date: 2026-05-22
- Status: Approved for implementation planning
- Scope: Web login only
- Decision: Add "Google로 계속하기" to the existing login page and allow first-time Google users to create a LifeDiary account automatically.

## Background

LifeDiary currently uses Django's built-in username/password authentication through `apps.users.views.login_view`. The login page is rendered by `apps/users/templates/users/login.html`, and web authentication is already protected by `django-axes`, session expiry policy, and production cookie settings.

The requested feature is social login with Google from the login page. Existing username/password login, signup, account recovery, and desktop authentication behavior must remain unchanged.

## Selected Approach

Use `django-allauth` with the Google social provider.

This is the preferred option because OAuth state handling, callback routing, provider integration, and account creation are security-sensitive and should use a maintained library rather than local OAuth code. The official allauth Google provider documentation requires registering `allauth.socialaccount.providers.google` and configuring a Google OAuth client ID and secret. The provider configuration documentation supports settings-based configuration, which avoids storing OAuth secrets in the database.

## User Flow

1. The login page shows the existing username/password form.
2. Under the existing submit button, it shows a secondary "Google로 계속하기" action.
3. Selecting the Google action starts the allauth Google OAuth flow.
4. On success, allauth logs in an existing linked account or creates a new user from the Google account.
5. The user lands on the existing home page after login.
6. On OAuth cancellation or error, allauth returns the user to the login/account flow with an error message.

## Architecture

The implementation should add allauth as a web authentication integration while preserving the current `users:login` route for username/password login.

Expected changes:

- Add `django-allauth` to `requirements.txt`.
- Add required allauth apps and middleware to `lifeDiary/settings/dev.py`.
- Add `allauth.account.auth_backends.AuthenticationBackend` after the existing Django model backend.
- Add `allauth.socialaccount.providers.google`.
- Configure Google provider credentials from environment variables, not admin database records.
- Include allauth URLs under `accounts/` in `lifeDiary/urls.py`, after the project user URLs so existing routes keep precedence.
- Add a Google login button to `apps/users/templates/users/login.html`.

The desktop settings inherit from development settings today, but desktop social login is not part of this scope. If allauth causes desktop-specific issues, document the issue as deferred work rather than expanding the feature.

## Account Policy

- First-time Google users may create an account automatically.
- Google should request only `profile` and `email`.
- Existing username/password accounts remain valid.
- Email verification is not introduced in this task.
- MFA, Google One Tap, account deletion, and custom account-linking UX are out of scope.

## Configuration

Use environment variables:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

For local Google Console setup, the authorized redirect URI should match the allauth Google callback route:

- local: `http://127.0.0.1:8000/accounts/google/login/callback/`
- production: `https://lifediary.onrender.com/accounts/google/login/callback/`

The exact deployed domain must be checked before production rollout.

## Acceptance Criteria

- Login page renders a "Google로 계속하기" action.
- The action resolves to allauth's Google login URL.
- Existing username/password login still works.
- Google provider is registered in Django settings.
- OAuth client credentials are read from environment variables.
- Missing local Google credentials do not break normal username/password login page rendering.
- Focused tests cover the login page Google entry point and settings registration.
- Fresh verification output is recorded before completion.

## Non-Scope

- Desktop app Google login.
- Email verification.
- MFA / 2FA.
- Google One Tap.
- Custom account merge UI.
- Replacing existing login, signup, or recovery views.
- Storing OAuth secrets through the Django admin.

## Risks

- OAuth redirect URI mismatch can block login until Google Console settings match the deployed host.
- Social login creates an external dependency on Google OAuth availability.
- Auto-created accounts can create email/account-linking edge cases that need later policy work.
- allauth may introduce migrations for social account tables; these must be applied before production use.

## Verification Plan

Minimum commands:

```bash
conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py apps/users/tests.py --tb=short
conda run -n knou-life-diary python manage.py check
git diff --check
```

Manual verification remains required for a real Google OAuth round trip because it depends on external Google credentials and redirect URI configuration.

## Deferred Refactoring Note

- Topic: Custom account-linking policy for users with existing password accounts and matching Google email.
- Why it is not part of the current scope: The approved scope is the first Google login entry point and basic allauth integration.
- Why it may be needed later: Existing users may expect Google login to attach cleanly to their current LifeDiary account.
- Trigger condition: A real user reports duplicate account creation or account-linking confusion.
- Expected change location: `apps/users/`, allauth adapter configuration, login/signup templates.
- Related tests: social login account linking, duplicate email handling, login page rendering.
