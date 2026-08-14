from datetime import date

from apps.stats.aggregation.weekly_summary import build_weekly_summary


def monthly_stats(daily_totals, tag_daily=None, start=date(2026, 7, 1)):
    """July 2026 starts on a Wednesday, so the first bucket is a 5-day stub."""
    total_days = len(daily_totals)
    tag_stats = []
    if tag_daily:
        for name, hours in tag_daily.items():
            tag_stats.append(
                {"name": name, "daily_hours": hours, "total_hours": round(sum(hours), 1)}
            )
    return {
        "start_date": start,
        "end_date": date(start.year, start.month, total_days),
        "total_days": total_days,
        "daily_totals": daily_totals,
        "tag_stats": tag_stats,
    }


class TestWeekBoundaries:
    def test_month_is_cut_into_calendar_weeks(self):
        rows = build_weekly_summary(monthly_stats([1.0] * 31))

        assert [r["start"].day for r in rows] == [1, 6, 13, 20, 27]

    def test_a_stub_week_reports_its_own_length(self):
        rows = build_weekly_summary(monthly_stats([1.0] * 31))

        assert rows[0]["days"] == 5
        assert rows[1]["days"] == 7

    def test_the_last_bucket_stops_at_the_month_end(self):
        rows = build_weekly_summary(monthly_stats([1.0] * 31))

        assert rows[-1]["end"] == date(2026, 7, 31)
        assert rows[-1]["days"] == 5


class TestWeekTotals:
    def test_recorded_hours_add_up_per_week(self):
        stats = monthly_stats([24.0] * 31, tag_daily={"집중 작업": [2.0] * 31})

        rows = build_weekly_summary(stats)

        assert rows[0]["hours"] == 10.0
        assert rows[1]["hours"] == 14.0

    def test_daily_average_divides_by_the_days_in_that_week(self):
        stats = monthly_stats([24.0] * 31, tag_daily={"집중 작업": [2.0] * 31})

        rows = build_weekly_summary(stats)

        assert rows[0]["avg_hours"] == 2.0


class TestFocusTagColumn:
    def test_the_column_follows_the_months_top_tag(self):
        stats = monthly_stats(
            [2.0] * 31,
            tag_daily={"집중 작업": [1.0] * 31, "여가": [0.5] * 31},
        )

        rows = build_weekly_summary(stats)

        assert rows[0]["top_tag_name"] == "집중 작업"
        assert rows[0]["top_tag_hours"] == 5.0

    def test_no_tags_means_no_focus_column(self):
        rows = build_weekly_summary(monthly_stats([2.0] * 31))

        assert rows[0]["top_tag_name"] is None


class TestDelta:
    def test_the_first_week_has_nothing_to_compare_against(self):
        stats = monthly_stats([2.0] * 31, tag_daily={"집중 작업": [1.0] * 31})

        rows = build_weekly_summary(stats)

        assert rows[0]["delta"] is None

    def test_later_weeks_compare_the_focus_tag_to_the_week_before(self):
        focus = [1.0] * 5 + [2.0] * 7 + [1.0] * 19
        stats = monthly_stats([3.0] * 31, tag_daily={"집중 작업": focus})

        rows = build_weekly_summary(stats)

        assert rows[1]["delta"] == 9.0

    def test_a_week_holding_today_is_still_running(self):
        stats = monthly_stats([2.0] * 31, tag_daily={"집중 작업": [1.0] * 31})

        rows = build_weekly_summary(stats, today=date(2026, 7, 29))

        assert rows[-1]["in_progress"] is True
        assert rows[0]["in_progress"] is False

    def test_a_finished_month_has_no_running_week(self):
        stats = monthly_stats([2.0] * 31, tag_daily={"집중 작업": [1.0] * 31})

        rows = build_weekly_summary(stats, today=date(2026, 8, 10))

        assert all(not r["in_progress"] for r in rows)


class TestUnrecordedTimeIsNotCounted:
    """`daily_totals` 에는 미분류 채움이 섞여 있어 하루가 늘 24h 가 된다.

    기록 열은 태그가 붙은 시간만 세야 한다. 아니면 기록이 없는 미래 주까지
    24h 로 보고된다.
    """

    def test_weeks_report_tagged_hours_not_a_full_day(self):
        stats = monthly_stats(
            [24.0] * 31,
            tag_daily={"집중 작업": [2.0] * 5 + [0.0] * 26},
        )

        rows = build_weekly_summary(stats)

        assert rows[0]["hours"] == 10.0
        assert rows[1]["hours"] == 0.0

    def test_focus_hours_stay_a_float(self):
        stats = monthly_stats([24.0] * 31, tag_daily={"집중 작업": [0.0] * 31})

        rows = build_weekly_summary(stats)

        assert isinstance(rows[0]["top_tag_hours"], float)
