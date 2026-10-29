"""통계에 쓰는 미분류 합성 항목과 분·시간 변환."""

from django.utils.translation import gettext

from apps.core.utils import (
    DAYS_PER_WEEK,
    MINUTES_PER_HOUR,
    UNCLASSIFIED_TAG_COLOR,
)
from apps.stats.aggregation.identity import UNCLASSIFIED_KEY


def _unclassified_display_name():
    return gettext("미분류")


def build_unclassified_daily_entry():
    """일간 통계의 미분류 합성 항목을 만든다."""
    return {
        "key": UNCLASSIFIED_KEY,
        "tag_id": None,
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "minutes": 0,
        "blocks": 0,
        "is_unclassified": True,
    }


def build_unclassified_weekly_entry(days=DAYS_PER_WEEK):
    """주간 통계의 미분류 합성 항목을 만든다."""
    return {
        "key": UNCLASSIFIED_KEY,
        "tag_id": None,
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "daily_minutes": [0] * days,
        "is_unclassified": True,
    }


def build_unclassified_monthly_entry(total_days):
    """월간 통계의 미분류 합성 항목을 만든다."""
    return {
        "key": UNCLASSIFIED_KEY,
        "tag_id": None,
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "daily_hours": [0] * total_days,
        "total_hours": 0,
        "is_unclassified": True,
    }


def build_unclassified_analysis_entry():
    """분석 통계의 미분류 합성 항목을 만든다."""
    return {
        "key": UNCLASSIFIED_KEY,
        "tag_id": None,
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "total_minutes": 0,
        "total_blocks": 0,
        "is_unclassified": True,
    }


def minutes_to_hours(minutes):
    """분을 소수 첫째 자리까지 반올림한 시간으로 바꾼다."""
    return round(minutes / MINUTES_PER_HOUR, 1)
