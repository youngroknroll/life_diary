"""요약 탭 컨텍스트."""

from datetime import date, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.summary import build_summary
from apps.tags.models import Category, Tag
from apps.users.models import UserGoal


SATURDAY = date(2026, 8, 1)


@pytest.fixture
def user(make_user):
    return make_user(username="summaryuser")


@pytest.fixture
def focus(user):
    return Tag.objects.create(
        user=user,
        name="집중",
        is_default=False,
        category=Category.objects.get(slug="investment"),
    )


def record(user, tag, on_date, slots=1, first_slot=0):
    for offset in range(slots):
        TimeBlock.objects.create(
            user=user, date=on_date, slot_index=first_slot + offset, tag=tag
        )


@pytest.mark.django_db
class TestTiles:
    def test_today_tile_reports_the_selected_day(self, user, focus):
        record(user, focus, SATURDAY, slots=6)

        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["today"]["total_minutes"] == 60

    def test_rolling_week_tile_covers_the_last_seven_days(self, user, focus):
        record(user, focus, SATURDAY, slots=6)
        record(user, focus, SATURDAY - timedelta(days=6), slots=6)

        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["rolling_week"]["total_minutes"] == 120

    def test_rolling_week_tile_excludes_the_eighth_day_back(self, user, focus):
        record(user, focus, SATURDAY - timedelta(days=7), slots=6)

        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["rolling_week"]["total_minutes"] == 0

    def test_month_tile_covers_the_calendar_month(self, user, focus):
        record(user, focus, date(2026, 8, 1), slots=6)
        record(user, focus, date(2026, 7, 31), slots=6)

        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["month"]["total_minutes"] == 60

    def test_goal_tile_is_absent_without_goals(self, user, focus):
        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["goal"] is None

    def test_goal_tile_counts_hit_days_against_elapsed_days(self, user, focus):
        UserGoal.objects.create(
            user=user, tag=focus, period="daily", target_hours=1.0
        )
        record(user, focus, SATURDAY, slots=6)
        record(user, focus, SATURDAY - timedelta(days=1), slots=3)

        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["goal"]["hit_days"] == 1
        assert summary["goal"]["total_days"] == 7


@pytest.mark.django_db
class TestHeatmap:
    def test_heatmap_carries_a_seven_by_twenty_four_grid(self, user):
        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert len(summary["density"]["grid"]) == 7
        assert all(len(row) == 24 for row in summary["density"]["grid"])

    def test_heatmap_reports_the_gap_pattern(self, user, focus):
        for offset in range(7):
            day = SATURDAY - timedelta(days=offset)
            for hour in range(24):
                if hour in (15, 16):
                    continue
                record(user, focus, day, slots=6, first_slot=hour * 6)

        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["density"]["pattern"]["worst_range"] == (15, 17)
        assert summary["density"]["pattern"]["missing_days"] == 7


@pytest.mark.django_db
class TestObservations:
    def test_no_records_yields_no_observations(self, user):
        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert summary["observations"] == []

    def test_a_gap_becomes_an_observation(self, user, focus):
        for offset in range(7):
            day = SATURDAY - timedelta(days=offset)
            for hour in range(24):
                if hour in (15, 16):
                    continue
                record(user, focus, day, slots=6, first_slot=hour * 6)

        summary = build_summary(user, SATURDAY, today=SATURDAY)
        kinds = [item["kind"] for item in summary["observations"]]

        assert "gap" in kinds

    def test_the_biggest_tag_becomes_an_observation(self, user, focus):
        record(user, focus, SATURDAY, slots=12)

        summary = build_summary(user, SATURDAY, today=SATURDAY)
        kinds = [item["kind"] for item in summary["observations"]]

        assert "top_tag" in kinds

    def test_observations_carry_a_tag_color_not_a_verdict(self, user, focus):
        record(user, focus, SATURDAY, slots=12)

        summary = build_summary(user, SATURDAY, today=SATURDAY)
        top = next(o for o in summary["observations"] if o["kind"] == "top_tag")

        assert top["color"] == Category.objects.get(slug="investment").color

    def test_observations_stay_within_four_items(self, user, focus):
        for offset in range(7):
            day = SATURDAY - timedelta(days=offset)
            for hour in range(24):
                if hour in (15, 16):
                    continue
                record(user, focus, day, slots=6, first_slot=hour * 6)
        UserGoal.objects.create(
            user=user, tag=focus, period="daily", target_hours=1.0
        )

        summary = build_summary(user, SATURDAY, today=SATURDAY)

        assert len(summary["observations"]) <= 4
