"""환영 화면(#7) 회귀 테스트.

- 회원가입 성공 시 welcome으로 리다이렉트
- 환영 화면은 로그인 필수
- CTA가 dashboard로, skip이 home으로 향함
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestSignupRedirectsToWelcome:
    def test_signup_redirects_to_welcome(self, client):
        response = client.post(
            reverse("users:signup"),
            {
                "username": "newcomer",
                "email": "newcomer@example.com",
                "password1": "Strong-Pass-9!",
                "password2": "Strong-Pass-9!",
            },
            follow=False,
        )
        assert response.status_code == 302
        assert response.url == reverse("users:welcome")


@pytest.mark.django_db
class TestWelcomeView:
    def test_anonymous_redirected_to_login(self, client):
        response = client.get(reverse("users:welcome"), follow=False)
        assert response.status_code == 302
        assert reverse("users:login") in response.url

    def test_authenticated_renders(self, auth_client):
        response = auth_client.get(reverse("users:welcome"))
        assert response.status_code == 200
        h = response.content.decode()
        assert reverse("dashboard:index") in h
        assert reverse("home") in h
        # 가치 3가지 + CTA
        assert h.count("welcome-screen__feature") >= 3
        assert "welcome-screen__cta-btn" in h
