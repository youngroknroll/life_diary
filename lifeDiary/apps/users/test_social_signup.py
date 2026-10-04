"""구글 소셜 가입 — 약관 동의, 이메일 충돌, 이메일 인증 상태."""
from datetime import timedelta

import pytest
from allauth.account.models import EmailAddress
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.tags.models import Tag
from apps.tags.seed_tags import SEED_TAGS
from apps.users.account_deletion import request_account_deletion
from apps.users.email_verification import is_email_verified
from apps.users.models import AccountDeletionRequest
from apps.users.social_forms import SocialSignupForm

User = get_user_model()


def make_social_login(email="jiwoo@example.com", email_verified=True):
    provider = get_adapter().get_provider(RequestFactory().get("/"), "google")
    return SocialLogin(
        user=User(username="", email=email),
        account=SocialAccount(provider="google", uid="google-uid-1"),
        email_addresses=[
            EmailAddress(email=email, verified=email_verified, primary=True)
        ],
        provider=provider,
    )


def social_signup_request(rf):
    request = rf.post("/accounts/google/signup/")
    request.user = AnonymousUser()
    SessionMiddleware(lambda req: None).process_request(request)
    request.session.save()
    return request


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

    def test_signup_gives_the_account_the_same_seed_tags_as_local_signup(self, rf):
        form = SocialSignupForm(
            sociallogin=make_social_login(),
            data={
                "username": "jiwoo",
                "email": "jiwoo@example.com",
                "consent": "on",
            },
        )
        assert form.is_valid(), form.errors

        user = form.save(social_signup_request(rf))

        assert Tag.objects.filter(user=user).count() == len(SEED_TAGS)

    def test_failed_seed_tags_leave_no_account_behind(self, rf, monkeypatch):
        def failing_seed(user):
            raise RuntimeError("seed failure")

        monkeypatch.setattr("apps.users.social_forms.create_seed_tags", failing_seed)
        form = SocialSignupForm(
            sociallogin=make_social_login(),
            data={
                "username": "jiwoo",
                "email": "jiwoo@example.com",
                "consent": "on",
            },
        )
        assert form.is_valid(), form.errors

        with pytest.raises(RuntimeError):
            form.save(social_signup_request(rf))

        assert not User.objects.filter(username="jiwoo").exists()
        assert not SocialAccount.objects.exists()

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


def start_pending_signup(client, email="jiwoo@example.com", email_verified=True):
    session = client.session
    session["socialaccount_sociallogin"] = make_social_login(
        email, email_verified
    ).serialize()
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

    def test_signup_ignores_a_posted_email_the_provider_did_not_supply(self, client):
        start_pending_signup(client, email="jiwoo@example.com")

        client.post(
            reverse("socialaccount_signup"),
            {"username": "jiwoo", "email": "victim@example.com", "consent": "on"},
        )

        user = User.objects.get(username="jiwoo")
        assert user.email == "jiwoo@example.com"
        assert not User.objects.filter(email="victim@example.com").exists()

    def test_a_posted_email_the_provider_did_not_supply_is_never_verified(
        self, client
    ):
        start_pending_signup(client, email="jiwoo@example.com")

        client.post(
            reverse("socialaccount_signup"),
            {"username": "jiwoo", "email": "victim@example.com", "consent": "on"},
        )

        assert not EmailAddress.objects.filter(email="victim@example.com").exists()
        assert not User.objects.filter(
            email="victim@example.com", email_verification__verified_at__isnull=False
        ).exists()

    def test_an_email_the_provider_did_not_verify_does_not_verify_the_account(
        self, client
    ):
        start_pending_signup(client, email_verified=False)

        client.post(
            reverse("socialaccount_signup"),
            {"username": "jiwoo", "email": "jiwoo@example.com", "consent": "on"},
        )

        user = User.objects.get(username="jiwoo")
        assert not is_email_verified(user)

    def test_taken_email_shows_the_conflict_screen(self, client, make_user):
        make_user(username="existing", email="jiwoo@example.com")
        start_pending_signup(client)

        response = client.get(reverse("socialaccount_signup"))

        assert response.status_code == 200
        assert response.context["form"].conflicting_email == "jiwoo@example.com"


def linked_google_login(make_user):
    user = make_user(username="linked", email="linked@example.com")
    account = SocialAccount.objects.create(
        user=user, provider="google", uid="google-uid-linked"
    )
    return user, SocialLogin(user=user, account=account)


@pytest.mark.django_db
class TestGoogleLoginDuringDeletionGrace:
    def test_login_within_the_grace_period_cancels_the_deletion(
        self, rf, make_user
    ):
        user, sociallogin = linked_google_login(make_user)
        request_account_deletion(user)

        get_adapter().pre_social_login(rf.get("/"), sociallogin)

        user.refresh_from_db()
        assert user.is_active
        assert AccountDeletionRequest.objects.get(user=user).cancelled_at is not None

    def test_login_after_the_grace_period_leaves_the_account_inactive(
        self, rf, make_user
    ):
        user, sociallogin = linked_google_login(make_user)
        request_account_deletion(user, now=timezone.now() - timedelta(days=16))

        get_adapter().pre_social_login(rf.get("/"), sociallogin)

        user.refresh_from_db()
        assert not user.is_active
        assert AccountDeletionRequest.objects.get(user=user).cancelled_at is None
