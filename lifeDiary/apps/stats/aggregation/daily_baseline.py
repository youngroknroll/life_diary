"""하루 구성 표의 '7일 평균 대비' 열 (시안 3b).

기준일을 포함한 지난 7일의 태그별 하루 평균과, 기준일 실제 기록의 차이다.
"양이 는 건지 준 건지"를 한 숫자로 말해 준다.
"""

from datetime import timedelta

from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT
from apps.stats.aggregation.calculator import read_blocks

WINDOW_DAYS = 7


def get_tag_deltas_vs_week(user, selected_date, calculator=None):
    """{tag_id: 기준일 시간 − 7일 하루 평균} 을 돌려준다.

    미기록 구간은 태그가 없으므로 빠진다. 이 열은 태그가 붙은 시간만 다룬다.
    """
    window_start = selected_date - timedelta(days=WINDOW_DAYS - 1)
    blocks = read_blocks(user, window_start, selected_date, calculator)

    window_minutes = {}
    today_minutes = {}
    for block in blocks:
        if not block.tag:
            continue
        tag_id = block.tag_id
        window_minutes[tag_id] = window_minutes.get(tag_id, 0) + MINUTES_PER_SLOT
        if block.date == selected_date:
            today_minutes[tag_id] = today_minutes.get(tag_id, 0) + MINUTES_PER_SLOT

    deltas = {}
    for tag_id, total in window_minutes.items():
        average = total / WINDOW_DAYS / MINUTES_PER_HOUR
        actual = today_minutes.get(tag_id, 0) / MINUTES_PER_HOUR
        deltas[tag_id] = round(actual - average, 1)
    return deltas
