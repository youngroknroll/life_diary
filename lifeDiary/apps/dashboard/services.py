from django.utils.translation import gettext

from apps.core.utils import HOURS_PER_DAY, SLOTS_PER_HOUR, TOTAL_SLOTS_PER_DAY


SLOT_START_MINUTES = [0, 10, 20, 30, 40, 50]


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


def hours_to_refresh(slot_indexes):
    """라벨은 구간이 시작하는 블록에 붙으므로, 한 시간을 고치면 옆 시간의
    라벨이 따라 움직인다. 건드린 시간만 돌려주면 옛 라벨이 화면에 남는다.
    """
    touched = {index // SLOTS_PER_HOUR for index in slot_indexes}
    widened = {hour + offset for hour in touched for offset in (-1, 0, 1)}
    return sorted(hour for hour in widened if 0 <= hour < HOURS_PER_DAY)


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
    """구간마다 라벨은 한 번, 구간이 시작하는 블록에.

    좁은 블록에서는 이름이 잘려 보인다. 전체 이름은 블록의 title 에 남는다.
    """
    labelled_stretches = set()

    for row in rows:
        for run in row["runs"]:
            if run["tag"] is None:
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
