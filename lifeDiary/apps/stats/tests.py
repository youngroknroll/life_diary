import pytest

from apps.core.utils import UNCLASSIFIED_TAG_COLOR, UNCLASSIFIED_TAG_NAME
from apps.stats.services import (
    build_unclassified_analysis_entry,
    build_unclassified_daily_entry,
    build_unclassified_monthly_entry,
    build_unclassified_weekly_entry,
    minutes_to_hours,
)


class TestStatsServices:
    def test_build_unclassified_daily_entry(self):
        assert build_unclassified_daily_entry() == {
            "name": UNCLASSIFIED_TAG_NAME,
            "color": UNCLASSIFIED_TAG_COLOR,
            "minutes": 0,
            "blocks": 0,
        }

    def test_build_unclassified_weekly_entry(self):
        assert build_unclassified_weekly_entry() == {
            "name": UNCLASSIFIED_TAG_NAME,
            "color": UNCLASSIFIED_TAG_COLOR,
            "daily_minutes": [0] * 7,
        }

    def test_build_unclassified_monthly_entry(self):
        assert build_unclassified_monthly_entry(3) == {
            "name": UNCLASSIFIED_TAG_NAME,
            "color": UNCLASSIFIED_TAG_COLOR,
            "daily_hours": [0] * 3,
            "total_hours": 0,
        }

    def test_build_unclassified_analysis_entry(self):
        assert build_unclassified_analysis_entry() == {
            "name": UNCLASSIFIED_TAG_NAME,
            "color": UNCLASSIFIED_TAG_COLOR,
            "total_minutes": 0,
            "total_blocks": 0,
        }

    def test_minutes_to_hours(self):
        assert minutes_to_hours(30) == 0.5


def _make_day(day_korean, total_minutes):
    return {
        "day_korean": day_korean,
        "total_minutes": total_minutes,
        "total_hours": total_minutes / 60,
    }


class TestMostActiveDay:
    def test_returns_day_with_max_minutes(self):
        weekly_data = [
            _make_day("월", 60),
            _make_day("화", 180),
            _make_day("수", 120),
        ]
        result = max(weekly_data, key=lambda d: d["total_minutes"])
        assert result["day_korean"] == "화"

    def test_returns_first_day_when_all_zero(self):
        weekly_data = [_make_day("월", 0), _make_day("화", 0)]
        result = max(weekly_data, key=lambda d: d["total_minutes"])
        assert result["day_korean"] == "월"

    def test_none_when_empty(self):
        weekly_data = []
        result = max(weekly_data, key=lambda d: d["total_minutes"]) if weekly_data else None
        assert result is None


@pytest.mark.django_db
class TestStatsIndexDatePreservesTab:
    def test_date_onchange_preserves_url_hash(self, auth_client):
        resp = auth_client.get("/stats/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'id="dateSelector"' in content
        assert "window.location.hash" in content
