from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT
from apps.dashboard.repositories import TimeBlockRepository


_time_block_repo = TimeBlockRepository()

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
