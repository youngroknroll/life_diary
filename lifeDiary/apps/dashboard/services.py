from django.utils.translation import gettext

from apps.core.utils import HOURS_PER_DAY, SLOTS_PER_HOUR, TOTAL_SLOTS_PER_DAY


# 한 시간을 가르는 6칸의 시작 분. 그리드가 24행 × 6열이 되면서 헤더도
# 끝나는 분(10·20…60)이 아니라 시작하는 분을 가리킨다.
SLOT_START_MINUTES = [0, 10, 20, 30, 40, 50]

# 라벨을 넣을 최소 블록 폭. 3칸 = 30분.
MIN_LABEL_SPAN = 3


def build_time_headers(slot_start_minutes=None):
    """그리드 위 한 줄짜리 분 헤더. 6칸 고정."""
    minutes = slot_start_minutes or SLOT_START_MINUTES
    return [f":{minute:02d}" for minute in minutes]


def build_slot_rows(slot_data):
    """슬롯 144개를 24행 × 6열 그리드로 묶고 같은 태그 연속 칸을 병합한다.

    Args:
        slot_data: {슬롯 인덱스: {"tag": Tag|None, "memo": str, "id": int|None}}
            기록이 없는 슬롯은 키 자체가 없다.

    Returns:
        [{"hour": int, "runs": [run]}] 형태의 24개 행.
        run 은 {"start_index", "span", "tag", "memo", "label"}.
        빈 구간도 tag=None 인 run 으로 자리를 차지한다.

    라벨 규칙 — 블록이 3칸(30분) 이상일 때만 넣고, 여러 시간에 걸친 같은 태그
    구간은 한 번만 넣는다. 첫 행 조각이 3칸에 못 미치면 라벨이 통째로 사라지므로
    폭이 충분한 첫 행이 대신 받는다.
    """
    rows = [
        {"hour": hour, "runs": _merge_hour_runs(slot_data, hour)}
        for hour in range(HOURS_PER_DAY)
    ]
    _assign_labels(rows, slot_data)
    return rows


def _merge_hour_runs(slot_data, hour):
    """한 시간(6칸) 안에서 같은 태그가 이어지는 칸을 하나의 run 으로 묶는다."""
    runs = []
    first_index = hour * SLOTS_PER_HOUR

    for offset in range(SLOTS_PER_HOUR):
        slot_index = first_index + offset
        entry = slot_data.get(slot_index)
        tag = entry["tag"] if entry else None
        previous = runs[-1] if runs else None

        if previous is not None and _same_tag(previous["tag"], tag):
            previous["span"] += 1
            continue

        runs.append(
            {
                "start_index": slot_index,
                "span": 1,
                "tag": tag,
                "memo": entry["memo"] if entry else "",
                "label": "",
            }
        )

    return runs


def _assign_labels(rows, slot_data):
    """같은 태그 구간마다 라벨을 한 번씩만 붙인다."""
    labelled_stretches = set()

    for row in rows:
        for run in row["runs"]:
            if run["tag"] is None or run["span"] < MIN_LABEL_SPAN:
                continue

            stretch_start = _stretch_start(slot_data, run["start_index"])
            if stretch_start in labelled_stretches:
                continue

            labelled_stretches.add(stretch_start)
            run["label"] = run["tag"].name


def _stretch_start(slot_data, slot_index):
    """시간 경계를 넘어 이어지는 같은 태그 구간의 첫 슬롯 인덱스."""
    tag = slot_data[slot_index]["tag"]
    start = slot_index

    while start > 0:
        previous = slot_data.get(start - 1)
        if previous is None or not _same_tag(previous["tag"], tag):
            break
        start -= 1

    return start


def _same_tag(left, right):
    if left is None or right is None:
        return left is right
    return left.id == right.id


def validate_slot_indexes(slot_indexes):
    return isinstance(slot_indexes, list) and all(
        isinstance(slot_index, int) and 0 <= slot_index < TOTAL_SLOTS_PER_DAY
        for slot_index in slot_indexes
    )
