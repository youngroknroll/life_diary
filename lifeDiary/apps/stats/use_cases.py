from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date

from django.core.cache import cache
from django.utils.translation import get_language, gettext

from apps.dashboard.repositories import TimeBlockRepository

from .export import build_monthly_workbook
from .logic import get_stats_context

_time_block_repo = TimeBlockRepository()

_PAST_TTL = 60 * 60 * 24   # 과거 날짜: 24시간
_TODAY_TTL = 60 * 5         # 오늘: 5분


def _generation_key(user_id: int) -> str:
    return f"stats-generation:{user_id}"


def get_stats_generation(user_id: int) -> str:
    """eviction 뒤에도 새 token이 만들어져 옛 세대 key가 되살아나지 않는다.

    FileBasedCache의 incr()가 원자적이지 않아 숫자 증가 대신 무작위 값을 쓴다.
    """
    token = cache.get(_generation_key(user_id))
    if token is None:
        token = secrets.token_urlsafe(12)
        cache.set(_generation_key(user_id), token, timeout=None)
    return token


def rotate_stats_generation(user_id: int) -> None:
    cache.set(_generation_key(user_id), secrets.token_urlsafe(12), timeout=None)


def _cache_key(user_id: int, target_date: date, language: str | None = None) -> str:
    lang = language or get_language() or "default"
    generation = get_stats_generation(user_id)
    return f"stats:{user_id}:{generation}:{target_date.isoformat()}:{lang}:v3"


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


@dataclass(frozen=True)
class StatsContextResult:
    context: dict
    cache_hit: bool


class GetStatsContextUseCase:
    def execute(self, user, target_date: date) -> StatsContextResult:
        key = _cache_key(user.id, target_date)
        cached = cache.get(key)
        if cached is not None:
            return StatsContextResult(context=cached, cache_hit=True)

        context = get_stats_context(user, target_date)
        ttl = _PAST_TTL if target_date < date.today() else _TODAY_TTL
        cache.set(key, context, ttl)
        return StatsContextResult(context=context, cache_hit=False)
