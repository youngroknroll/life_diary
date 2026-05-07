"""통계 페이지 모바일 레이아웃 회귀 테스트.

데스크톱은 nav-tabs 그대로, 모바일에서는 4개 섹션이 모두 보이도록
CSS-only 변경. 템플릿 차원에서는 4개의 .mobile-section-title 헤더가
각 .tab-pane 안에 존재하는지 확인.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestStatsMobileLayout:
    def test_mobile_section_titles_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        assert response.status_code == 200
        h = response.content.decode()
        # 4개 섹션마다 한 번씩 모바일 헤더 노드
        assert h.count("mobile-section-title") == 4

    def test_each_tab_pane_has_mobile_header(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        # 각 .tab-pane 안에 mobile-section-title이 있는지 (id 직후 헤더)
        for pane_id in ("daily", "weekly", "monthly", "tags"):
            marker = f'id="{pane_id}"'
            idx = h.find(marker)
            assert idx >= 0, f"pane {pane_id} not found"
            # 다음 1500자 안에 mobile-section-title 등장
            assert "mobile-section-title" in h[idx:idx + 1500]

    def test_nav_tabs_still_present_for_desktop(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        h = response.content.decode()
        # 데스크톱용 탭 바는 그대로 유지
        assert 'id="statsTabs"' in h
        assert 'data-bs-toggle="tab"' in h
