# 라이프 피드백 생성 로직 — LocalizableMessage 반환

import statistics

from apps.core.messages import LocalizableMessage
from apps.core.utils import SLEEP_TAG_NAME, UNCLASSIFIED_TAG_NAME

# 피드백 타입 상수 (severity)
POSITIVE = "positive"
INFO = "info"
WARNING = "warning"


def _msg(code: str, params: dict, severity: str = INFO) -> LocalizableMessage:
    return LocalizableMessage(code=code, params=params, severity=severity)


def _goal_feedback(goals, period: str):
    """일간/주간/월간 목표 달성률 피드백 생성. period: 'daily'/'weekly'/'monthly'."""
    feedback = []
    for goal in goals:
        if goal.percent is None:
            continue
        if goal.percent >= 100:
            feedback.append(_msg(
                "stats.feedback.goal_achieved",
                {"period": period, "name": goal.tag.name, "hours": goal.target_hours},
                POSITIVE,
            ))
        else:
            remain = goal.target_hours - goal.actual
            if remain > 0:
                feedback.append(_msg(
                    "stats.feedback.goal_in_progress",
                    {
                        "period": period,
                        "name": goal.tag.name,
                        "hours": goal.target_hours,
                        "actual": goal.actual,
                        "remain": remain,
                    },
                    INFO,
                ))
    return feedback


def generate_feedback(context):
    feedback = []

    # 1. 목표 기반 피드백 (일간/주간/월간)
    feedback.extend(_goal_feedback(context.get("user_goals_daily", []), "daily"))
    feedback.extend(_goal_feedback(context.get("user_goals_weekly", []), "weekly"))
    feedback.extend(_goal_feedback(context.get("user_goals_monthly", []), "monthly"))

    # 2. 불균형/과다/부족 경고 + 4. 리듬 붕괴(변동성) 피드백 (월간)
    for tag in context["monthly_stats"]["tag_stats"]:
        if (
            tag["name"] not in [UNCLASSIFIED_TAG_NAME, SLEEP_TAG_NAME]
            and tag["total_hours"] > 0
            and context["monthly_stats"]["total_hours"] > 0
        ):
            percent = int(
                (tag["total_hours"] / context["monthly_stats"]["total_hours"]) * 100
            )
            if percent >= 60:
                feedback.append(_msg(
                    "stats.feedback.tag_imbalance",
                    {"name": tag["name"], "percent": percent},
                    WARNING,
                ))

        # 4. 리듬 붕괴(변동성) 피드백
        daily_hours = tag.get("daily_hours")
        if daily_hours:
            values = [h for h in daily_hours if h > 0]
            if len(values) >= 2:
                avg = statistics.mean(values)
                stdev = statistics.stdev(values)
                cv = stdev / avg if avg > 0 else 0
                if cv >= 0.7:
                    feedback.append(_msg(
                        "stats.feedback.tag_volatility",
                        {"name": tag["name"]},
                        WARNING,
                    ))

    # 5. 휴식 과다 경고
    rest = next(
        (tag for tag in context["monthly_stats"]["tag_stats"] if tag["name"] == SLEEP_TAG_NAME),
        None,
    )
    if rest and context["monthly_stats"]["total_hours"] > 0:
        percent = int(
            (rest["total_hours"] / context["monthly_stats"]["total_hours"]) * 100
        )
        if percent >= 60:
            feedback.append(_msg(
                "stats.feedback.rest_excess",
                {"percent": percent},
                WARNING,
            ))

    # 6. 미분류/공백 시간 경고 (월간)
    unclassified = next(
        (
            tag
            for tag in context["monthly_stats"]["tag_stats"]
            if tag["name"] == UNCLASSIFIED_TAG_NAME
        ),
        None,
    )
    if unclassified and context["monthly_stats"]["total_hours"] > 0:
        percent = int(
            (unclassified["total_hours"] / context["monthly_stats"]["total_hours"])
            * 100
        )
        if percent >= 20:
            feedback.append(_msg(
                "stats.feedback.unclassified_excess",
                {"percent": percent},
                WARNING,
            ))

    # 7. 습관/루틴 제안 — 기획 필요, 보류

    return feedback
