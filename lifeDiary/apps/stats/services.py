from django.utils.translation import gettext

from apps.core.utils import (
    DAYS_PER_WEEK,
    MINUTES_PER_HOUR,
    UNCLASSIFIED_TAG_COLOR,
    UNCLASSIFIED_TAG_NAME,
)


def _unclassified_display_name():
    return gettext("미분류")


def build_unclassified_daily_entry():
    return {
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "minutes": 0,
        "blocks": 0,
        "is_unclassified": True,
    }


def build_unclassified_weekly_entry(days=DAYS_PER_WEEK):
    return {
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "daily_minutes": [0] * days,
        "is_unclassified": True,
    }


def build_unclassified_monthly_entry(total_days):
    return {
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "daily_hours": [0] * total_days,
        "total_hours": 0,
        "is_unclassified": True,
    }


def build_unclassified_analysis_entry():
    return {
        "name": _unclassified_display_name(),
        "color": UNCLASSIFIED_TAG_COLOR,
        "total_minutes": 0,
        "total_blocks": 0,
        "is_unclassified": True,
    }


def minutes_to_hours(minutes):
    return round(minutes / MINUTES_PER_HOUR, 1)
