"""
users Use Case 단위 테스트 — DB 의존 제거 확인용.
SaveGoalUseCase/SaveNoteUseCase가 ModelForm이 아닌 순수 DTO를 받는지 검증.
"""
from __future__ import annotations

import pytest

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
