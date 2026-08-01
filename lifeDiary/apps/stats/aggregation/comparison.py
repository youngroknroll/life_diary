"""직전 동일 기간 비교.

분석 화면의 증감·스파크라인·기준선이 전부 여기서 나온다. 이 값이 없으면
"+6.2h"나 "4주 평균 대비 −1.4h" 같은 표기가 성립하지 않는다.

주는 달력 주(월~일)를 쓴다. 시안은 롤링 7일 기준이지만 달력 주로 결정됐고,
그래서 진행 중인 주가 완료된 주보다 늘 낮게 읽히는 문제가 따라온다. 답은
is_partial 플래그와 경과일 기준 분모다 — 아직 오지 않은 날을 분모에 넣으면
0%가 실패처럼 보인다.
"""

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


def get_period_delta(user, kind, end_date, today=None):
    """기준 기간과 직전 동일 기간, 기준선, 스파크라인을 함께 돌려준다."""
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
        "baseline": _baseline(user, start),
        "sparkline": _sparkline(user, end_date),
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
    """기간 합계와 태그별 분해. 진행 중이면 경과일까지만 분모로 센다."""
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
    """기준 기간 직전의 완결된 주들. 기준 기간 자체는 넣지 않는다."""
    week_start, _ = get_week_date_range(start)
    weekly_totals = []

    for weeks_back in range(1, BASELINE_MAX_WEEKS + 1):
        period_start = week_start - timedelta(weeks=weeks_back)
        period_end = period_start + timedelta(days=6)
        weekly_totals.append(_total_minutes(user, period_start, period_end))

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


def _total_minutes(user, start, end):
    return sum(
        MINUTES_PER_SLOT
        for _ in _time_block_repo.find_by_date_range(user, start, end)
    )
