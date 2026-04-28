"""Phase 5 (stats) i18n + life_feedback 코드+파라미터 검증 테스트 — pytest 스타일."""

import pytest
from django.urls import reverse

from apps.core.messages import LocalizableMessage
from apps.stats.life_feedback import generate_feedback


def _ctx(**overrides):
    base = {
        "user_goals_daily": [],
        "user_goals_weekly": [],
        "user_goals_monthly": [],
        "monthly_stats": {"tag_stats": [], "total_hours": 0},
    }
    base.update(overrides)
    return base


class _FakeTag:
    def __init__(self, name):
        self.name = name


class _FakeGoal:
    def __init__(self, name, target, actual, percent):
        self.tag = _FakeTag(name)
        self.target_hours = target
        self.actual = actual
        self.percent = percent


class TestLifeFeedbackReturnType:
    def test_goal_achieved_returns_localizable_message(self):
        result = generate_feedback(_ctx(user_goals_daily=[_FakeGoal("운동", 5, 5.0, 100)]))
        assert len(result) == 1
        assert isinstance(result[0], LocalizableMessage)
        assert result[0].code == "stats.feedback.goal_achieved"
        assert result[0].params["name"] == "운동"
        assert result[0].params["period"] == "daily"
        assert result[0].severity == "positive"

    def test_goal_in_progress_returns_localizable_message(self):
        result = generate_feedback(_ctx(user_goals_weekly=[_FakeGoal("독서", 5, 2.0, 40)]))
        assert any(
            m.code == "stats.feedback.goal_in_progress"
            and m.params["name"] == "독서"
            and m.params["period"] == "weekly"
            for m in result
        )

    def test_tag_imbalance_returns_localizable_message(self):
        ctx = _ctx(monthly_stats={
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


@pytest.mark.django_db
class TestStatsTemplatesEnglish:
    def test_stats_index_renders_english(self, auth_en_client):
        response = auth_en_client.get(reverse("stats:index"))
        body = response.content.decode()
        assert "stats analysis" in body
        assert "Daily stats" in body
        assert "Weekly stats" in body
        assert "Monthly stats" in body
        assert "Tag analysis" in body
        assert "일별 통계" not in body
        assert "주간 통계" not in body

    def test_stats_index_summary_labels_english(self, auth_en_client):
        response = auth_en_client.get(reverse("stats:index"))
        body = response.content.decode()
        assert "logged hours" in body
        assert "active days" in body
        assert "Today's logged rate" in body
        assert "Today's active hours" in body

    def test_life_feedback_section_english(self, auth_en_client):
        response = auth_en_client.get(reverse("stats:index"))
        body = response.content.decode()
        assert "Goal progress" in body
        assert "Daily goals" in body
