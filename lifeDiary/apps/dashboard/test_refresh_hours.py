"""변이 뒤 클라이언트가 다시 그려야 하는 시간대."""

import pytest

from apps.dashboard.services import hours_to_refresh


def test_refresh_hours_expand_by_one_hour_each_side():
    assert hours_to_refresh([34, 35]) == [4, 5, 6]


@pytest.mark.parametrize(
    ("slot_indexes", "expected"),
    [([0, 1], [0, 1]), ([142, 143], [22, 23])],
    ids=["start_of_day", "end_of_day"],
)
def test_refresh_hours_clamp_at_day_boundaries(slot_indexes, expected):
    assert hours_to_refresh(slot_indexes) == expected
