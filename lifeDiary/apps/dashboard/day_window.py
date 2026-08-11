"""아직 오지 않은 시간.

안 채운 것과 아직 올 수 없는 것은 다르다. 같은 회색으로 두면 아침 아홉 시의
빈 하루가 실패한 하루로 읽힌다.
"""

SLOTS_PER_HOUR = 6


def current_slot_index(selected_date, now):
    """선택한 날이 오늘일 때만 '지금'이 있다.

    어제 화면에 "아직 오지 않은 시간"을 칠하면 거짓말이 된다. 그 시간은 이미
    지나갔고 비어 있을 뿐이다.
    """
    if selected_date != now.date():
        return None
    return now.hour * SLOTS_PER_HOUR + now.minute // 10


def annotate_future(rows, current_slot):
    """행마다 아직 오지 않은 시간이 시작하는 열을 붙인 새 목록.

    음영만으로는 경계가 읽히지 않는다 — 라이트 테마의 빈 칸은 이미 거의
    흰색이라 "더 연하게" 칠할 여지가 없다. 지금이 걸린 한 행에 경계선을
    그어 그 자리가 어디인지 분명히 한다.
    """
    now_hour = None if current_slot is None else current_slot // SLOTS_PER_HOUR

    return [
        {
            **row,
            "future_from_col": future_column(row["hour"], current_slot),
            "now_col": (
                future_column(row["hour"], current_slot)
                if row["hour"] == now_hour
                else None
            ),
        }
        for row in rows
    ]


def future_column(hour, current_slot_index):
    """이 시간대에서 아직 오지 않은 시간이 시작하는 열. 없으면 None."""
    if current_slot_index is None:
        return None

    row_start = hour * SLOTS_PER_HOUR
    if current_slot_index <= row_start:
        return 0
    if current_slot_index >= row_start + SLOTS_PER_HOUR:
        return None
    return current_slot_index - row_start
