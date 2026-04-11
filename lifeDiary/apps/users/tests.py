from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.users.domain_services import GoalProgressService


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
