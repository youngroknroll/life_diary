class GoalProgressService:
    """
    목표 달성률 계산 도메인 서비스.
    ORM 없음, request 없음. 순수 계산만 담당.
    core/utils.py의 calculate_goal_percent() 이전.
    """

    def calculate(self, goal, daily_stats=None, weekly_stats=None, monthly_stats=None):
        """
        단일 목표의 실제 달성 시간과 달성률을 계산한다.

        Returns:
            tuple: (actual_hours: float, percent: int | None)
        """
        actual = 0
        if goal.period == "daily" and daily_stats:
            for tag_stat in daily_stats.get("tag_stats", []):
                if tag_stat["name"] == goal.tag.name:
                    actual = tag_stat.get("hours", 0)
        elif goal.period == "weekly" and weekly_stats:
            for tag_stat in weekly_stats.get("tag_weekly_stats", []):
                if tag_stat["name"] == goal.tag.name:
                    actual = tag_stat.get("total_hours", 0)
        elif goal.period == "monthly" and monthly_stats:
            for tag_stat in monthly_stats.get("tag_stats", []):
                if tag_stat["name"] == goal.tag.name:
                    actual = tag_stat.get("total_hours", 0)

        percent = (
            int((actual / goal.target_hours) * 100) if goal.target_hours > 0 else None
        )
        return actual, percent

    def attach_progress(self, goals, daily_stats=None, weekly_stats=None, monthly_stats=None):
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
