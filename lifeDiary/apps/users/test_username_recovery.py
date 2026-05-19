import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from smtplib import SMTPServerDisconnected


@pytest.mark.django_db
class TestUsernameRecovery:
    def test_known_email_sends_username(self, client, make_user):
        make_user(username="alice", email="alice@example.com")
        response = client.post(
            reverse("users:username_recovery"), {"email": "alice@example.com"}
        )
        assert response.status_code == 302
        assert response.url == reverse("users:username_recovery_done")
        assert len(mail.outbox) == 1
        assert "alice" in mail.outbox[0].body
        assert "alice@example.com" in mail.outbox[0].to

    def test_unknown_email_no_mail_same_response(self, client):
        response = client.post(
            reverse("users:username_recovery"), {"email": "ghost@example.com"}
        )
        assert response.status_code == 302
        assert response.url == reverse("users:username_recovery_done")
        assert len(mail.outbox) == 0

    def test_multiple_accounts_same_email(self, client, make_user):
        make_user(username="alice", email="shared@example.com")
        make_user(username="bob", email="shared@example.com")
        response = client.post(
            reverse("users:username_recovery"), {"email": "shared@example.com"}
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 1
        body = mail.outbox[0].body
        assert "alice" in body
        assert "bob" in body

    def test_case_insensitive_email_match(self, client, make_user):
        make_user(username="alice", email="alice@example.com")
        response = client.post(
            reverse("users:username_recovery"), {"email": "ALICE@example.com"}
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 1

    def test_mail_server_disconnect_still_returns_done(
        self, client, make_user, monkeypatch
    ):
        make_user(username="alice", email="alice@example.com")

        def raise_disconnect(*args, **kwargs):
            raise SMTPServerDisconnected("please run connect() first")

        monkeypatch.setattr("apps.users.views.send_mail", raise_disconnect)

        response = client.post(
            reverse("users:username_recovery"), {"email": "alice@example.com"}
        )

        assert response.status_code == 302
        assert response.url == reverse("users:username_recovery_done")

    @override_settings(
        RECOVERY_RATE_LIMIT_MAX_ATTEMPTS=2,
        RECOVERY_RATE_LIMIT_WINDOW_SECONDS=60,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "users-test-username-recovery-rate-limit",
            }
        },
    )
    def test_recovery_is_rate_limited_without_changing_redirect_contract(
        self, client, make_user
    ):
        make_user(username="alice", email="alice@example.com")

        first = client.post(reverse("users:username_recovery"), {"email": "alice@example.com"})
        second = client.post(reverse("users:username_recovery"), {"email": "alice@example.com"})
        third = client.post(reverse("users:username_recovery"), {"email": "alice@example.com"})

        assert first.status_code == 302
        assert second.status_code == 302
        assert third.status_code == 302
        assert first.url == reverse("users:username_recovery_done")
        assert second.url == reverse("users:username_recovery_done")
        assert third.url == reverse("users:username_recovery_done")
        assert len(mail.outbox) == 2
