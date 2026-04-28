"""Phase 4 (users) i18n 검증 테스트 — pytest 스타일."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestUsersAuthEnglish:
    def test_login_page_renders_english(self, en_client):
        response = en_client.get(reverse("users:login"))
        body = response.content.decode()
        assert "Log in" in body
        assert "Username" in body
        assert "Password" in body
        assert "Don't have an account?" in body
        assert "Sign up" in body
        assert "사용자명" not in body
        assert "비밀번호" not in body

    def test_signup_page_renders_english(self, en_client):
        response = en_client.get(reverse("users:signup"))
        body = response.content.decode()
        assert "Sign up" in body
        assert "Username" in body
        assert "Password" in body
        assert "Confirm password" in body
        assert "Already have an account?" in body
        assert "회원가입" not in body
        assert "비밀번호 확인" not in body


@pytest.mark.django_db
class TestMypageEnglish:
    def test_mypage_renders_english(self, auth_en_client):
        response = auth_en_client.get(reverse("users:mypage"))
        body = response.content.decode()
        assert "My page" in body
        assert "Add goal" in body
        assert "My goals" in body
        assert "Tag" in body
        assert "Period" in body
        assert "Target hours" in body
        assert "마이페이지" not in body
        assert "목표 추가" not in body

    def test_mypage_period_choices_english(self, auth_en_client):
        response = auth_en_client.get(reverse("users:mypage"))
        body = response.content.decode()
        assert "Daily" in body
        assert "Weekly" in body
        assert "Monthly" in body


@pytest.mark.django_db
class TestUserGoalFormEnglish:
    def test_usergoal_create_form_english(self, auth_en_client):
        response = auth_en_client.get(reverse("users:usergoal_create"))
        body = response.content.decode()
        assert "Add goal" in body
        assert "Save" in body
        assert "Back to list" in body
        assert "목록으로" not in body


@pytest.mark.django_db
class TestUserNoteEnglish:
    def test_usernote_list_english(self, auth_en_client):
        response = auth_en_client.get(reverse("users:usernote_list"))
        body = response.content.decode()
        assert "My notes" in body
        assert "Add note" in body
        assert "No notes yet." in body
        assert "특이사항" not in body

    def test_usernote_create_form_english(self, auth_en_client):
        response = auth_en_client.get(reverse("users:usernote_create"))
        body = response.content.decode()
        assert "Add note" in body
        assert "Save" in body


@pytest.mark.django_db
class TestLogoutMessageEnglish:
    def test_logout_success_message_english(self, auth_en_client):
        response = auth_en_client.post(reverse("users:logout"), follow=True)
        assert "Successfully logged out." in response.content.decode()
