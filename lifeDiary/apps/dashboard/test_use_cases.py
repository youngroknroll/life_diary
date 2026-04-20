"""
Use Case 단위 테스트 — DB 없이 Fake Port로 실행
"""
from datetime import date

import pytest

from apps.dashboard.commands import DeleteTimeBlocksCommand, UpsertTimeBlocksCommand
from apps.dashboard.use_cases import DeleteTimeBlocksUseCase, UpsertTimeBlocksUseCase


class FakeTag:
    def __init__(self, tag_id=1, name="work", color="#ff0000"):
        self.id = tag_id
        self.name = name
        self.color = color


class FakeBlock:
    def __init__(self, slot_index, tag=None, memo=""):
        self.slot_index = slot_index
        self.tag = tag
        self.memo = memo


class FakeTagReader:
    def __init__(self, tag=None):
        self._tag = tag

    def find_by_id_accessible(self, tag_id, user):
        return self._tag

    def find_accessible_ordered(self, user):
        return [self._tag] if self._tag else []


class FakeWriter:
    def __init__(self, existing_slots=None):
        self.created = []
        self.updated = []
        self.deleted_slots = []
        self._existing = {s: FakeBlock(s) for s in (existing_slots or [])}

    def find_by_slots(self, user, target_date, slot_indexes):
        return [self._existing[s] for s in slot_indexes if s in self._existing]

    def build(self, user, target_date, slot_index, tag, memo):
        return FakeBlock(slot_index, tag, memo)

    def bulk_create(self, blocks):
        self.created.extend(blocks)

    def bulk_update(self, blocks, fields):
        self.updated.extend(blocks)

    def delete_by_slots(self, user, target_date, slot_indexes):
        count = sum(1 for s in slot_indexes if s in self._existing)
        self.deleted_slots.extend(slot_indexes)
        return count

    def is_tag_in_use(self, tag):
        return False


class FakeUser:
    id = 99


@pytest.fixture
def user():
    return FakeUser()


@pytest.fixture
def tag():
    return FakeTag()


class TestUpsertTimeBlocksUseCase:
    def test_creates_new_blocks(self, user, tag):
        writer = FakeWriter(existing_slots=[])
        uc = UpsertTimeBlocksUseCase(writer=writer, tags=FakeTagReader(tag))
        cmd = UpsertTimeBlocksCommand(
            user_id=user.id, target_date=date(2026, 4, 20),
            slot_indexes=[0, 1, 2], tag_id=tag.id, memo="테스트"
        )
        result = uc.execute(cmd, user)

        assert result.created == 3
        assert result.updated == 0
        assert len(writer.created) == 3

    def test_updates_existing_blocks(self, user, tag):
        writer = FakeWriter(existing_slots=[0, 1])
        uc = UpsertTimeBlocksUseCase(writer=writer, tags=FakeTagReader(tag))
        cmd = UpsertTimeBlocksCommand(
            user_id=user.id, target_date=date(2026, 4, 20),
            slot_indexes=[0, 1], tag_id=tag.id, memo="수정"
        )
        result = uc.execute(cmd, user)

        assert result.created == 0
        assert result.updated == 2
        assert writer.updated[0].memo == "수정"

    def test_mixed_create_and_update(self, user, tag):
        writer = FakeWriter(existing_slots=[0])
        uc = UpsertTimeBlocksUseCase(writer=writer, tags=FakeTagReader(tag))
        cmd = UpsertTimeBlocksCommand(
            user_id=user.id, target_date=date(2026, 4, 20),
            slot_indexes=[0, 1], tag_id=tag.id
        )
        result = uc.execute(cmd, user)

        assert result.created == 1
        assert result.updated == 1

    def test_raises_on_inaccessible_tag(self, user):
        writer = FakeWriter()
        uc = UpsertTimeBlocksUseCase(writer=writer, tags=FakeTagReader(tag=None))
        cmd = UpsertTimeBlocksCommand(
            user_id=user.id, target_date=date(2026, 4, 20),
            slot_indexes=[0], tag_id=99
        )
        with pytest.raises(PermissionError):
            uc.execute(cmd, user)


class TestDeleteTimeBlocksUseCase:
    def test_deletes_existing_blocks(self, user):
        writer = FakeWriter(existing_slots=[5, 6, 7])
        uc = DeleteTimeBlocksUseCase(writer=writer)
        cmd = DeleteTimeBlocksCommand(
            user_id=user.id, target_date=date(2026, 4, 20), slot_indexes=[5, 6, 7]
        )
        result = uc.execute(cmd, user)

        assert result.deleted == 3
        assert result.requested == 3

    def test_returns_zero_when_nothing_to_delete(self, user):
        writer = FakeWriter(existing_slots=[])
        uc = DeleteTimeBlocksUseCase(writer=writer)
        cmd = DeleteTimeBlocksCommand(
            user_id=user.id, target_date=date(2026, 4, 20), slot_indexes=[10]
        )
        result = uc.execute(cmd, user)

        assert result.deleted == 0


class TestUpsertTimeBlocksCommand:
    def test_rejects_out_of_range_slots(self):
        with pytest.raises(Exception):
            UpsertTimeBlocksCommand(
                user_id=1, target_date=date(2026, 4, 20),
                slot_indexes=[0, 144], tag_id=1
            )

    def test_rejects_empty_slots(self):
        with pytest.raises(Exception):
            UpsertTimeBlocksCommand(
                user_id=1, target_date=date(2026, 4, 20),
                slot_indexes=[], tag_id=1
            )

    def test_rejects_memo_over_500_chars(self):
        with pytest.raises(Exception):
            UpsertTimeBlocksCommand(
                user_id=1, target_date=date(2026, 4, 20),
                slot_indexes=[0], tag_id=1, memo="x" * 501
            )
