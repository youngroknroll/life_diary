from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils.translation import gettext

from apps.tags.ports import TagReader
from apps.tags.repositories import TagRepository
from .models import UserGoal, UserNote
from .repositories import GoalRepository, NoteRepository


@dataclass(frozen=True)
class GoalData:
    tag_id: int
    period: str
    target_hours: float


@dataclass(frozen=True)
class NoteData:
    note: str

_goal_repo = GoalRepository()
_note_repo = NoteRepository()


class GetMyPageUseCase:
    def execute(self, user) -> dict:
        """설정은 목표를 정하는 자리다. 달성 결과는 분석 탭 소관이다.

        예전에는 여기서 통계 집계를 세 번 돌려 달성률을 붙였는데, 설정 화면이
        그 값을 더는 그리지 않는다.
        """
        return {
            "goals": list(_goal_repo.find_by_user(user)),
            "note": _note_repo.find_latest(user),
        }


class SaveGoalUseCase:
    """UserGoal 생성/수정 — 순수 DTO 기반, 프레임워크 독립."""

    def __init__(self, tags: TagReader | None = None):
        self._tags: TagReader = tags or TagRepository()

    @transaction.atomic
    def execute(self, data: GoalData, user, goal_id: int | None = None) -> UserGoal:
        if self._tags.find_by_id_accessible(data.tag_id, user) is None:
            raise LookupError(gettext("접근할 수 없는 태그입니다."))
        if goal_id is not None:
            goal = _goal_repo.get_or_404(goal_id, user)
        else:
            goal = UserGoal(user=user)
        goal.tag_id = data.tag_id
        goal.period = data.period
        goal.target_hours = data.target_hours
        goal.full_clean()
        goal.save()
        return goal


class DeleteGoalUseCase:
    @transaction.atomic
    def execute(self, user, goal_id: int) -> None:
        goal = _goal_repo.get_or_404(goal_id, user)
        goal.delete()


class SaveNoteUseCase:
    """UserNote 생성/수정 — 순수 DTO 기반, 프레임워크 독립."""

    @transaction.atomic
    def execute(self, data: NoteData, user, note_id: int | None = None) -> UserNote:
        if note_id is not None:
            note = _note_repo.get_or_404(note_id, user)
        else:
            note = UserNote(user=user)
        note.note = data.note
        note.full_clean()
        note.save()
        return note


class DeleteNoteUseCase:
    @transaction.atomic
    def execute(self, user, note_id: int) -> None:
        note = _note_repo.get_or_404(note_id, user)
        note.delete()
