from __future__ import annotations

from datetime import date

from django.core.cache import cache

from .logic import get_stats_context

_PAST_TTL = 60 * 60 * 24   # 과거 날짜: 24시간
_TODAY_TTL = 60 * 5         # 오늘: 5분


def _cache_key(user_id: int, target_date: date) -> str:
    return f"stats:{user_id}:{target_date.isoformat()}"


class GetStatsContextUseCase:
    def execute(self, user, target_date: date) -> dict:
        key = _cache_key(user.id, target_date)
        cached = cache.get(key)
        if cached is not None:
            return cached

        context = get_stats_context(user, target_date)
        ttl = _PAST_TTL if target_date < date.today() else _TODAY_TTL
        cache.set(key, context, ttl)
        return context


def invalidate_stats_cache(user_id: int, target_date: date) -> None:
    cache.delete(_cache_key(user_id, target_date))
