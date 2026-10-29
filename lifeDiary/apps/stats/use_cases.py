"""통계 화면 컨텍스트 조회, 캐시 세대 관리, 월간 엑셀 내보내기 유스케이스."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import date

from django.core.cache import cache
from django.utils import timezone
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
    """Eviction 뒤에도 새 token이 만들어져 옛 세대 key가 되살아나지 않는다.

    FileBasedCache의 incr()가 원자적이지 않아 숫자 증가 대신 무작위 값을 쓴다.
    """
    token = cache.get(_generation_key(user_id))
    if token is None:
        token = secrets.token_urlsafe(12)
        cache.set(_generation_key(user_id), token, timeout=None)
    return token


def rotate_stats_generation(user_id: int) -> None:
    """사용자의 통계 캐시 세대를 바꿔 이전 세대의 캐시 키를 모두 쓸 수 없게 한다."""
    cache.set(_generation_key(user_id), secrets.token_urlsafe(12), timeout=None)


def _cache_key(user_id: int, target_date: date, language: str | None = None) -> str:
    lang = language or get_language() or "default"
    generation = get_stats_generation(user_id)
    return f"stats:{user_id}:{generation}:{target_date.isoformat()}:{lang}:v5"


class ExportMonthlyWorkbookUseCase:
    """기록이 없는 달은 거절한다. 빈 워크북은 "기록이 사라졌다"로 읽힌다."""

    def available_months(self, user) -> list[tuple[int, int]]:
        """기록이 있는 (연, 월) 목록을 돌려준다."""
        dates = _time_block_repo.find_recorded_months(user)
        return [(item.year, item.month) for item in dates]

    def execute(self, user, year: int, month: int):
        """한 달 기록을 엑셀 워크북으로 만들어 (워크북, 파일명)으로 돌려준다.

        Raises:
            ValueError: 달이 1~12가 아니거나 그 달에 기록이 없을 때.
        """
        if not 1 <= month <= 12:
            raise ValueError(gettext("올바른 달이 아닙니다."))
        if (year, month) not in self.available_months(user):
            raise ValueError(gettext("그 달에는 기록이 없습니다."))

        book = build_monthly_workbook(user, year, month)
        return book, f"lifediary-{year:04d}-{month:02d}.xlsx"


@dataclass(frozen=True)
class StatsContextResult:
    """통계 컨텍스트와 캐시 적중 여부."""

    context: dict
    cache_hit: bool


class GetStatsContextUseCase:
    """통계 화면 컨텍스트를 캐시를 거쳐 돌려준다."""

    def execute(self, user, target_date: date) -> StatsContextResult:
        """캐시에 있으면 그 컨텍스트를, 없으면 집계해서 만든 컨텍스트를 돌려준다."""
        key = _cache_key(user.id, target_date)
        cached = cache.get(key)
        if cached is not None:
            return StatsContextResult(context=cached, cache_hit=True)

        context = get_stats_context(user, target_date)
        ttl = _PAST_TTL if target_date < timezone.localdate() else _TODAY_TTL
        cache.set(key, context, ttl)
        return StatsContextResult(context=context, cache_hit=False)
