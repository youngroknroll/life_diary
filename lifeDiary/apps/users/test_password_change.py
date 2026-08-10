import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

CURRENT_PASSWORD = "old-pass-2026!"
NEW_PASSWORD = "new-pass-2026!"


@pytest.fixture
def member(db):
    return User.objects.create_user(username="youngrok", password=CURRENT_PASSWORD)


@pytest.mark.django_db
class TestPasswordChangeAccess:
    def test_anonymous_visitor_is_sent_to_login(self, client):
        response = client.get(reverse("users:password_change"))

        assert response.status_code == 302
        assert reverse("users:login") in response.url

    def test_signed_in_member_sees_the_form(self, client, member):
        client.force_login(member)

        response = client.get(reverse("users:password_change"))

        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordChange:
    def test_correct_current_password_changes_it(self, client, member):
        client.force_login(member)

        response = client.post(
            reverse("users:password_change"),
            {
                "old_password": CURRENT_PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )

        assert response.status_code == 302
        member.refresh_from_db()
        assert member.check_password(NEW_PASSWORD)

    def test_member_stays_signed_in_after_changing(self, client, member):
        client.force_login(member)

        client.post(
            reverse("users:password_change"),
            {
                "old_password": CURRENT_PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )

        assert client.get(reverse("users:mypage")).status_code == 200

    def test_wrong_current_password_leaves_it_alone(self, client, member):
        client.force_login(member)

        response = client.post(
            reverse("users:password_change"),
            {
                "old_password": "not-the-current-one",
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )

        assert response.status_code == 200
        member.refresh_from_db()
        assert member.check_password(CURRENT_PASSWORD)

    def test_mismatched_confirmation_leaves_it_alone(self, client, member):
        client.force_login(member)

        response = client.post(
            reverse("users:password_change"),
            {
                "old_password": CURRENT_PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": "something-else-2026!",
            },
        )

        assert response.status_code == 200
        member.refresh_from_db()
        assert member.check_password(CURRENT_PASSWORD)
