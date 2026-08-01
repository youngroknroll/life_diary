from datetime import timedelta

from django.utils.translation import gettext

from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT
from apps.dashboard.repositories import TimeBlockRepository
from apps.tags.models import Tag
from apps.users.repositories import GoalRepository

from .comparison import get_period_delta
from .density import get_density_grid, get_gap_pattern
from .goal_progress import goal_hit_days


_goal_repo = GoalRepository()
_time_block_repo = TimeBlockRepository()

ROLLING_DAYS = 7
MAX_OBSERVATIONS = 4
NEUTRAL_COLOR = "#8A9A91"


def build_summary(user, selected_date, today=None):
    day = get_period_delta(user, "day", selected_date, today=today)
    month = get_period_delta(user, "month", selected_date, today=today, with_trend=False)

    grid = get_density_grid(user, selected_date, days=ROLLING_DAYS)
    rolling_week = _rolling_week(user, selected_date, grid)
    pattern = get_gap_pattern(grid)
    goal = _goal_tile(user, selected_date)

    return {
        "today": day["current"],
        "today_delta": day,
        "rolling_week": rolling_week,
        "month": month["current"],
        "month_delta": month,
        "goal": goal,
        "density": {"grid": grid, "pattern": pattern},
        "observations": _observations(rolling_week, pattern, goal),
    }


def _rolling_week(user, selected_date, grid):
    """달력 주와 나란히 놓기 위해 지난 7일은 롤링으로 둔다."""
    start = selected_date - timedelta(days=ROLLING_DAYS - 1)
    total_minutes = sum(minutes for row in grid for minutes in row)
    tag_minutes = _tag_minutes(user, start, selected_date)

    return {
        "start": start,
        "end": selected_date,
        "days": ROLLING_DAYS,
        "total_minutes": total_minutes,
        "tag_minutes": tag_minutes,
    }


def _tag_minutes(user, start, end):
    minutes = {}
    for block in _time_block_repo.find_by_date_range(user, start, end):
        if block.tag and block.tag.name:
            minutes[block.tag.name] = minutes.get(block.tag.name, 0) + MINUTES_PER_SLOT
    return minutes


def _goal_tile(user, selected_date):
    goal = _goal_repo.find_by_user(user).first()
    if goal is None:
        return None

    start = selected_date - timedelta(days=ROLLING_DAYS - 1)

    return {
        "tag_name": goal.tag.name,
        "color": goal.tag.color,
        "target_hours": goal.target_hours,
        "period": goal.period,
        "hit_days": goal_hit_days(user, start, selected_date, goal),
        "total_days": ROLLING_DAYS,
    }


def _observations(rolling_week, pattern, goal):
    """사실만 말하고 판단하지 않는다. 색은 판정이 아니라 태그를 가리킨다.

    기록이 하나도 없으면 모든 시간대가 공백이라 "비어 있습니다"만 늘어놓게
    된다. 대조할 것이 없으면 아무 말도 하지 않는다.
    """
    if not rolling_week["total_minutes"]:
        return []

    observations = []

    top = _top_tag(rolling_week["tag_minutes"])
    if top:
        name, minutes = top
        observations.append(
            {
                "kind": "top_tag",
                "color": _tag_color(name),
                "headline": gettext("%(tag)s %(hours)s시간")
                % {"tag": name, "hours": _hours(minutes)},
                "detail": gettext("지난 7일 기록의 %(share)d%%")
                % {"share": round(minutes / rolling_week["total_minutes"] * 100)},
            }
        )

    if pattern["worst_range"] and pattern["missing_days"]:
        start, end = pattern["worst_range"]
        observations.append(
            {
                "kind": "gap",
                "color": NEUTRAL_COLOR,
                "headline": gettext("%(start)02d–%(end)02d시가 비어 있습니다")
                % {"start": start, "end": end},
                "detail": gettext("지난 7일 중 %(days)d일")
                % {"days": pattern["missing_days"]},
            }
        )

    if pattern["best_range"]:
        start, end = pattern["best_range"]
        observations.append(
            {
                "kind": "steady",
                "color": NEUTRAL_COLOR,
                "headline": gettext("%(start)02d–%(end)02d시는 매일 기록했습니다")
                % {"start": start, "end": end},
                "detail": "",
            }
        )

    if goal:
        observations.append(
            {
                "kind": "goal",
                "color": goal["color"],
                "headline": gettext("%(tag)s 목표 %(days)d/%(total)d일")
                % {
                    "tag": goal["tag_name"],
                    "days": goal["hit_days"],
                    "total": goal["total_days"],
                },
                "detail": gettext("하루 %(hours)s시간 기준")
                % {"hours": _hours(goal["target_hours"] * MINUTES_PER_HOUR)},
            }
        )

    return observations[:MAX_OBSERVATIONS]


def _top_tag(tag_minutes):
    if not tag_minutes:
        return None
    return max(tag_minutes.items(), key=lambda item: item[1])


def _tag_color(name):
    tag = Tag.objects.filter(name=name).first()
    return tag.color if tag else NEUTRAL_COLOR


def _hours(minutes):
    return f"{minutes / MINUTES_PER_HOUR:.1f}"
