from datetime import date

from django.core.cache import cache

from apps.dashboard.signals import time_blocks_changed
from apps.stats.use_cases import _cache_key


def test_time_block_change_invalidates_stats_cache():
    """대시보드 슬롯 기록이 바뀌면 해당 사용자·날짜의 통계 캐시가 비워진다."""
    user_id = 987654
    target_date = date(2026, 7, 18)
    for lang in ("ko", "en", "default"):
        cache.set(_cache_key(user_id, target_date, language=lang), {"cached": lang}, 60)

    time_blocks_changed.send(sender=None, user_id=user_id, target_date=target_date)

    for lang in ("ko", "en", "default"):
        assert cache.get(_cache_key(user_id, target_date, language=lang)) is None
