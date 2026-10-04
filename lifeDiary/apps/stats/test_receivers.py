from datetime import date

import pytest
from django.core.cache import cache

from apps.dashboard.signals import time_blocks_changed
from apps.stats.use_cases import get_stats_generation


@pytest.fixture
def receiver_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "stats-receiver-tests",
        }
    }
    cache.clear()
    yield cache
    cache.clear()


def test_time_block_change_rotates_the_user_stats_generation(receiver_cache):
    """대시보드 슬롯 기록이 바뀌면 그 사용자의 통계 캐시 세대가 교체된다."""
    user_id = 987654
    generation_before = get_stats_generation(user_id)

    time_blocks_changed.send(
        sender=None, user_id=user_id, target_date=date(2026, 7, 18)
    )

    assert get_stats_generation(user_id) != generation_before
