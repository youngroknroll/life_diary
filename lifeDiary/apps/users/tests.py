from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.tags.models import Category, Tag
from apps.users.domain_services import GoalProgressService
from apps.users.models import UserGoal


class GoalProgressServiceTests(SimpleTestCase):
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

        self.assertEqual(actual, 1.5)

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

        self.assertEqual(actual, 6.5)


class UserGoalTagOwnershipTests(TestCase):
    """IDOR 회귀 방지: 타 사용자 태그 ID로 목표를 생성/수정할 수 없어야 한다."""

    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw")
        self.bob = User.objects.create_user("bob", password="pw")
        self.category = Category.objects.create(name="일반", slug="general", color="#000000")
        self.bob_tag = Tag.objects.create(
            user=self.bob,
            name="bob_only",
            color="#123456",
            is_default=False,
            category=self.category,
        )

    def test_create_rejects_other_users_tag(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("users:usergoal_create"),
            data={"tag": self.bob_tag.id, "period": "daily", "target_hours": 1.0},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            UserGoal.objects.filter(user=self.alice, tag=self.bob_tag).exists()
        )

    def test_mypage_rejects_other_users_tag(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("users:mypage"),
            data={"tag": self.bob_tag.id, "period": "monthly", "target_hours": 10.0},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            UserGoal.objects.filter(user=self.alice, tag=self.bob_tag).exists()
        )
