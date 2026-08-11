from django.utils.translation import gettext

from apps.core.utils import HOURS_PER_DAY, SLOTS_PER_HOUR, TOTAL_SLOTS_PER_DAY


SLOT_START_MINUTES = [0, 10, 20, 30, 40, 50]

MIN_LABEL_SPAN = 3


def build_time_headers(slot_start_minutes=None):
    """분 눈금. 칸이 아니라 경계선을 가리키므로 6칸에 눈금은 7개다.

    마지막 `:60` 은 다음 시각의 `:00` 과 같은 선이다. 없으면 마지막 칸이
    어디서 끝나는지 축이 말해 주지 않는다.
    """
    minutes = slot_start_minutes or SLOT_START_MINUTES
    return [f":{minute:02d}" for minute in minutes] + [f":{minutes[-1] + 10:02d}"]


def build_slot_rows(slot_data):
    """슬롯 144개를 24행 × 6열로 묶고 같은 태그 연속 칸을 병합한다.

    빈 구간도 tag=None 인 run 으로 자리를 차지한다.
    """
    rows = [
        {"hour": hour, "runs": _merge_hour_runs(slot_data, hour)}
        for hour in range(HOURS_PER_DAY)
    ]
    _assign_labels(rows, slot_data)
    return rows


def serialize_rows(rows, hours=None):
    wanted = None if hours is None else set(hours)

    return [
        {
            "hour": row["hour"],
            "runs": [
                {
                    "start_index": run["start_index"],
                    "span": run["span"],
                    "tag_id": run["tag"].id if run["tag"] else None,
                    "tag_name": run["tag"].name if run["tag"] else None,
                    "color": run["tag"].color if run["tag"] else None,
                    "label": run["label"],
                    "memo": run["memo"],
                }
                for run in row["runs"]
            ],
        }
        for row in rows
        if wanted is None or row["hour"] in wanted
    ]


def hours_touched(slot_indexes):
    return sorted({index // SLOTS_PER_HOUR for index in slot_indexes})


def _merge_hour_runs(slot_data, hour):
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
    """구간마다 라벨은 한 번.

    폭이 3칸에 못 미치는 첫 행이 라벨을 가져가면 13:40–15:00 같은 구간의
    이름이 통째로 사라진다. 그래서 충분히 넓은 첫 행이 받는다.
    """
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
