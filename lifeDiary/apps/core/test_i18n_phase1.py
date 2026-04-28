"""Phase 1 (base/core) i18n 검증 테스트 — pytest 스타일."""

import pytest
from django.urls import reverse
from django.utils.translation import activate, deactivate

from apps.core.utils import format_time_display


@pytest.mark.django_db
class TestHomePageEnglish:
    def test_home_page_renders_english_hero(self, en_client):
        response = en_client.get(reverse("home"))
        body = response.content.decode()
        assert "Capture your day, simply." in body
        assert "Pick activities, log the flow of your day, then look back." in body
        assert "하루를 단순하게 기록하세요" not in body

    def test_home_page_renders_english_navbar(self, en_client):
        response = en_client.get(reverse("home"))
        body = response.content.decode()
        assert "Home" in body
        assert "Dashboard" in body
        assert "Stats" in body
        assert "Tags" in body
        assert "대시보드" not in body
        assert "태그 관리" not in body

    def test_javascript_catalog_url_is_loaded(self, en_client):
        response = en_client.get(reverse("home"))
        assert reverse("javascript-catalog") in response.content.decode()

    def test_javascript_catalog_endpoint_returns_translations(self, en_client):
        response = en_client.get(reverse("javascript-catalog"))
        assert response.status_code == 200
        body = response.content.decode("utf-8")
        assert "Select a category" in body
        assert "Create new tag" in body
        assert "Processing..." in body


class TestFormatTimeDisplay:
    def test_korean_default(self):
        activate("ko")
        try:
            assert format_time_display(2, 30) == "2시간 30분"
            assert format_time_display(0, 0) == "0분"
        finally:
            deactivate()

    def test_english(self):
        activate("en")
        try:
            assert format_time_display(2, 30) == "2h 30m"
            assert format_time_display(2, 0) == "2h"
            assert format_time_display(0, 30) == "30m"
            assert format_time_display(0, 0) == "0m"
        finally:
            deactivate()
