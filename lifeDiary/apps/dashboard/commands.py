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
