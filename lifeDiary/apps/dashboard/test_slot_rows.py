"""24행 × 6열 그리드의 run 병합 규칙."""

import pytest

from apps.dashboard.services import build_slot_rows


class FakeTag:
    def __init__(self, tag_id, name, color="#4E8F63"):
        self.id = tag_id
        self.name = name
        self.color = color


@pytest.fixture
def focus():
    return FakeTag(1, "집중 작업")


@pytest.fixture
def meal():
    return FakeTag(2, "식사", "#C99A2E")


def slot(tag, memo=""):
    return {"tag": tag, "memo": memo, "id": None}


def find_row(rows, hour):
    return next(row for row in rows if row["hour"] == hour)


def test_returns_24_rows_of_one_hour_each():
    rows = build_slot_rows({})

    assert len(rows) == 24
    assert [row["hour"] for row in rows] == list(range(24))


def test_empty_day_renders_one_empty_run_per_row():
    rows = build_slot_rows({})

    for row in rows:
        assert len(row["runs"]) == 1
        run = row["runs"][0]
        assert run["tag"] is None
        assert run["span"] == 6
        assert run["label"] == ""


def test_consecutive_same_tag_slots_merge_into_one_run(focus):
    slot_data = {index: slot(focus) for index in range(54, 60)}

    row = find_row(build_slot_rows(slot_data), 9)

    assert len(row["runs"]) == 1
    assert row["runs"][0]["tag"] is focus
    assert row["runs"][0]["span"] == 6
    assert row["runs"][0]["start_index"] == 54


def test_different_tags_do_not_merge(focus, meal):
    slot_data = {54 + 18 + i: slot(meal) for i in range(3)}
    slot_data.update({72 + 3 + i: slot(focus) for i in range(3)})

    row = find_row(build_slot_rows(slot_data), 12)

    assert [run["span"] for run in row["runs"]] == [3, 3]
    assert [run["tag"] for run in row["runs"]] == [meal, focus]


def test_runs_never_cross_an_hour_boundary(focus):
    slot_data = {index: slot(focus) for index in range(57, 63)}

    rows = build_slot_rows(slot_data)

    assert [run["span"] for run in find_row(rows, 9)["runs"]] == [3, 3]
    assert [run["span"] for run in find_row(rows, 10)["runs"]] == [3, 3]


def test_empty_gaps_become_empty_runs(focus):
    slot_data = {48: slot(focus), 49: slot(focus)}

    row = find_row(build_slot_rows(slot_data), 8)

    assert [(run["span"], run["tag"] is None) for run in row["runs"]] == [
        (2, False),
        (4, True),
    ]


def test_label_appears_only_from_three_slots(focus):
    short = {0: slot(focus), 1: slot(focus)}
    long = {6: slot(focus), 7: slot(focus), 8: slot(focus)}

    assert find_row(build_slot_rows(short), 0)["runs"][0]["label"] == ""
    assert find_row(build_slot_rows(long), 1)["runs"][0]["label"] == "집중 작업"


def test_multi_hour_stretch_labels_only_the_first_row(focus):
    slot_data = {index: slot(focus) for index in range(54, 66)}

    rows = build_slot_rows(slot_data)

    assert find_row(rows, 9)["runs"][0]["label"] == "집중 작업"
    assert find_row(rows, 10)["runs"][0]["label"] == ""


def test_stretch_labels_first_row_that_is_wide_enough(focus):
    """첫 행 조각이 3칸 미만이면 라벨이 통째로 사라지면 안 된다.

    13:40–15:00 은 13시 행에서 2칸뿐이라 그 행에는 라벨을 넣을 수 없다.
    이때는 폭이 충분한 첫 행(14시)이 라벨을 받는다.
    """
    slot_data = {index: slot(focus) for index in range(82, 90)}

    rows = build_slot_rows(slot_data)

    assert find_row(rows, 13)["runs"][-1]["label"] == ""
    assert find_row(rows, 14)["runs"][0]["label"] == "집중 작업"
    assert find_row(rows, 15)["runs"][0]["label"] == ""


def test_same_tag_in_separate_stretches_labels_each(focus):
    slot_data = {index: slot(focus) for index in (54, 55, 56, 60, 61, 62)}

    rows = build_slot_rows(slot_data)

    assert find_row(rows, 9)["runs"][0]["label"] == "집중 작업"
    assert find_row(rows, 10)["runs"][0]["label"] == "집중 작업"


def test_run_carries_memo_and_slot_range(focus):
    slot_data = {index: slot(focus, memo="회고") for index in range(54, 57)}

    run = find_row(build_slot_rows(slot_data), 9)["runs"][0]

    assert run["start_index"] == 54
    assert run["span"] == 3
    assert run["memo"] == "회고"


def test_memo_difference_does_not_split_a_run(focus):
    """병합 기준은 태그다. 메모는 첫 칸의 것을 대표로 싣는다."""
    slot_data = {54: slot(focus, "a"), 55: slot(focus, "b"), 56: slot(focus, "b")}

    row = find_row(build_slot_rows(slot_data), 9)

    assert row["runs"][0]["span"] == 3
    assert row["runs"][0]["memo"] == "a"
