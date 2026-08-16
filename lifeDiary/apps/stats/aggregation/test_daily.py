"""일간 집계 — hourly_stats를 태그명이 아니라 카테고리 key로 (P0 v2 §2)."""

from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.calculator import StatsCalculator
from apps.stats.aggregation.daily import get_daily_stats_data
from apps.tags.models import Category, Tag

TODAY = date(2026, 8, 5)


@pytest.fixture
def user(make_user):
    return make_user(username="dailyuser")


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
def test_hourly_stats_key_by_category_not_tag_name(user, work_tag):
    record(user, work_tag, TODAY, slots=3, first_slot=0)  # 00:00-00:30

    calculator = StatsCalculator(user, TODAY)
    stats = get_daily_stats_data(user, TODAY, calculator)

    assert stats["hourly_stats"][0] == {"work": 30}


@pytest.mark.django_db
def test_two_tags_in_same_category_sum_into_one_hourly_entry(user):
    focus = Tag.objects.create(
        user=user, name="집중", category=Category.objects.get(slug="investment")
    )
    study = Tag.objects.create(
        user=user, name="공부", category=Category.objects.get(slug="investment")
    )
    record(user, focus, TODAY, slots=2, first_slot=0)
    record(user, study, TODAY, slots=1, first_slot=2)

    calculator = StatsCalculator(user, TODAY)
    stats = get_daily_stats_data(user, TODAY, calculator)

    assert stats["hourly_stats"][0] == {"work": 30}


@pytest.mark.django_db
def test_unrecorded_time_is_absent_from_hourly_stats_not_a_key(user, work_tag):
    record(user, work_tag, TODAY, slots=2, first_slot=0)  # 00:00-00:20만 기록

    calculator = StatsCalculator(user, TODAY)
    stats = get_daily_stats_data(user, TODAY, calculator)

    assert stats["hourly_stats"][0] == {"work": 20}
    assert "미분류" not in stats["hourly_stats"][0]


@pytest.mark.django_db
def test_tag_level_table_still_reports_unclassified_time(user, work_tag):
    record(user, work_tag, TODAY, slots=1, first_slot=0)

    calculator = StatsCalculator(user, TODAY)
    stats = get_daily_stats_data(user, TODAY, calculator)

    unclassified = next(t for t in stats["tag_stats"] if t["name"] == "미분류")
    assert unclassified["minutes"] > 0
