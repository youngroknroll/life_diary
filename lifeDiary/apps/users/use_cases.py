"""마이페이지, 목표, 메모 유스케이스."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.db import transaction
from django.utils.translation import gettext

from apps.tags.ports import TagReader
from apps.tags.repositories import TagRepository

from .goal_deadline import DeadlineState, deadline_state
from .models import UserGoal, UserNote
from .repositories import GoalRepository, NoteRepository
from .signals import goals_changed, notes_changed


def _notify_goals_changed(sender, user_id: int) -> None:
    transaction.on_commit(
        lambda user_id=user_id: goals_changed.send(sender=sender, user_id=user_id)
    )


def _notify_notes_changed(sender, user_id: int) -> None:
    transaction.on_commit(
        lambda user_id=user_id: notes_changed.send(sender=sender, user_id=user_id)
    )


@dataclass(frozen=True)
class GoalData:
    """목표 저장 입력값."""

    tag_id: int
    period: str
    target_hours: float
    due_date: date | None = None


@dataclass(frozen=True)
class NoteData:
    """메모 저장 입력값."""

    note: str

_goal_repo = GoalRepository()
_note_repo = NoteRepository()


class GetMyPageUseCase:
    """마이페이지에 필요한 목표 목록과 최근 메모를 모은다."""

    def execute(self, user) -> dict:
        """설정은 목표를 정하는 자리다. 달성 결과는 분석 탭 소관이다.

        예전에는 여기서 통계 집계를 세 번 돌려 달성률을 붙였는데, 설정 화면이
        그 값을 더는 그리지 않는다.
        """
        return {
            "goals": list(_goal_repo.find_by_user(user)),
            "note": _note_repo.find_latest(user),
        }


@dataclass(frozen=True)
class DueSoonGoal:
    """대시보드 배너에 올릴 목표의 태그 이름과 기한 상태."""

    tag_name: str
    deadline: DeadlineState


class ListDueSoonGoalsUseCase:
    """대시보드 상기 배너에 올릴 목표. 지난 기한은 사흘까지만 올린다.

    그 뒤로는 목표 페이지 배지로 충분하고, 배너가 매일 같은 말을 반복한다.
    """

    DAYS_AHEAD = 7
    DAYS_OVERDUE = 3

    def execute(self, user, today: date) -> list[DueSoonGoal]:
        """기한이 임박했거나 막 지난 목표를 돌려준다."""
        goals = _goal_repo.find_due_between(
            user,
            today - timedelta(days=self.DAYS_OVERDUE),
            today + timedelta(days=self.DAYS_AHEAD),
        )
        return [
            DueSoonGoal(goal.tag.name, deadline_state(goal.due_date, today))
            for goal in goals
        ]


class SaveGoalUseCase:
    """UserGoal 생성/수정 — 순수 DTO 기반, 프레임워크 독립."""

    def __init__(self, tags: TagReader | None = None):
        """태그 조회 포트를 받는다. 주지 않으면 저장소를 쓴다."""
        self._tags: TagReader = tags or TagRepository()

    @transaction.atomic
    def execute(self, data: GoalData, user, goal_id: int | None = None) -> UserGoal:
        """목표를 만들거나 goal_id의 목표를 수정한다.

        Raises:
            LookupError: 접근할 수 없는 태그일 때.
            ValidationError: 목표 값이 모델 검증을 통과하지 못할 때.
            Http404: goal_id의 목표가 내 것이 아닐 때.
        """
        if self._tags.find_by_id_accessible(data.tag_id, user) is None:
            raise LookupError(gettext("접근할 수 없는 태그입니다."))
        goal = _goal_repo.get_or_404(goal_id, user) if goal_id is not None else UserGoal(user=user)
        goal.tag_id = data.tag_id
        goal.period = data.period
        goal.target_hours = data.target_hours
        goal.due_date = data.due_date
        goal.full_clean()
        goal.save()
        _notify_goals_changed(SaveGoalUseCase, user.id)
        return goal


class DeleteGoalUseCase:
    """내 목표를 삭제한다."""

    @transaction.atomic
    def execute(self, user, goal_id: int) -> None:
        """goal_id의 목표를 삭제한다.

        Raises:
            Http404: 내 목표가 아닐 때.
        """
        goal = _goal_repo.get_or_404(goal_id, user)
        goal.delete()
        _notify_goals_changed(DeleteGoalUseCase, user.id)


class SaveNoteUseCase:
    """UserNote 생성/수정 — 순수 DTO 기반, 프레임워크 독립."""

    @transaction.atomic
    def execute(self, data: NoteData, user, note_id: int | None = None) -> UserNote:
        """메모를 만들거나 note_id의 메모를 수정한다.

        Raises:
            ValidationError: 메모가 모델 검증을 통과하지 못할 때.
            Http404: note_id의 메모가 내 것이 아닐 때.
        """
        note = _note_repo.get_or_404(note_id, user) if note_id is not None else UserNote(user=user)
        note.note = data.note
        note.full_clean()
        note.save()
        _notify_notes_changed(SaveNoteUseCase, user.id)
        return note


class DeleteNoteUseCase:
    """내 메모를 삭제한다."""

    @transaction.atomic
    def execute(self, user, note_id: int) -> None:
        """note_id의 메모를 삭제한다.

        Raises:
            Http404: 내 메모가 아닐 때.
        """
        note = _note_repo.get_or_404(note_id, user)
        note.delete()
        _notify_notes_changed(DeleteNoteUseCase, user.id)
