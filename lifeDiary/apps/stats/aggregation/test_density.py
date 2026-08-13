"""기록 밀도 — 요일 × 시간 격자와 공백 패턴."""

from datetime import date, timedelta

import pytest

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.density import get_density_grid, get_gap_pattern
from apps.tags.models import Category, Tag


END = date(2026, 8, 1)


def empty_grid(days=7):
    return [[0] * 24 for _ in range(days)]


def contradiction_grid():
    """00–02시가 5일은 완전히 비고 2일은 꽉 찬 주.

    나머지 시간은 30분씩이라 비지도 꽉 차지도 않는다 — 그래서 00–02시가
    "가장 자주 비는 구간"이자 "가장 자주 꽉 찬 구간"이 된다.
    """
    grid = [[30] * 24 for _ in range(7)]
    for day in (0, 6):
        grid[day][0] = grid[day][1] = 60
    for day in range(1, 6):
        grid[day][0] = grid[day][1] = 0
    return grid


def record(user, tag, slot_index, on_date=END):
    return TimeBlock.objects.create(
        user=user, date=on_date, slot_index=slot_index, tag=tag
    )


class TestGapPattern:
    def test_finds_the_window_that_is_empty_on_the_most_days(self):
        grid = [[60] * 24 for _ in range(7)]
        for day in range(5):
            grid[day][15] = 0
            grid[day][16] = 0

        pattern = get_gap_pattern(grid)

        assert pattern["worst_range"] == (15, 17)
        assert pattern["missing_days"] == 5

    def test_finds_the_window_that_is_full_every_day(self):
        grid = empty_grid()
        for day in range(7):
            grid[day][9] = 60
            grid[day][10] = 60

        pattern = get_gap_pattern(grid)

        assert pattern["best_range"] == (9, 11)

    def test_a_window_full_on_only_some_days_is_not_steady(self):
        """화면은 "매일 기록했습니다"라고 말한다. 하루라도 비면 거짓이 된다."""
        grid = contradiction_grid()

        assert get_gap_pattern(grid)["best_range"] is None

    def test_one_window_is_never_both_the_gap_and_the_steady_one(self):
        """운영 데이터에서 나온 모순.

        7일 중 5일 비고 2일 꽉 찬 구간이 "비어 있습니다"와 "매일 기록했습니다"
        양쪽에 동시에 뽑혔다. 두 문구가 같은 시간대를 두고 서로 반대로 말했다.
        """
        pattern = get_gap_pattern(contradiction_grid())

        assert pattern["worst_range"] == (0, 2)
        assert pattern["best_range"] != pattern["worst_range"]

    def test_a_fully_recorded_week_has_no_gap(self):
        pattern = get_gap_pattern([[60] * 24 for _ in range(7)])

        assert pattern["missing_days"] == 0
        assert pattern["worst_range"] is None

    def test_an_empty_week_has_no_best_range(self):
        pattern = get_gap_pattern(empty_grid())

        assert pattern["best_range"] is None

    def test_a_partly_recorded_hour_does_not_count_as_empty(self):
        """10분이라도 기록이 있으면 그 시간은 공백이 아니다."""
        grid = [[60] * 24 for _ in range(7)]
        for day in range(7):
            grid[day][15] = 10
            grid[day][16] = 10

        assert get_gap_pattern(grid)["missing_days"] == 0

    def test_ties_are_broken_by_the_earlier_window(self):
        """같은 날 수로 비는 구간이 둘이면 이른 시간대를 말한다."""
        grid = [[60] * 24 for _ in range(7)]
        for day in range(7):
            grid[day][3] = grid[day][4] = 0
            grid[day][20] = grid[day][21] = 0

        assert get_gap_pattern(grid)["worst_range"] == (3, 5)

    def test_no_days_yields_empty_pattern(self):
        pattern = get_gap_pattern([])

        assert pattern["worst_range"] is None
        assert pattern["best_range"] is None


@pytest.fixture
def user(make_user):
    return make_user(username="densityuser")


@pytest.fixture
def tag(user):
    return Tag.objects.create(
        user=user,
        name="집중",
        color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )


@pytest.mark.django_db
class TestDensityGrid:
    def test_grid_shape_is_days_by_hours(self, user):
        grid = get_density_grid(user, END, days=7)

        assert len(grid) == 7
        assert all(len(row) == 24 for row in grid)

    def test_untouched_week_is_all_zero(self, user):
        grid = get_density_grid(user, END, days=7)

        assert all(minutes == 0 for row in grid for minutes in row)

    def test_each_slot_contributes_ten_minutes_to_its_hour(self, user, tag):
        for slot_index in (54, 55, 56):
            record(user, tag, slot_index)

        grid = get_density_grid(user, END, days=7)

        assert grid[-1][9] == 30

    def test_rows_run_oldest_first_and_end_on_the_given_date(self, user, tag):
        record(user, tag, 0, on_date=END - timedelta(days=6))

        grid = get_density_grid(user, END, days=7)

        assert grid[0][0] == 10
        assert grid[-1][0] == 0

    def test_days_outside_the_window_are_ignored(self, user, tag):
        record(user, tag, 0, on_date=END - timedelta(days=7))

        grid = get_density_grid(user, END, days=7)

        assert all(minutes == 0 for row in grid for minutes in row)

    def test_another_users_records_do_not_leak(self, user, make_user):
        stranger = make_user(username="stranger")
        stranger_tag = Tag.objects.create(
            user=stranger,
            name="남의태그",
            color="#4E8F63",
            category=Category.objects.get(slug="investment"),
        )
        record(stranger, stranger_tag, 54)

        grid = get_density_grid(user, END, days=7)

        assert grid[-1][9] == 0

    def test_an_hour_never_exceeds_sixty_minutes(self, user, tag):
        for slot_index in range(54, 60):
            record(user, tag, slot_index)

        grid = get_density_grid(user, END, days=7)

        assert grid[-1][9] == 60
