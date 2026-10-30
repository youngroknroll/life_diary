import pytest
from django.core.cache import caches
from django.urls import reverse

from conftest import DEFAULT_TEST_PASSWORD

LOCMEM = "django.core.cache.backends.locmem.LocMemCache"
LIMIT = 3


@pytest.fixture(autouse=True)
def _two_caches(settings):
    settings.LOGIN_RECAPTCHA_ENABLED = True
    settings.LOGIN_RECAPTCHA_FAILURE_LIMIT = LIMIT
    settings.RECAPTCHA_SITE_KEY = "site-key"
    settings.RECAPTCHA_SECRET_KEY = "secret-key"
    settings.CACHES = {
        "default": {"BACKEND": LOCMEM, "LOCATION": "isolation-default"},
        "security": {"BACKEND": LOCMEM, "LOCATION": "isolation-security"},
    }
    caches["default"].clear()
    caches["security"].clear()


def _fail_login(client):
    return client.post(
        reverse("users:login"),
        {"username": "youngrok", "password": f"{DEFAULT_TEST_PASSWORD}-wrong"},
    )


@pytest.mark.django_db
def test_login_failure_budget_survives_a_statistics_cache_flush(client, make_user):
    make_user(username="youngrok")
    _fail_login(client)
    _fail_login(client)

    caches["default"].clear()
    response = _fail_login(client)

    assert "g-recaptcha" in response.content.decode()
