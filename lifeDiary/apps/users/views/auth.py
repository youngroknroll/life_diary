"""로그아웃, 회원가입, 로그인 뷰."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.translation import gettext
from django.views.decorators.http import require_POST

from apps.tags.seed_tags import create_seed_tags

from .. import login_protection
from ..account_deletion import cancel_account_deletion
from ..forms import (
    SignupForm,
)
from ..repositories import UserAccountRepository
from .verification import (
    requires_email_verification,
    start_login_verification,
    start_signup_verification,
)

_user_repo = UserAccountRepository()


@require_POST
def logout_view(request):
    """사용자 로그아웃 (POST 요청만 허용)."""
    logout(request)
    messages.success(request, gettext("성공적으로 로그아웃되었습니다."))
    return redirect("home")


def signup_view(request):
    """사용자 회원가입."""
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                create_seed_tags(user)
            return start_signup_verification(request, user)
    else:
        form = SignupForm()

    # Bootstrap 클래스 추가
    for field in form.fields.values():
        field.widget.attrs.update({"class": "form-control"})

    return render(
        request, "users/signup.html", {"form": form, "page_title": gettext("회원가입")}
    )


REMEMBER_ME_DURATION_SECONDS = 60 * 60 * 24 * 14  # 14 days


def login_view(request):
    """사용자 로그인."""
    recaptcha_required = False
    failure_count = 0
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        recaptcha_required = login_protection.login_requires_recaptcha(request, username)
        if recaptcha_required:
            token = request.POST.get("g-recaptcha-response", "")
            if not login_protection.verify_recaptcha(
                token, login_protection.get_client_identifier(request)
            ):
                form = AuthenticationForm(request, data=request.POST)
                messages.error(request, gettext("reCAPTCHA 확인 후 다시 로그인해주세요."))
                for field in form.fields.values():
                    field.widget.attrs.update({"class": "form-control"})
                return render(
                    request,
                    "users/login.html",
                    {
                        "form": form,
                        "page_title": gettext("로그인"),
                        "show_recaptcha": True,
                        "recaptcha_site_key": getattr(settings, "RECAPTCHA_SITE_KEY", ""),
                        "remaining_attempts": login_protection.login_attempts_remaining(
                            login_protection.get_login_failure_count(request, username)
                        ),
                    },
                )
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if requires_email_verification(user):
                login_protection.reset_login_failures(request, username)
                return start_login_verification(request, user)
            login(request, user)
            login_protection.reset_login_failures(request, username)
            # Remember me: 체크 시 14일 유지, 미체크 시 브라우저 종료 시 만료
            if request.POST.get("remember_me"):
                request.session.set_expiry(REMEMBER_ME_DURATION_SECONDS)
            else:
                request.session.set_expiry(0)
            messages.success(
                request,
                gettext("%(username)s님, 환영합니다!") % {"username": user.username},
            )
            return redirect("home")
        pending_user = _get_pending_deletion_user_for_login(username, request.POST.get("password"))
        if pending_user and cancel_account_deletion(pending_user):
            login(request, pending_user, backend="django.contrib.auth.backends.ModelBackend")
            login_protection.reset_login_failures(request, username)
            messages.success(
                request,
                gettext("계정 탈퇴 요청이 취소되었습니다. 다시 로그인되었습니다."),
            )
            return redirect("home")
        failure_count = login_protection.record_login_failure(request, username)
        recaptcha_required = (
            login_protection.login_recaptcha_enabled()
            and failure_count >= login_protection.login_failure_limit()
        )
    else:
        form = AuthenticationForm()

    # Bootstrap 클래스 추가
    for field in form.fields.values():
        field.widget.attrs.update({"class": "form-control"})

    return render(
        request,
        "users/login.html",
        {
            "form": form,
            "page_title": gettext("로그인"),
            "show_recaptcha": recaptcha_required,
            "recaptcha_site_key": getattr(settings, "RECAPTCHA_SITE_KEY", ""),
            "remaining_attempts": login_protection.login_attempts_remaining(failure_count),
        },
    )


def _get_pending_deletion_user_for_login(username, password):
    if not username or not password:
        return None
    user = _user_repo.find_inactive_with_pending_deletion(username)
    if user and check_password(password, user.password):
        return user
    return None
