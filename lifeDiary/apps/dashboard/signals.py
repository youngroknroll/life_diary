from django.dispatch import Signal

# 슬롯 기록 생성/수정/삭제 후 발신된다. kwargs: user_id, target_date
# Why: stats 등 다른 앱이 dashboard를 구독하는 방향(stats -> dashboard)만
# 허용하기 위해 dashboard는 자신의 변경 사실만 알리고 구독자를 모른다.
time_blocks_changed = Signal()
