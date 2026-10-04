from datetime import date

import pytest
from django.core.cache import cache
from django.db import transaction

from apps.dashboard.commands import UpsertTimeBlocksCommand
from apps.dashboard.models import TimeBlock
from apps.dashboard.repositories import TimeBlockRepository
from apps.dashboard.use_cases import UpsertTimeBlocksUseCase
from apps.stats.use_cases import GetStatsContextUseCase
from apps.tags.models import Category, Tag
from apps.tags.repositories import TagRepository
from apps.tags.use_cases import UpdateTagUseCase
from apps.users.use_cases import GoalData, NoteData, SaveGoalUseCase, SaveNoteUseCase

class ForcedRollback(Exception):
    pass


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


def test_committed_goal_change_refreshes_cached_statistics(
    stats_cache, owner, focus_tag, django_capture_on_commit_callbacks
):
    use_case = GetStatsContextUseCase()
    before = use_case.execute(owner, SELECTED_DATE)
    assert before.context["goal_progress_rows"] == []

    with django_capture_on_commit_callbacks(execute=True):
        SaveGoalUseCase().execute(
            GoalData(tag_id=focus_tag.id, period="weekly", target_hours=5), owner
        )

    after = use_case.execute(owner, SELECTED_DATE)
    assert after.cache_hit is False
    assert [row["tag_name"] for row in after.context["goal_progress_rows"]] == ["집중"]


def test_committed_note_change_refreshes_cached_statistics(
    stats_cache, owner, django_capture_on_commit_callbacks
):
    SaveNoteUseCase().execute(NoteData(note="옛 메모"), owner)
    use_case = GetStatsContextUseCase()
    before = use_case.execute(owner, SELECTED_DATE)
    assert before.context["user_note"].note == "옛 메모"

    with django_capture_on_commit_callbacks(execute=True):
        SaveNoteUseCase().execute(NoteData(note="새 메모"), owner)

    after = use_case.execute(owner, SELECTED_DATE)
    assert after.cache_hit is False
    assert after.context["user_note"].note == "새 메모"


def test_committed_tag_change_refreshes_cached_statistics(
    stats_cache, owner, focus_tag, django_capture_on_commit_callbacks
):
    TimeBlock.objects.create(
        user=owner, date=SELECTED_DATE, slot_index=0, tag=focus_tag
    )
    use_case = GetStatsContextUseCase()
    before = use_case.execute(owner, SELECTED_DATE)
    assert "집중" in [e["name"] for e in before.context["daily_stats"]["tag_stats"]]

    with django_capture_on_commit_callbacks(execute=True):
        UpdateTagUseCase().execute(
            owner,
            focus_tag.id,
            name="몰입",
            color=focus_tag.color,
            category_id=focus_tag.category_id,
        )

    after = use_case.execute(owner, SELECTED_DATE)
    assert after.cache_hit is False
    names_after = [e["name"] for e in after.context["daily_stats"]["tag_stats"]]
    assert "몰입" in names_after
    assert "집중" not in names_after


def test_rolled_back_slot_change_keeps_serving_cached_statistics(
    stats_cache, owner, focus_tag, django_capture_on_commit_callbacks
):
    use_case = GetStatsContextUseCase()
    use_case.execute(owner, SELECTED_DATE)

    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(ForcedRollback):
            with transaction.atomic():
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
                raise ForcedRollback()

    assert use_case.execute(owner, SELECTED_DATE).cache_hit is True
