"""월간 집계 — category_stats 롤업 (P0 v2 §2)."""

from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.calculator import StatsCalculator
from apps.stats.aggregation.monthly import get_monthly_stats_data
from apps.tags.models import Category, Tag

AUG_5 = date(2026, 8, 5)
DAYS_IN_AUGUST = 31


@pytest.fixture
def user(make_user):
    return make_user(username="monthlyuser")


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
def test_category_daily_hours_sum_matches_its_tags_time(user, work_tag):
    record(user, work_tag, AUG_5, slots=6)

    calculator = StatsCalculator(user, AUG_5)
    stats = get_monthly_stats_data(user, AUG_5, calculator)

    work_category = next(c for c in stats["category_stats"] if c["key"] == "work")
    assert work_category["daily_hours"][4] == 1.0  # 8/5 = day_index 4
    assert work_category["total_hours"] == 1.0
    assert len(work_category["daily_hours"]) == DAYS_IN_AUGUST


@pytest.mark.django_db
def test_category_stats_always_lists_all_five_categories(user, work_tag):
    record(user, work_tag, AUG_5, slots=1)

    calculator = StatsCalculator(user, AUG_5)
    stats = get_monthly_stats_data(user, AUG_5, calculator)

    keys = {c["key"] for c in stats["category_stats"]}
    assert keys == {"work", "move", "care", "life", "sleep"}


@pytest.mark.django_db
def test_unrecorded_category_reports_zero_hours(user, work_tag):
    record(user, work_tag, AUG_5, slots=1)

    calculator = StatsCalculator(user, AUG_5)
    stats = get_monthly_stats_data(user, AUG_5, calculator)

    sleep_category = next(c for c in stats["category_stats"] if c["key"] == "sleep")
    assert sleep_category["daily_hours"] == [0] * DAYS_IN_AUGUST
    assert sleep_category["total_hours"] == 0


@pytest.mark.django_db
def test_two_categories_stay_independent(user, work_tag, move_tag):
    record(user, work_tag, AUG_5, slots=3, first_slot=0)
    record(user, move_tag, AUG_5, slots=2, first_slot=3)

    calculator = StatsCalculator(user, AUG_5)
    stats = get_monthly_stats_data(user, AUG_5, calculator)

    work_category = next(c for c in stats["category_stats"] if c["key"] == "work")
    move_category = next(c for c in stats["category_stats"] if c["key"] == "move")
    assert work_category["daily_hours"][4] == 0.5
    assert move_category["daily_hours"][4] == 0.3  # 20분 → round(20/60, 1)
