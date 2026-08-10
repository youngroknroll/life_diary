import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse

User = get_user_model()

PASSWORD = "right-pass-2026!"
WRONG = "wrong-pass-2026!"
LIMIT = 3


@pytest.fixture
def member(db):
    return User.objects.create_user(username="youngrok", password=PASSWORD)


@pytest.fixture(autouse=True)
def counting_cache(settings):
    """conftest pins every test to DummyCache, which cannot count.

    The failure budget lives in the cache, so this suite needs a backend that
    actually retains and increments.
    """
    settings.LOGIN_RECAPTCHA_FAILURE_LIMIT = LIMIT
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "login-remaining-attempts",
        }
    }
    cache.clear()
    yield
    cache.clear()


def fail_login(client, times=1):
    response = None
    for _ in range(times):
        response = client.post(
            reverse("users:login"), {"username": "youngrok", "password": WRONG}
        )
    return response


@pytest.mark.django_db
class TestRemainingAttempts:
    def test_first_failure_reports_the_rest_of_the_budget(self, client, member):
        response = fail_login(client)

        assert response.context["remaining_attempts"] == LIMIT - 1

    def test_countdown_follows_each_failure(self, client, member):
        response = fail_login(client, times=2)

        assert response.context["remaining_attempts"] == LIMIT - 2

    def test_budget_stops_at_zero(self, client, member):
        response = fail_login(client, times=LIMIT + 2)

        assert response.context["remaining_attempts"] == 0

    def test_a_fresh_visitor_has_no_countdown_to_show(self, client, member):
        response = client.get(reverse("users:login"))

        assert response.context["remaining_attempts"] is None

    def test_signing_in_clears_the_countdown(self, client, member):
        fail_login(client, times=2)

        client.post(reverse("users:login"), {"username": "youngrok", "password": PASSWORD})
        response = client.get(reverse("users:login"))

        assert response.context["remaining_attempts"] is None
