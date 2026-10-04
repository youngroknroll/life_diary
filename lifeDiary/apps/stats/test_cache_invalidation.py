from datetime import date

import pytest
from django.core.cache import cache

from apps.dashboard.commands import UpsertTimeBlocksCommand
from apps.dashboard.repositories import TimeBlockRepository
from apps.dashboard.use_cases import UpsertTimeBlocksUseCase
from apps.stats.use_cases import GetStatsContextUseCase
from apps.tags.models import Category, Tag
from apps.tags.repositories import TagRepository

SELECTED_DATE = date(2026, 8, 15)
OTHER_DATE_IN_SELECTED_WEEK = date(2026, 8, 13)


@pytest.fixture
def stats_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "stats-cache-invalidation-tests",
        }
    }
    cache.clear()
    yield cache
    cache.clear()


@pytest.fixture
def owner(make_user):
    return make_user(username="cacheowner")


@pytest.fixture
def focus_tag(owner):
    return Tag.objects.create(
        user=owner, name="집중", category=Category.objects.get(slug="investment")
    )


def test_committed_slot_change_on_another_date_refreshes_cached_week(
    stats_cache, owner, focus_tag, django_capture_on_commit_callbacks
):
    use_case = GetStatsContextUseCase()
    before = use_case.execute(owner, SELECTED_DATE)
    assert before.context["weekly_stats"]["week_total_hours"] == 0.0

    with django_capture_on_commit_callbacks(execute=True):
        UpsertTimeBlocksUseCase(
            writer=TimeBlockRepository(), tags=TagRepository()
        ).execute(
            UpsertTimeBlocksCommand(
                user_id=owner.id,
                target_date=OTHER_DATE_IN_SELECTED_WEEK,
                slot_indexes=[0],
                tag_id=focus_tag.id,
                memo="",
            ),
            owner,
        )

    after = use_case.execute(owner, SELECTED_DATE)
    assert after.cache_hit is False
    assert after.context["weekly_stats"]["week_total_hours"] == 0.2
