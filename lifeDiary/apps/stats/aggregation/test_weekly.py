"""주간 집계 — category_stats 롤업과 기간 라벨 규칙 (P0 v2 §2)."""

from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.calculator import StatsCalculator
from apps.stats.aggregation.weekly import get_weekly_stats_data
from apps.tags.models import Category, Tag

MONDAY = date(2026, 7, 20)


@pytest.fixture
def user(make_user):
    return make_user(username="weeklyuser")


@pytest.fixture
def work_tag(user):
    return Tag.objects.create(
        user=user, name="집중", category=Category.objects.get(slug="investment")
    )


@pytest.fixture
def move_tag(user):
    return Tag.objects.create(
        user=user, name="운동", category=Category.objects.get(slug="proactive")
    )


def record(user, tag, on_date, slots=1, first_slot=0):
    for offset in range(slots):
        TimeBlock.objects.create(
            user=user, date=on_date, slot_index=first_slot + offset, tag=tag
        )


@pytest.mark.django_db
class TestCategoryStats:
    def test_category_daily_hours_sum_matches_its_tags_time(self, user, work_tag):
        record(user, work_tag, MONDAY, slots=6)

        calculator = StatsCalculator(user, MONDAY)
        stats = get_weekly_stats_data(user, MONDAY, calculator)

        work_category = next(c for c in stats["category_stats"] if c["key"] == "work")
        assert work_category["daily_hours"][0] == 1.0
        assert work_category["total_hours"] == 1.0

    def test_category_stats_always_lists_all_five_categories(self, user, work_tag):
        record(user, work_tag, MONDAY, slots=1)

        calculator = StatsCalculator(user, MONDAY)
        stats = get_weekly_stats_data(user, MONDAY, calculator)

        keys = {c["key"] for c in stats["category_stats"]}
        assert keys == {"work", "move", "care", "life", "sleep"}

    def test_unrecorded_category_reports_zero_hours(self, user, work_tag):
        record(user, work_tag, MONDAY, slots=1)

        calculator = StatsCalculator(user, MONDAY)
        stats = get_weekly_stats_data(user, MONDAY, calculator)

        sleep_category = next(c for c in stats["category_stats"] if c["key"] == "sleep")
        assert sleep_category["daily_hours"] == [0] * 7
        assert sleep_category["total_hours"] == 0

    def test_unclassified_time_is_excluded_from_category_stats(self, user, work_tag):
        record(user, work_tag, MONDAY, slots=1)  # 나머지 143칸은 자동으로 미분류

        calculator = StatsCalculator(user, MONDAY)
        stats = get_weekly_stats_data(user, MONDAY, calculator)

        total_category_hours = sum(
            hours for c in stats["category_stats"] for hours in c["daily_hours"]
        )
        assert total_category_hours == 0.2  # work 1칸(10분)만 반영, 미분류 제외


@pytest.mark.django_db
def test_two_tags_in_same_category_sum_into_one_entry(user):
    focus = Tag.objects.create(
        user=user, name="집중", category=Category.objects.get(slug="investment")
    )
    study = Tag.objects.create(
        user=user, name="공부", category=Category.objects.get(slug="investment")
    )
    record(user, focus, MONDAY, slots=2, first_slot=0)
    record(user, study, MONDAY, slots=3, first_slot=2)

    calculator = StatsCalculator(user, MONDAY)
    stats = get_weekly_stats_data(user, MONDAY, calculator)

    work_category = next(c for c in stats["category_stats"] if c["key"] == "work")
    assert work_category["daily_hours"][0] == 0.8  # 50분 → round(50/60, 1)


@pytest.mark.django_db
def test_two_categories_stay_independent(user, work_tag, move_tag):
    record(user, work_tag, MONDAY, slots=3, first_slot=0)
    record(user, move_tag, MONDAY, slots=2, first_slot=3)

    calculator = StatsCalculator(user, MONDAY)
    stats = get_weekly_stats_data(user, MONDAY, calculator)

    work_category = next(c for c in stats["category_stats"] if c["key"] == "work")
    move_category = next(c for c in stats["category_stats"] if c["key"] == "move")
    assert work_category["daily_hours"][0] == 0.5
    assert move_category["daily_hours"][0] == 0.3  # 20분 → round(20/60, 1)


@pytest.mark.django_db
def test_week_start_is_always_monday(user, work_tag):
    calculator = StatsCalculator(user, MONDAY)
    stats = get_weekly_stats_data(user, MONDAY, calculator)

    assert stats["week_start"] == MONDAY
    assert stats["week_start"].weekday() == 0
