import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

PASSWORD = "signup-pass-2026!"


def signup_payload(**overrides):
    payload = {
        "username": "newcomer",
        "email": "newcomer@example.com",
        "password1": PASSWORD,
        "password2": PASSWORD,
        "consent": "on",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestSignupConsent:
    def test_agreeing_lets_the_account_through(self, client):
        client.post(reverse("users:signup"), signup_payload())

        assert User.objects.filter(username="newcomer").exists()

    def test_omitting_consent_blocks_the_account(self, client):
        payload = signup_payload()
        payload.pop("consent")

        response = client.post(reverse("users:signup"), payload)

        assert response.status_code == 200
        assert not User.objects.filter(username="newcomer").exists()

    def test_the_blocked_form_says_why(self, client):
        payload = signup_payload()
        payload.pop("consent")

        response = client.post(reverse("users:signup"), payload)

        assert response.context["form"].errors.get("consent")
