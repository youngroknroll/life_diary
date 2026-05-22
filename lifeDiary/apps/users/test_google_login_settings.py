from django.conf import settings
from django.urls import reverse

from lifeDiary.settings import dev as dev_settings


def test_google_allauth_apps_are_registered():
    assert "allauth" in settings.INSTALLED_APPS
    assert "allauth.account" in settings.INSTALLED_APPS
    assert "allauth.socialaccount" in settings.INSTALLED_APPS
    assert "allauth.socialaccount.providers.google" in settings.INSTALLED_APPS


def test_allauth_backend_is_registered_after_model_backend():
    backends = list(dev_settings.AUTHENTICATION_BACKENDS)
    assert "django.contrib.auth.backends.ModelBackend" in backends
    assert "allauth.account.auth_backends.AuthenticationBackend" in backends
    assert backends.index("django.contrib.auth.backends.ModelBackend") < backends.index(
        "allauth.account.auth_backends.AuthenticationBackend"
    )


def test_google_provider_uses_settings_based_environment_config():
    providers = settings.SOCIALACCOUNT_PROVIDERS
    google = providers["google"]
    google_app = google["APPS"][0]

    assert set(google_app) == {"client_id", "secret", "key"}
    assert google_app["client_id"] == settings.GOOGLE_OAUTH_CLIENT_ID
    assert google_app["secret"] == settings.GOOGLE_OAUTH_CLIENT_SECRET
    assert google["SCOPE"] == ["profile", "email"]


def test_google_login_url_is_registered():
    assert reverse("google_login") == "/accounts/google/login/"
