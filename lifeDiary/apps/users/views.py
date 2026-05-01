from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import SignupForm, UserGoalForm, UserNoteForm, UsernameRecoveryForm
from .repositories import GoalRepository, NoteRepository
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

_goal_repo = GoalRepository()
_note_repo = NoteRepository()
_tag_repo = TagRepository()
_mypage_use_case = GetMyPageUseCase()
_save_goal = SaveGoalUseCase(tags=_tag_repo)
_delete_goal = DeleteGoalUseCase()
_save_note = SaveNoteUseCase()
_delete_note = DeleteNoteUseCase()


def _get_user_tag_queryset(user):
    """사용자 태그 + 기본 태그 쿼리셋"""
    return _tag_repo.find_accessible(user)


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
            messages.success(
                request,
                gettext("%(username)s님, 환영합니다! 회원가입이 완료되었습니다.")
                % {"username": user.username},
            )
            return redirect("home")
    else:
        form = SignupForm()

    # Bootstrap 클래스 추가
    for field in form.fields.values():
        field.widget.attrs.update({"class": "form-control"})

    return render(
        request, "users/signup.html", {"form": form, "page_title": gettext("회원가입")}
    )


def login_view(request):
    """
    사용자 로그인
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request,
                gettext("%(username)s님, 환영합니다!") % {"username": user.username},
            )
            return redirect("home")
    else:
        form = AuthenticationForm()

    # Bootstrap 클래스 추가
    for field in form.fields.values():
        field.widget.attrs.update({"class": "form-control"})

    return render(request, "users/login.html", {"form": form, "page_title": gettext("로그인")})


def _send_username_recovery_email(request, email):
    """이메일과 일치하는 모든 계정의 username을 메일로 발송한다.

    Why: 한 이메일에 여러 계정이 있을 수 있으므로 모두 안내.
    """
    User = get_user_model()
    users = list(User.objects.filter(email__iexact=email, is_active=True))
    if not users:
        return
    context = {
        "usernames": [u.get_username() for u in users],
        "domain": request.get_host(),
        "protocol": "https" if request.is_secure() else "http",
    }
    subject = render_to_string("users/recovery/username_recovery_subject.txt").strip()
    body = render_to_string("users/recovery/username_recovery_email.txt", context)
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def username_recovery_view(request):
    """아이디(username) 찾기.

    Why: 등록 여부 노출 방지를 위해 결과 페이지는 항상 동일.
    """
    if request.method == "POST":
        form = UsernameRecoveryForm(request.POST)
        if form.is_valid():
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
