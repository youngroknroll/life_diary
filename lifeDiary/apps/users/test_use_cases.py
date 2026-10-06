"""
users Use Case 단위 테스트 — DB 의존 제거 확인용.
SaveGoalUseCase/SaveNoteUseCase가 ModelForm이 아닌 순수 DTO를 받는지 검증.
"""
from __future__ import annotations

from datetime import date

import pytest

from apps.tags.models import Category, Tag
from apps.users.use_cases import GoalData, NoteData, SaveGoalUseCase


class TestGoalDataDTO:
    def test_is_frozen(self):
        data = GoalData(tag_id=1, period="daily", target_hours=2.0)
        with pytest.raises(Exception):
            data.tag_id = 2  # type: ignore[misc]

    def test_fields(self):
        data = GoalData(tag_id=5, period="weekly", target_hours=10.0)
        assert data.tag_id == 5
        assert data.period == "weekly"
        assert data.target_hours == 10.0

    def test_a_goal_has_no_due_date_unless_one_is_given(self):
        data = GoalData(tag_id=5, period="weekly", target_hours=10.0)

        assert data.due_date is None


class TestNoteDataDTO:
    def test_is_frozen(self):
        data = NoteData(note="hello")
        with pytest.raises(Exception):
            data.note = "world"  # type: ignore[misc]

    def test_fields(self):
        data = NoteData(note="메모 내용")
        assert data.note == "메모 내용"


class FakeTagReader:
    """접근 가능한 태그 ID 집합만 반환하는 Fake."""

    def __init__(self, accessible_ids: set[int]):
        self._accessible = accessible_ids

    def find_by_id_accessible(self, tag_id, user):
        if tag_id in self._accessible:
            return object()
        return None

    def find_accessible_ordered(self, user):
        return []


@pytest.mark.django_db
class TestSaveGoalUseCaseAuthz:
    """IDOR 차단: 다른 사용자 태그 ID로 목표를 만들 수 없어야 한다."""

    def test_rejects_inaccessible_tag(self):
        fake_reader = FakeTagReader(accessible_ids={1, 2})
        use_case = SaveGoalUseCase(tags=fake_reader)

        data = GoalData(tag_id=999, period="daily", target_hours=2.0)

        # 메시지는 active locale에 따라 한/영 다름 → 예외 종류만 검증
        with pytest.raises(LookupError):
            use_case.execute(data, user=object())


@pytest.fixture
def goal_owner(make_user):
    return make_user(username="dueowner")


@pytest.fixture
def owned_tag(goal_owner):
    return Tag.objects.create(
        user=goal_owner,
        name="공부",
        category=Category.objects.get(slug="investment"),
    )


@pytest.mark.django_db
class TestSaveGoalUseCaseDueDate:
    def test_saving_a_goal_keeps_its_due_date(self, goal_owner, owned_tag):
        due = date(2026, 12, 31)

        goal = SaveGoalUseCase().execute(
            GoalData(
                tag_id=owned_tag.id, period="daily", target_hours=2.0, due_date=due
            ),
            goal_owner,
        )

        goal.refresh_from_db()
        assert goal.due_date == due

    def test_saving_without_a_due_date_clears_the_old_one(
        self, goal_owner, owned_tag, goal_factory
    ):
        goal = goal_factory(goal_owner, owned_tag, due_date=date(2026, 12, 31))

        SaveGoalUseCase().execute(
            GoalData(tag_id=owned_tag.id, period="daily", target_hours=2.0),
            goal_owner,
            goal_id=goal.id,
        )

        goal.refresh_from_db()
        assert goal.due_date is None
