"""통계 집계가 요청당 기록을 한 번만 읽어도 결과가 같은지."""

from datetime import date, time, timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.dashboard.models import TimeBlock
from apps.dashboard.repositories import TimeBlockRepository
from apps.stats.aggregation.calculator import StatsCalculator
from apps.stats.aggregation.comparison import get_period_delta
from apps.stats.aggregation.analysis import get_tag_analysis_data
from apps.stats.aggregation.daily import get_daily_stats_data
from apps.stats.aggregation.daily_baseline import get_tag_deltas_vs_week
from apps.stats.aggregation.goal_progress import build_goal_progress_rows
from apps.stats.aggregation.density import get_density_grid
from apps.stats.aggregation.monthly import get_monthly_stats_data
from apps.stats.aggregation.summary import build_summary
from apps.stats.aggregation.weekly import get_weekly_stats_data
from apps.stats.logic import get_stats_context
from apps.stats.test_stats_perf import TARGET_MAX_QUERIES
from apps.tags.models import Category, Tag
from apps.users.models import UserGoal


RECORDS_START = date(2026, 1, 5)
RECORDS_END = date(2026, 8, 31)
MID_MONTH = date(2026, 4, 15)
# 4/13(4/15 의 주 시작) 12주 전부터 4월 끝까지.
MID_MONTH_WINDOW = (date(2026, 1, 19), date(2026, 4, 30))
# 어느 집계의 기간이든 덮는다. 창 범위 공식은 get_stats_context 의 쿼리 예산이 검증한다.
FULL_WINDOW = (RECORDS_START, RECORDS_END)
LATER = date(2026, 10, 1)
NOON = time(hour=12)

# (선택일, 오늘). "today" 는 선택일을 오늘로 넘겨 진행 중인 기간을 만든다.
SCENARIOS = {
    "past": (MID_MONTH, LATER),
    "week_into_last_month": (date(2026, 8, 2), LATER),
    "today": (MID_MONTH, MID_MONTH),
}

# calculator 가 None 이면 창 없이 직접 읽는다.
AGGREGATIONS = {
    "daily": lambda user, selected, today, calculator: get_daily_stats_data(
        user, selected, calculator or StatsCalculator(user, selected)
    ),
    "weekly": lambda user, selected, today, calculator: get_weekly_stats_data(
        user, selected, calculator or StatsCalculator(user, selected)
    ),
    "monthly": lambda user, selected, today, calculator: get_monthly_stats_data(
        user, selected, calculator or StatsCalculator(user, selected)
    ),
    "tag_analysis": lambda user, selected, today, calculator: get_tag_analysis_data(
        user, selected, calculator or StatsCalculator(user, selected)
    ),
    "period_delta_day": lambda user, selected, today, calculator: get_period_delta(
        user, "day", selected, today=today, calculator=calculator
    ),
    "period_delta_month": lambda user, selected, today, calculator: get_period_delta(
        user, "month", selected, today=today, with_trend=False, calculator=calculator
    ),
    "density": lambda user, selected, today, calculator: get_density_grid(
        user, selected, days=7, calculator=calculator
    ),
    "tag_deltas": lambda user, selected, today, calculator: get_tag_deltas_vs_week(
        user, selected, calculator=calculator
    ),
    "summary": lambda user, selected, today, calculator: build_summary(
        user, selected, today=today, calculator=calculator
    ),
    "goal_progress": lambda user, selected, today, calculator: build_goal_progress_rows(
        user, selected, today=today, now=NOON, calculator=calculator
    ),
}


@pytest.fixture
def owner(make_user):
    return make_user(username="window_owner")


@pytest.fixture
def recorded(owner, make_user):
    """두 사용자가 같은 날짜에 기록한다. 주인의 기록에는 비어 있는 칸(미분류)과 빈 날이 섞인다."""
    focus = Tag.objects.create(
        user=owner, name="집중", color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )
    chores = Tag.objects.create(
        user=owner, name="집안일", color="#C99A2E",
        category=Category.objects.get(slug="basic_life"),
    )
    other = make_user(username="window_other")
    others_focus = Tag.objects.create(
        user=other, name="집중", color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )

    blocks = []
    day = RECORDS_START
    while day <= RECORDS_END:
        seed = day.toordinal()
        if seed % 9:
            for n in range(seed % 7 + 3):
                tag = focus if n % 2 else chores
                blocks.append(
                    TimeBlock(user=owner, date=day, slot_index=(seed * 5 + n * 11) % 144, tag=tag)
                )
            blocks.append(
                TimeBlock(user=other, date=day, slot_index=(seed * 3) % 144, tag=others_focus)
            )
        day += timedelta(days=1)
    TimeBlock.objects.bulk_create(blocks)

    UserGoal.objects.create(user=owner, tag=focus, period="daily", target_hours=1.0)
    UserGoal.objects.create(user=owner, tag=chores, period="weekly", target_hours=5.0)
    UserGoal.objects.create(user=owner, tag=focus, period="monthly", target_hours=20.0)
    return owner


def _block_ids(blocks):
    return [(block.date, block.slot_index, block.tag_id) for block in blocks]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "start, end",
    [
        (MID_MONTH, MID_MONTH),
        (date(2026, 4, 13), date(2026, 4, 19)),
        (date(2026, 4, 1), date(2026, 4, 30)),
        (date(2026, 3, 1), date(2026, 3, 31)),
        (date(2026, 1, 19), date(2026, 4, 12)),
        (date(2026, 4, 9), MID_MONTH),
    ],
    ids=["day", "week", "month", "previous_month", "baseline_weeks", "last_seven_days"],
)
def test_window_returns_the_same_blocks_in_the_same_order_as_direct_reads(
    recorded, start, end
):
    calculator = StatsCalculator(recorded, MID_MONTH, window=MID_MONTH_WINDOW)

    blocks = calculator.blocks_between(start, end)

    direct = TimeBlockRepository().find_by_date_range(recorded, start, end)
    assert _block_ids(blocks) == _block_ids(direct)


@pytest.mark.django_db
def test_window_reads_blocks_once_for_any_number_of_ranges(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=MID_MONTH_WINDOW)

    with CaptureQueriesContext(connection) as queries:
        calculator.blocks_between(MID_MONTH, MID_MONTH)
        calculator.blocks_between(date(2026, 4, 13), date(2026, 4, 19))
        calculator.blocks_between(date(2026, 1, 19), date(2026, 4, 12))

    assert len(queries.captured_queries) == 1


@pytest.mark.django_db
def test_ranges_outside_the_window_still_return_every_block(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=MID_MONTH_WINDOW)
    before_window = (date(2026, 1, 5), date(2026, 1, 25))

    blocks = calculator.blocks_between(*before_window)

    direct = TimeBlockRepository().find_by_date_range(recorded, *before_window)
    assert _block_ids(blocks) == _block_ids(direct)


@pytest.mark.django_db
def test_categories_are_read_once_per_calculator(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH)

    with CaptureQueriesContext(connection) as queries:
        first = calculator.categories()
        second = calculator.categories()

    assert len(queries.captured_queries) == 1
    assert [category.slug for category in first] == [category.slug for category in second]


def _timeblock_queries(queries):
    return [query["sql"] for query in queries.captured_queries if "dashboard_timeblock" in query["sql"]]


@pytest.mark.django_db
@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("aggregation", AGGREGATIONS)
def test_stats_from_one_read_match_direct_reads(recorded, aggregation, scenario):
    selected, today = SCENARIOS[scenario]
    build = AGGREGATIONS[aggregation]
    windowed = StatsCalculator(recorded, selected, window=FULL_WINDOW)

    assert build(recorded, selected, today, windowed) == build(recorded, selected, today, None)


@pytest.mark.django_db
def test_daily_stats_reuse_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)

    with CaptureQueriesContext(connection) as queries:
        get_daily_stats_data(recorded, MID_MONTH, calculator)

    assert _timeblock_queries(queries) == []


@pytest.mark.django_db
def test_weekly_stats_reuse_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)
    calculator.categories()

    with CaptureQueriesContext(connection) as queries:
        get_weekly_stats_data(recorded, MID_MONTH, calculator)

    assert [query["sql"] for query in queries.captured_queries] == []


@pytest.mark.django_db
def test_monthly_stats_reuse_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)
    calculator.categories()

    with CaptureQueriesContext(connection) as queries:
        get_monthly_stats_data(recorded, MID_MONTH, calculator)
        get_tag_analysis_data(recorded, MID_MONTH, calculator)

    assert [query["sql"] for query in queries.captured_queries] == []


@pytest.mark.django_db
def test_monthly_daily_counts_match_the_database_count(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)

    counts = calculator.get_monthly_daily_counts()

    assert dict(counts) == TimeBlockRepository().find_daily_counts(
        recorded, calculator.start_of_month, calculator.end_of_month
    )


@pytest.mark.django_db
def test_period_comparison_reuses_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)

    with CaptureQueriesContext(connection) as queries:
        get_period_delta(recorded, "day", MID_MONTH, today=LATER, calculator=calculator)
        get_period_delta(
            recorded, "month", MID_MONTH, today=LATER, with_trend=False, calculator=calculator
        )

    assert _timeblock_queries(queries) == []


@pytest.mark.django_db
def test_density_grid_reuses_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)

    with CaptureQueriesContext(connection) as queries:
        get_density_grid(recorded, MID_MONTH, days=7, calculator=calculator)

    assert _timeblock_queries(queries) == []


@pytest.mark.django_db
def test_tag_deltas_reuse_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)

    with CaptureQueriesContext(connection) as queries:
        get_tag_deltas_vs_week(recorded, MID_MONTH, calculator=calculator)

    assert _timeblock_queries(queries) == []


@pytest.mark.django_db
def test_summary_reuses_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)

    with CaptureQueriesContext(connection) as queries:
        build_summary(recorded, MID_MONTH, today=LATER, calculator=calculator)

    assert _timeblock_queries(queries) == []


@pytest.mark.django_db
def test_goal_progress_reuses_the_window(recorded):
    calculator = StatsCalculator(recorded, MID_MONTH, window=FULL_WINDOW)
    calculator.blocks_between(*FULL_WINDOW)

    with CaptureQueriesContext(connection) as queries:
        build_goal_progress_rows(recorded, MID_MONTH, today=LATER, now=NOON, calculator=calculator)

    assert _timeblock_queries(queries) == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "selected",
    [MID_MONTH, date(2026, 8, 2), date(2026, 6, 30)],
    ids=["mid_month", "week_into_last_month", "week_into_next_month"],
)
def test_stats_context_query_count_stays_within_target_with_goals(recorded, selected):
    get_stats_context(recorded, selected)

    with CaptureQueriesContext(connection) as queries:
        get_stats_context(recorded, selected)

    assert len(queries.captured_queries) <= TARGET_MAX_QUERIES
