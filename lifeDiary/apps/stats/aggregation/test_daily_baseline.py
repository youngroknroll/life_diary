"""하루 구성 표의 '7일 평균 대비' 열 (시안 3b)."""

from datetime import date, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.daily_baseline import get_tag_deltas_vs_week
from apps.tags.models import Category, Tag

TODAY = date(2026, 7, 29)
SLOTS_PER_HOUR = 6


@pytest.fixture
def user(make_user):
    return make_user(username="baselineuser")


@pytest.fixture
def focus(user):
    return Tag.objects.create(
        user=user,
        name="집중",
        color="#4E8F63",
        is_default=False,
        category=Category.objects.get(slug="investment"),
    )


def log_hours(user, tag, day, hours, start_slot=0):
    for offset in range(int(hours * SLOTS_PER_HOUR)):
        TimeBlock.objects.create(
            user=user, tag=tag, date=day, slot_index=start_slot + offset
        )


@pytest.mark.django_db
class TestDeltaAgainstTheWeek:
    def test_a_steady_week_shows_no_movement(self, user, focus):
        for back in range(7):
            log_hours(user, focus, TODAY - timedelta(days=back), 2)

        deltas = get_tag_deltas_vs_week(user, TODAY)

        assert deltas["집중"] == 0.0

    def test_a_heavier_day_reads_positive(self, user, focus):
        for back in range(1, 7):
            log_hours(user, focus, TODAY - timedelta(days=back), 1)
        log_hours(user, focus, TODAY, 8)

        deltas = get_tag_deltas_vs_week(user, TODAY)

        assert deltas["집중"] > 0

    def test_a_lighter_day_reads_negative(self, user, focus):
        for back in range(1, 7):
            log_hours(user, focus, TODAY - timedelta(days=back), 5)
        log_hours(user, focus, TODAY, 1)

        deltas = get_tag_deltas_vs_week(user, TODAY)

        assert deltas["집중"] < 0

    def test_a_tag_used_only_today_is_all_upside(self, user, focus):
        log_hours(user, focus, TODAY, 7)

        deltas = get_tag_deltas_vs_week(user, TODAY)

        assert deltas["집중"] == 6.0

    def test_days_outside_the_window_do_not_count(self, user, focus):
        log_hours(user, focus, TODAY - timedelta(days=30), 24)
        log_hours(user, focus, TODAY, 1)

        deltas = get_tag_deltas_vs_week(user, TODAY)

        assert deltas["집중"] == pytest.approx(1 - 1 / 7, abs=0.05)

    def test_an_untouched_week_yields_nothing(self, user, focus):
        deltas = get_tag_deltas_vs_week(user, TODAY)

        assert deltas == {}
