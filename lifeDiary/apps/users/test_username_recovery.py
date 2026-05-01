import pytest
from django.core import mail
from django.urls import reverse


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
