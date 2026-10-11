from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login
from django.utils.translation import gettext
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from ..forms import (
    VerificationCodeForm,
)
from .. import verification_policy
from ..email_verification import (
    SIGNUP,
    ResendBlocked,
    VerificationStatus,
    ensure_active_code,
    is_email_verified,
    issue_and_send,
    mark_email_verified,
    mask_email,
    resend_and_send,
    seconds_until_expiry,
    seconds_until_resend_allowed,
    start_verification,
    verify_code,
)
from ..repositories import UserAccountRepository

_user_repo = UserAccountRepository()


SIGNUP_VERIFICATION_SESSION_KEY = "signup_verification_user_id"


def start_signup_verification(request, user):
    """가입 직후 이메일 인증 단계로 넘긴다."""
    if not verification_policy.is_enabled():
        mark_email_verified(user)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("users:welcome")

    start_verification(user)
    issue_and_send(user, SIGNUP)
    request.session[SIGNUP_VERIFICATION_SESSION_KEY] = user.pk
    return redirect("users:signup_verify")


def requires_email_verification(user):
    return verification_policy.is_enabled() and not is_email_verified(user)


def start_login_verification(request, user):
    start_verification(user)
    ensure_active_code(user, SIGNUP)
    request.session[SIGNUP_VERIFICATION_SESSION_KEY] = user.pk
    messages.info(
        request,
        gettext("이메일 인증을 마쳐야 로그인할 수 있습니다. 메일로 보낸 코드를 입력해주세요."),
    )
    return redirect("users:signup_verify")


def _pending_verification_user(request):
    user_id = request.session.get(SIGNUP_VERIFICATION_SESSION_KEY)
    return _user_repo.find_by_id(user_id) if user_id else None


def _verification_error_message(outcome):
    if outcome.status is VerificationStatus.EXPIRED:
        return gettext("코드가 만료되었습니다. 코드를 다시 받아주세요.")
    if outcome.status is VerificationStatus.LOCKED:
        return gettext("입력 횟수를 넘겼습니다. 코드를 다시 받아주세요.")
    if outcome.status is VerificationStatus.MISSING:
        return gettext("유효한 코드가 없습니다. 코드를 다시 받아주세요.")
    return gettext("코드가 맞지 않습니다.")


def verification_context(email, user, purpose, form, outcome=None, **extra):
    """코드 화면 컨텍스트.

    `user`가 없어도 화면은 똑같이 그려진다. 재설정 흐름에서 가입되지 않은
    주소를 구분할 수 없게 하려면 타이머까지 같아야 한다.
    """
    if user is not None:
        remaining_seconds = seconds_until_expiry(user, purpose)
        resend_seconds = seconds_until_resend_allowed(user, purpose)
    else:
        remaining_seconds = verification_policy.code_ttl_seconds()
        resend_seconds = verification_policy.resend_cooldown_seconds()

    context = {
        "form": form,
        "masked_email": mask_email(email),
        "expires_in_seconds": remaining_seconds,
        "expires_in_minutes": -(-remaining_seconds // 60),
        "resend_in_seconds": resend_seconds,
        "verification_error": _verification_error_message(outcome) if outcome else "",
        "attempts_remaining": outcome.attempts_remaining if outcome else None,
    }
    context.update(extra)
    return context


def resend_verification(request, user, purpose):
    try:
        resend_and_send(user, purpose)
    except ResendBlocked as blocked:
        messages.info(
            request,
            gettext("%(seconds)s초 후에 코드를 다시 받을 수 있습니다.")
            % {"seconds": blocked.retry_after_seconds},
        )
    else:
        messages.success(request, gettext("새 코드를 보냈습니다."))


@require_http_methods(["GET", "POST"])
def signup_verify_view(request):
    """가입 이메일 인증 코드 입력."""
    user = _pending_verification_user(request)
    if user is None:
        return redirect("users:login")

    form = VerificationCodeForm(request.POST or None)
    outcome = None
    if request.method == "POST" and form.is_valid():
        outcome = verify_code(user, SIGNUP, form.cleaned_data["code"])
        if outcome.ok:
            mark_email_verified(user)
            request.session.pop(SIGNUP_VERIFICATION_SESSION_KEY, None)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, gettext("이메일 인증이 끝났습니다."))
            return redirect("users:welcome")
        form = VerificationCodeForm()

    return render(
        request,
        "users/verification/verify_code.html",
        verification_context(
            user.email,
            user,
            SIGNUP,
            form,
            outcome,
            page_title=gettext("이메일 인증"),
            heading=gettext("메일로 보낸 코드를 입력하세요"),
            resend_url=reverse("users:signup_verify_resend"),
            back_url=reverse("users:login"),
            back_label=gettext("로그인으로 돌아가기"),
        ),
    )


@require_POST
def signup_verify_resend_view(request):
    user = _pending_verification_user(request)
    if user is None:
        return redirect("users:login")
    resend_verification(request, user, SIGNUP)
    return redirect("users:signup_verify")
