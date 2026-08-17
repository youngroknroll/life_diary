"""목표 달성 일수, 목표 진행 바 행."""

from datetime import date, time, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.goal_progress import build_goal_progress_rows, goal_hit_days
from apps.tags.models import Category, Tag
from apps.users.models import UserGoal


MONDAY = date(2026, 7, 27)
SUNDAY = date(2026, 8, 2)


@pytest.fixture
def user(make_user):
    return make_user(username="goaluser")


@pytest.fixture
def focus(user):
    return Tag.objects.create(
        user=user,
        name="집중",
        color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )


@pytest.fixture
def goal(user, focus):
    return UserGoal.objects.create(
        user=user, tag=focus, period="daily", target_hours=1.0
    )


def record_hours(user, tag, on_date, hours):
    for slot_index in range(int(hours * 6)):
        TimeBlock.objects.create(
            user=user, date=on_date, slot_index=slot_index, tag=tag
        )


@pytest.mark.django_db
class TestGoalHitDays:
    def test_counts_only_days_that_reached_the_target(self, user, focus, goal):
        record_hours(user, focus, MONDAY, 1.0)
        record_hours(user, focus, MONDAY + timedelta(days=1), 0.5)
        record_hours(user, focus, MONDAY + timedelta(days=2), 2.0)

        assert goal_hit_days(user, MONDAY, SUNDAY, goal) == 2

    def test_exactly_the_target_counts_as_reached(self, user, focus, goal):
        record_hours(user, focus, MONDAY, 1.0)

        assert goal_hit_days(user, MONDAY, SUNDAY, goal) == 1

    def test_a_day_without_records_does_not_count(self, user, focus, goal):
        assert goal_hit_days(user, MONDAY, SUNDAY, goal) == 0

    def test_days_outside_the_range_are_ignored(self, user, focus, goal):
        record_hours(user, focus, MONDAY - timedelta(days=1), 3.0)

        assert goal_hit_days(user, MONDAY, SUNDAY, goal) == 0

    def test_other_tags_do_not_count_toward_the_goal(self, user, focus, goal):
        other = Tag.objects.create(
            user=user,
            name="여가",
            color="#C1715A",
            category=Category.objects.get(slug="passive"),
        )
        record_hours(user, other, MONDAY, 5.0)

        assert goal_hit_days(user, MONDAY, SUNDAY, goal) == 0

    def test_another_users_records_do_not_count(self, user, focus, goal, make_user):
        stranger = make_user(username="stranger")
        record_hours(stranger, focus, MONDAY, 5.0)

        assert goal_hit_days(user, MONDAY, SUNDAY, goal) == 0

    def test_a_weekly_goal_is_measured_against_its_daily_share(
        self, user, focus
    ):
        """주 7시간 목표는 하루 1시간으로 환산해 달성일을 센다."""
        weekly = UserGoal.objects.create(
            user=user, tag=focus, period="weekly", target_hours=7.0
        )
        record_hours(user, focus, MONDAY, 1.0)
        record_hours(user, focus, MONDAY + timedelta(days=1), 0.5)

        assert goal_hit_days(user, MONDAY, SUNDAY, weekly) == 1

    def test_a_zero_target_is_reached_only_with_a_record(self, user, focus):
        zero = UserGoal.objects.create(
            user=user, tag=focus, period="daily", target_hours=0.0
        )
        record_hours(user, focus, MONDAY, 0.5)

        assert goal_hit_days(user, MONDAY, SUNDAY, zero) == 1


@pytest.mark.django_db
class TestGoalProgressRows:
    def test_daily_goal_percentage_reflects_selected_dates_recorded_hours(
        self, user, focus
    ):
        UserGoal.objects.create(user=user, tag=focus, period="daily", target_hours=4.0)
        record_hours(user, focus, MONDAY, 3.0)

        rows = build_goal_progress_rows(
            user, MONDAY, today=MONDAY, now=time(hour=12, minute=0)
        )

        assert len(rows) == 1
        assert rows[0]["period"] == "daily"
        assert rows[0]["current_hours"] == 3.0
        assert rows[0]["target_hours"] == 4.0
        assert rows[0]["percentage"] == 75
        assert rows[0]["pace_percentage"] == 50

    def test_weekly_goal_sums_the_whole_week_and_reports_pace(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="weekly", target_hours=10.0)
        wednesday = MONDAY + timedelta(days=2)
        record_hours(user, focus, MONDAY, 3.0)
        record_hours(user, focus, wednesday, 2.0)

        rows = build_goal_progress_rows(user, wednesday, today=wednesday)

        assert rows[0]["period"] == "weekly"
        assert rows[0]["current_hours"] == 5.0
        assert rows[0]["percentage"] == 50
        assert rows[0]["pace_percentage"] == round(3 / 7 * 100)

    def test_monthly_goal_sums_the_whole_month_and_reports_pace(self, user, focus):
        first_of_month = date(2026, 8, 1)
        UserGoal.objects.create(user=user, tag=focus, period="monthly", target_hours=20.0)
        record_hours(user, focus, first_of_month, 5.0)

        fifth = date(2026, 8, 5)
        rows = build_goal_progress_rows(user, fifth, today=fifth)

        assert rows[0]["period"] == "monthly"
        assert rows[0]["current_hours"] == 5.0
        assert rows[0]["percentage"] == 25
        assert rows[0]["pace_percentage"] == round(5 / 31 * 100)

    def test_a_past_daily_goal_reports_a_fully_elapsed_pace(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="daily", target_hours=4.0)
        record_hours(user, focus, MONDAY, 1.0)

        rows = build_goal_progress_rows(user, MONDAY, today=MONDAY + timedelta(days=1))

        assert rows[0]["pace_percentage"] == 100

    def test_todays_daily_goal_paces_by_the_elapsed_part_of_the_day(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="daily", target_hours=4.0)

        rows = build_goal_progress_rows(
            user, MONDAY, today=MONDAY, now=time(hour=6, minute=0)
        )

        assert rows[0]["pace_percentage"] == 25

    def test_a_goal_trailing_its_pace_is_marked_behind(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="weekly", target_hours=10.0)
        wednesday = MONDAY + timedelta(days=2)
        record_hours(user, focus, MONDAY, 1.0)

        rows = build_goal_progress_rows(user, wednesday, today=wednesday)

        assert rows[0]["percentage"] == 10
        assert rows[0]["pace_percentage"] == 43
        assert rows[0]["is_behind_pace"] is True

    def test_a_goal_matching_its_pace_is_not_marked_behind(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="weekly", target_hours=10.0)
        wednesday = MONDAY + timedelta(days=2)
        record_hours(user, focus, MONDAY, 5.0)

        rows = build_goal_progress_rows(user, wednesday, today=wednesday)

        assert rows[0]["percentage"] == 50
        assert rows[0]["pace_percentage"] == 43
        assert rows[0]["is_behind_pace"] is False

    def test_no_goals_returns_an_empty_list(self, user):
        assert build_goal_progress_rows(user, MONDAY, today=MONDAY) == []

    def test_in_progress_period_under_target_is_not_marked_danger(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="daily", target_hours=4.0)
        record_hours(user, focus, MONDAY, 1.0)

        rows = build_goal_progress_rows(user, MONDAY, today=MONDAY)

        assert rows[0]["is_under_target"] is False

    def test_confirmed_past_period_under_target_is_marked_danger(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="daily", target_hours=4.0)
        record_hours(user, focus, MONDAY, 1.0)

        rows = build_goal_progress_rows(user, MONDAY, today=MONDAY + timedelta(days=1))

        assert rows[0]["is_under_target"] is True

    def test_percentage_caps_at_100_when_exceeding_target(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="daily", target_hours=1.0)
        record_hours(user, focus, MONDAY, 3.0)

        rows = build_goal_progress_rows(user, MONDAY, today=MONDAY)

        assert rows[0]["percentage"] == 100
        assert rows[0]["is_under_target"] is False

    def test_rows_are_ordered_daily_then_weekly_then_monthly(self, user, focus):
        UserGoal.objects.create(user=user, tag=focus, period="monthly", target_hours=20.0)
        UserGoal.objects.create(user=user, tag=focus, period="daily", target_hours=4.0)
        UserGoal.objects.create(user=user, tag=focus, period="weekly", target_hours=10.0)

        rows = build_goal_progress_rows(user, MONDAY, today=MONDAY)

        assert [r["period"] for r in rows] == ["daily", "weekly", "monthly"]
