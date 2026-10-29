"""이메일로 받은 코드를 확인해 비밀번호를 재설정하는 뷰."""

from datetime import datetime

from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods, require_POST

from .. import login_protection, verification_policy
from ..email_verification import (
    PASSWORD_RESET,
    VerificationOutcome,
    VerificationStatus,
    issue_and_send,
    mark_email_verified,
    verify_code,
)
from ..forms import (
    PasswordResetEmailForm,
    VerificationCodeForm,
)
from ..repositories import UserAccountRepository
from .verification import resend_verification, verification_context

_user_repo = UserAccountRepository()


PASSWORD_RESET_EMAIL_KEY = "password_reset_email"


PASSWORD_RESET_CANDIDATES_KEY = "password_reset_candidate_ids"


PASSWORD_RESET_VERIFIED_KEY = "password_reset_verified_user_id"


PASSWORD_RESET_VERIFIED_AT_KEY = "password_reset_verified_at"


def _clear_password_reset_session(request):
    for key in (
        PASSWORD_RESET_EMAIL_KEY,
        PASSWORD_RESET_CANDIDATES_KEY,
        PASSWORD_RESET_VERIFIED_KEY,
        PASSWORD_RESET_VERIFIED_AT_KEY,
    ):
        request.session.pop(key, None)


def _send_password_reset_codes(request, email):
    """가입 여부와 무관하게 같은 다음 화면으로 보낸다."""
    _clear_password_reset_session(request)
    request.session[PASSWORD_RESET_EMAIL_KEY] = email
    request.session[PASSWORD_RESET_CANDIDATES_KEY] = []

    if login_protection.is_rate_limited(
        request,
        "password-reset",
        "RECOVERY_RATE_LIMIT_MAX_ATTEMPTS",
        "RECOVERY_RATE_LIMIT_WINDOW_SECONDS",
    ):
        return

    users = _user_repo.find_active_by_email(email)
    request.session[PASSWORD_RESET_CANDIDATES_KEY] = [user.pk for user in users]
    for user in users:
        issue_and_send(user, PASSWORD_RESET)


def _password_reset_candidates(request):
    ids = request.session.get(PASSWORD_RESET_CANDIDATES_KEY) or []
    return [user for user in (_user_repo.find_by_id(pk) for pk in ids) if user]


def _match_password_reset_code(candidates, raw_code):
    """한 이메일에 여러 계정이 있을 수 있어 후보를 모두 시도한다."""
    last_outcome = None
    for user in candidates:
        outcome = verify_code(user, PASSWORD_RESET, raw_code)
        if outcome.ok:
            return user, outcome
        last_outcome = outcome
    return None, last_outcome


@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    """이메일을 받아 재설정 코드를 보낸다."""
    if request.method == "POST":
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            _send_password_reset_codes(request, form.cleaned_data["email"])
            return redirect("users:password_reset_verify")
    else:
        form = PasswordResetEmailForm()

    return render(
        request,
        "users/password/password_reset_form.html",
        {"form": form, "page_title": gettext("비밀번호 재설정")},
    )


@require_http_methods(["GET", "POST"])
def password_reset_verify_view(request):
    """이메일로 받은 재설정 코드를 확인한다."""
    email = request.session.get(PASSWORD_RESET_EMAIL_KEY)
    if not email:
        return redirect("users:password_reset")

    candidates = _password_reset_candidates(request)
    form = VerificationCodeForm(request.POST or None)
    outcome = None
    if request.method == "POST" and form.is_valid():
        user, outcome = _match_password_reset_code(candidates, form.cleaned_data["code"])
        if user is not None:
            mark_email_verified(user)
            request.session[PASSWORD_RESET_VERIFIED_KEY] = user.pk
            request.session[PASSWORD_RESET_VERIFIED_AT_KEY] = timezone.now().isoformat()
            return redirect("users:password_reset_set")
        outcome = outcome or VerificationOutcome(VerificationStatus.INVALID)
        form = VerificationCodeForm()

    return render(
        request,
        "users/verification/verify_code.html",
        verification_context(
            email,
            candidates[0] if candidates else None,
            PASSWORD_RESET,
            form,
            outcome,
            page_title=gettext("비밀번호 재설정"),
            heading=gettext("메일로 보낸 코드를 입력하세요"),
            resend_url=reverse("users:password_reset_resend"),
            back_url=reverse("users:login"),
            back_label=gettext("로그인으로 돌아가기"),
            # 가입 화면과 달리 남은 횟수를 숨긴다. 가입되지 않은 주소는 셀 코드
            # 자체가 없어, 숫자가 보이는지 여부로 가입 여부가 드러난다.
            attempts_remaining=None,
        ),
    )


@require_POST
def password_reset_resend_view(request):
    """재설정 코드를 다시 보낸다."""
    if not request.session.get(PASSWORD_RESET_EMAIL_KEY):
        return redirect("users:password_reset")
    for user in _password_reset_candidates(request):
        resend_verification(request, user, PASSWORD_RESET)
    return redirect("users:password_reset_verify")


def _verified_password_reset_user(request):
    user_id = request.session.get(PASSWORD_RESET_VERIFIED_KEY)
    verified_at = request.session.get(PASSWORD_RESET_VERIFIED_AT_KEY)
    if not user_id or not verified_at:
        return None

    elapsed = (timezone.now() - datetime.fromisoformat(verified_at)).total_seconds()
    if elapsed > verification_policy.reset_session_ttl_seconds():
        _clear_password_reset_session(request)
        return None
    return _user_repo.find_by_id(user_id)


@require_http_methods(["GET", "POST"])
def password_reset_set_view(request):
    """코드 확인을 마친 사용자의 새 비밀번호를 저장한다."""
    user = _verified_password_reset_user(request)
    if user is None:
        return redirect("users:password_reset")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            _clear_password_reset_session(request)
            request.session.cycle_key()
            return redirect("users:password_reset_complete")
    else:
        form = SetPasswordForm(user)

    return render(
        request,
        "users/password/password_reset_set.html",
        {"form": form, "page_title": gettext("새 비밀번호 설정")},
    )
