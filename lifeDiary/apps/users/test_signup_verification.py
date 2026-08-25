import re

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from apps.users.email_verification import (
    SIGNUP,
    is_email_verified,
    issue_code,
    mark_email_verified,
    start_verification,
)

SIGNUP_PAYLOAD = {
    "username": "newbie",
    "email": "newbie@example.com",
    "password1": "Str0ngPass!2026",
    "password2": "Str0ngPass!2026",
    "consent": "on",
}


def code_from_outbox():
    match = re.search(r"\b(\d{6})\b", mail.outbox[-1].body)
    assert match, mail.outbox[-1].body
    return match.group(1)


def signed_in(client):
    return "_auth_user_id" in client.session


@pytest.mark.django_db
class TestSignupIssuesCode:
    def test_signup_does_not_open_a_session(self, client):
        client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        assert not signed_in(client)

    def test_signup_sends_one_code_email_to_the_new_address(self, client):
        client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["newbie@example.com"]
        assert re.search(r"\b\d{6}\b", mail.outbox[0].body)

    def test_signup_redirects_to_the_code_screen(self, client):
        response = client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        assert response.status_code == 302
        assert response.url == reverse("users:signup_verify")

    def test_new_account_starts_unverified(self, client, django_user_model):
        client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        user = django_user_model.objects.get(username="newbie")
        assert not is_email_verified(user)


@pytest.mark.django_db
class TestSignupVerification:
    def test_correct_code_verifies_and_signs_in(self, client, django_user_model):
        client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        response = client.post(
            reverse("users:signup_verify"), {"code": code_from_outbox()}
        )

        assert response.status_code == 302
        assert response.url == reverse("users:welcome")
        assert signed_in(client)
        assert is_email_verified(django_user_model.objects.get(username="newbie"))

    def test_wrong_code_keeps_the_visitor_out(self, client):
        client.post(reverse("users:signup"), SIGNUP_PAYLOAD)
        correct = code_from_outbox()

        response = client.post(
            reverse("users:signup_verify"),
            {"code": "000000" if correct != "000000" else "111111"},
        )

        assert response.status_code == 200
        assert not signed_in(client)

    def test_code_screen_without_a_pending_signup_redirects_to_login(self, client):
        response = client.get(reverse("users:signup_verify"))

        assert response.status_code == 302
        assert response.url == reverse("users:login")

    def test_resend_within_cooldown_does_not_send_another_mail(self, client):
        client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        client.post(reverse("users:signup_verify_resend"))

        assert len(mail.outbox) == 1

    @override_settings(EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS=0)
    def test_resend_sends_a_working_code(self, client):
        client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        client.post(reverse("users:signup_verify_resend"))
        response = client.post(
            reverse("users:signup_verify"), {"code": code_from_outbox()}
        )

        assert len(mail.outbox) == 2
        assert response.url == reverse("users:welcome")


@pytest.mark.django_db
class TestLoginGate:
    def test_unverified_account_cannot_open_a_session(
        self, client, make_user, test_password
    ):
        user = make_user(username="pending", email="pending@example.com")
        start_verification(user)

        response = client.post(
            reverse("users:login"), {"username": "pending", "password": test_password}
        )

        assert not signed_in(client)
        assert response.status_code == 302
        assert response.url == reverse("users:signup_verify")

    def test_gated_login_sends_a_code_when_none_is_active(
        self, client, make_user, test_password
    ):
        user = make_user(username="pending", email="pending@example.com")
        start_verification(user)

        client.post(
            reverse("users:login"), {"username": "pending", "password": test_password}
        )

        assert len(mail.outbox) == 1

    def test_gated_login_reuses_a_still_valid_code(
        self, client, make_user, test_password
    ):
        user = make_user(username="pending", email="pending@example.com")
        start_verification(user)
        issue_code(user, SIGNUP)

        client.post(
            reverse("users:login"), {"username": "pending", "password": test_password}
        )

        assert len(mail.outbox) == 0

    def test_verified_account_logs_in_as_before(
        self, client, make_user, test_password
    ):
        user = make_user(username="settled", email="settled@example.com")
        mark_email_verified(user)

        response = client.post(
            reverse("users:login"), {"username": "settled", "password": test_password}
        )

        assert signed_in(client)
        assert response.url == reverse("home")


@pytest.mark.django_db
class TestVerificationDisabled:
    @override_settings(EMAIL_VERIFICATION_ENABLED=False)
    def test_signup_signs_in_immediately_without_a_code_email(self, client):
        response = client.post(reverse("users:signup"), SIGNUP_PAYLOAD)

        assert signed_in(client)
        assert response.url == reverse("users:welcome")
        assert len(mail.outbox) == 0
