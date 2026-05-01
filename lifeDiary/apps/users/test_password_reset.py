import re
import pytest
from django.core import mail
from django.urls import reverse


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
