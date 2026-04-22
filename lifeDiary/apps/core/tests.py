from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_page_presents_simple_daily_recording_for_anonymous_user(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "하루를 단순하게 기록하세요")
        self.assertContains(response, "로그인하고 기록 시작")
        self.assertContains(response, "활동을 고르고, 오늘의 흐름을 남기고, 돌아봅니다.")
        self.assertContains(response, "소비시간의 분류")
        self.assertContains(response, 'data-bs-target="#homePreviewImageModal"', html=False)
        self.assertContains(response, 'id="homePreviewImageModal"', html=False)
        self.assertNotContains(response, "10분 단위")

    def test_home_page_invites_authenticated_user_to_record_today(self):
        user = get_user_model().objects.create_user(
            username="daily-user",
            password="password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "daily-user님")
        self.assertContains(response, "오늘 기록하기")
        self.assertNotContains(response, "로그인하고 기록 시작")
