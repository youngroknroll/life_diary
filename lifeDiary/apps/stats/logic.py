"""
stats/logic.py — 얇은 오케스트레이터.
집계 로직은 aggregation/ 패키지에 위치한다.
"""
from apps.users.repositories import GoalRepository, NoteRepository
from apps.users.domain_services import _goal_progress_service

from .aggregation.calculator import StatsCalculator
from .aggregation.daily import get_daily_stats_data
from .aggregation.weekly import get_weekly_stats_data
from .aggregation.monthly import get_monthly_stats_data
from .aggregation.analysis import get_tag_analysis_data

__all__ = [
    "StatsCalculator",
    "get_daily_stats_data",
    "get_weekly_stats_data",
    "get_monthly_stats_data",
    "get_tag_analysis_data",
    "get_stats_context",
]

_goal_repo = GoalRepository()
_note_repo = NoteRepository()


def get_stats_context(user, selected_date):
    calculator = StatsCalculator(user, selected_date)
    daily_stats = get_daily_stats_data(user, selected_date, calculator)
    weekly_stats = get_weekly_stats_data(user, selected_date, calculator)
    monthly_stats = get_monthly_stats_data(user, selected_date, calculator)
    tag_analysis = get_tag_analysis_data(user, selected_date, calculator)

    context = {
        "page_title": "통계",
        "selected_date": selected_date,
        "total_blocks": len(daily_stats["tag_stats"]),
        "total_days": monthly_stats["total_days"],
        "total_hours": monthly_stats["total_hours"],
        "daily_stats": daily_stats,
        "weekly_stats": weekly_stats,
        "monthly_stats": monthly_stats,
        "tag_analysis": tag_analysis,
        "daily_stats_json": {
            "tag_stats": daily_stats["tag_stats"],
            "hourly_stats": daily_stats["hourly_stats"],
        },
        "weekly_stats_json": {
            "weekly_data": [
                {"day_korean": d["day_korean"], "total_hours": d["total_hours"]}
                for d in weekly_stats["weekly_data"]
            ],
            "tag_weekly_stats": weekly_stats["tag_weekly_stats"],
        },
        "tag_analysis_json": tag_analysis,
        "monthly_stats_json": {
            "day_labels": monthly_stats["day_labels"],
            "tag_stats": monthly_stats["tag_stats"],
            "daily_totals": monthly_stats["daily_totals"],
        },
    }

    grouped_goals = _goal_repo.find_grouped_by_period(user)
    user_goals_daily = grouped_goals["daily"]
    user_goals_weekly = grouped_goals["weekly"]
    user_goals_monthly = grouped_goals["monthly"]
    context["user_goals_daily"] = user_goals_daily
    context["user_goals_weekly"] = user_goals_weekly
    context["user_goals_monthly"] = user_goals_monthly

    for goals in [user_goals_daily, user_goals_weekly, user_goals_monthly]:
        _goal_progress_service.attach_progress(
            goals,
            daily_stats=daily_stats,
            weekly_stats=weekly_stats,
            monthly_stats=monthly_stats,
        )

    context["user_note"] = _note_repo.find_latest(user)
    return context
