from calendar import monthrange
from datetime import timedelta

from django.utils import timezone

from apps.core.utils import (
    MINUTES_PER_SLOT,
    TOTAL_SLOTS_PER_DAY,
    get_week_date_range,
)
from apps.dashboard.repositories import TimeBlockRepository


_time_block_repo = TimeBlockRepository()

SPARKLINE_DAYS = 7
BASELINE_AVG_WEEKS = 4
BASELINE_MAX_WEEKS = 12
MINUTES_PER_DAY = TOTAL_SLOTS_PER_DAY * MINUTES_PER_SLOT


def get_period_delta(user, kind, end_date, today=None, with_trend=True):
    """기준 기간과 직전 동일 기간, 기준선, 스파크라인.

    시각을 인자로 받는 이유는 진행 중인 기간을 판정해야 하는데 전역 시간을
    모킹하지 않기 위해서다. 기준선과 스파크라인은 종료일이 같으면 값도 같아,
    한 화면에서 여러 기간을 볼 때 with_trend=False 로 중복 조회를 뺀다.
    """
    today = today or timezone.localdate()

    start, end = _period_bounds(kind, end_date)
    previous_start, previous_end = _previous_bounds(kind, start)

    current = _summarize(user, start, end, today)
    previous = _summarize(user, previous_start, previous_end, today, complete=True)

    return {
        "kind": kind,
        "current": current,
        "previous": previous,
        "delta_minutes": current["total_minutes"] - previous["total_minutes"],
        "has_previous": previous["total_minutes"] > 0,
        "baseline": _baseline(user, start) if with_trend else None,
        "sparkline": _sparkline(user, end_date) if with_trend else None,
    }


def _period_bounds(kind, end_date):
    if kind == "day":
        return end_date, end_date
    if kind == "week":
        return get_week_date_range(end_date)
    if kind == "month":
        last_day = monthrange(end_date.year, end_date.month)[1]
        return end_date.replace(day=1), end_date.replace(day=last_day)
    raise ValueError(f"알 수 없는 기간 종류입니다: {kind}")


def _previous_bounds(kind, start):
    if kind == "day":
        previous = start - timedelta(days=1)
        return previous, previous
    if kind == "week":
        return get_week_date_range(start - timedelta(days=7))
    if kind == "month":
        previous_end = start - timedelta(days=1)
        return previous_end.replace(day=1), previous_end
    raise ValueError(f"알 수 없는 기간 종류입니다: {kind}")


def _summarize(user, start, end, today, complete=False):
    """진행 중인 기간은 아직 오지 않은 날을 분모에서 뺀다.

    7일로 나누면 수요일에 보는 이번 주가 늘 실패처럼 읽힌다.
    """
    days = (end - start).days + 1
    is_partial = not complete and today < end
    elapsed_days = days if complete else _elapsed_days(start, end, today)

    tag_minutes = {}
    total_minutes = 0

    for block in _time_block_repo.find_by_date_range(user, start, end):
        total_minutes += MINUTES_PER_SLOT
        name = block.tag.name if block.tag else None
        if name:
            tag_minutes[name] = tag_minutes.get(name, 0) + MINUTES_PER_SLOT

    possible_minutes = elapsed_days * MINUTES_PER_DAY

    return {
        "start": start,
        "end": end,
        "days": days,
        "elapsed_days": elapsed_days,
        "is_partial": is_partial,
        "total_minutes": total_minutes,
        "tag_minutes": tag_minutes,
        "fill_percentage": round(total_minutes / possible_minutes * 100, 1)
        if possible_minutes
        else 0.0,
    }


def _elapsed_days(start, end, today):
    if today < start:
        return 1
    return min((min(end, today) - start).days + 1, (end - start).days + 1)


def _baseline(user, start):
    """기준 기간 직전의 완결된 주들. 진행 중인 기간은 자기 기준선에 못 든다.

    12주를 주마다 따로 조회하면 쿼리가 12개가 된다. 한 번에 읽고 주 단위로
    나눈다.
    """
    week_start, _ = get_week_date_range(start)
    oldest_start = week_start - timedelta(weeks=BASELINE_MAX_WEEKS)

    weekly_totals = [0] * BASELINE_MAX_WEEKS
    for block in _time_block_repo.find_by_date_range(
        user, oldest_start, week_start - timedelta(days=1)
    ):
        weeks_back = ((week_start - block.date).days - 1) // 7
        if 0 <= weeks_back < BASELINE_MAX_WEEKS:
            weekly_totals[weeks_back] += MINUTES_PER_SLOT

    recent_four = weekly_totals[:BASELINE_AVG_WEEKS]

    return {
        "avg_4w": round(sum(recent_four) / len(recent_four), 1) if recent_four else 0,
        "max_12w": max(weekly_totals) if weekly_totals else 0,
    }


def _sparkline(user, end_date):
    start = end_date - timedelta(days=SPARKLINE_DAYS - 1)
    daily = [0] * SPARKLINE_DAYS

    for block in _time_block_repo.find_by_date_range(user, start, end_date):
        index = (block.date - start).days
        if 0 <= index < SPARKLINE_DAYS:
            daily[index] += MINUTES_PER_SLOT

    return daily
