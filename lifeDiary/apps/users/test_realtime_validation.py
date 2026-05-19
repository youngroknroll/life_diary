"""signup 실시간 검증 endpoint 회귀 테스트.

- /accounts/signup/check-username/ : 빈값/너무 김/규칙위반/중복/사용가능
- /accounts/signup/check-email/    : 빈값/형식오류/중복/사용가능
- signup.html: data 속성 + 스크립트 로드
"""
import json
import secrets
import pytest
from django.test import override_settings
from django.urls import reverse

# Test-only password generated per run (no real credential).
_TEST_PASSWORD = secrets.token_urlsafe(16)


def _get_json(client, url, **params):
    response = client.get(url, params)
    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/json")
    return response.status_code, json.loads(response.content)


@pytest.mark.django_db
class TestCheckUsername:
    def test_empty(self, client):
        _, data = _get_json(client, reverse("users:check_username"))
        assert data["available"] is False
        assert data["message"]

    def test_too_long(self, client):
        _, data = _get_json(client, reverse("users:check_username"), username="a" * 31)
        assert data["available"] is False

    def test_invalid_chars(self, client):
        _, data = _get_json(client, reverse("users:check_username"), username="홍길동$")
        assert data["available"] is False

    def test_taken(self, client, make_user):
        make_user(username="taken_one", password=_TEST_PASSWORD)
        _, data = _get_json(client, reverse("users:check_username"), username="taken_one")
        assert data["available"] is False

    def test_taken_case_insensitive(self, client, make_user):
        make_user(username="MixedCase", password=_TEST_PASSWORD)
        _, data = _get_json(client, reverse("users:check_username"), username="mixedcase")
        assert data["available"] is False

    def test_available(self, client):
        _, data = _get_json(client, reverse("users:check_username"), username="brand_new_42")
        assert data["available"] is True

    @override_settings(
        VALIDATION_RATE_LIMIT_MAX_ATTEMPTS=2,
        VALIDATION_RATE_LIMIT_WINDOW_SECONDS=60,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "users-test-check-username-rate-limit",
            }
        },
    )
    def test_rate_limited_returns_generic_unavailable_response(self, client):
        url = reverse("users:check_username")

        _, first = _get_json(client, url, username="brand_new_42")
        _, second = _get_json(client, url, username="brand_new_42")
        status, third = _get_json(client, url, username="brand_new_42")

        assert status == 200
        assert first["available"] is True
        assert second["available"] is True
        assert third["available"] is False
        assert third["message"]

    @override_settings(
        VALIDATION_RATE_LIMIT_MAX_ATTEMPTS=2,
        VALIDATION_RATE_LIMIT_WINDOW_SECONDS=60,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "users-test-check-username-xff-bypass",
            }
        },
    )
    def test_rate_limit_ignores_spoofed_forwarded_for_header(self, client):
        url = reverse("users:check_username")
        environ = {"REMOTE_ADDR": "10.0.0.1"}

        _, first = _get_json(
            client,
            url,
            username="brand_new_42",
            **environ,
            HTTP_X_FORWARDED_FOR="1.1.1.1",
        )
        _, second = _get_json(
            client,
            url,
            username="brand_new_42",
            **environ,
            HTTP_X_FORWARDED_FOR="2.2.2.2",
        )
        status, third = _get_json(
            client,
            url,
            username="brand_new_42",
            **environ,
            HTTP_X_FORWARDED_FOR="3.3.3.3",
        )

        assert status == 200
        assert first["available"] is True
        assert second["available"] is True
        assert third["available"] is False


@pytest.mark.django_db
class TestCheckEmail:
    def test_empty(self, client):
        _, data = _get_json(client, reverse("users:check_email"))
        assert data["available"] is False

    def test_invalid_format(self, client):
        _, data = _get_json(client, reverse("users:check_email"), email="not-an-email")
        assert data["available"] is False

    def test_taken(self, client, make_user):
        make_user(
            username="user_email_taken",
            email="taken@example.com",
            password=_TEST_PASSWORD,
        )
        _, data = _get_json(client, reverse("users:check_email"), email="taken@example.com")
        assert data["available"] is False

    def test_taken_case_insensitive(self, client, make_user):
        make_user(
            username="case_email_user",
            email="Case@Example.com",
            password=_TEST_PASSWORD,
        )
        _, data = _get_json(client, reverse("users:check_email"), email="case@example.com")
        assert data["available"] is False

    def test_available(self, client):
        _, data = _get_json(client, reverse("users:check_email"), email="fresh@example.com")
        assert data["available"] is True

    @override_settings(
        VALIDATION_RATE_LIMIT_MAX_ATTEMPTS=2,
        VALIDATION_RATE_LIMIT_WINDOW_SECONDS=60,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "users-test-check-email-rate-limit",
            }
        },
    )
    def test_rate_limited_returns_generic_unavailable_response(self, client):
        url = reverse("users:check_email")

        _, first = _get_json(client, url, email="fresh@example.com")
        _, second = _get_json(client, url, email="fresh@example.com")
        status, third = _get_json(client, url, email="fresh@example.com")

        assert status == 200
        assert first["available"] is True
        assert second["available"] is True
        assert third["available"] is False
        assert third["message"]

    @override_settings(
        VALIDATION_RATE_LIMIT_MAX_ATTEMPTS=2,
        VALIDATION_RATE_LIMIT_WINDOW_SECONDS=60,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "users-test-check-email-en-rate-limit",
            }
        },
    )
    def test_rate_limited_message_respects_english_locale(self, en_client):
        url = reverse("users:check_email")

        _get_json(en_client, url, email="fresh@example.com")
        _get_json(en_client, url, email="fresh@example.com")
        _, third = _get_json(en_client, url, email="fresh@example.com")

        assert third["available"] is False
        assert third["message"] == "Please try again later."


@pytest.mark.django_db
class TestSignupTemplateWiring:
    def test_signup_includes_data_attrs_and_script(self, client):
        response = client.get(reverse("users:signup"))
        assert response.status_code == 200
        h = response.content.decode()
        assert reverse("users:check_username") in h
        assert reverse("users:check_email") in h
        assert "signup-validate.js" in h
        assert 'novalidate' in h
