import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestHomePage:
    def test_home_page_presents_simple_daily_recording_for_anonymous_user(self, ko_client):
        response = ko_client.get(reverse("home"))
        body = response.content.decode()
        assert "하루를 단순하게 기록하세요" in body
        assert "로그인하고 기록 시작" in body
        assert "활동을 고르고, 오늘의 흐름을 남기고, 돌아봅니다." in body
        assert "소비시간의 분류" in body
        assert 'data-bs-target="#homePreviewImageModal"' in body
        assert 'id="homePreviewImageModal"' in body
        assert "10분 단위" not in body

    def test_home_page_invites_authenticated_user_to_record_today(self, ko_client, make_user):
        user = make_user(username="daily-user")
        ko_client.force_login(user)
        response = ko_client.get(reverse("home"))
        body = response.content.decode()
        assert "daily-user님" in body
        assert "오늘 기록하기" in body
        assert "로그인하고 기록 시작" not in body
