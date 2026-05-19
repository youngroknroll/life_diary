"""Remember me 체크박스 동작 회귀 테스트.

체크 시: 세션 만료를 14일로 명시 설정 (브라우저 종료에도 유지)
미체크 시: 세션을 브라우저 종료 시 만료 (set_expiry(0))
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestLoginRememberMe:
    def _post(self, client, **overrides):
        data = {
            "username": "loginuser",
            "password": "pass-Long-9!",
        }
        data.update(overrides)
        return client.post(reverse("users:login"), data, follow=False)

    def test_remember_me_checked_sets_14_day_expiry(self, client, make_user):
        make_user(username="loginuser", password="pass-Long-9!")
        response = self._post(client, remember_me="1")
        assert response.status_code == 302
        assert client.session.get_expiry_age() == 60 * 60 * 24 * 14

    def test_remember_me_unchecked_expires_at_browser_close(self, client, make_user):
        make_user(username="loginuser", password="pass-Long-9!")
        response = self._post(client)  # remember_me 미포함
        assert response.status_code == 302
        # set_expiry(0) → 브라우저 종료 시 만료
        assert client.session.get_expire_at_browser_close() is True

    def test_login_page_renders_remember_me_checkbox(self, client):
        response = client.get(reverse("users:login"))
        assert response.status_code == 200
        h = response.content.decode()
        assert 'name="remember_me"' in h
        assert 'id="remember_me"' in h
