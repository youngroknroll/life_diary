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

    def test_signup_rejects_username_over_30_chars(self, client):
        too_long = "a" * 31
        response = self._post(client, username=too_long)
        assert response.status_code == 200
        assert not User.objects.filter(username=too_long).exists()

    def test_signup_accepts_username_exactly_30_chars(self, client):
        boundary = "a" * 30
        response = self._post(client, username=boundary)
        assert response.status_code == 302
        assert User.objects.filter(username=boundary).exists()

    def test_signup_accepts_username_between_old_and_new_limit(self, client):
        """과거 10자 제한 → 30자 완화. 11~30자 사용자명도 허용되어야 한다."""
        mid = "abcdefghijk"  # 11자, 과거에는 거부됐던 길이
        response = self._post(client, username=mid)
        assert response.status_code == 302
        assert User.objects.filter(username=mid).exists()
