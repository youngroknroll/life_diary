import logging
import re
import json
from datetime import datetime
from smtplib import SMTPException
from urllib import parse, request as urlrequest
from urllib.error import URLError

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import (
    PasswordResetEmailForm,
    SignupForm,
    UserGoalForm,
    UserNoteForm,
    UsernameRecoveryForm,
    VerificationCodeForm,
)
from .models import UserGoal
from .account_deletion import cancel_account_deletion, request_account_deletion
from . import verification_policy
from .email_verification import (
    PASSWORD_RESET,
    SIGNUP,
    ResendBlocked,
    VerificationOutcome,
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
from .repositories import GoalRepository, NoteRepository, UserAccountRepository
from apps.tags.models import Category
from apps.tags.repositories import TagRepository
from apps.tags.seed_tags import create_seed_tags
from apps.dashboard.day_window import annotate_future, current_slot_index
from apps.dashboard.repositories import TimeBlockRepository
from apps.dashboard.services import build_slot_rows, build_time_headers
from apps.stats.aggregation.goal_progress import build_goal_progress_rows
from .use_cases import (
    DeleteGoalUseCase,
    DeleteNoteUseCase,
    GetMyPageUseCase,
    GoalData,
    NoteData,
    SaveGoalUseCase,
    SaveNoteUseCase,
)

logger = logging.getLogger(__name__)

_goal_repo = GoalRepository()
_note_repo = NoteRepository()
_tag_repo = TagRepository()
_time_block_repo = TimeBlockRepository()
_user_repo = UserAccountRepository()
_mypage_use_case = GetMyPageUseCase()
_save_goal = SaveGoalUseCase(tags=_tag_repo)
_delete_goal = DeleteGoalUseCase()
_save_note = SaveNoteUseCase()
_delete_note = DeleteNoteUseCase()


RECOVERY_RATE_LIMIT_MAX_ATTEMPTS = 5
RECOVERY_RATE_LIMIT_WINDOW_SECONDS = 60 * 10
VALIDATION_RATE_LIMIT_MAX_ATTEMPTS = 10
VALIDATION_RATE_LIMIT_WINDOW_SECONDS = 60
LOGIN_RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def _get_user_tag_queryset(user):
    """사용자 태그 쿼리셋"""
    return _tag_repo.find_accessible(user)


def _get_client_identifier(request):
    return request.META.get("REMOTE_ADDR", "unknown")


def _get_rate_limit_retry_message():
    return gettext("잠시 후 다시 시도해주세요.")


def _is_rate_limited(request, scope, max_attempts_setting, window_setting):
    max_attempts = getattr(settings, max_attempts_setting, globals()[max_attempts_setting])
    window_seconds = getattr(settings, window_setting, globals()[window_setting])
    key = f"rate-limit:{scope}:{_get_client_identifier(request)}"
    if cache.add(key, 1, timeout=window_seconds):
        return False
    attempts = cache.incr(key)
    return attempts > max_attempts


def _login_recaptcha_enabled():
    return bool(getattr(settings, "LOGIN_RECAPTCHA_ENABLED", False))


def _login_failure_limit():
    return getattr(settings, "LOGIN_RECAPTCHA_FAILURE_LIMIT", 5)


def _login_failure_cache_timeout():
    return getattr(settings, "LOGIN_RECAPTCHA_CACHE_TIMEOUT", 60 * 60)


def _login_failure_key(request, username):
    normalized_username = (username or "").strip().lower() or "anonymous"
    return f"login-failure:{_get_client_identifier(request)}:{normalized_username}"


def _get_login_failure_count(request, username):
    return int(cache.get(_login_failure_key(request, username), 0) or 0)


def _record_login_failure(request, username):
    key = _login_failure_key(request, username)
    if cache.add(key, 1, timeout=_login_failure_cache_timeout()):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=_login_failure_cache_timeout())
        return 1


def _reset_login_failures(request, username):
    cache.delete(_login_failure_key(request, username))


def _login_attempts_remaining(failure_count):
    """How many tries are left before reCAPTCHA gates the form.

    Returns None when nothing has failed yet, so the template can stay silent
    instead of announcing a full budget to a first-time visitor.
    """
    if not failure_count:
        return None
    return max(_login_failure_limit() - failure_count, 0)


def _login_requires_recaptcha(request, username):
    return (
        _login_recaptcha_enabled()
        and _get_login_failure_count(request, username) >= _login_failure_limit()
    )


def _verify_recaptcha(token, remote_ip=None):
    if not token:
        return False
    secret = getattr(settings, "RECAPTCHA_SECRET_KEY", "")
    if not secret:
        return False
    data = {
        "secret": secret,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip
    encoded_data = parse.urlencode(data).encode()
    req = urlrequest.Request(LOGIN_RECAPTCHA_VERIFY_URL, data=encoded_data, method="POST")
    try:
        with urlrequest.urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, URLError, json.JSONDecodeError):
        logger.exception("Failed to verify login reCAPTCHA")
        return False
    return payload.get("success") is True


def _goal_data_from_form(form: UserGoalForm) -> GoalData:
    cleaned = form.cleaned_data
    return GoalData(
        tag_id=cleaned["tag"].id,
        period=cleaned["period"],
        target_hours=cleaned["target_hours"],
    )


def _note_data_from_form(form: UserNoteForm) -> NoteData:
    return NoteData(note=form.cleaned_data["note"])


@require_POST
def logout_view(request):
    """
    사용자 로그아웃 (POST 요청만 허용)
    """
    logout(request)
    messages.success(request, gettext("성공적으로 로그아웃되었습니다."))
    return redirect("home")


def signup_view(request):
    """
    사용자 회원가입
    """
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            create_seed_tags(user)
            return _start_signup_verification(request, user)
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
    """
    사용자 로그인
    """
    recaptcha_required = False
    failure_count = 0
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        recaptcha_required = _login_requires_recaptcha(request, username)
        if recaptcha_required:
            token = request.POST.get("g-recaptcha-response", "")
            if not _verify_recaptcha(token, _get_client_identifier(request)):
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
                        "remaining_attempts": _login_attempts_remaining(
                            _get_login_failure_count(request, username)
                        ),
                    },
                )
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if _requires_email_verification(user):
                _reset_login_failures(request, username)
                return _start_login_verification(request, user)
            login(request, user)
            _reset_login_failures(request, username)
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
            _reset_login_failures(request, username)
            messages.success(
                request,
                gettext("계정 탈퇴 요청이 취소되었습니다. 다시 로그인되었습니다."),
            )
            return redirect("home")
        failure_count = _record_login_failure(request, username)
        recaptcha_required = (
            _login_recaptcha_enabled() and failure_count >= _login_failure_limit()
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
            "remaining_attempts": _login_attempts_remaining(failure_count),
        },
    )


SIGNUP_VERIFICATION_SESSION_KEY = "signup_verification_user_id"


def _start_signup_verification(request, user):
    """가입 직후 이메일 인증 단계로 넘긴다."""
    if not verification_policy.is_enabled():
        mark_email_verified(user)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect("users:welcome")

    start_verification(user)
    issue_and_send(user, SIGNUP)
    request.session[SIGNUP_VERIFICATION_SESSION_KEY] = user.pk
    return redirect("users:signup_verify")


def _requires_email_verification(user):
    return verification_policy.is_enabled() and not is_email_verified(user)


def _start_login_verification(request, user):
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


def _verification_context(email, user, purpose, form, outcome=None, **extra):
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


def _resend_verification(request, user, purpose):
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
        _verification_context(
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
    _resend_verification(request, user, SIGNUP)
    return redirect("users:signup_verify")


def _get_pending_deletion_user_for_login(username, password):
    if not username or not password:
        return None
    user = _user_repo.find_inactive_with_pending_deletion(username)
    if user and check_password(password, user.password):
        return user
    return None


def _send_username_recovery_email(request, email):
    """이메일과 일치하는 모든 계정의 username을 메일로 발송한다.

    Why: 한 이메일에 여러 계정이 있을 수 있으므로 모두 안내.
    """
    users = _user_repo.find_active_by_email(email)
    if not users:
        return
    context = {
        "usernames": [u.get_username() for u in users],
        "domain": request.get_host(),
        "protocol": "https" if request.is_secure() else "http",
    }
    subject = render_to_string("users/recovery/username_recovery_subject.txt").strip()
    body = render_to_string("users/recovery/username_recovery_email.txt", context)
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except (SMTPException, OSError):
        logger.exception("Failed to send username recovery email")


def username_recovery_view(request):
    """아이디(username) 찾기.

    Why: 등록 여부 노출 방지를 위해 결과 페이지는 항상 동일.
    """
    if request.method == "POST":
        form = UsernameRecoveryForm(request.POST)
        if form.is_valid():
            if _is_rate_limited(
                request,
                "username-recovery",
                "RECOVERY_RATE_LIMIT_MAX_ATTEMPTS",
                "RECOVERY_RATE_LIMIT_WINDOW_SECONDS",
            ):
                return redirect("users:username_recovery_done")
            _send_username_recovery_email(request, form.cleaned_data["email"])
            return redirect("users:username_recovery_done")
    else:
        form = UsernameRecoveryForm()
    return render(
        request,
        "users/recovery/username_recovery_form.html",
        {"form": form, "page_title": gettext("아이디 찾기")},
    )


def username_recovery_done_view(request):
    return render(
        request,
        "users/recovery/username_recovery_done.html",
        {"page_title": gettext("아이디 찾기")},
    )


_USERNAME_RE = re.compile(r"^[\w.@+\-]+$")
_USERNAME_MAX_LENGTH = 30


@require_GET
def check_username_view(request):
    """signup blur 시 username 중복/형식 비동기 검증."""
    if _is_rate_limited(
        request,
        "check-username",
        "VALIDATION_RATE_LIMIT_MAX_ATTEMPTS",
        "VALIDATION_RATE_LIMIT_WINDOW_SECONDS",
    ):
        return JsonResponse({"available": False, "message": _get_rate_limit_retry_message()})
    username = (request.GET.get("username") or "").strip()
    if not username:
        return JsonResponse({"available": False, "message": gettext("사용자명을 입력해주세요.")})
    if len(username) > _USERNAME_MAX_LENGTH:
        return JsonResponse(
            {"available": False, "message": gettext("사용자명은 30자 이하여야 합니다.")}
        )
    if not _USERNAME_RE.match(username):
        return JsonResponse(
            {"available": False, "message": gettext("영문자, 숫자, @/./+/-/_ 만 가능합니다.")}
        )
    if _user_repo.username_exists(username):
        return JsonResponse(
            {"available": False, "message": gettext("이미 사용 중인 사용자명입니다.")}
        )
    return JsonResponse({"available": True, "message": gettext("사용 가능합니다.")})


@require_GET
def check_email_view(request):
    """signup blur 시 email 형식/중복 비동기 검증."""
    if _is_rate_limited(
        request,
        "check-email",
        "VALIDATION_RATE_LIMIT_MAX_ATTEMPTS",
        "VALIDATION_RATE_LIMIT_WINDOW_SECONDS",
    ):
        return JsonResponse({"available": False, "message": _get_rate_limit_retry_message()})
    email = (request.GET.get("email") or "").strip()
    if not email:
        return JsonResponse({"available": False, "message": gettext("이메일을 입력해주세요.")})
    try:
        validate_email(email)
    except DjangoValidationError:
        return JsonResponse(
            {"available": False, "message": gettext("올바른 이메일 형식이 아닙니다.")}
        )
    if _user_repo.email_exists(email):
        return JsonResponse(
            {"available": False, "message": gettext("이미 사용 중인 이메일입니다.")}
        )
    return JsonResponse({"available": True, "message": gettext("사용 가능합니다.")})


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

    if _is_rate_limited(
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
        _verification_context(
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
    if not request.session.get(PASSWORD_RESET_EMAIL_KEY):
        return redirect("users:password_reset")
    for user in _password_reset_candidates(request):
        _resend_verification(request, user, PASSWORD_RESET)
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


ONBOARDING_STEPS = 3


@login_required
def welcome_view(request):
    """가입 직후 1회 노출되는 온보딩.

    읽는 화면이 아니라 고르는 화면이다. 세 스텝 모두 건너뛸 수 있어 가입
    이탈을 만들지 않는다.
    """
    try:
        step = int(request.GET.get("step", 1))
    except (TypeError, ValueError):
        step = 1
    step = min(max(step, 1), ONBOARDING_STEPS)

    context = {
        "page_title": gettext("시작하기"),
        "step": step,
        "total_steps": ONBOARDING_STEPS,
        "step_range": range(1, ONBOARDING_STEPS + 1),
    }
    if step == 1:
        context["tags"] = _tag_repo.find_accessible_ordered(request.user)
    if step == 2:
        today = timezone.localdate()
        blocks = _time_block_repo.find_by_date(request.user, today)
        slot_data = {
            block.slot_index: {"tag": block.tag, "memo": block.memo, "id": block.id}
            for block in blocks
        }
        context["today"] = today
        context["time_headers"] = build_time_headers()
        context["slot_rows"] = annotate_future(
            build_slot_rows(slot_data), current_slot_index(today, timezone.localtime())
        )
        context["tags"] = _tag_repo.find_accessible_ordered(request.user)
    if step == 3:
        context["tags"] = _tag_repo.find_accessible_ordered(request.user)
        context["periods"] = [("daily", gettext("하루")), ("weekly", gettext("한 주"))]

    return render(request, "users/welcome.html", context)


def _submitted_goal_values(request):
    """거절된 폼이 사용자가 입력한 값을 그대로 들고 있게 한다 — 저장된 값으로
    되돌리면 무엇을 잘못 넣었는지 화면에서 사라진다."""
    return {
        "tag": request.POST.get("tag", ""),
        "period": request.POST.get("period", ""),
        "target_hours": request.POST.get("target_hours", ""),
    }


def _goal_page_context(
    request, add_error="", row_error="", error_goal_id=None, keep_values=False
):
    submitted = _submitted_goal_values(request) if keep_values else None
    return {
        "goals": _goal_repo.find_by_user(request.user),
        "goal_progress_rows": build_goal_progress_rows(
            request.user, timezone.localdate()
        ),
        "assignable_tags": _get_user_tag_queryset(request.user),
        "period_choices": UserGoal.PERIOD_CHOICES,
        "add_error": add_error,
        "row_error": row_error,
        "error_goal_id": error_goal_id,
        "add_values": submitted if add_error else None,
        "row_values": submitted if row_error else None,
    }


def _wants_goal_partial(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _render_goal_partial(request, status=200, **context_kwargs):
    return render(
        request,
        "users/_goal_manager.html",
        _goal_page_context(request, **context_kwargs),
        status=status,
    )


def _goal_mutation_done(request):
    """성공 응답. XHR 이면 페이지를 갈아끼우지 않고 본문만 되받는다."""
    if _wants_goal_partial(request):
        return _render_goal_partial(request)
    return redirect("users:usergoal_list")


def _goal_mutation_failed(request, **errors):
    if _wants_goal_partial(request):
        return _render_goal_partial(request, status=422, keep_values=True, **errors)
    return render(
        request,
        "users/goals.html",
        _goal_page_context(request, keep_values=True, **errors),
    )


def _first_form_error(form) -> str:
    """행 안에 한 줄로 보여줄 오류. 세 필드뿐이라 첫 오류면 충분하다."""
    for errors in form.errors.values():
        if errors:
            return errors[0]
    return ""


@login_required
def usergoal_list(request):
    return render(request, "users/goals.html", _goal_page_context(request))


@login_required
def usergoal_create(request):
    if request.method != "POST":
        return redirect("users:usergoal_list")

    form = UserGoalForm(request.POST, user=request.user)
    form.fields["tag"].queryset = _get_user_tag_queryset(request.user)
    if form.is_valid():
        _save_goal.execute(_goal_data_from_form(form), request.user)
        return _goal_mutation_done(request)
    return _goal_mutation_failed(request, add_error=_first_form_error(form))


@login_required
def usergoal_update(request, pk):
    goal = _goal_repo.get_or_404(pk, request.user)
    if request.method != "POST":
        return redirect("users:usergoal_list")

    form = UserGoalForm(request.POST, instance=goal, user=request.user)
    form.fields["tag"].queryset = _get_user_tag_queryset(request.user)
    if form.is_valid():
        _save_goal.execute(_goal_data_from_form(form), request.user, goal_id=pk)
        return _goal_mutation_done(request)
    return _goal_mutation_failed(
        request, row_error=_first_form_error(form), error_goal_id=pk
    )


@login_required
@require_http_methods(["GET", "POST"])
def usergoal_delete(request, pk):
    goal = _goal_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        _delete_goal.execute(request.user, pk)
        return _goal_mutation_done(request)
    # JS 없는 환경 폴백. 목록에서 이 화면으로 가는 링크는 없다 — 행 안에서 확인한다.
    return render(request, "users/usergoal_confirm_delete.html", {"goal": goal})


@login_required
def usernote_list(request):
    notes = _note_repo.find_by_user(request.user)
    return render(request, "users/usernote_list.html", {"notes": notes})


@login_required
def usernote_create(request):
    if request.method == "POST":
        form = UserNoteForm(request.POST)
        if form.is_valid():
            _save_note.execute(_note_data_from_form(form), request.user)
            return redirect("users:usernote_list")
    else:
        form = UserNoteForm()
    return render(request, "users/usernote_form.html", {"form": form, "mode": "create"})


@login_required
def usernote_update(request, pk):
    note = _note_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        form = UserNoteForm(request.POST, instance=note)
        if form.is_valid():
            _save_note.execute(_note_data_from_form(form), request.user, note_id=pk)
            return redirect("users:usernote_list")
    else:
        form = UserNoteForm(instance=note)
    return render(request, "users/usernote_form.html", {"form": form, "mode": "update"})


@login_required
@require_http_methods(["GET", "POST"])
def usernote_delete(request, pk):
    note = _note_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        _delete_note.execute(request.user, pk)
        return redirect("users:usernote_list")
    return render(request, "users/usernote_confirm_delete.html", {"note": note})


@login_required
def mypage(request):
    user = request.user
    form = UserGoalForm(request.POST or None)
    form.fields["tag"].queryset = _get_user_tag_queryset(user)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if request.method == "POST":
        if form.is_valid():
            _save_goal.execute(_goal_data_from_form(form), user)
            if is_ajax:
                return HttpResponse(status=204)
            return redirect(f"{reverse('users:mypage')}?saved=1")
        if is_ajax:
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
            return JsonResponse({"errors": errors}, status=400)
    else:
        form.fields["period"].initial = "monthly"

    data = _mypage_use_case.execute(user)
    return render(
        request,
        "users/mypage.html",
        {
            "goals": data["goals"],
            "form": form,
            # 시안 5c 는 설정 안에서 태그와 카테고리 색을 바로 보여 준다.
            "settings_tags": _get_user_tag_queryset(user).select_related("category"),
            "categories": Category.objects.all(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def account_delete(request):
    if request.method == "POST":
        request_account_deletion(request.user)
        logout(request)
        messages.warning(
            request,
            gettext("계정 탈퇴 요청이 접수되었습니다. 15일 안에 다시 로그인하면 취소됩니다."),
        )
        return redirect("home")
    return render(
        request,
        "users/account_delete_confirm.html",
        {"page_title": gettext("계정 탈퇴")},
    )
