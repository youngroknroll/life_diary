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
