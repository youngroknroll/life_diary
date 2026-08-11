"""달성률 분모는 지난 시간만 센다.

끝나지 않은 오늘을 실패한 날로 세면 아침 9시의 0% 가 실패로 읽힌다. 시안은
아직 오지 않은 시간을 분모에서 빼라고 한다.
"""

from datetime import date, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.summary import ROLLING_DAYS, build_summary
from apps.tags.models import Category, Tag
from apps.users.models import UserGoal


TODAY = date(2026, 8, 5)


@pytest.fixture
def user(make_user):
    return make_user(username="denomuser")


@pytest.fixture
def focus(user):
    return Tag.objects.create(
        user=user, name="집중", category=Category.objects.get(slug="investment")
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


def goal_tile(user, selected_date, today=TODAY):
    return build_summary(user, selected_date, today=today)["goal"]


class TestUnfinishedDayIsNotCountedAsFailed:
    def test_today_is_left_out_while_the_goal_is_unmet(self, user, focus, goal):
        """오늘 아직 못 채웠으면 오늘은 분모에 없다."""
        tile = goal_tile(user, TODAY)

        assert tile["total_days"] == ROLLING_DAYS - 1

    def test_today_joins_the_denominator_once_the_goal_is_met(self, user, focus, goal):
        """채운 것을 감추지는 않는다."""
        record_hours(user, focus, TODAY, 1.0)

        tile = goal_tile(user, TODAY)

        assert tile["hit_days"] == 1
        assert tile["total_days"] == ROLLING_DAYS

    def test_partial_progress_today_still_leaves_today_out(self, user, focus, goal):
        record_hours(user, focus, TODAY, 0.5)

        tile = goal_tile(user, TODAY)

        assert tile["hit_days"] == 0
        assert tile["total_days"] == ROLLING_DAYS - 1


class TestPastWindowsCountEveryDay:
    def test_a_window_that_ended_yesterday_counts_all_of_it(self, user, focus, goal):
        yesterday = TODAY - timedelta(days=1)

        tile = goal_tile(user, yesterday)

        assert tile["total_days"] == ROLLING_DAYS

    def test_hits_in_a_finished_window_are_counted(self, user, focus, goal):
        yesterday = TODAY - timedelta(days=1)
        record_hours(user, focus, yesterday, 2.0)
        record_hours(user, focus, yesterday - timedelta(days=1), 1.0)

        tile = goal_tile(user, yesterday)

        assert tile["hit_days"] == 2
        assert tile["total_days"] == ROLLING_DAYS


class TestFutureDaysNeverCount:
    def test_days_after_today_are_excluded(self, user, focus, goal):
        """앞으로 사흘을 미리 보아도 오지 않은 날은 분모에 없다."""
        tile = goal_tile(user, TODAY + timedelta(days=3))

        # 창은 [TODAY-3, TODAY+3]. 지난 날은 TODAY-3..TODAY-1 세 날뿐이다.
        assert tile["total_days"] == 3

    def test_a_window_entirely_in_the_future_counts_nothing(self, user, focus, goal):
        tile = goal_tile(user, TODAY + timedelta(days=ROLLING_DAYS + 2))

        assert tile["total_days"] == 0
        assert tile["hit_days"] == 0


class TestNoGoal:
    def test_tile_is_absent_without_a_goal(self, user, focus):
        assert goal_tile(user, TODAY) is None
