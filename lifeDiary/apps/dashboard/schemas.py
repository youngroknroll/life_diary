import datetime

from ninja import Schema


class TimeBlockUpsertIn(Schema):
    date: datetime.date | None = None
    slot_indexes: list[int] = []
    tag_id: int | None = None
    memo: str = ""


class TimeBlockDeleteIn(Schema):
    date: datetime.date | None = None
    slot_indexes: list[int] = []


class UndoIn(Schema):
    undo_token: str = ""


class SlotRunOut(Schema):
    start_index: int
    span: int
    tag_id: int | None
    tag_name: str | None
    color: str | None
    label: str | None
    memo: str | None


class HourRunsOut(Schema):
    hour: int
    runs: list[SlotRunOut]


class DayStatsOut(Schema):
    logged_minutes: int
    fill_percentage: float


class TagBriefOut(Schema):
    id: int
    name: str
    color: str


class UpsertResultOut(Schema):
    success: bool
    message: str
    created_count: int
    updated_count: int
    total_count: int
    tag: TagBriefOut
    runs: list[HourRunsOut]
    stats: DayStatsOut
    undo_token: str


class DeleteResultOut(Schema):
    success: bool
    message: str
    deleted_count: int
    requested_count: int
    runs: list[HourRunsOut]
    stats: DayStatsOut
    undo_token: str


class UndoResultOut(Schema):
    success: bool
    message: str
    runs: list[HourRunsOut]
    stats: DayStatsOut
