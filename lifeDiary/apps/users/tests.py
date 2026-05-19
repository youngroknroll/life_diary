import time
from datetime import timedelta
from types import SimpleNamespace

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
