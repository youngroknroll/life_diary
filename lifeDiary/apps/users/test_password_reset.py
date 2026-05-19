import re
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


@pytest.mark.django_db
class TestPasswordReset:
    def test_known_email_sends_mail(self, client, make_user):
        make_user(username="alice", email="alice@example.com")
        response = client.post(
            reverse("users:password_reset"), {"email": "alice@example.com"}
        )
        assert response.status_code == 302
        assert response.url == reverse("users:password_reset_done")
        assert len(mail.outbox) == 1
        assert "alice@example.com" in mail.outbox[0].to

    def test_unknown_email_no_mail_same_response(self, client):
        response = client.post(
            reverse("users:password_reset"), {"email": "ghost@example.com"}
        )
        assert response.status_code == 302
        assert response.url == reverse("users:password_reset_done")
        assert len(mail.outbox) == 0

    def test_full_reset_flow(self, client, make_user):
        user = make_user(username="bob", email="bob@example.com")
        client.post(reverse("users:password_reset"), {"email": "bob@example.com"})
        body = mail.outbox[0].body
        match = re.search(r"/reset/([^/]+)/([^/\s]+)/", body)
        assert match
        uidb64, token = match.group(1), match.group(2)

        confirm_url = reverse(
            "users:password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        # GET → redirects to set-password URL with session token
        get_response = client.get(confirm_url)
        assert get_response.status_code == 302

        set_password_url = get_response.url
        new_pw = "brand-new-Pass-9!"
        post_response = client.post(
            set_password_url,
            {"new_password1": new_pw, "new_password2": new_pw},
        )
        assert post_response.status_code == 302
        assert post_response.url == reverse("users:password_reset_complete")

        user.refresh_from_db()
        assert user.check_password(new_pw)

    @override_settings(
        RECOVERY_RATE_LIMIT_MAX_ATTEMPTS=2,
        RECOVERY_RATE_LIMIT_WINDOW_SECONDS=60,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "users-test-password-reset-rate-limit",
            }
        },
    )
    def test_password_reset_is_rate_limited_without_changing_redirect_contract(
        self, client, make_user
    ):
        make_user(username="alice", email="alice@example.com")

        first = client.post(reverse("users:password_reset"), {"email": "alice@example.com"})
        second = client.post(reverse("users:password_reset"), {"email": "alice@example.com"})
        third = client.post(reverse("users:password_reset"), {"email": "alice@example.com"})

        assert first.status_code == 302
        assert second.status_code == 302
        assert third.status_code == 302
        assert first.url == reverse("users:password_reset_done")
        assert second.url == reverse("users:password_reset_done")
        assert third.url == reverse("users:password_reset_done")
        assert len(mail.outbox) == 2

    def test_invalid_token_renders_invalid_link_state(self, client, make_user):
        user = make_user(username="alice", email="alice@example.com")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        response = client.get(
            reverse(
                "users:password_reset_confirm",
                kwargs={"uidb64": uidb64, "token": "bad-token"},
            )
        )

        assert response.status_code == 200
        assert "재설정 링크가 유효하지 않거나 이미 사용되었습니다." in response.content.decode()

    @override_settings(PASSWORD_RESET_TIMEOUT=60 * 60 * 3)
    def test_expired_token_renders_invalid_link_state(self, client, make_user):
        user = make_user(username="alice", email="alice@example.com")
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        issued_at = datetime(2026, 5, 19, 9, 0, 0)

        with patch(
            "django.contrib.auth.tokens.PasswordResetTokenGenerator._now",
            return_value=issued_at,
        ):
            token = default_token_generator.make_token(user)

        with patch(
            "django.contrib.auth.tokens.PasswordResetTokenGenerator._now",
            return_value=issued_at + timedelta(minutes=1),
        ):
            response = client.get(
                reverse(
                    "users:password_reset_confirm",
                    kwargs={"uidb64": uidb64, "token": token},
                )
            )
        assert response.status_code == 302

        with patch(
            "django.contrib.auth.tokens.PasswordResetTokenGenerator._now",
            return_value=issued_at + timedelta(hours=4),
        ):
            expired_response = client.get(
                reverse(
                    "users:password_reset_confirm",
                    kwargs={"uidb64": uidb64, "token": token},
                )
            )

        assert expired_response.status_code == 200
        assert (
            "재설정 링크가 유효하지 않거나 이미 사용되었습니다."
            in expired_response.content.decode()
        )

    def test_reused_token_renders_invalid_link_state(self, client, make_user):
        user = make_user(username="bob", email="bob@example.com")
        client.post(reverse("users:password_reset"), {"email": "bob@example.com"})
        body = mail.outbox[0].body
        match = re.search(r"/reset/([^/]+)/([^/\s]+)/", body)
        assert match
        uidb64, token = match.group(1), match.group(2)

        confirm_url = reverse(
            "users:password_reset_confirm", kwargs={"uidb64": uidb64, "token": token}
        )
        first_get = client.get(confirm_url)
        assert first_get.status_code == 302

        new_pw = "brand-new-Pass-9!"
        post_response = client.post(
            first_get.url,
            {"new_password1": new_pw, "new_password2": new_pw},
        )
        assert post_response.status_code == 302

        reused_response = client.get(confirm_url)
        assert reused_response.status_code == 200
        assert (
            "재설정 링크가 유효하지 않거나 이미 사용되었습니다."
            in reused_response.content.decode()
        )
