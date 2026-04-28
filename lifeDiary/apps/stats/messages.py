"""stats 앱 메시지 카탈로그.

life_feedback의 LocalizableMessage 코드를 가독성 좋은 lazy 번역 문자열로 매핑.
ENUM_LABELS는 params 안 enum 키(period 등)를 표시 라벨로 변환할 때 사용.
"""

from django.utils.translation import gettext_lazy as _

CATALOG = {
    "stats.feedback.goal_achieved": _(
        "%(period)s '%(name)s' 목표(%(hours)s시간)를 이미 달성했습니다!"
    ),
    "stats.feedback.goal_in_progress": _(
        "%(period)s '%(name)s' 목표(%(hours)s시간) 중 %(actual).1f시간을 달성했습니다. "
        "%(remain).1f시간만 더 해보세요!"
    ),
    "stats.feedback.tag_imbalance": _(
        "'%(name)s' 시간이 전체의 %(percent)d%%를 차지합니다. 활동의 균형을 점검해보세요."
    ),
    "stats.feedback.tag_volatility": _(
        "최근 '%(name)s' 활동 시간이 들쭉날쭉해요. 규칙적인 리듬을 만들어보세요!"
    ),
    "stats.feedback.rest_excess": _(
        "휴식 시간이 전체의 %(percent)d%%를 차지합니다. 활동적인 시간을 늘려보세요."
    ),
    "stats.feedback.unclassified_excess": _(
        "기록되지 않은 시간이 전체의 %(percent)d%%입니다. 하루를 더 꼼꼼히 기록해보세요."
    ),
}

ENUM_LABELS = {
    "period": {
        "daily": _("오늘"),
        "weekly": _("이번주"),
        "monthly": _("이번 달"),
    },
}
