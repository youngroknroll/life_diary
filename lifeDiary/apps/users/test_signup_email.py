import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


@pytest.mark.django_db
class TestSignupEmail:
    def _post(self, client, **overrides):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "pass-Long-9!",
            "password2": "pass-Long-9!",
        }
        data.update(overrides)
        return client.post(reverse("users:signup"), data)

    def test_signup_persists_email(self, client):
        response = self._post(client)
        assert response.status_code == 302
        user = User.objects.get(username="newuser")
        assert user.email == "newuser@example.com"

    def test_signup_requires_email(self, client):
        response = self._post(client, email="")
        assert response.status_code == 200
        assert not User.objects.filter(username="newuser").exists()

    def test_signup_rejects_duplicate_email(self, client, make_user):
        make_user(username="existing", email="dup@example.com")
        response = self._post(client, email="dup@example.com")
        assert response.status_code == 200
        assert not User.objects.filter(username="newuser").exists()

    def test_signup_rejects_duplicate_email_case_insensitive(self, client, make_user):
        make_user(username="existing", email="dup@example.com")
        response = self._post(client, email="DUP@example.com")
        assert response.status_code == 200
        assert not User.objects.filter(username="newuser").exists()

    def test_signup_rejects_username_over_10_chars(self, client):
        response = self._post(client, username="abcdefghijk")  # 11
        assert response.status_code == 200
        assert not User.objects.filter(username="abcdefghijk").exists()

    def test_signup_accepts_username_exactly_10_chars(self, client):
        response = self._post(client, username="abcdefghij")  # 10
        assert response.status_code == 302
        assert User.objects.filter(username="abcdefghij").exists()
