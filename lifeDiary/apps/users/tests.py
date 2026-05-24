import time
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse

from apps.tags.models import Category, Tag
from apps.users.domain_services import GoalProgressService
from apps.users.models import UserGoal


class TestGoalProgressService:
    def test_get_actual_hours_from_daily_stats(self):
        service = GoalProgressService()
        goal = SimpleNamespace(
            period="daily",
            tag=SimpleNamespace(name="운동"),
            target_hours=2,
        )
        actual = service.get_actual_hours(
            goal,
            daily_stats={"tag_stats": [{"name": "운동", "hours": 1.5}]},
        )
        assert actual == 1.5

    def test_get_actual_hours_from_weekly_stats(self):
        service = GoalProgressService()
        goal = SimpleNamespace(
            period="weekly",
            tag=SimpleNamespace(name="공부"),
            target_hours=8,
        )
        actual = service.get_actual_hours(
            goal,
            weekly_stats={"tag_weekly_stats": [{"name": "공부", "total_hours": 6.5}]},
        )
        assert actual == 6.5


@pytest.fixture
def alice_bob_with_bob_tag(make_user):
    alice = make_user(username="alice")
    bob = make_user(username="bob")
    category = Category.objects.create(name="일반", slug="general", color="#000000")
    bob_tag = Tag.objects.create(
        user=bob,
        name="bob_only",
        color="#123456",
        is_default=False,
        category=category,
    )
    return alice, bob, bob_tag


@pytest.mark.django_db
class TestUserGoalTagOwnership:
    def test_create_rejects_other_users_tag(self, client, alice_bob_with_bob_tag):
        alice, _, bob_tag = alice_bob_with_bob_tag
        client.force_login(alice)
        resp = client.post(
            reverse("users:usergoal_create"),
            data={"tag": bob_tag.id, "period": "daily", "target_hours": 1.0},
        )
        assert resp.status_code == 200
        assert not UserGoal.objects.filter(user=alice, tag=bob_tag).exists()

    def test_mypage_rejects_other_users_tag(self, client, alice_bob_with_bob_tag):
        alice, _, bob_tag = alice_bob_with_bob_tag
        client.force_login(alice)
        resp = client.post(
            reverse("users:mypage"),
            data={"tag": bob_tag.id, "period": "monthly", "target_hours": 10.0},
        )
        assert resp.status_code == 200
        assert not UserGoal.objects.filter(user=alice, tag=bob_tag).exists()


@pytest.mark.django_db
class TestLoginView:
    def test_login_succeeds_with_axes_backend_enabled(self, client, make_user):
        make_user(username="login-user", password="pw123456!!")
        with override_settings(
            AXES_ENABLED=True,
            AUTHENTICATION_BACKENDS=[
                "axes.backends.AxesStandaloneBackend",
                "django.contrib.auth.backends.ModelBackend",
            ],
        ):
            response = client.post(
                reverse("users:login"),
                data={"username": "login-user", "password": "pw123456!!"},
            )
        assert response.status_code == 302
        assert response.url == reverse("home")

    def test_local_development_disables_axes(self):
        from lifeDiary.settings import dev

        assert dev.AXES_ENABLED is False


@pytest.mark.django_db
class TestLoginRecaptchaChallenge:
    @pytest.fixture(autouse=True)
    def _settings(self, settings):
        settings.LOGIN_RECAPTCHA_ENABLED = True
        settings.LOGIN_RECAPTCHA_FAILURE_LIMIT = 5
        settings.LOGIN_RECAPTCHA_CACHE_TIMEOUT = 60 * 60
        settings.RECAPTCHA_SITE_KEY = "site-key"
        settings.RECAPTCHA_SECRET_KEY = "secret-key"
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "users-login-recaptcha-tests",
            }
        }
        settings.AXES_ENABLED = False
        call_command("axes_reset")

    def _login(self, client, password, token=None):
        data = {"username": "login-user", "password": password}
        if token is not None:
            data["g-recaptcha-response"] = token
        return client.post(reverse("users:login"), data=data)

    def test_fifth_failed_login_shows_recaptcha(self, client, make_user):
        make_user(username="login-user", password="pw123456!!")

        for _ in range(4):
            response = self._login(client, "wrong-password")
            assert response.status_code == 200
            assert "g-recaptcha" not in response.content.decode()

        response = self._login(client, "wrong-password")
        content = response.content.decode()

        assert response.status_code == 200
        assert "g-recaptcha" in content
        assert "site-key" in content

    def test_challenged_login_requires_recaptcha_even_with_correct_password(
        self, client, make_user
    ):
        make_user(username="login-user", password="pw123456!!")

        for _ in range(5):
            self._login(client, "wrong-password")

        response = self._login(client, "pw123456!!")

        assert response.status_code == 200
        assert "g-recaptcha" in response.content.decode()

    def test_valid_recaptcha_allows_challenged_login(self, client, make_user):
        make_user(username="login-user", password="pw123456!!")

        for _ in range(5):
            self._login(client, "wrong-password")

        with patch("apps.users.views._verify_recaptcha", return_value=True):
            response = self._login(client, "pw123456!!", token="valid-token")

        assert response.status_code == 302
        assert response.url == reverse("home")


@pytest.mark.django_db
class TestLoginAxesBehavior:
    @pytest.fixture(autouse=True)
    def _axes_settings(self, settings):
        settings.AXES_ENABLED = True
        settings.AXES_FAILURE_LIMIT = 2
        settings.AXES_COOLOFF_TIME = timedelta(seconds=1)
        settings.AXES_RESET_ON_SUCCESS = True
        settings.AUTHENTICATION_BACKENDS = [
            "axes.backends.AxesStandaloneBackend",
            "django.contrib.auth.backends.ModelBackend",
        ]
        call_command("axes_reset")

    def _login(self, client, password):
        return client.post(
            reverse("users:login"),
            data={"username": "login-user", "password": password},
        )

    def test_lockout_after_failure_limit(self, client, make_user):
        make_user(username="login-user", password="pw123456!!")

        first = self._login(client, "wrong-password")
        lockout_trigger = self._login(client, "wrong-password")
        locked = self._login(client, "wrong-password")

        assert first.status_code == 200
        assert lockout_trigger.status_code == 429
        assert locked.status_code == 429

    def test_cooloff_allows_login_again(self, client, make_user):
        make_user(username="login-user", password="pw123456!!")

        self._login(client, "wrong-password")
        self._login(client, "wrong-password")
        locked = self._login(client, "wrong-password")
        assert locked.status_code == 429

        time.sleep(1.1)

        recovered = self._login(client, "pw123456!!")
        assert recovered.status_code == 302
        assert recovered.url == reverse("home")

    def test_successful_login_resets_failure_count(self, client, make_user):
        make_user(username="login-user", password="pw123456!!")

        first_failure = self._login(client, "wrong-password")
        success = self._login(client, "pw123456!!")
        second_failure_after_success = self._login(client, "wrong-password")

        assert first_failure.status_code == 200
        assert success.status_code == 302
        assert second_failure_after_success.status_code == 200
