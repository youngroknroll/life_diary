"""비밀번호 재설정 — 이메일 6자리 코드 흐름.

이메일 입력 → 코드 입력 → 새 비밀번호 설정. 링크(uidb64/token) 경로는 없다.
"""
import re

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import NoReverseMatch, reverse

from apps.users.email_verification import PASSWORD_RESET, is_email_verified, issue_code

NEW_PASSWORD = "brand-new-Pass-9!"


def code_from_outbox():
    match = re.search(r"\b(\d{6})\b", mail.outbox[-1].body)
    assert match, mail.outbox[-1].body
    return match.group(1)


def request_reset(client, email="alice@example.com"):
    return client.post(reverse("users:password_reset"), {"email": email})


def verify(client, code):
    return client.post(reverse("users:password_reset_verify"), {"code": code})


def set_password(client, password=NEW_PASSWORD):
    return client.post(
        reverse("users:password_reset_set"),
        {"new_password1": password, "new_password2": password},
    )


@pytest.fixture
def alice(make_user):
    return make_user(username="alice", email="alice@example.com")


@pytest.mark.django_db
class TestResetRequest:
    def test_known_email_gets_a_code_and_goes_to_the_code_screen(self, client, alice):
        response = request_reset(client)

        assert response.status_code == 302
        assert response.url == reverse("users:password_reset_verify")
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["alice@example.com"]
        assert re.search(r"\b\d{6}\b", mail.outbox[0].body)

    def test_unknown_email_looks_identical_and_sends_nothing(self, client):
        response = request_reset(client, "ghost@example.com")

        assert response.status_code == 302
        assert response.url == reverse("users:password_reset_verify")
        assert len(mail.outbox) == 0

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
    def test_rate_limit_stops_the_mail_without_changing_the_response(
        self, client, alice
    ):
        responses = [request_reset(client) for _ in range(3)]

        assert {response.url for response in responses} == {
            reverse("users:password_reset_verify")
        }
        assert len(mail.outbox) == 2


@pytest.mark.django_db
class TestResetCodeVerification:
    def test_correct_code_opens_the_new_password_screen(self, client, alice):
        request_reset(client)

        response = verify(client, code_from_outbox())

        assert response.status_code == 302
        assert response.url == reverse("users:password_reset_set")
        assert client.get(reverse("users:password_reset_set")).status_code == 200

    def test_wrong_code_does_not_open_the_new_password_screen(self, client, alice):
        request_reset(client)
        correct = code_from_outbox()

        verify(client, "000000" if correct != "000000" else "111111")

        assert client.get(reverse("users:password_reset_set")).status_code == 302

    def test_verifying_the_code_also_verifies_the_email(self, client, alice):
        from apps.users.models import EmailVerification

        EmailVerification.objects.filter(user=alice).update(verified_at=None)
        request_reset(client)

        verify(client, code_from_outbox())

        assert is_email_verified(alice)

    def test_code_screen_without_a_request_redirects_to_the_email_step(self, client):
        response = client.get(reverse("users:password_reset_verify"))

        assert response.status_code == 302
        assert response.url == reverse("users:password_reset")


@pytest.mark.django_db
class TestNewPassword:
    def test_saved_password_is_the_one_that_logs_in(self, client, alice):
        request_reset(client)
        verify(client, code_from_outbox())

        response = set_password(client)

        assert response.status_code == 302
        assert response.url == reverse("users:password_reset_complete")
        alice.refresh_from_db()
        assert alice.check_password(NEW_PASSWORD)

    def test_new_password_screen_is_closed_without_a_verified_code(self, client, alice):
        request_reset(client)

        response = set_password(client)

        assert response.status_code == 302
        assert response.url == reverse("users:password_reset")
        alice.refresh_from_db()
        assert not alice.check_password(NEW_PASSWORD)

    @override_settings(PASSWORD_RESET_SESSION_TTL_SECONDS=0)
    def test_verified_session_expires(self, client, alice):
        request_reset(client)
        verify(client, code_from_outbox())

        response = client.get(reverse("users:password_reset_set"))

        assert response.status_code == 302
        assert response.url == reverse("users:password_reset")

    def test_code_cannot_be_replayed_after_the_password_changed(self, client, alice):
        request_reset(client)
        code = code_from_outbox()
        verify(client, code)
        set_password(client)

        request_reset(client)
        replay = verify(client, code)

        assert replay.status_code == 200
        assert client.get(reverse("users:password_reset_set")).status_code == 302

    def test_completed_reset_lets_the_user_log_in(self, client, alice):
        request_reset(client)
        verify(client, code_from_outbox())
        set_password(client)

        response = client.post(
            reverse("users:login"),
            {"username": "alice", "password": NEW_PASSWORD},
        )

        assert "_auth_user_id" in client.session
        assert response.url == reverse("home")


@pytest.mark.django_db
class TestResendCode:
    def test_resend_within_cooldown_sends_nothing(self, client, alice):
        request_reset(client)

        client.post(reverse("users:password_reset_resend"))

        assert len(mail.outbox) == 1

    @override_settings(EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=0)
    def test_resend_sends_a_working_code(self, client, alice):
        request_reset(client)

        client.post(reverse("users:password_reset_resend"))
        response = verify(client, code_from_outbox())

        assert len(mail.outbox) == 2
        assert response.url == reverse("users:password_reset_set")


@pytest.mark.django_db
class TestLinkFlowIsGone:
    def test_token_link_route_no_longer_exists(self):
        with pytest.raises(NoReverseMatch):
            reverse(
                "users:password_reset_confirm",
                kwargs={"uidb64": "abc", "token": "def"},
            )

    def test_allauth_reset_route_no_longer_exists(self):
        with pytest.raises(NoReverseMatch):
            reverse("account_reset_password")

    def test_old_link_url_is_not_served(self, client):
        assert client.get("/accounts/reset/abc/def-ghi/").status_code == 404
        assert client.get("/accounts/password/reset/").status_code == 404
