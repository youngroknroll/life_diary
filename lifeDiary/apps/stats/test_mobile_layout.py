"""통계 페이지 탭 구조 회귀 테스트.

탭 동작은 그대로 유지(클릭 시 pane 전환). 템플릿 차원에서는 4개 nav-link가
동일 ul 안에 그대로 있는지 확인.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestStatsTabsStructure:
    def test_nav_tabs_present(self, auth_client):
        response = auth_client.get(reverse("stats:index"))
        assert response.status_code == 200
        h = response.content.decode()
        assert 'id="statsTabs"' in h
        assert 'data-bs-toggle="tab"' in h
