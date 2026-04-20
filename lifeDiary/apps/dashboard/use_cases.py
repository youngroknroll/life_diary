from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from .commands import DeleteTimeBlocksCommand, UpsertTimeBlocksCommand
from .ports import TimeBlockWriter
from apps.tags.ports import TagReader
from apps.stats.use_cases import invalidate_stats_cache


@dataclass(frozen=True)
class UpsertResult:
    created: int
    updated: int
    tag_id: int
    tag_name: str
    tag_color: str


@dataclass(frozen=True)
class DeleteResult:
    deleted: int
    requested: int


class UpsertTimeBlocksUseCase:
    def __init__(self, writer: TimeBlockWriter, tags: TagReader):
        self._writer = writer
        self._tags = tags

    @transaction.atomic
    def execute(self, cmd: UpsertTimeBlocksCommand, user) -> UpsertResult:
        tag = self._tags.find_by_id_accessible(cmd.tag_id, user)
        if not tag:
            raise PermissionError("존재하지 않는 태그이거나 접근 권한이 없습니다.")

        existing_blocks = self._writer.find_by_slots(user, cmd.target_date, cmd.slot_indexes)
        existing_slots = {block.slot_index: block for block in existing_blocks}

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

        invalidate_stats_cache(cmd.user_id, cmd.target_date)

        return UpsertResult(
            created=len(to_create),
            updated=len(to_update),
            tag_id=tag.id,
            tag_name=tag.name,
            tag_color=tag.color,
        )


class DeleteTimeBlocksUseCase:
    def __init__(self, writer: TimeBlockWriter):
        self._writer = writer

    @transaction.atomic
    def execute(self, cmd: DeleteTimeBlocksCommand, user) -> DeleteResult:
        deleted = self._writer.delete_by_slots(user, cmd.target_date, cmd.slot_indexes)
        return DeleteResult(deleted=deleted, requested=len(cmd.slot_indexes))
