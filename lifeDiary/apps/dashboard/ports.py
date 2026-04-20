from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable


@runtime_checkable
class TimeBlockReader(Protocol):
    """stats 등 외부 앱이 TimeBlock을 읽을 때 사용하는 Port."""

    def find_by_date(self, user, target_date: date): ...

    def find_by_month(self, user, start: date, end: date): ...

    def find_daily_counts(self, user, start: date, end: date) -> dict: ...


@runtime_checkable
class TimeBlockWriter(Protocol):
    """TimeBlock 쓰기 전용 Port."""

    def build(self, user, target_date: date, slot_index: int, tag, memo: str): ...

    def find_by_slots(self, user, target_date: date, slot_indexes: list[int]): ...

    def bulk_create(self, blocks: list) -> None: ...

    def bulk_update(self, blocks: list, fields: list[str]) -> None: ...

    def delete_by_slots(self, user, target_date: date, slot_indexes: list[int]) -> int: ...

    def is_tag_in_use(self, tag) -> bool: ...
