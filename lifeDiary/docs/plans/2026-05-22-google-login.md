# Google Login Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Google로 계속하기" login path using `django-allauth` while keeping the current username/password login flow intact.

**Architecture:** Integrate `django-allauth` at the Django settings and URL layer, then expose the provider login URL from the existing login template. Keep `apps.users.views.login_view` as the owner of username/password login and use settings-based Google OAuth credentials from environment variables.

**Tech Stack:** Django 5.2.4, django-allauth Google social provider, pytest, pytest-django, django-axes.

---

## Approved Scope

- Web login page only.
- Add Google social login entry point.
- Allow first-time Google users to create accounts automatically through allauth.
- Preserve existing username/password login behavior.
- Configure Google OAuth credentials with environment variables.

## Non-Scope

- Desktop social login.
- Email verification.
- MFA / 2FA.
- Google One Tap.
- Custom account merge UI.
- Replacing current login, signup, or account recovery views.
- Storing OAuth credentials in Django admin `SocialApp` records.

## External Setup Required

Before a real OAuth browser round trip can pass, create a Google OAuth web application and configure redirect URIs:

- local: `http://127.0.0.1:8000/accounts/google/login/callback/`
- production: `https://lifediary.onrender.com/accounts/google/login/callback/`

Set these environment variables in the runtime environment:

- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

## Task 1: Add Failing Tests For Login Page Google Entry

**Files:**
- Modify: `apps/users/test_auth_enhance_render.py`

**Step 1: Write the failing test**

Add this behavior test:

```python
@pytest.mark.django_db
def test_login_page_has_google_continue_link(client):
    r = client.get("/accounts/login/")

    assert r.status_code == 200
    h = r.content.decode()
    assert "Google로 계속하기" in h
    assert "/accounts/google/login/" in h
```

**Step 2: Run test to verify it fails**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py::test_login_page_has_google_continue_link --tb=short
```

Expected: FAIL because the login page does not yet render the Google login action.

**Step 3: Stop**

Do not modify the template until the RED failure has been verified.

## Task 2: Add Failing Tests For Settings And URL Registration

**Files:**
- Create: `apps/users/test_google_login_settings.py`

**Step 1: Write the failing tests**

Create:

```python
from django.conf import settings
from django.urls import reverse


def test_google_allauth_apps_are_registered():
    assert "allauth" in settings.INSTALLED_APPS
    assert "allauth.account" in settings.INSTALLED_APPS
    assert "allauth.socialaccount" in settings.INSTALLED_APPS
    assert "allauth.socialaccount.providers.google" in settings.INSTALLED_APPS


def test_allauth_backend_is_registered_after_model_backend():
    backends = list(settings.AUTHENTICATION_BACKENDS)
    assert "django.contrib.auth.backends.ModelBackend" in backends
    assert "allauth.account.auth_backends.AuthenticationBackend" in backends
    assert backends.index("django.contrib.auth.backends.ModelBackend") < backends.index(
        "allauth.account.auth_backends.AuthenticationBackend"
    )


def test_google_provider_uses_environment_config(settings, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-client-secret")

    providers = settings.SOCIALACCOUNT_PROVIDERS
    google_app = providers["google"]["APPS"][0]

    assert google_app["client_id"] == "test-client-id"
    assert google_app["secret"] == "test-client-secret"
    assert providers["google"]["SCOPE"] == ["profile", "email"]


def test_google_login_url_is_registered():
    assert reverse("google_login") == "/accounts/google/login/"
```

If the environment-based settings are read at import time, adjust the third test to assert the configured keys and document that runtime env changes require process restart.

**Step 2: Run tests to verify they fail**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_google_login_settings.py --tb=short
```

Expected: FAIL because allauth is not installed or registered yet.

## Task 3: Add allauth Dependency

**Files:**
- Modify: `requirements.txt`

**Step 1: Add dependency**

Add a pinned `django-allauth` version compatible with Django 5.2.

Recommended after checking the installed package index:

```text
django-allauth==64.3.0
```

If package resolution shows a newer stable version, use that version and record it in the final verification notes.

**Step 2: Install dependency if missing**

Run:

```bash
conda run -n knou-life-diary python -m pip install -r requirements.txt
```

Expected: dependency installed successfully.

If network access is blocked, request approval for the install command with escalated network access.

## Task 4: Register allauth In Django Settings

**Files:**
- Modify: `lifeDiary/settings/dev.py`

**Step 1: Minimal implementation**

Add allauth apps after Django contrib apps and before project apps:

```python
"django.contrib.sites",
"allauth",
"allauth.account",
"allauth.socialaccount",
"allauth.socialaccount.providers.google",
```

Add middleware after Django authentication middleware:

```python
"allauth.account.middleware.AccountMiddleware",
```

Add the allauth backend after the existing model backend:

```python
"allauth.account.auth_backends.AuthenticationBackend",
```

Add settings:

```python
SITE_ID = 1
LOGIN_REDIRECT_URL = "home"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
                "secret": os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", ""),
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}
```

Use the setting names supported by the installed allauth version. If the installed version warns about deprecated account settings, update to the non-deprecated names and record the change.

**Step 2: Run settings tests**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_google_login_settings.py --tb=short
```

Expected: settings assertions may pass, URL assertion may still fail until Task 5.

## Task 5: Register allauth URLs

**Files:**
- Modify: `lifeDiary/urls.py`

**Step 1: Add allauth URL include**

Keep the existing project user URLs first:

```python
path("accounts/", include("apps.users.urls")),
path("accounts/", include("allauth.urls")),
```

This preserves current `/accounts/login/`, `/accounts/signup/`, password reset, and recovery routes while allowing `/accounts/google/login/`.

**Step 2: Run URL test**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_google_login_settings.py::test_google_login_url_is_registered --tb=short
```

Expected: PASS.

## Task 6: Render Google Login Button

**Files:**
- Modify: `apps/users/templates/users/login.html`

**Step 1: Minimal implementation**

Load the socialaccount template tags:

```django
{% load socialaccount %}
```

Add the button below the existing username/password submit button:

```django
<div class="d-grid gap-2 mt-2">
    <a href="{% provider_login_url 'google' %}" class="btn btn-outline-secondary">
        <i class="fab fa-google me-1" aria-hidden="true"></i>
        {% trans "Google로 계속하기" %}
    </a>
</div>
```

Use existing Bootstrap and Font Awesome conventions already present in the template. Do not redesign the auth page.

**Step 2: Run login render test**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py::test_login_page_has_google_continue_link --tb=short
```

Expected: PASS.

## Task 7: Run Focused Regression Tests

**Files:**
- Test only.

**Step 1: Run auth tests**

Run:

```bash
conda run -n knou-life-diary pytest apps/users/test_auth_enhance_render.py apps/users/test_google_login_settings.py apps/users/tests.py --tb=short
```

Expected: PASS.

**Step 2: Run Django system check**

Run:

```bash
conda run -n knou-life-diary python manage.py check
```

Expected: no system check errors.

**Step 3: Run diff hygiene**

Run:

```bash
git diff --check
```

Expected: exit 0.

## Task 8: Post-Work Documentation

**Files:**
- Create: `docs/refactoring/2026-05-22-google-login.md`
- Modify: `docs/project-status.md`

**Step 1: Write refactoring document**

Include:

- approved scope
- changed files
- verification commands and exact outcomes
- unverified manual Google OAuth browser round trip, unless real credentials were available and tested
- deferred account-linking policy note

**Step 2: Update project status**

Add a row or section for Google login with links to:

- `docs/plans/2026-05-22-google-login-design.md`
- `docs/plans/2026-05-22-google-login.md`
- `docs/refactoring/2026-05-22-google-login.md`

Record only fresh verification evidence.

## Completion Gate

The feature is complete only when:

- RED failures were observed before implementation.
- Focused auth tests pass.
- `manage.py check` passes.
- `git diff --check` passes.
- Documentation records unverified external OAuth round trip if credentials were not available.
