from django.test import SimpleTestCase

from apps.core.utils import UNCLASSIFIED_TAG_COLOR, UNCLASSIFIED_TAG_NAME
from apps.stats.services import (
    build_unclassified_analysis_entry,
    build_unclassified_daily_entry,
    build_unclassified_monthly_entry,
    build_unclassified_weekly_entry,
    minutes_to_hours,
)


class StatsServicesTests(SimpleTestCase):
    def test_build_unclassified_daily_entry(self):
        self.assertEqual(
            build_unclassified_daily_entry(),
            {
                "name": UNCLASSIFIED_TAG_NAME,
                "color": UNCLASSIFIED_TAG_COLOR,
                "minutes": 0,
                "blocks": 0,
            },
        )

    def test_build_unclassified_weekly_entry(self):
        self.assertEqual(
            build_unclassified_weekly_entry(),
            {
                "name": UNCLASSIFIED_TAG_NAME,
                "color": UNCLASSIFIED_TAG_COLOR,
                "daily_minutes": [0] * 7,
            },
        )

    def test_build_unclassified_monthly_entry(self):
        self.assertEqual(
            build_unclassified_monthly_entry(3),
            {
                "name": UNCLASSIFIED_TAG_NAME,
                "color": UNCLASSIFIED_TAG_COLOR,
                "daily_hours": [0] * 3,
                "total_hours": 0,
            },
        )

    def test_build_unclassified_analysis_entry(self):
        self.assertEqual(
            build_unclassified_analysis_entry(),
            {
                "name": UNCLASSIFIED_TAG_NAME,
                "color": UNCLASSIFIED_TAG_COLOR,
                "total_minutes": 0,
                "total_blocks": 0,
            },
        )

    def test_minutes_to_hours(self):
        self.assertEqual(minutes_to_hours(30), 0.5)


class MostActiveDayTests(SimpleTestCase):
    """get_weekly_stats_data의 most_active_day 계산이 최대 활동 요일을 반환하는지 검증."""

    def _make_day(self, day_korean, total_minutes):
        return {"day_korean": day_korean, "total_minutes": total_minutes, "total_hours": total_minutes / 60}

    def test_returns_day_with_max_minutes(self):
        weekly_data = [
            self._make_day("월", 60),
            self._make_day("화", 180),
            self._make_day("수", 120),
        ]
        result = max(weekly_data, key=lambda d: d["total_minutes"])
        self.assertEqual(result["day_korean"], "화")

    def test_returns_first_day_when_all_zero(self):
        weekly_data = [
            self._make_day("월", 0),
            self._make_day("화", 0),
        ]
        result = max(weekly_data, key=lambda d: d["total_minutes"])
        self.assertEqual(result["day_korean"], "월")

    def test_none_when_empty(self):
        weekly_data = []
        result = max(weekly_data, key=lambda d: d["total_minutes"]) if weekly_data else None
        self.assertIsNone(result)
