from datetime import date

import pytest
from django.core.cache import cache

from apps.dashboard.models import TimeBlock
from apps.stats.use_cases import GetStatsContextUseCase
from apps.tags.models import Category, Tag

LOCMEM_CACHE_BACKEND = "django.core.cache.backends.locmem.LocMemCache"
STATS_DATE = date(2026, 4, 15)


@pytest.fixture
def recorded_user(make_user):
    user = make_user(username="timing_user")
    category = Category.objects.create(
        name="타이밍", slug="timing_cat", color="#112233", display_order=998
    )
    tag = Tag.objects.create(user=user, name="work", color="#abcdef", category=category)
    TimeBlock.objects.create(user=user, date=STATS_DATE, slot_index=0, tag=tag, memo="")
    return user


def test_second_stats_context_lookup_is_a_cache_hit(recorded_user, settings):
    settings.CACHES = {
        "default": {"BACKEND": LOCMEM_CACHE_BACKEND, "LOCATION": "server-timing-use-case"}
    }
    cache.clear()

    first = GetStatsContextUseCase().execute(recorded_user, STATS_DATE)
    second = GetStatsContextUseCase().execute(recorded_user, STATS_DATE)

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.context == first.context
