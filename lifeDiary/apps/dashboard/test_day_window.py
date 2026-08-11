"""아직 오지 않은 시간.

안 채운 것과 아직 올 수 없는 것은 다르다. 같은 회색으로 두면 아침 아홉 시의
빈 하루가 실패한 하루로 읽힌다.
"""

from datetime import date, datetime

import pytest

from apps.dashboard.day_window import (
    SLOTS_PER_HOUR,
    annotate_future,
    current_slot_index,
    future_column,
)


def rows_for_full_day():
    return [{"hour": hour, "runs": []} for hour in range(24)]


class TestCurrentSlotIndex:
    def test_today_has_a_now(self):
        now = datetime(2026, 8, 11, 10, 25)

        assert current_slot_index(date(2026, 8, 11), now) == 10 * SLOTS_PER_HOUR + 2

    def test_another_day_has_no_now(self):
        """어제에는 '지금'이 없다. 지난/미래를 나눌 기준도 없다."""
        now = datetime(2026, 8, 11, 10, 25)

        assert current_slot_index(date(2026, 8, 10), now) is None
        assert current_slot_index(date(2026, 8, 12), now) is None

    def test_midnight_is_the_first_slot(self):
        assert current_slot_index(date(2026, 8, 11), datetime(2026, 8, 11, 0, 0)) == 0


class TestAnnotateFuture:
    def test_each_row_learns_where_the_future_starts(self):
        rows = annotate_future(rows_for_full_day(), 10 * SLOTS_PER_HOUR + 2)

        assert rows[9]["future_from_col"] is None
        assert rows[10]["future_from_col"] == 2
        assert rows[11]["future_from_col"] == 0

    def test_the_original_rows_are_left_alone(self):
        original = rows_for_full_day()

        annotate_future(original, 10 * SLOTS_PER_HOUR)

        assert "future_from_col" not in original[0]

    def test_only_the_current_hour_carries_the_now_line(self):
        """경계선은 지금이 걸린 한 행에만 긋는다."""
        rows = annotate_future(rows_for_full_day(), 10 * SLOTS_PER_HOUR + 2)

        assert rows[10]["now_col"] == 2
        assert rows[9]["now_col"] is None
        assert rows[11]["now_col"] is None

    def test_a_past_day_has_no_now_line(self):
        rows = annotate_future(rows_for_full_day(), None)

        assert all(row["now_col"] is None for row in rows)

    def test_a_past_day_marks_nothing(self):
        rows = annotate_future(rows_for_full_day(), None)

        assert all(row["future_from_col"] is None for row in rows)


class TestFutureColumn:
    def test_hours_before_now_have_nothing_future(self):
        assert future_column(hour=9, current_slot_index=10 * SLOTS_PER_HOUR) is None

    def test_hours_after_now_are_future_from_the_first_column(self):
        assert future_column(hour=11, current_slot_index=10 * SLOTS_PER_HOUR) == 0

    def test_the_current_hour_splits_at_the_current_slot(self):
        # 10:20 → 10 시의 세 번째 칸부터가 아직 오지 않은 시간
        assert future_column(hour=10, current_slot_index=10 * SLOTS_PER_HOUR + 2) == 2

    def test_no_current_slot_means_no_future_shading(self):
        """오늘이 아닌 날에는 지난/미래를 나눌 기준이 없다."""
        assert future_column(hour=10, current_slot_index=None) is None
