class GoalProgressService:
    """
    목표 달성률 계산 도메인 서비스.
    ORM 없음, request 없음. 순수 계산만 담당.
    core/utils.py의 calculate_goal_percent() 이전.
    """

    _PERIOD_SOURCES = {
        "daily": ("tag_stats", "hours"),
        "weekly": ("tag_weekly_stats", "total_hours"),
        "monthly": ("tag_stats", "total_hours"),
    }

    def get_actual_hours(self, goal, daily_stats=None, weekly_stats=None, monthly_stats=None):
        stats_by_period = {
            "daily": daily_stats,
            "weekly": weekly_stats,
            "monthly": monthly_stats,
        }
        stats = stats_by_period.get(goal.period)
        config = self._PERIOD_SOURCES.get(goal.period)
        if not stats or not config:
            return 0

        stats_key, value_key = config
        for tag_stat in stats.get(stats_key, []):
            if tag_stat["name"] == goal.tag.name:
                return tag_stat.get(value_key, 0)
        return 0

    def calculate(self, goal, daily_stats=None, weekly_stats=None, monthly_stats=None):
        """
        단일 목표의 실제 달성 시간과 달성률을 계산한다.

        Returns:
            tuple: (actual_hours: float, percent: int | None)
        """
        actual = self.get_actual_hours(
            goal,
            daily_stats=daily_stats,
            weekly_stats=weekly_stats,
            monthly_stats=monthly_stats,
        )

        percent = (
            int((actual / goal.target_hours) * 100) if goal.target_hours > 0 else None
        )
        return actual, percent

    def attach_progress(
        self, goals, daily_stats=None, weekly_stats=None, monthly_stats=None
    ):
        """목표 리스트에 actual, percent를 주입하고 반환한다."""
        for goal in goals:
            goal.actual, goal.percent = self.calculate(
                goal,
                daily_stats=daily_stats,
                weekly_stats=weekly_stats,
                monthly_stats=monthly_stats,
            )
        return goals


_goal_progress_service = GoalProgressService()
