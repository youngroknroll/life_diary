from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class UpsertTimeBlocksCommand(BaseModel):
    user_id: int
    target_date: date
    slot_indexes: list[int] = Field(min_length=1)
    tag_id: int
    memo: str = Field(default="", max_length=500)

    @field_validator("slot_indexes")
    @classmethod
    def validate_slots(cls, v: list[int]) -> list[int]:
        if not all(0 <= i < 144 for i in v):
            raise ValueError("슬롯 인덱스는 0~143 범위여야 합니다.")
        return v


class SlotSnapshot(BaseModel):
    """tag_id 가 None 이면 그 슬롯은 비어 있었다는 뜻이다."""

    slot_index: int
    tag_id: int | None = None
    memo: str = Field(default="", max_length=500)

    @field_validator("slot_index")
    @classmethod
    def validate_slot(cls, v: int) -> int:
        if not 0 <= v < 144:
            raise ValueError("슬롯 인덱스는 0~143 범위여야 합니다.")
        return v


class RestoreTimeBlocksCommand(BaseModel):
    """요청 본문에서 날짜나 슬롯을 받지 않는다.

    받으면 오래된 스냅샷을 엉뚱한 날짜에 덮어쓸 수 있다.
    """

    target_date: date
    slots: list[SlotSnapshot] = Field(min_length=1)


class DeleteTimeBlocksCommand(BaseModel):
    user_id: int
    target_date: date
    slot_indexes: list[int] = Field(min_length=1)

    @field_validator("slot_indexes")
    @classmethod
    def validate_slots(cls, v: list[int]) -> list[int]:
        if not all(0 <= i < 144 for i in v):
            raise ValueError("슬롯 인덱스는 0~143 범위여야 합니다.")
        return v
