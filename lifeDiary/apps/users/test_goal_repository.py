"""
GoalRepository 단위 테스트 — find_grouped_by_period 동작 검증.

목적:
- period별 3회 쿼리 → 1회 쿼리 통합 (성능 최적화)
- 모든 period 키가 존재하는지 보장 (빈 리스트 기본값)
"""
from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.tags.models import Category, Tag
from apps.users.models import UserGoal
from apps.users.repositories import GoalRepository


@pytest.fixture
def user_with_goals(db, django_user_model):
    user = django_user_model.objects.create_user(username="goal_user", password="x")
    category = Category.objects.create(
        name="목표카테고리", slug="goal_cat", color="#aaaaaa", display_order=998,
    )
    tag = Tag.objects.create(user=user, name="목표태그", color="#bbbbbb", category=category)

    UserGoal.objects.create(user=user, tag=tag, period="daily", target_hours=2.0)
    UserGoal.objects.create(user=user, tag=tag, period="daily", target_hours=1.0)
    UserGoal.objects.create(user=user, tag=tag, period="weekly", target_hours=10.0)
    # monthly 의도적으로 비움 — 빈 리스트 기본값 보장 검증용
    return user


def test_find_grouped_by_period_returns_all_keys(user_with_goals, settings):
    """daily/weekly/monthly 키가 모두 존재해야 한다 (없는 period는 빈 리스트)."""
    settings.DEBUG = True
    repo = GoalRepository()

    grouped = repo.find_grouped_by_period(user_with_goals)

    assert set(grouped.keys()) == {"daily", "weekly", "monthly"}
    assert len(grouped["daily"]) == 2
    assert len(grouped["weekly"]) == 1
    assert grouped["monthly"] == []


def test_find_grouped_by_period_uses_single_query(user_with_goals, settings):
    """1회 호출 시 DB 쿼리는 1번만 발생해야 한다."""
    settings.DEBUG = True
    repo = GoalRepository()

    with CaptureQueriesContext(connection) as ctx:
        grouped = repo.find_grouped_by_period(user_with_goals)
        # 결과 evaluation까지 포함 (lazy queryset 방지)
        for goals in grouped.values():
            list(goals)

    assert len(ctx.captured_queries) == 1, (
        f"1쿼리 기대했지만 {len(ctx.captured_queries)}개 발생함"
    )


def test_find_grouped_by_period_isolates_users(db, django_user_model):
    """다른 사용자의 목표는 포함되지 않아야 한다."""
    user_a = django_user_model.objects.create_user(username="user_a", password="x")
    user_b = django_user_model.objects.create_user(username="user_b", password="x")
    category = Category.objects.create(
        name="격리카테고리", slug="iso_cat", color="#cccccc", display_order=997,
    )
    tag_a = Tag.objects.create(user=user_a, name="A태그", color="#dddddd", category=category)
    tag_b = Tag.objects.create(user=user_b, name="B태그", color="#eeeeee", category=category)
    UserGoal.objects.create(user=user_a, tag=tag_a, period="daily", target_hours=1.0)
    UserGoal.objects.create(user=user_b, tag=tag_b, period="daily", target_hours=2.0)

    grouped = GoalRepository().find_grouped_by_period(user_a)

    assert len(grouped["daily"]) == 1
    assert grouped["daily"][0].tag.name == "A태그"
