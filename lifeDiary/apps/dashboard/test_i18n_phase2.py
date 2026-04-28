"""Phase 2 (dashboard) i18n 검증 테스트 — pytest 스타일."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestDashboardEnglish:
    def test_dashboard_renders_english_stats_labels(self, auth_en_client):
        response = auth_en_client.get(reverse("dashboard:index"))
        body = response.content.decode()
        assert "Total slots" in body
        assert "Logged slots" in body
        assert "Logged rate" in body
        assert "Total time logged" in body
        assert "총 슬롯" not in body

    def test_dashboard_renders_english_sidebar(self, auth_en_client):
        response = auth_en_client.get(reverse("dashboard:index"))
        body = response.content.decode()
        assert "Entry" in body
        assert "Select a tag" in body
        assert "New tag" in body
        assert "Memo (optional)" in body
        assert "Save" in body

    def test_dashboard_title_uses_blocktrans(self, auth_en_client):
        response = auth_en_client.get(reverse("dashboard:index"))
        body = response.content.decode()
        assert "Dashboard -" in body
        assert "| Life Diary" in body

    def test_dashboard_post_invalid_json_returns_english(self, auth_en_client):
        response = auth_en_client.post(
            "/api/time-blocks/", "not json", content_type="application/json"
        )
        assert response.status_code == 400
        assert "Invalid JSON format." in response.json()["message"]
