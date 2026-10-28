"""실제 태그와 합성 미분류 항목의 통계 identity 분리 (STAT-ID-01~06)."""

from datetime import date, timedelta

import pytest
from django.utils import translation

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.analysis import get_tag_analysis_data
from apps.stats.aggregation.calculator import StatsCalculator
from apps.stats.aggregation.daily import get_daily_stats_data
from apps.stats.aggregation.monthly import get_monthly_stats_data
from apps.stats.aggregation.weekly import get_weekly_stats_data
from apps.stats.logic import get_stats_context
from apps.tags.models import Category, Tag

SELECTED_DATE = date(2026, 8, 5)

LOCALE_AND_TAG_NAME = pytest.mark.parametrize(
    ("locale", "tag_name"),
    [("ko", "미분류"), ("en", "Unclassified")],
    ids=["ko", "en"],
)


@pytest.fixture
def owner(make_user):
    return make_user(username="identityuser")


def _record_one_slot_with_tag_named(owner, tag_name):
    tag = Tag.objects.create(
        user=owner, name=tag_name, category=Category.objects.get(slug="passive")
    )
    TimeBlock.objects.create(user=owner, date=SELECTED_DATE, slot_index=0, tag=tag)
    return tag


def _by_key(entries):
    return {entry.get("key"): entry for entry in entries}


@pytest.mark.django_db
@LOCALE_AND_TAG_NAME
def test_user_tag_named_unclassified_stays_separate_in_daily_statistics(
    owner, locale, tag_name
):
    tag = _record_one_slot_with_tag_named(owner, tag_name)

    with translation.override(locale):
        stats = get_daily_stats_data(
            owner, SELECTED_DATE, StatsCalculator(owner, SELECTED_DATE)
        )

    entries = _by_key(stats["tag_stats"])
    real_entry = entries.get(f"tag:{tag.id}")
    synthetic_entry = entries.get("unclassified")
    assert real_entry is not None, stats["tag_stats"]
    assert synthetic_entry is not None, stats["tag_stats"]
    assert real_entry["minutes"] == 10
    assert real_entry["blocks"] == 1
    assert real_entry["name"] == tag_name
    assert synthetic_entry["minutes"] == 1430
    assert synthetic_entry["is_unclassified"] is True
    assert stats["active_hours"] == 0.2


@pytest.mark.django_db
@LOCALE_AND_TAG_NAME
def test_user_tag_named_unclassified_stays_separate_in_weekly_statistics(
    owner, locale, tag_name
):
    tag = _record_one_slot_with_tag_named(owner, tag_name)

    with translation.override(locale):
        stats = get_weekly_stats_data(
            owner, SELECTED_DATE, StatsCalculator(owner, SELECTED_DATE)
        )

    entries = _by_key(stats["tag_weekly_stats"])
    real_entry = entries.get(f"tag:{tag.id}")
    synthetic_entry = entries.get("unclassified")
    assert real_entry is not None, stats["tag_weekly_stats"]
    assert sum(real_entry["daily_minutes"]) == 10
    assert synthetic_entry is not None, stats["tag_weekly_stats"]
    assert synthetic_entry["is_unclassified"] is True
    assert stats["week_total_hours"] == 0.2


@pytest.mark.django_db
@LOCALE_AND_TAG_NAME
def test_user_tag_named_unclassified_stays_separate_in_monthly_statistics(
    owner, locale, tag_name
):
    tag = _record_one_slot_with_tag_named(owner, tag_name)

    with translation.override(locale):
        stats = get_monthly_stats_data(
            owner, SELECTED_DATE, StatsCalculator(owner, SELECTED_DATE)
        )

    real_entry = _by_key(stats["tag_stats"]).get(f"tag:{tag.id}")
    assert real_entry is not None, stats["tag_stats"]
    assert real_entry["total_hours"] == 0.2
    assert sum(1 for hours in real_entry["daily_hours"] if hours > 0) == 1


@pytest.mark.django_db
@LOCALE_AND_TAG_NAME
def test_user_tag_named_unclassified_stays_separate_in_tag_analysis(
    owner, locale, tag_name
):
    tag = _record_one_slot_with_tag_named(owner, tag_name)

    with translation.override(locale):
        analysis = get_tag_analysis_data(
            owner, SELECTED_DATE, StatsCalculator(owner, SELECTED_DATE)
        )

    real_entry = _by_key(analysis).get(f"tag:{tag.id}")
    assert real_entry is not None, analysis
    assert real_entry["total_hours"] == 0.2
    assert real_entry["total_blocks"] == 1


@pytest.mark.django_db
def test_synthetic_unclassified_row_does_not_borrow_the_delta_of_a_tag_with_that_name(
    owner,
):
    tag = _record_one_slot_with_tag_named(owner, "미분류")
    for back in range(1, 7):
        TimeBlock.objects.create(
            user=owner, date=SELECTED_DATE - timedelta(days=back), slot_index=0, tag=tag
        )

    with translation.override("ko"):
        context = get_stats_context(owner, SELECTED_DATE)

    entries = _by_key(context["daily_stats"]["tag_stats"])
    assert entries[f"tag:{tag.id}"]["delta_vs_week"] == 0.0
    assert entries["unclassified"]["delta_vs_week"] is None
