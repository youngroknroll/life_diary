from datetime import timedelta

from apps.core.utils import (
    HOURS_PER_DAY,
    MINUTES_PER_HOUR,
    MINUTES_PER_SLOT,
    SLOTS_PER_HOUR,
)
from apps.dashboard.repositories import TimeBlockRepository


_time_block_repo = TimeBlockRepository()

PATTERN_WINDOW_HOURS = 2


def get_density_grid(user, end_date, days=7):
    """[일][시간] = 그 시간에 기록된 분. 오래된 날이 앞에 온다."""
    start_date = end_date - timedelta(days=days - 1)
    grid = [[0] * HOURS_PER_DAY for _ in range(days)]

    for block in _time_block_repo.find_by_date_range(user, start_date, end_date):
        day_index = (block.date - start_date).days
        if 0 <= day_index < days:
            grid[day_index][block.slot_index // SLOTS_PER_HOUR] += MINUTES_PER_SLOT

    return grid


def get_gap_pattern(grid, window=PATTERN_WINDOW_HOURS):
    """가장 자주 비는 구간과 하루도 빠짐없이 채운 구간."""
    if not grid:
        return {"worst_range": None, "missing_days": 0, "best_range": None}

    worst_range, missing_days = _most_common_window(grid, window, _is_empty_window)
    best_range, full_days = _most_common_window(grid, window, _is_full_window)

    return {
        "worst_range": worst_range if missing_days else None,
        "missing_days": missing_days,
        # 화면은 이 구간을 "매일 기록했습니다"라고 소개한다. 가장 자주 꽉 찬
        # 구간이 아니라 정말 매일 꽉 찬 구간일 때만 내세운다 — 7일 중 2일만
        # 채운 구간이 "비어 있습니다"와 "매일 기록했습니다" 양쪽에 동시에
        # 뽑히던 모순도 이걸로 사라진다.
        "best_range": best_range if full_days == len(grid) else None,
    }


def _most_common_window(grid, window, matches):
    winner = None
    best_count = 0

    for start in range(HOURS_PER_DAY - window + 1):
        count = sum(1 for row in grid if matches(row, start, window))
        if count > best_count:
            winner = (start, start + window)
            best_count = count

    return winner, best_count


def _is_empty_window(row, start, window):
    """10분만 남긴 시간을 공백으로 부르면 사용자가 납득하지 못한다."""
    return all(row[hour] == 0 for hour in range(start, start + window))


def _is_full_window(row, start, window):
    return all(row[hour] >= MINUTES_PER_HOUR for hour in range(start, start + window))
