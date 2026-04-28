from types import SimpleNamespace

import pytest
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
