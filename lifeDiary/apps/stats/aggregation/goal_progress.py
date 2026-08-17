from django.utils import timezone

from apps.core.utils import (
    MINUTES_PER_HOUR,
    MINUTES_PER_SLOT,
    get_month_date_range,
    get_week_date_range,
)
from apps.dashboard.repositories import TimeBlockRepository
from apps.stats.aggregation.category_keys import CATEGORY_KEY_BY_SLUG, CATEGORY_LINE_COLOR
from apps.users.repositories import GoalRepository


_time_block_repo = TimeBlockRepository()
_goal_repo = GoalRepository()

DAYS_PER_PERIOD = {"daily": 1, "weekly": 7, "monthly": 30}


def goal_hit_dates(user, start, end, goal) -> set:
    """기간 안에서 목표 시간을 채운 날들.

    주간·월간 목표도 하루치로 환산해 센다. 달성일은 "그날 목표만큼 했나"를
    묻는 지표라 기간 총합으로는 답할 수 없다.
    """
    target_minutes = _daily_target_minutes(goal)
    minutes_by_date = {}

    for block in _time_block_repo.find_by_date_range(user, start, end):
        if block.tag_id != goal.tag_id:
            continue
        minutes_by_date[block.date] = (
            minutes_by_date.get(block.date, 0) + MINUTES_PER_SLOT
        )

    return {
        day
        for day, minutes in minutes_by_date.items()
        if minutes >= target_minutes
    }


def goal_hit_days(user, start, end, goal) -> int:
    return len(goal_hit_dates(user, start, end, goal))


def _daily_target_minutes(goal) -> float:
    return goal.target_hours * MINUTES_PER_HOUR / DAYS_PER_PERIOD.get(goal.period, 1)


def _period_bounds(period, selected_date):
    if period == "weekly":
        return get_week_date_range(selected_date)
    if period == "monthly":
        return get_month_date_range(selected_date)
    return selected_date, selected_date


def _minutes_recorded(user, tag_id, start, end):
    return sum(
        MINUTES_PER_SLOT
        for block in _time_block_repo.find_by_date_range(user, start, end)
        if block.tag_id == tag_id
    )


def _pace_percentage(period, selected_date, start, end):
    if period == "daily":
        return None
    total_days = (end - start).days + 1
    elapsed_days = (selected_date - start).days + 1
    return round(elapsed_days / total_days * 100)


def _goal_progress_row(user, goal, selected_date, today):
    start, end = _period_bounds(goal.period, selected_date)
    current_minutes = _minutes_recorded(user, goal.tag_id, start, end)
    target_minutes = goal.target_hours * MINUTES_PER_HOUR

    if target_minutes <= 0:
        percentage = 100 if current_minutes > 0 else 0
    else:
        percentage = min(100, round(current_minutes / target_minutes * 100))

    period_ended = end < today
    is_under_target = (
        period_ended and target_minutes > 0 and current_minutes < target_minutes
    )

    category_slug = goal.tag.category.slug
    category_key = CATEGORY_KEY_BY_SLUG.get(category_slug, category_slug)
    return {
        "goal_id": goal.id,
        "tag_name": goal.tag.name,
        "tag_color": goal.tag.color,
        "category_key": category_key,
        "category_line_color": CATEGORY_LINE_COLOR.get(category_key, goal.tag.color),
        "period": goal.period,
        "current_hours": round(current_minutes / MINUTES_PER_HOUR, 1),
        "target_hours": goal.target_hours,
        "percentage": percentage,
        "pace_percentage": _pace_percentage(goal.period, selected_date, start, end),
        "is_under_target": is_under_target,
    }


def build_goal_progress_rows(user, selected_date, today=None):
    """요약 탭 목표 진행 바 행. 일간 → 주간 → 월간 순, 조회일(selected_date)
    기준 그 기간의 누적 진행률이다.

    `today`(실제 오늘)와 `selected_date`(조회 중인 날)를 분리하는 이유는
    "미달 확정"을 판단하려면 그 기간이 실제로 끝났는지가 필요한데,
    전역 시각을 모킹하지 않고 테스트하기 위해서다(comparison.get_period_delta와
    같은 이유).
    """
    today = today or timezone.localdate()
    grouped = _goal_repo.find_grouped_by_period(user)
    return [
        _goal_progress_row(user, goal, selected_date, today)
        for period in ("daily", "weekly", "monthly")
        for goal in grouped[period]
    ]
