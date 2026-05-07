"""목표 진행 카드(3 컬럼 가로 + 카드별 토글) 회귀 테스트.

- 3개 카드 (daily/weekly/monthly) 모두 렌더
- weekly만 기본 expanded (collapse show)
- 빈 상태 시 '추가하기' 링크 노출
- 카드별 카운트 뱃지 노출
"""
import re
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestGoalCardsStructure:
    def test_three_sections_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        assert response.status_code == 200
        h = response.content.decode()
        for sec in ("goalDaily", "goalWeekly", "goalMonthly"):
            assert f'id="{sec}"' in h, f"{sec} 섹션 누락"

    def test_three_cards_in_row(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        # col-md-4 가로 3분할
        assert h.count('class="col-md-4"') >= 3

    def test_only_weekly_expanded_by_default(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        for sec, expected_show in [("goalDaily", False), ("goalWeekly", True), ("goalMonthly", False)]:
            m = re.search(r'id="' + sec + r'" class="collapse([^"]*)"', h)
            assert m, f"{sec} collapse 클래스 추출 실패"
            classes = m.group(1)
            if expected_show:
                assert "show" in classes, f"{sec}는 기본 펼쳐져야 함"
            else:
                assert "show" not in classes, f"{sec}는 기본 접혀야 함"


@pytest.mark.django_db
class TestGoalCardsEmptyState:
    def test_empty_state_shows_add_link(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        assert "goal-empty" in h
        assert reverse("users:usergoal_create") in h

    def test_count_badge_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        badges = re.findall(
            r'<span class="badge bg-(?:primary|secondary)[^"]*">\s*(\d+)\s*</span>', h
        )
        assert len(badges) >= 3, f"3개 카운트 뱃지 필요, 발견: {len(badges)}"
