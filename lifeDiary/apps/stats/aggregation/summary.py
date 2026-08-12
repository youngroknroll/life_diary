from datetime import date, timedelta

from django.utils.translation import gettext

from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT
from apps.dashboard.repositories import TimeBlockRepository
from apps.users.repositories import GoalRepository

from .comparison import get_period_delta
from .density import get_density_grid, get_gap_pattern
from .goal_progress import goal_hit_dates


_goal_repo = GoalRepository()
_time_block_repo = TimeBlockRepository()

ROLLING_DAYS = 7
MAX_OBSERVATIONS = 4

# 선으로 읽히려면 점이 이만큼은 있어야 한다. 이틀은 선이 아니라 점 두 개다.
MIN_DAYS_FOR_TREND = 7
NEUTRAL_COLOR = "#8A9A91"


def build_summary(user, selected_date, today=None):
    day = get_period_delta(user, "day", selected_date, today=today)
    month = get_period_delta(user, "month", selected_date, today=today, with_trend=False)

    grid = get_density_grid(user, selected_date, days=ROLLING_DAYS)
    rolling_week = _rolling_week(user, selected_date, grid)
    pattern = get_gap_pattern(grid)
    goal = _goal_tile(user, selected_date, today or date.today())

    return {
        "today": _with_hours(day["current"]),
        "today_delta": day,
        "rolling_week": _with_hours(rolling_week),
        "month": _with_hours(month["current"]),
        "month_delta": month,
        "goal": goal,
        "category_share": _category_share(rolling_week),
        "logged_days": _logged_days(grid),
        "days_until_trend": max(0, MIN_DAYS_FOR_TREND - _logged_days(grid)),
        "density": {
            "grid": grid,
            "pattern": pattern,
            "rows": _density_rows(grid, selected_date),
        },
        "observations": _observations(rolling_week, pattern, goal),
    }


def _with_hours(tile):
    return {**tile, "hours": _hours(tile["total_minutes"])}


def _category_share(rolling_week):
    """통계와 피드백은 태그가 아니라 카테고리로 읽는다.

    이름이 달라도 같은 카테고리면 한 덩어리다.
    """
    total = rolling_week["total_minutes"]
    if not total:
        return []

    shares = sorted(
        rolling_week["category_minutes"].values(),
        key=lambda e: e["total_minutes"],
        reverse=True,
    )
    for entry in shares:
        entry["hours"] = _hours(entry["total_minutes"])
        entry["percentage"] = round(entry["total_minutes"] / total * 100, 1)
    return shares


def _logged_days(grid):
    return sum(1 for row in grid if any(row))


def _density_rows(grid, end_date):
    """히트맵을 표로도 읽을 수 있게 날짜와 6시간 구간 합을 함께 낸다."""
    start = end_date - timedelta(days=len(grid) - 1)

    return [
        {
            "date": start + timedelta(days=index),
            "blocks": [sum(row[block * 6 : block * 6 + 6]) for block in range(4)],
            "total_minutes": sum(row),
        }
        for index, row in enumerate(grid)
    ]


def _rolling_week(user, selected_date, grid):
    """달력 주와 나란히 놓기 위해 지난 7일은 롤링으로 둔다.

    태그 합과 카테고리 합을 한 번의 조회에서 함께 낸다.
    """
    start = selected_date - timedelta(days=ROLLING_DAYS - 1)
    tag_minutes = {}
    tag_colors = {}
    category_minutes = {}

    for block in _time_block_repo.find_by_date_range(user, start, selected_date):
        if not (block.tag and block.tag.name):
            continue
        tag_minutes[block.tag.name] = (
            tag_minutes.get(block.tag.name, 0) + MINUTES_PER_SLOT
        )
        # 색은 여기서 챙긴다. 나중에 이름으로 되찾으면 같은 이름을 가진 다른
        # 사용자의 태그를 집을 수 있다 — 태그는 전부 개인 소유다.
        tag_colors[block.tag.name] = block.tag.color
        category = block.tag.category
        entry = category_minutes.setdefault(
            category.slug,
            {
                "slug": category.slug,
                "name": category.display_name,
                "color": category.color,
                "total_minutes": 0,
            },
        )
        entry["total_minutes"] += MINUTES_PER_SLOT

    return {
        "start": start,
        "end": selected_date,
        "days": ROLLING_DAYS,
        "total_minutes": sum(minutes for row in grid for minutes in row),
        "tag_minutes": tag_minutes,
        "tag_colors": tag_colors,
        "category_minutes": category_minutes,
    }


def _goal_tile(user, selected_date, today):
    goal = _goal_repo.find_by_user(user).first()
    if goal is None:
        return None

    start = selected_date - timedelta(days=ROLLING_DAYS - 1)
    hit_dates = goal_hit_dates(user, start, selected_date, goal)

    return {
        "tag_name": goal.tag.name,
        "color": goal.tag.color,
        "target_hours": goal.target_hours,
        "period": goal.period,
        "hit_days": len(hit_dates),
        "total_days": _counted_days(start, selected_date, today, hit_dates),
    }


def _counted_days(start, end, today, hit_dates):
    """아직 오지 않은 날은 분모에서 뺀다.

    끝나지 않은 날을 실패로 세면 아침 9시의 0% 가 실패로 읽힌다. 오늘은 이미
    목표를 채웠을 때만 분모에 넣는다 — 채운 것을 감추지 않으면서 아직 남은
    시간을 실패로 만들지도 않는다.
    """
    counted = 0
    day = start
    while day <= end:
        if day < today or day in hit_dates:
            counted += 1
        day += timedelta(days=1)
    return counted


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
                "color": rolling_week["tag_colors"].get(name, NEUTRAL_COLOR),
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


def _hours(minutes):
    return f"{minutes / MINUTES_PER_HOUR:.1f}"
