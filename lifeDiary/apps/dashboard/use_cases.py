"""시간 블록 저장·복원·삭제 유스케이스."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.tags.ports import TagReader

from .commands import (
    DeleteTimeBlocksCommand,
    RestoreTimeBlocksCommand,
    UpsertTimeBlocksCommand,
)
from .ports import TimeBlockWriter
from .signals import time_blocks_changed


@dataclass(frozen=True)
class UpsertResult:
    """저장 결과: 새로 만든 슬롯 수, 갱신한 슬롯 수, 적용한 태그."""

    created: int
    updated: int
    tag_id: int
    tag_name: str
    tag_color: str
    previous_state: list[dict]


@dataclass(frozen=True)
class DeleteResult:
    """삭제 결과: 삭제한 슬롯 수, 요청한 슬롯 수, 삭제 전 상태."""

    deleted: int
    requested: int
    previous_state: list[dict]


@dataclass(frozen=True)
class RestoreResult:
    """복원 결과: 되살린 슬롯 수와 비운 슬롯 수."""

    restored: int
    cleared: int


class UpsertTimeBlocksUseCase:
    """선택한 슬롯에 태그와 메모를 저장한다. 이미 있는 슬롯은 갱신한다."""

    def __init__(self, writer: TimeBlockWriter, tags: TagReader):
        """시간 블록 저장소와 태그 조회 포트를 받는다."""
        self._writer = writer
        self._tags = tags

    @transaction.atomic
    def execute(self, cmd: UpsertTimeBlocksCommand, user) -> UpsertResult:
        """선택한 슬롯에 태그와 메모를 저장한다.

        Raises:
            PermissionError: 태그가 없거나 사용자의 태그가 아닐 때.
        """
        tag = self._tags.find_by_id_accessible(cmd.tag_id, user)
        if not tag:
            raise PermissionError("존재하지 않는 태그이거나 접근 권한이 없습니다.")

        existing_blocks = self._writer.find_by_slots(user, cmd.target_date, cmd.slot_indexes)
        existing_slots = {block.slot_index: block for block in existing_blocks}

        previous_state = [
            {
                "slot_index": slot_index,
                "tag_id": existing_slots[slot_index].tag_id
                if slot_index in existing_slots
                else None,
                "memo": existing_slots[slot_index].memo
                if slot_index in existing_slots
                else "",
            }
            for slot_index in cmd.slot_indexes
        ]

        to_create = []
        to_update = []

        for slot_index in cmd.slot_indexes:
            if slot_index in existing_slots:
                block = existing_slots[slot_index]
                block.tag = tag
                block.memo = cmd.memo
                to_update.append(block)
            else:
                to_create.append(
                    self._writer.build(
                        user=user,
                        target_date=cmd.target_date,
                        slot_index=slot_index,
                        tag=tag,
                        memo=cmd.memo,
                    )
                )

        if to_create:
            self._writer.bulk_create(to_create)
        if to_update:
            self._writer.bulk_update(to_update, ["tag", "memo"])

        transaction.on_commit(
            lambda user_id=cmd.user_id, target_date=cmd.target_date: (
                time_blocks_changed.send(
                    sender=UpsertTimeBlocksUseCase,
                    user_id=user_id,
                    target_date=target_date,
                )
            )
        )

        return UpsertResult(
            created=len(to_create),
            updated=len(to_update),
            tag_id=tag.id,
            tag_name=tag.name,
            tag_color=tag.color,
            previous_state=previous_state,
        )


class RestoreTimeBlocksUseCase:
    """슬롯마다 돌아갈 태그와 메모가 달라 저장 use case를 재사용하지 않는다."""

    def __init__(self, writer: TimeBlockWriter, tags: TagReader):
        """시간 블록 저장소와 태그 조회 포트를 받는다."""
        self._writer = writer
        self._tags = tags

    @transaction.atomic
    def execute(self, cmd: RestoreTimeBlocksCommand, user) -> RestoreResult:
        """삭제·저장 직전의 슬롯 상태로 되돌린다. 태그가 없던 슬롯은 비운다."""
        tags_by_id = self._resolve_tags(cmd, user)

        to_delete = [slot.slot_index for slot in cmd.slots if slot.tag_id is None]
        to_restore = [slot for slot in cmd.slots if slot.tag_id is not None]

        if to_delete:
            self._writer.delete_by_slots(user, cmd.target_date, to_delete)

        restored = self._write_back(cmd, user, to_restore, tags_by_id)

        transaction.on_commit(
            lambda user_id=user.id, target_date=cmd.target_date: (
                time_blocks_changed.send(
                    sender=RestoreTimeBlocksUseCase,
                    user_id=user_id,
                    target_date=target_date,
                )
            )
        )

        return RestoreResult(restored=restored, cleared=len(to_delete))

    def _resolve_tags(self, cmd: RestoreTimeBlocksCommand, user) -> dict:
        """스냅샷의 tag_id 를 믿지 않고 복원 시점에 소유권을 다시 확인한다.

        그사이 지워졌거나 남의 것이 된 태그로 절반만 복원된 상태를 남기지
        않도록, 하나라도 막히면 통째로 거절한다.
        """
        tags_by_id = {}

        for slot in cmd.slots:
            if slot.tag_id is None or slot.tag_id in tags_by_id:
                continue

            tag = self._tags.find_by_id_accessible(slot.tag_id, user)
            if not tag:
                raise PermissionError(
                    "되돌릴 태그가 더 이상 존재하지 않거나 접근 권한이 없습니다."
                )
            tags_by_id[slot.tag_id] = tag

        return tags_by_id

    def _write_back(self, cmd, user, slots, tags_by_id) -> int:
        if not slots:
            return 0

        existing = {
            block.slot_index: block
            for block in self._writer.find_by_slots(
                user, cmd.target_date, [slot.slot_index for slot in slots]
            )
        }

        to_create = []
        to_update = []

        for slot in slots:
            tag = tags_by_id[slot.tag_id]
            block = existing.get(slot.slot_index)

            if block is None:
                to_create.append(
                    self._writer.build(
                        user=user,
                        target_date=cmd.target_date,
                        slot_index=slot.slot_index,
                        tag=tag,
                        memo=slot.memo,
                    )
                )
            else:
                block.tag = tag
                block.memo = slot.memo
                to_update.append(block)

        if to_create:
            self._writer.bulk_create(to_create)
        if to_update:
            self._writer.bulk_update(to_update, ["tag", "memo"])

        return len(to_create) + len(to_update)


class DeleteTimeBlocksUseCase:
    """선택한 슬롯의 기록을 삭제하고 삭제 전 상태를 돌려준다."""

    def __init__(self, writer: TimeBlockWriter):
        """시간 블록 저장소를 받는다."""
        self._writer = writer

    @transaction.atomic
    def execute(self, cmd: DeleteTimeBlocksCommand, user) -> DeleteResult:
        """선택한 슬롯의 기록을 삭제하고, 되돌릴 수 있도록 삭제 전 상태를 담아 돌려준다."""
        previous_state = self._writer.snapshot_slots(
            user, cmd.target_date, cmd.slot_indexes
        )
        deleted = self._writer.delete_by_slots(user, cmd.target_date, cmd.slot_indexes)
        transaction.on_commit(
            lambda user_id=cmd.user_id, target_date=cmd.target_date: (
                time_blocks_changed.send(
                    sender=DeleteTimeBlocksUseCase,
                    user_id=user_id,
                    target_date=target_date,
                )
            )
        )
        return DeleteResult(
            deleted=deleted,
            requested=len(cmd.slot_indexes),
            previous_state=previous_state,
        )
