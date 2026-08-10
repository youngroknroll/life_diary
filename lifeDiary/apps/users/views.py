import logging
import re
import json
from smtplib import SMTPException
from urllib import parse, request as urlrequest
from urllib.error import URLError

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import SignupForm, UserGoalForm, UserNoteForm, UsernameRecoveryForm
from .account_deletion import cancel_account_deletion, request_account_deletion
from .repositories import GoalRepository, NoteRepository, UserAccountRepository
from apps.tags.repositories import TagRepository
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
    """사용자 태그 + 기본 태그 쿼리셋"""
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
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("users:welcome")
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


class RateLimitedPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        if _is_rate_limited(
            self.request,
            "password-reset",
            "RECOVERY_RATE_LIMIT_MAX_ATTEMPTS",
            "RECOVERY_RATE_LIMIT_WINDOW_SECONDS",
        ):
            return redirect(self.get_success_url())
        opts = {
            "use_https": self.request.is_secure(),
            "token_generator": self.token_generator,
            "from_email": self.from_email,
            "email_template_name": self.email_template_name,
            "subject_template_name": self.subject_template_name,
            "request": self.request,
            "domain_override": self.request.get_host(),
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.extra_email_context,
        }
        form.save(**opts)
        return super(PasswordResetView, self).form_valid(form)


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
    if step == 3:
        context["tags"] = _tag_repo.find_accessible_ordered(request.user)
        context["periods"] = [("daily", gettext("하루")), ("weekly", gettext("한 주"))]

    return render(request, "users/welcome.html", context)


@login_required
def usergoal_list(request):
    goals = _goal_repo.find_by_user(request.user)
    return render(request, "users/usergoal_list.html", {"goals": goals})


@login_required
def usergoal_create(request):
    form = UserGoalForm(request.POST or None)
    form.fields["tag"].queryset = _get_user_tag_queryset(request.user)
    if request.method == "POST" and form.is_valid():
        _save_goal.execute(_goal_data_from_form(form), request.user)
        return redirect("users:mypage")
    return render(request, "users/usergoal_form.html", {"form": form, "mode": "create"})


@login_required
def usergoal_update(request, pk):
    goal = _goal_repo.get_or_404(pk, request.user)
    form = UserGoalForm(request.POST or None, instance=goal)
    form.fields["tag"].queryset = _get_user_tag_queryset(request.user)
    if request.method == "POST" and form.is_valid():
        _save_goal.execute(_goal_data_from_form(form), request.user, goal_id=pk)
        return redirect("users:mypage")
    return render(request, "users/usergoal_form.html", {"form": form, "mode": "update"})


@login_required
@require_http_methods(["GET", "POST"])
def usergoal_delete(request, pk):
    goal = _goal_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        _delete_goal.execute(request.user, pk)
        return redirect("users:mypage")
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
    return render(request, "users/mypage.html", {"goals": data["goals"], "form": form})


@login_required
def mypage_goals_partial(request):
    data = _mypage_use_case.execute(request.user)
    return render(request, "users/usergoal_list.html", {"goals": data["goals"]})


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
