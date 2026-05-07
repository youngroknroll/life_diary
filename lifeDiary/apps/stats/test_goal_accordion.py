"""목표 진행 accordion 회귀 테스트.

- 3개 섹션 (daily/weekly/monthly) 모두 렌더
- weekly만 기본 expanded (show)
- 빈 상태 시 '추가하기' 링크 노출
- 목표 있을 때 카운트 뱃지가 0보다 큰 값
"""
import re
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestGoalAccordionStructure:
    def test_three_sections_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        assert response.status_code == 200
        h = response.content.decode()
        assert 'id="goalAccordion"' in h
        for sec in ("goalDaily", "goalWeekly", "goalMonthly"):
            assert f'id="{sec}"' in h, f"{sec} 섹션 누락"

    def test_only_weekly_expanded_by_default(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        for sec, expected_show in [("goalDaily", False), ("goalWeekly", True), ("goalMonthly", False)]:
            m = re.search(r'id="' + sec + r'"[^>]*class="([^"]+)"', h)
            assert m, f"{sec} 클래스 추출 실패"
            classes = m.group(1)
            if expected_show:
                assert "show" in classes, f"{sec}는 기본 펼쳐져야 함"
            else:
                assert "show" not in classes, f"{sec}는 기본 접혀야 함"


@pytest.mark.django_db
class TestGoalAccordionEmptyState:
    def test_empty_state_shows_add_link(self, auth_client):
        # 목표 없는 새 사용자 — 빈 상태 메시지 + 추가 링크
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        # 추가하기 버튼이 사라진 적 없는지 (각 빈 섹션마다 1회 등장)
        assert "goal-empty" in h
        assert reverse("users:usergoal_create") in h

    def test_empty_state_count_badge_zero(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        # daily/monthly는 빈 상태이므로 bg-secondary 뱃지에 0
        # accordion-button 안의 badge 텍스트 추출
        badges = re.findall(
            r'<span class="badge bg-(?:primary|secondary)[^"]*">\s*(\d+)\s*</span>', h
        )
        # 3개 섹션 → 3개 뱃지
        assert len(badges) >= 3
