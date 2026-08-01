"""기록 밀도 — 요일 × 시간 격자와 공백 패턴.

태그와 무관하게 "언제 기록이 있었나"만 본다. 시안 4a의 히트맵과
"규칙적 09–11시 · 공백 15–17시" 문구가 여기서 나온다.
"""

from datetime import timedelta

from apps.core.utils import HOURS_PER_DAY, MINUTES_PER_HOUR, MINUTES_PER_SLOT, SLOTS_PER_HOUR
from apps.dashboard.repositories import TimeBlockRepository


_time_block_repo = TimeBlockRepository()

# 패턴을 찾을 때 보는 구간 길이. 시안이 두 시간 폭으로 말한다("09–11시").
PATTERN_WINDOW_HOURS = 2


def get_density_grid(user, end_date, days=7):
    """[일][시간] = 그 시간에 기록된 분. 행은 오래된 날이 먼저 온다."""
    start_date = end_date - timedelta(days=days - 1)
    grid = [[0] * HOURS_PER_DAY for _ in range(days)]

    for block in _time_block_repo.find_by_date_range(user, start_date, end_date):
        day_index = (block.date - start_date).days
        if not 0 <= day_index < days:
            continue
        grid[day_index][block.slot_index // SLOTS_PER_HOUR] += MINUTES_PER_SLOT

    return grid


def get_gap_pattern(grid, window=PATTERN_WINDOW_HOURS):
    """가장 자주 비는 구간과 가장 꾸준히 채워지는 구간.

    한 칸이라도 기록이 있으면 그 시간은 비었다고 보지 않는다. 10분만 남긴
    시간을 공백으로 부르면 사용자가 납득하지 못한다.
    """
    if not grid:
        return {"worst_range": None, "missing_days": 0, "best_range": None}

    worst_range, missing_days = _best_window(grid, window, _is_empty_window)
    best_range, full_days = _best_window(grid, window, _is_full_window)

    return {
        "worst_range": worst_range if missing_days else None,
        "missing_days": missing_days,
        "best_range": best_range if full_days else None,
    }


def _best_window(grid, window, matches):
    """조건에 해당하는 날이 가장 많은 구간과 그 날 수."""
    winner = None
    best_count = 0

    for start in range(HOURS_PER_DAY - window + 1):
        count = sum(1 for row in grid if matches(row, start, window))
        if count > best_count:
            winner = (start, start + window)
            best_count = count

    return winner, best_count


def _is_empty_window(row, start, window):
    return all(row[hour] == 0 for hour in range(start, start + window))


def _is_full_window(row, start, window):
    return all(row[hour] >= MINUTES_PER_HOUR for hour in range(start, start + window))
