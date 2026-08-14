"""하루 구성 표의 '7일 평균 대비' 열 (시안 3b).

기준일을 포함한 지난 7일의 태그별 하루 평균과, 기준일 실제 기록의 차이다.
"양이 는 건지 준 건지"를 한 숫자로 말해 준다.
"""

from datetime import timedelta

from apps.core.utils import MINUTES_PER_HOUR, MINUTES_PER_SLOT
from apps.dashboard.repositories import TimeBlockRepository

WINDOW_DAYS = 7

_time_block_repo = TimeBlockRepository()


def get_tag_deltas_vs_week(user, selected_date):
    """{태그명: 기준일 시간 − 7일 하루 평균} 을 돌려준다.

    미기록 구간은 태그가 없으므로 빠진다. 이 열은 태그가 붙은 시간만 다룬다.
    """
    window_start = selected_date - timedelta(days=WINDOW_DAYS - 1)
    blocks = _time_block_repo.find_by_date_range(user, window_start, selected_date)

    window_minutes = {}
    today_minutes = {}
    for block in blocks:
        if not block.tag:
            continue
        name = block.tag.name
        window_minutes[name] = window_minutes.get(name, 0) + MINUTES_PER_SLOT
        if block.date == selected_date:
            today_minutes[name] = today_minutes.get(name, 0) + MINUTES_PER_SLOT

    deltas = {}
    for name, total in window_minutes.items():
        average = total / WINDOW_DAYS / MINUTES_PER_HOUR
        actual = today_minutes.get(name, 0) / MINUTES_PER_HOUR
        deltas[name] = round(actual - average, 1)
    return deltas
