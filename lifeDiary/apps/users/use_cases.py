from __future__ import annotations

import datetime

from apps.stats.logic import (
    StatsCalculator,
    get_daily_stats_data,
    get_monthly_stats_data,
    get_weekly_stats_data,
)
from .domain_services import _goal_progress_service
from .repositories import GoalRepository, NoteRepository

_goal_repo = GoalRepository()
_note_repo = NoteRepository()

_EMPTY_STATS = {"tag_stats": [], "tag_weekly_stats": [], "weekly_data": []}


class GetMyPageUseCase:
    def execute(self, user) -> dict:
        today = datetime.date.today()
        goals = list(_goal_repo.find_by_user(user))
        needed = {g.period for g in goals}

        calculator = StatsCalculator(user, today)
        daily_stats = get_daily_stats_data(user, today, calculator) if "daily" in needed else _EMPTY_STATS
        weekly_stats = get_weekly_stats_data(user, today, calculator) if "weekly" in needed else _EMPTY_STATS
        monthly_stats = get_monthly_stats_data(user, today, calculator) if "monthly" in needed else _EMPTY_STATS

        _goal_progress_service.attach_progress(
            goals,
            daily_stats=daily_stats,
            weekly_stats=weekly_stats,
            monthly_stats=monthly_stats,
        )
        return {
            "goals": goals,
            "note": _note_repo.find_latest(user),
        }
