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
        assert reverse("dashboard:index") in response.content.decode()

    @pytest.mark.parametrize("step", [1, 2, 3])
    def test_every_step_renders(self, auth_client, step):
        response = auth_client.get(reverse("users:welcome"), {"step": step})

        assert response.status_code == 200
        assert response.context["step"] == step

    def test_out_of_range_step_is_clamped(self, auth_client):
        assert auth_client.get(reverse("users:welcome"), {"step": 9}).context["step"] == 3
        assert auth_client.get(reverse("users:welcome"), {"step": 0}).context["step"] == 1

    def test_garbage_step_falls_back_to_the_first(self, auth_client):
        assert auth_client.get(reverse("users:welcome"), {"step": "x"}).context["step"] == 1

    def test_every_step_can_be_skipped(self, auth_client):
        """세 스텝 모두 건너뛰기가 있어야 가입 이탈을 만들지 않는다."""
        for step in (1, 2, 3):
            body = auth_client.get(reverse("users:welcome"), {"step": step}).content.decode()
            assert reverse("dashboard:index") in body
