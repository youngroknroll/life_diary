# 라이프 피드백 생성 로직

import statistics

from apps.core.utils import SLEEP_TAG_NAME, UNCLASSIFIED_TAG_NAME

# 피드백 타입 상수
POSITIVE = "positive"  # text-bg-primary (초록)
INFO = "info"          # text-bg-info (파랑)
WARNING = "warning"    # text-bg-warning (주황)


def _fb(message, fb_type=INFO):
    return {"message": message, "type": fb_type}


def _goal_feedback(goals, period_label):
    """일간/주간/월간 목표 달성률 피드백 생성."""
    feedback = []
    for goal in goals:
        if goal.percent is None:
            continue
        if goal.percent >= 100:
            feedback.append(_fb(
                f"{period_label} '{goal.tag.name}' 목표({goal.target_hours}시간)를 이미 달성했습니다!",
                POSITIVE,
            ))
        else:
            remain = goal.target_hours - goal.actual
            if remain > 0:
                feedback.append(_fb(
                    f"{period_label} '{goal.tag.name}' 목표({goal.target_hours}시간) 중 "
                    f"{goal.actual:.1f}시간을 달성했습니다. {remain:.1f}시간만 더 해보세요!",
                    INFO,
                ))
    return feedback


def generate_feedback(context):
    feedback = []

    # 1. 목표 기반 피드백 (일간/주간/월간)
    feedback.extend(_goal_feedback(context.get("user_goals_daily", []), "오늘"))
    feedback.extend(_goal_feedback(context.get("user_goals_weekly", []), "이번주"))
    feedback.extend(_goal_feedback(context.get("user_goals_monthly", []), "이번 달"))

    # 2. 불균형/과다/부족 경고 (월간)
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
                feedback.append(_fb(
                    f"'{tag['name']}' 시간이 전체의 {percent}%를 차지합니다. 활동의 균형을 점검해보세요.",
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
                    feedback.append(_fb(
                        f"최근 '{tag['name']}' 활동 시간이 들쭉날쭉해요. 규칙적인 리듬을 만들어보세요!",
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
            feedback.append(_fb(
                f"휴식 시간이 전체의 {percent}%를 차지합니다. 활동적인 시간을 늘려보세요.",
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
            feedback.append(_fb(
                f"기록되지 않은 시간이 전체의 {percent}%입니다. 하루를 더 꼼꼼히 기록해보세요.",
                WARNING,
            ))

    # 7. 습관/루틴 제안 — 기획 필요, 보류

    return feedback
