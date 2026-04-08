# AI 피드백 생성 로직 분리

import logging
import statistics

from apps.core.utils import UNCLASSIFIED_TAG_NAME, SLEEP_TAG_NAME

logger = logging.getLogger(__name__)


def generate_feedback(context):
    feedback = []
    # 1. 목표 기반 피드백 (월간)
    for goal in context.get("user_goals_monthly", []):
        if goal.percent is not None and goal.percent < 100:
            remain = goal.target_hours - goal.actual
            if remain > 0:
                feedback.append(
                    f"이번 달 '{goal.tag.name}' 목표({goal.target_hours}시간) 중 {goal.actual:.1f}시간을 달성했습니다. {remain:.1f}시간만 더 해보세요!"
                )
        elif goal.percent is not None and goal.percent >= 100:
            feedback.append(
                f"이번 달 '{goal.tag.name}' 목표({goal.target_hours}시간)를 이미 달성했습니다! 멋져요!"
            )
    # 2. 비교 기반 피드백 (주간/월간)
    # 주간: 이번주 vs 지난주
    try:
        weekly_stats = context["weekly_stats"]
        prev_weekly_stats = context.get("prev_weekly_stats")
        if prev_weekly_stats:
            for tag in weekly_stats["tag_weekly_stats"]:
                prev_tag = next(
                    (
                        t
                        for t in prev_weekly_stats["tag_weekly_stats"]
                        if t["name"] == tag["name"]
                    ),
                    None,
                )
                if prev_tag:
                    diff = tag["total_hours"] - prev_tag["total_hours"]
                    if abs(diff) >= 1:  # 1시간 이상 변화만 피드백
                        percent = (
                            int((diff / prev_tag["total_hours"]) * 100)
                            if prev_tag["total_hours"] > 0
                            else 0
                        )
                        if diff > 0:
                            feedback.append(
                                f"이번주 '{tag['name']}' 시간이 지난주보다 {percent}% 늘었습니다. 잘하고 있어요!"
                            )
                        else:
                            feedback.append(
                                f"이번주 '{tag['name']}' 시간이 지난주보다 {abs(percent)}% 줄었습니다. 다음주엔 더 노력해봐요!"
                            )
    except Exception:
        logger.exception("주간 비교 피드백 생성 중 오류")
    # 3. 불균형/과다/부족 경고 (월간)
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
                feedback.append(
                    f"'{tag['name']}' 시간이 전체의 {percent}%를 차지합니다. 활동의 균형을 점검해보세요."
                )
        # 4. 리듬 붕괴(변동성) 피드백
        daily_hours = tag.get("daily_hours")
        if daily_hours:
            values = [h for h in daily_hours if h > 0]
            if len(values) >= 2:
                avg = statistics.mean(values)
                stdev = statistics.stdev(values)
                cv = stdev / avg if avg > 0 else 0
                if cv >= 0.7:
                    feedback.append(
                        f"최근 '{tag['name']}' 활동 시간이 들쭉날쭉해요. 규칙적인 리듬을 만들어보세요!"
                    )
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
            feedback.append(
                f"휴식 시간이 전체의 {percent}%를 차지합니다. 활동적인 시간을 늘려보세요."
            )
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
            feedback.append(
                f"기록되지 않은 시간이 전체의 {percent}%입니다. 하루를 더 꼼꼼히 기록해보세요."
            )
    # 7. 습관/루틴 제안 (예시: '기상' 태그가 없으면 제안)
    tag_names = [tag["name"] for tag in context["monthly_stats"]["tag_stats"]]
    if "기상" not in tag_names:
        feedback.append(
            "매일 같은 시간에 '기상' 기록을 남겨보세요. 규칙적인 생활에 도움이 됩니다."
        )
    return feedback
