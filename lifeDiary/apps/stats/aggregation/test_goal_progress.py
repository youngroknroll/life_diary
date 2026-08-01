"""목표 달성 일수.

시안 4a "목표 집중 4h/일 · 4/7일"과 6d "목표 달성 1/2일"의 근거다.
하루 단위로 목표 시간을 채운 날이 며칠인지만 센다.
"""

from datetime import date, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.goal_progress import goal_hit_days
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
        is_default=False,
        category=Category.objects.get(slug="investment"),
    )


@pytest.fixture
def goal(user, focus):
    return UserGoal.objects.create(
        user=user, tag=focus, period="daily", target_hours=1.0
    )


def record_hours(user, tag, on_date, hours):
    """한 시간은 6칸이다."""
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
            is_default=False,
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
