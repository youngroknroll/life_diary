"""Phase 5 (stats) i18n + life_feedback 코드+파라미터 검증 테스트."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.messages import LocalizableMessage


class LifeFeedbackReturnTypeTests(TestCase):
    """life_feedback.generate_feedback는 LocalizableMessage 리스트를 반환해야 한다."""

    def _ctx(self, **overrides):
        base = {
            "user_goals_daily": [],
            "user_goals_weekly": [],
            "user_goals_monthly": [],
            "monthly_stats": {"tag_stats": [], "total_hours": 0},
        }
        base.update(overrides)
        return base

    def test_goal_achieved_returns_localizable_message(self):
        from apps.stats.life_feedback import generate_feedback

        class FakeTag:
            name = "운동"

        class FakeGoal:
            tag = FakeTag()
            target_hours = 5
            actual = 5.0
            percent = 100

        result = generate_feedback(self._ctx(user_goals_daily=[FakeGoal()]))
        assert len(result) == 1
        assert isinstance(result[0], LocalizableMessage)
        assert result[0].code == "stats.feedback.goal_achieved"
        assert result[0].params["name"] == "운동"
        assert result[0].params["period"] == "daily"
        assert result[0].severity == "positive"

    def test_goal_in_progress_returns_localizable_message(self):
        from apps.stats.life_feedback import generate_feedback

        class FakeTag:
            name = "독서"

        class FakeGoal:
            tag = FakeTag()
            target_hours = 5
            actual = 2.0
            percent = 40

        result = generate_feedback(self._ctx(user_goals_weekly=[FakeGoal()]))
        assert any(
            m.code == "stats.feedback.goal_in_progress"
            and m.params["name"] == "독서"
            and m.params["period"] == "weekly"
            for m in result
        )

    def test_tag_imbalance_returns_localizable_message(self):
        from apps.stats.life_feedback import generate_feedback

        ctx = self._ctx(monthly_stats={
            "total_hours": 100,
            "tag_stats": [{"name": "업무", "total_hours": 65, "daily_hours": []}],
        })
        result = generate_feedback(ctx)
        assert any(
            m.code == "stats.feedback.tag_imbalance"
            and m.params["name"] == "업무"
            and m.params["percent"] == 65
            and m.severity == "warning"
            for m in result
        )


class StatsTemplatesEnglishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="stats-en-user", password="testpass-Long-9!"
        )

    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.client.force_login(self.user)

    def test_stats_index_renders_english(self):
        response = self.client.get(reverse("stats:index"))
        # 통계 분석 헤더
        self.assertContains(response, "stats analysis")
        # 탭
        self.assertContains(response, "Daily stats")
        self.assertContains(response, "Weekly stats")
        self.assertContains(response, "Monthly stats")
        self.assertContains(response, "Tag analysis")
        self.assertNotContains(response, "일별 통계")
        self.assertNotContains(response, "주간 통계")

    def test_stats_index_summary_labels_english(self):
        response = self.client.get(reverse("stats:index"))
        self.assertContains(response, "logged hours")  # "April 2026 logged hours"
        self.assertContains(response, "active days")  # "April 2026 active days"
        self.assertContains(response, "Today's logged rate")
        self.assertContains(response, "Today's active hours")

    def test_life_feedback_section_english(self):
        response = self.client.get(reverse("stats:index"))
        # 목표 달성률 섹션
        self.assertContains(response, "Goal progress")
        self.assertContains(response, "Daily goals")  # 카드 헤더
