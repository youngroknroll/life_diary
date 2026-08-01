"""직전 동일 기간 비교.

시안 분석 화면의 증감·스파크라인·기준선이 전부 여기서 나온다. 이 값이 없으면
"+6.2h" "4주 평균 대비 −1.4h" 같은 표기가 성립하지 않는다.

주 기간은 달력 주(월~일)를 쓴다. 시안은 롤링 7일 기준이지만 사용자가 달력
주로 결정했다. 그래서 진행 중인 주를 완료된 주와 같은 자리에 두면 항상 낮게
읽히는 문제가 생기고, is_partial 과 경과일 기준 분모가 그 답이다.
"""

from datetime import date, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.comparison import get_period_delta
from apps.tags.models import Category, Tag


# 2026-08-01 은 토요일. 그 주는 07-27(월)~08-02(일).
SATURDAY = date(2026, 8, 1)
SUNDAY = date(2026, 8, 2)


@pytest.fixture
def user(make_user):
    return make_user(username="comparisonuser")


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
def leisure(user):
    return Tag.objects.create(
        user=user,
        name="여가",
        color="#C1715A",
        is_default=False,
        category=Category.objects.get(slug="passive"),
    )


def record(user, tag, on_date, slots=1, first_slot=0):
    for offset in range(slots):
        TimeBlock.objects.create(
            user=user, date=on_date, slot_index=first_slot + offset, tag=tag
        )


@pytest.mark.django_db
class TestPeriodBoundaries:
    def test_day_period_covers_only_that_day(self, user, focus):
        record(user, focus, SATURDAY, slots=3)
        record(user, focus, SATURDAY - timedelta(days=1), slots=6)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["current"]["total_minutes"] == 30

    def test_previous_day_is_the_day_before(self, user, focus):
        record(user, focus, SATURDAY - timedelta(days=1), slots=6)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["previous"]["total_minutes"] == 60

    def test_week_runs_monday_to_sunday(self, user, focus):
        result = get_period_delta(user, "week", SATURDAY, today=SUNDAY)

        assert result["current"]["start"] == date(2026, 7, 27)
        assert result["current"]["end"] == date(2026, 8, 2)

    def test_previous_week_is_the_calendar_week_before(self, user, focus):
        result = get_period_delta(user, "week", SATURDAY, today=SUNDAY)

        assert result["previous"]["start"] == date(2026, 7, 20)
        assert result["previous"]["end"] == date(2026, 7, 26)

    def test_month_runs_from_the_first_to_the_last_day(self, user, focus):
        result = get_period_delta(user, "month", SATURDAY, today=date(2026, 8, 31))

        assert result["current"]["start"] == date(2026, 8, 1)
        assert result["current"]["end"] == date(2026, 8, 31)

    def test_previous_month_is_the_month_before(self, user, focus):
        result = get_period_delta(user, "month", SATURDAY, today=date(2026, 8, 31))

        assert result["previous"]["start"] == date(2026, 7, 1)
        assert result["previous"]["end"] == date(2026, 7, 31)

    def test_unknown_kind_is_rejected(self, user):
        with pytest.raises(ValueError):
            get_period_delta(user, "분기", SATURDAY, today=SATURDAY)


@pytest.mark.django_db
class TestTotalsAndDelta:
    def test_delta_is_current_minus_previous(self, user, focus):
        record(user, focus, SATURDAY, slots=6)
        record(user, focus, SATURDAY - timedelta(days=1), slots=3)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["delta_minutes"] == 30

    def test_delta_is_negative_when_the_period_fell_behind(self, user, focus):
        record(user, focus, SATURDAY, slots=3)
        record(user, focus, SATURDAY - timedelta(days=1), slots=6)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["delta_minutes"] == -30

    def test_tag_minutes_are_broken_out(self, user, focus, leisure):
        record(user, focus, SATURDAY, slots=3, first_slot=0)
        record(user, leisure, SATURDAY, slots=6, first_slot=10)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["current"]["tag_minutes"] == {"집중": 30, "여가": 60}

    def test_tag_minutes_sum_to_the_period_total(self, user, focus, leisure):
        record(user, focus, SATURDAY, slots=3, first_slot=0)
        record(user, leisure, SATURDAY, slots=6, first_slot=10)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert sum(result["current"]["tag_minutes"].values()) == (
            result["current"]["total_minutes"]
        )

    def test_another_users_records_do_not_leak(self, user, make_user):
        stranger = make_user(username="stranger")
        stranger_tag = Tag.objects.create(
            user=stranger,
            name="남의태그",
            color="#4E8F63",
            is_default=False,
            category=Category.objects.get(slug="investment"),
        )
        record(stranger, stranger_tag, SATURDAY, slots=6)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["current"]["total_minutes"] == 0


@pytest.mark.django_db
class TestPartialPeriod:
    def test_a_week_still_running_is_marked_partial(self, user):
        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["current"]["is_partial"] is True
        assert result["current"]["elapsed_days"] == 6

    def test_a_finished_week_is_not_partial(self, user):
        result = get_period_delta(user, "week", SATURDAY, today=date(2026, 8, 5))

        assert result["current"]["is_partial"] is False
        assert result["current"]["elapsed_days"] == 7

    def test_the_previous_period_is_never_partial(self, user):
        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["previous"]["is_partial"] is False

    def test_fill_percentage_divides_by_elapsed_days_not_the_whole_week(
        self, user, focus
    ):
        """진행 중인 주를 7일로 나누면 0%가 실패처럼 읽힌다."""
        # 토요일까지 6일 경과. 하루를 통째로 채운다.
        for offset in range(6):
            record(
                user,
                focus,
                date(2026, 7, 27) + timedelta(days=offset),
                slots=144,
            )

        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["current"]["fill_percentage"] == pytest.approx(100.0)

    def test_a_finished_week_divides_by_all_seven_days(self, user, focus):
        for offset in range(7):
            record(
                user,
                focus,
                date(2026, 7, 27) + timedelta(days=offset),
                slots=72,
            )

        result = get_period_delta(user, "week", SATURDAY, today=date(2026, 8, 5))

        assert result["current"]["fill_percentage"] == pytest.approx(50.0)


@pytest.mark.django_db
class TestSparkline:
    def test_sparkline_has_seven_daily_values(self, user):
        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert len(result["sparkline"]) == 7

    def test_sparkline_ends_on_the_selected_date(self, user, focus):
        record(user, focus, SATURDAY, slots=6)

        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["sparkline"][-1] == 60

    def test_sparkline_starts_six_days_earlier(self, user, focus):
        record(user, focus, SATURDAY - timedelta(days=6), slots=3)

        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["sparkline"][0] == 30


@pytest.mark.django_db
class TestBaseline:
    def test_four_week_average_uses_the_four_finished_weeks_before(self, user, focus):
        # 직전 4주에 각각 하루씩 60분. 평균은 60분.
        for weeks_back in range(1, 5):
            record(user, focus, date(2026, 7, 27) - timedelta(weeks=weeks_back), slots=6)

        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["baseline"]["avg_4w"] == pytest.approx(60.0)

    def test_four_week_average_excludes_the_current_week(self, user, focus):
        record(user, focus, SATURDAY, slots=144)

        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["baseline"]["avg_4w"] == 0

    def test_twelve_week_max_is_the_best_single_week(self, user, focus):
        record(user, focus, date(2026, 7, 27) - timedelta(weeks=1), slots=6)
        record(user, focus, date(2026, 7, 27) - timedelta(weeks=5), slots=18)

        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["baseline"]["max_12w"] == 180

    def test_baseline_is_zero_without_history(self, user):
        result = get_period_delta(user, "week", SATURDAY, today=SATURDAY)

        assert result["baseline"] == {"avg_4w": 0, "max_12w": 0}


@pytest.mark.django_db
class TestNoComparablePeriod:
    def test_previous_period_without_records_reports_no_history(self, user, focus):
        record(user, focus, SATURDAY, slots=6)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["previous"]["total_minutes"] == 0
        assert result["has_previous"] is False

    def test_previous_period_with_records_is_comparable(self, user, focus):
        record(user, focus, SATURDAY - timedelta(days=1), slots=6)

        result = get_period_delta(user, "day", SATURDAY, today=SATURDAY)

        assert result["has_previous"] is True
