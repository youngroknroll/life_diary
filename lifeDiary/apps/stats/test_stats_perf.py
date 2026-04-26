"""
통계 탭 성능 회귀 테스트.

목적:
- StatsCalculator의 월간 데이터 lazy 캐시 동작 보장
- get_stats_context의 쿼리 수가 목표치(<=8) 이하 유지

실행:
    conda run -n knou-life-diary python -m pytest apps/stats/test_stats_perf.py -v
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.dashboard.models import TimeBlock
from apps.stats.aggregation.calculator import StatsCalculator
from apps.stats.logic import get_stats_context
from apps.tags.models import Category, Tag

# 베이스라인(2026-04-26) 측정치 10에서 중복 2건 제거가 목표.
TARGET_MAX_QUERIES = 8


@pytest.fixture
def seeded_user(db, django_user_model, settings):
    settings.DEBUG = True  # connection.queries 활성화
    user = django_user_model.objects.create_user(username="perf_user", password="x")

    category = Category.objects.create(
        name="벤치카테고리",
        slug="bench_cat",
        color="#112233",
        display_order=999,
    )
    tags = [
        Tag.objects.create(user=user, name=f"tag_{i}", color="#abcdef", category=category)
        for i in range(5)
    ]

    today = date(2026, 4, 15)
    start = today.replace(day=1)
    blocks = []
    for day_offset in range(30):
        d = start + timedelta(days=day_offset)
        for slot in range(0, 144, 2):
            tag = tags[(day_offset + slot) % len(tags)]
            blocks.append(TimeBlock(user=user, date=d, slot_index=slot, tag=tag, memo=""))
    TimeBlock.objects.bulk_create(blocks)
    return user, today


def test_get_monthly_blocks_caches_repeated_calls(seeded_user):
    """get_monthly_blocks를 두 번 호출해도 DB 쿼리는 1번만 발생해야 한다."""
    user, today = seeded_user
    calc = StatsCalculator(user, today)

    with CaptureQueriesContext(connection) as ctx:
        first = calc.get_monthly_blocks()
        second = calc.get_monthly_blocks()

    assert len(ctx.captured_queries) == 1, (
        f"두 번 호출했지만 {len(ctx.captured_queries)}개 쿼리가 발생함"
    )
    assert list(first) == list(second)


def test_get_monthly_daily_counts_caches_repeated_calls(seeded_user):
    """get_monthly_daily_counts를 두 번 호출해도 DB 쿼리는 1번만 발생해야 한다."""
    user, today = seeded_user
    calc = StatsCalculator(user, today)

    with CaptureQueriesContext(connection) as ctx:
        first = calc.get_monthly_daily_counts()
        second = calc.get_monthly_daily_counts()

    assert len(ctx.captured_queries) == 1, (
        f"두 번 호출했지만 {len(ctx.captured_queries)}개 쿼리가 발생함"
    )
    assert first == second


def test_get_stats_context_query_count_within_target(seeded_user):
    """get_stats_context 1회 호출 시 총 쿼리 수가 목표치 이하여야 한다 (베이스라인 10 → 8)."""
    user, today = seeded_user
    # 워밍업 (import 등 부수 비용 제외)
    get_stats_context(user, today)

    with CaptureQueriesContext(connection) as ctx:
        get_stats_context(user, today)

    n = len(ctx.captured_queries)
    assert n <= TARGET_MAX_QUERIES, (
        f"쿼리 수 {n}개로 목표 {TARGET_MAX_QUERIES}개 초과. "
        f"쿼리 내역:\n" + "\n".join(f"  {i}: {q['sql'][:120]}" for i, q in enumerate(ctx.captured_queries))
    )


def test_monthly_and_analysis_results_unchanged_under_caching(seeded_user):
    """월간 캐싱 후에도 monthly_stats와 tag_analysis 결과가 유지되어야 한다 (회귀 방지)."""
    user, today = seeded_user
    ctx = get_stats_context(user, today)

    monthly = ctx["monthly_stats"]
    analysis = ctx["tag_analysis"]

    # 시드: 30일 × 72블록(절반), 5개 태그가 라운드로빈으로 부착됨
    assert monthly["total_days"] == 30
    assert len(monthly["day_labels"]) == 30
    assert len(monthly["daily_totals"]) == 30
    assert monthly["total_hours"] > 0

    # 5개 사용자 태그가 모두 노출되어야 함 (UNCLASSIFIED 제외)
    tag_names = {t["name"] for t in monthly["tag_stats"]}
    assert tag_names == {f"tag_{i}" for i in range(5)}

    # 분석 탭에서도 동일한 5개 태그
    analysis_names = {t["name"] for t in analysis}
    assert analysis_names == {f"tag_{i}" for i in range(5)}

    # 일별 합계가 음수가 되거나 24시간을 초과해선 안 됨
    for hours in monthly["daily_totals"]:
        assert 0 <= hours <= 24
