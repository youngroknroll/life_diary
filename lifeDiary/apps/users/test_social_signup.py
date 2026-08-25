"""구글 소셜 가입 — 약관 동의, 이메일 충돌, 이메일 인증 상태."""
import pytest
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from apps.users.email_verification import is_email_verified
from apps.users.social_forms import SocialSignupForm

User = get_user_model()


def make_social_login(email="jiwoo@example.com"):
    provider = get_adapter().get_provider(RequestFactory().get("/"), "google")
    return SocialLogin(
        user=User(username="", email=email),
        account=SocialAccount(provider="google", uid="google-uid-1"),
        provider=provider,
    )


def test_auto_signup_is_off_so_consent_is_always_asked():
    assert settings.SOCIALACCOUNT_AUTO_SIGNUP is False


def test_social_signup_uses_the_consent_form():
    assert settings.SOCIALACCOUNT_FORMS["signup"] == (
        "apps.users.social_forms.SocialSignupForm"
    )


@pytest.mark.django_db
class TestSocialSignupForm:
    def test_signup_without_consent_is_rejected(self):
        form = SocialSignupForm(
            sociallogin=make_social_login(),
            data={"username": "jiwoo", "email": "jiwoo@example.com"},
        )

        assert not form.is_valid()
        assert "consent" in form.errors

    def test_signup_with_consent_is_accepted(self):
        form = SocialSignupForm(
            sociallogin=make_social_login(),
            data={
                "username": "jiwoo",
                "email": "jiwoo@example.com",
                "consent": "on",
            },
        )

        assert form.is_valid(), form.errors

    def test_taken_email_is_reported_before_the_visitor_picks_a_username(
        self, make_user
    ):
        make_user(username="existing", email="jiwoo@example.com")

        form = SocialSignupForm(sociallogin=make_social_login())

        assert form.conflicting_email == "jiwoo@example.com"

    def test_free_email_shows_no_conflict(self):
        form = SocialSignupForm(sociallogin=make_social_login())

        assert form.conflicting_email == ""


@pytest.mark.django_db
class TestSocialScreens:
    def test_cancelled_screen_renders(self, client):
        response = client.get(reverse("socialaccount_login_cancelled"))

        assert response.status_code == 200

    def test_authentication_error_screen_renders(self, client):
        """allauth 는 이 화면을 401 로 낸다. 렌더만 확인한다."""
        response = client.get(reverse("socialaccount_login_error"))

        assert response.status_code == 401

    def test_signup_screen_without_a_pending_login_goes_to_login(self, client):
        response = client.get(reverse("socialaccount_signup"))

        assert response.status_code == 302
        assert response.url == reverse("users:login")


def start_pending_signup(client, email="jiwoo@example.com"):
    session = client.session
    session["socialaccount_sociallogin"] = make_social_login(email).serialize()
    session.save()


@pytest.mark.django_db
class TestPendingSocialSignup:
    def test_screen_opens_for_a_pending_google_login(self, client):
        start_pending_signup(client)

        response = client.get(reverse("socialaccount_signup"))

        assert response.status_code == 200

    def test_signup_without_consent_creates_no_account(self, client):
        start_pending_signup(client)

        client.post(
            reverse("socialaccount_signup"),
            {"username": "jiwoo", "email": "jiwoo@example.com"},
        )

        assert not User.objects.filter(username="jiwoo").exists()

    def test_consented_signup_creates_a_verified_account(self, client):
        start_pending_signup(client)

        client.post(
            reverse("socialaccount_signup"),
            {"username": "jiwoo", "email": "jiwoo@example.com", "consent": "on"},
        )

        user = User.objects.get(username="jiwoo")
        assert is_email_verified(user)

    def test_taken_email_shows_the_conflict_screen(self, client, make_user):
        make_user(username="existing", email="jiwoo@example.com")
        start_pending_signup(client)

        response = client.get(reverse("socialaccount_signup"))

        assert response.status_code == 200
        assert response.context["form"].conflicting_email == "jiwoo@example.com"
