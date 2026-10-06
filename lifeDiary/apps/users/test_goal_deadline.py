"""목표 기한 상태 — 오늘 기준으로 기한이 얼마나 남았는가."""

from datetime import date, timedelta

import pytest

from apps.users.goal_deadline import deadline_state


TODAY = date(2026, 10, 6)


class TestDeadlineState:
    def test_a_goal_without_a_due_date_has_no_deadline(self):
        state = deadline_state(None, TODAY)

        assert state.state == "none"
        assert state.days is None

    @pytest.mark.parametrize("days_ahead", [1, 7])
    def test_a_future_due_date_counts_the_days_remaining(self, days_ahead):
        state = deadline_state(TODAY + timedelta(days=days_ahead), TODAY)

        assert state.state == "upcoming"
        assert state.days == days_ahead

    def test_a_due_date_of_today_is_due_today(self):
        state = deadline_state(TODAY, TODAY)

        assert state.state == "due_today"
        assert state.days == 0

    @pytest.mark.parametrize("days_past", [1, 5])
    def test_a_past_due_date_counts_the_days_overdue(self, days_past):
        state = deadline_state(TODAY - timedelta(days=days_past), TODAY)

        assert state.state == "overdue"
        assert state.days == days_past
