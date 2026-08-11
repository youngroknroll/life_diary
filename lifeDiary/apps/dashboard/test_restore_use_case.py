"""직전 상태 복원 규칙."""

from datetime import date

import pytest

from apps.dashboard.commands import RestoreTimeBlocksCommand
from apps.dashboard.models import TimeBlock
from apps.dashboard.repositories import TimeBlockRepository
from apps.dashboard.use_cases import RestoreTimeBlocksUseCase
from apps.tags.models import Category, Tag
from apps.tags.repositories import TagRepository


TARGET = date(2026, 8, 1)


@pytest.fixture
def restore():
    return RestoreTimeBlocksUseCase(writer=TimeBlockRepository(), tags=TagRepository())


@pytest.fixture
def user(make_user):
    return make_user(username="restoreuser")


@pytest.fixture
def focus(user):
    return Tag.objects.create(
        user=user,
        name="집중",
        color="#4E8F63",
        category=Category.objects.get(slug="investment"),
    )


@pytest.fixture
def leisure(user):
    return Tag.objects.create(
        user=user,
        name="여가",
        color="#C1715A",
        category=Category.objects.get(slug="passive"),
    )


def command(slots):
    return RestoreTimeBlocksCommand(target_date=TARGET, slots=slots)


def blocks_by_slot(user):
    return {
        block.slot_index: block
        for block in TimeBlock.objects.filter(user=user, date=TARGET)
    }


@pytest.mark.django_db
class TestRestore:
    def test_slot_that_was_empty_is_deleted(self, restore, user, focus):
        TimeBlock.objects.create(user=user, date=TARGET, slot_index=54, tag=focus)

        restore.execute(command([{"slot_index": 54, "tag_id": None, "memo": ""}]), user)

        assert blocks_by_slot(user) == {}

    def test_slot_goes_back_to_its_previous_tag(self, restore, user, focus, leisure):
        TimeBlock.objects.create(user=user, date=TARGET, slot_index=54, tag=leisure)

        restore.execute(
            command([{"slot_index": 54, "tag_id": focus.id, "memo": ""}]), user
        )

        assert blocks_by_slot(user)[54].tag_id == focus.id

    def test_slot_goes_back_to_its_previous_memo(self, restore, user, focus):
        TimeBlock.objects.create(
            user=user, date=TARGET, slot_index=54, tag=focus, memo="딴짓"
        )

        restore.execute(
            command([{"slot_index": 54, "tag_id": focus.id, "memo": "회고"}]), user
        )

        assert blocks_by_slot(user)[54].memo == "회고"

    def test_a_deleted_block_is_recreated(self, restore, user, focus):
        restore.execute(
            command([{"slot_index": 54, "tag_id": focus.id, "memo": ""}]), user
        )

        assert blocks_by_slot(user)[54].tag_id == focus.id

    def test_each_slot_can_return_to_a_different_tag(
        self, restore, user, focus, leisure
    ):
        restore.execute(
            command(
                [
                    {"slot_index": 54, "tag_id": focus.id, "memo": ""},
                    {"slot_index": 55, "tag_id": leisure.id, "memo": ""},
                    {"slot_index": 56, "tag_id": None, "memo": ""},
                ]
            ),
            user,
        )

        restored = blocks_by_slot(user)
        assert restored[54].tag_id == focus.id
        assert restored[55].tag_id == leisure.id
        assert 56 not in restored


@pytest.mark.django_db
class TestRestoreRefusesInaccessibleTags:
    def test_tag_deleted_since_the_snapshot_refuses_the_whole_restore(
        self, restore, user, focus, leisure
    ):
        vanished_id = leisure.id
        leisure.delete()

        with pytest.raises(PermissionError):
            restore.execute(
                command(
                    [
                        {"slot_index": 54, "tag_id": focus.id, "memo": ""},
                        {"slot_index": 55, "tag_id": vanished_id, "memo": ""},
                    ]
                ),
                user,
            )

    def test_refused_restore_writes_nothing(self, restore, user, focus, leisure):
        vanished_id = leisure.id
        leisure.delete()

        with pytest.raises(PermissionError):
            restore.execute(
                command(
                    [
                        {"slot_index": 54, "tag_id": focus.id, "memo": ""},
                        {"slot_index": 55, "tag_id": vanished_id, "memo": ""},
                    ]
                ),
                user,
            )

        assert blocks_by_slot(user) == {}

    def test_another_users_tag_is_refused(self, restore, user, make_user):
        stranger = make_user(username="stranger")
        stranger_tag = Tag.objects.create(
            user=stranger,
            name="남의태그",
            color="#4E8F63",
            category=Category.objects.get(slug="investment"),
        )

        with pytest.raises(PermissionError):
            restore.execute(
                command([{"slot_index": 54, "tag_id": stranger_tag.id, "memo": ""}]),
                user,
            )
