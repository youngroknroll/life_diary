from __future__ import annotations

from datetime import date

from django.core.cache import cache
from django.utils.translation import get_language, gettext

from apps.dashboard.repositories import TimeBlockRepository

from .export import build_monthly_workbook
from .logic import get_stats_context

_time_block_repo = TimeBlockRepository()

_PAST_TTL = 60 * 60 * 24   # 과거 날짜: 24시간
_TODAY_TTL = 60 * 5         # 오늘: 5분


def _cache_key(user_id: int, target_date: date, language: str | None = None) -> str:
    lang = language or get_language() or "default"
    return f"stats:{user_id}:{target_date.isoformat()}:{lang}:v2"


class ExportMonthlyWorkbookUseCase:
    """기록이 없는 달은 거절한다. 빈 워크북은 "기록이 사라졌다"로 읽힌다."""

    def available_months(self, user) -> list[tuple[int, int]]:
        dates = _time_block_repo.find_recorded_months(user)
        return [(item.year, item.month) for item in dates]

    def execute(self, user, year: int, month: int):
        if not 1 <= month <= 12:
            raise ValueError(gettext("올바른 달이 아닙니다."))
        if (year, month) not in self.available_months(user):
            raise ValueError(gettext("그 달에는 기록이 없습니다."))

        book = build_monthly_workbook(user, year, month)
        return book, f"lifediary-{year:04d}-{month:02d}.xlsx"


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
    for lang in ("ko", "en", "default"):
        cache.delete(_cache_key(user_id, target_date, language=lang))
