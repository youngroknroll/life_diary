"""Phase 4 (users) i18n 검증 테스트 — TDD RED 먼저 작성."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class UsersAuthEnglishTests(TestCase):
    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"

    def test_login_page_renders_english(self):
        response = self.client.get(reverse("users:login"))
        self.assertContains(response, "Log in")  # H4 헤더
        self.assertContains(response, "Username")  # 라벨
        self.assertContains(response, "Password")
        self.assertContains(response, "Don't have an account?")  # 안내 문구
        self.assertContains(response, "Sign up")  # 링크
        self.assertNotContains(response, "사용자명")
        self.assertNotContains(response, "비밀번호")

    def test_signup_page_renders_english(self):
        response = self.client.get(reverse("users:signup"))
        self.assertContains(response, "Sign up")
        self.assertContains(response, "Username")
        self.assertContains(response, "Password")
        self.assertContains(response, "Confirm password")
        self.assertContains(response, "Already have an account?")
        self.assertNotContains(response, "회원가입")
        self.assertNotContains(response, "비밀번호 확인")


class MypageEnglishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="user-en-mypage", password="testpass-Long-9!"
        )

    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.client.force_login(self.user)

    def test_mypage_renders_english(self):
        response = self.client.get(reverse("users:mypage"))
        self.assertContains(response, "My page")
        self.assertContains(response, "Add goal")
        self.assertContains(response, "My goals")
        # 폼 라벨
        self.assertContains(response, "Tag")
        self.assertContains(response, "Period")
        self.assertContains(response, "Target hours")
        self.assertNotContains(response, "마이페이지")
        self.assertNotContains(response, "목표 추가")

    def test_mypage_period_choices_english(self):
        response = self.client.get(reverse("users:mypage"))
        # period select 옵션
        self.assertContains(response, "Daily")
        self.assertContains(response, "Weekly")
        self.assertContains(response, "Monthly")


class UserGoalFormEnglishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="user-en-goal", password="testpass-Long-9!"
        )

    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.client.force_login(self.user)

    def test_usergoal_create_form_english(self):
        response = self.client.get(reverse("users:usergoal_create"))
        self.assertContains(response, "Add goal")
        self.assertContains(response, "Save")
        self.assertContains(response, "Back to list")
        self.assertNotContains(response, "목록으로")


class UserNoteEnglishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="user-en-note", password="testpass-Long-9!"
        )

    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.client.force_login(self.user)

    def test_usernote_list_english(self):
        response = self.client.get(reverse("users:usernote_list"))
        self.assertContains(response, "My notes")
        self.assertContains(response, "Add note")
        self.assertContains(response, "No notes yet.")
        self.assertNotContains(response, "특이사항")

    def test_usernote_create_form_english(self):
        response = self.client.get(reverse("users:usernote_create"))
        self.assertContains(response, "Add note")
        self.assertContains(response, "Save")


class LogoutMessageEnglishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="user-en-logout", password="testpass-Long-9!"
        )

    def test_logout_success_message_english(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.client.force_login(self.user)
        response = self.client.post(reverse("users:logout"), follow=True)
        # 메시지가 영문으로 렌더링됐는지 (홈 페이지 응답에 alert 메시지 포함)
        self.assertContains(response, "Successfully logged out.")
