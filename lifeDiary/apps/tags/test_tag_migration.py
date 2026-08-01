"""태그를 옮기고 지우기.

기록이 붙은 태그를 그냥 지우면 그 구간이 미기록으로 되돌아가 통계 수치가
조용히 바뀐다. 옮길 곳을 받아 기록을 살린 뒤 지운다.
"""

from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.tags.models import Category, Tag
from apps.tags.use_cases import DeleteTagUseCase


TARGET = date(2026, 8, 1)


@pytest.fixture
def user(make_user):
    return make_user(username="migrateuser")


@pytest.fixture
def source(user):
    return Tag.objects.create(
        user=user, name="회의", is_default=False,
        category=Category.objects.get(slug="investment"),
    )


@pytest.fixture
def destination(user):
    return Tag.objects.create(
        user=user, name="집중 작업", is_default=False,
        category=Category.objects.get(slug="investment"),
    )


def record(user, tag, count=3):
    for slot_index in range(count):
        TimeBlock.objects.create(
            user=user, date=TARGET, slot_index=slot_index, tag=tag
        )


@pytest.mark.django_db
class TestDeleteWithMigration:
    def test_blocks_move_to_the_destination_tag(self, user, source, destination):
        record(user, source, count=3)

        DeleteTagUseCase().execute(user, source.id, move_to_id=destination.id)

        assert TimeBlock.objects.filter(user=user, tag=destination).count() == 3

    def test_the_source_tag_is_gone(self, user, source, destination):
        record(user, source)

        DeleteTagUseCase().execute(user, source.id, move_to_id=destination.id)

        assert not Tag.objects.filter(pk=source.pk).exists()

    def test_no_block_is_left_behind(self, user, source, destination):
        record(user, source, count=3)

        DeleteTagUseCase().execute(user, source.id, move_to_id=destination.id)

        assert TimeBlock.objects.filter(user=user).count() == 3

    def test_other_tags_are_untouched(self, user, source, destination):
        record(user, source, count=2)
        other = Tag.objects.create(
            user=user, name="식사", is_default=False,
            category=Category.objects.get(slug="basic_life"),
        )
        TimeBlock.objects.create(user=user, date=TARGET, slot_index=50, tag=other)

        DeleteTagUseCase().execute(user, source.id, move_to_id=destination.id)

        assert TimeBlock.objects.filter(user=user, tag=other).count() == 1

    def test_moving_to_a_stranger_tag_is_refused(self, user, source, make_user):
        stranger = make_user(username="stranger")
        stranger_tag = Tag.objects.create(
            user=stranger, name="남의태그", is_default=False,
            category=Category.objects.get(slug="investment"),
        )
        record(user, source)

        with pytest.raises(ValueError):
            DeleteTagUseCase().execute(user, source.id, move_to_id=stranger_tag.id)

        assert Tag.objects.filter(pk=source.pk).exists()

    def test_moving_onto_itself_is_refused(self, user, source):
        record(user, source)

        with pytest.raises(ValueError):
            DeleteTagUseCase().execute(user, source.id, move_to_id=source.id)


@pytest.mark.django_db
class TestDeleteWithoutMigration:
    def test_an_unused_tag_deletes_outright(self, user, source):
        DeleteTagUseCase().execute(user, source.id)

        assert not Tag.objects.filter(pk=source.pk).exists()

    def test_deleting_a_used_tag_turns_its_blocks_unlogged(self, user, source):
        """옮길 곳을 주지 않으면 그 구간은 미기록으로 돌아간다."""
        record(user, source, count=3)

        DeleteTagUseCase().execute(user, source.id)

        assert TimeBlock.objects.filter(user=user, tag__isnull=True).count() == 3
