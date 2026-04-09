from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserGoalForm, UserNoteForm
from .repositories import GoalRepository, NoteRepository
from apps.tags.repositories import TagRepository
from apps.stats.logic import (
    get_daily_stats_data,
    get_weekly_stats_data,
    get_monthly_stats_data,
    StatsCalculator,
)
from .domain_services import _goal_progress_service

import datetime

_goal_repo = GoalRepository()
_note_repo = NoteRepository()
_tag_repo = TagRepository()


def _get_user_tag_queryset(user):
    """사용자 태그 + 기본 태그 쿼리셋"""
    return _tag_repo.find_accessible(user)


@require_POST
def logout_view(request):
    """
    사용자 로그아웃 (POST 요청만 허용)
    """
    logout(request)
    messages.success(request, "성공적으로 로그아웃되었습니다.")
    return redirect("home")


def signup_view(request):
    """
    사용자 회원가입
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"{user.username}님, 환영합니다! 회원가입이 완료되었습니다.")
            return redirect("home")
    else:
        form = UserCreationForm()

    # Bootstrap 클래스 추가
    for field in form.fields.values():
        field.widget.attrs.update({"class": "form-control"})

    return render(
        request, "users/signup.html", {"form": form, "page_title": "회원가입"}
    )


def login_view(request):
    """
    사용자 로그인
    """
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"{username}님, 환영합니다!")
                return redirect("home")
    else:
        form = AuthenticationForm()

    # Bootstrap 클래스 추가
    for field in form.fields.values():
        field.widget.attrs.update({"class": "form-control"})

    return render(request, "users/login.html", {"form": form, "page_title": "로그인"})


@login_required
def usergoal_list(request):
    goals = _goal_repo.find_by_user(request.user)
    return render(request, "users/usergoal_list.html", {"goals": goals})


@login_required
def usergoal_create(request):
    if request.method == "POST":
        form = UserGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect("users:mypage")
    else:
        form = UserGoalForm()
    form.fields["tag"].queryset = _get_user_tag_queryset(request.user)
    return render(request, "users/usergoal_form.html", {"form": form, "mode": "create"})


@login_required
def usergoal_update(request, pk):
    goal = _goal_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        form = UserGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            return redirect("users:mypage")
    else:
        form = UserGoalForm(instance=goal)
    form.fields["tag"].queryset = _get_user_tag_queryset(request.user)
    return render(request, "users/usergoal_form.html", {"form": form, "mode": "update"})


@login_required
@require_http_methods(["GET", "POST"])
def usergoal_delete(request, pk):
    goal = _goal_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        goal.delete()
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
            note = form.save(commit=False)
            note.user = request.user
            note.save()
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
            form.save()
            return redirect("users:usernote_list")
    else:
        form = UserNoteForm(instance=note)
    return render(request, "users/usernote_form.html", {"form": form, "mode": "update"})


@login_required
@require_http_methods(["GET", "POST"])
def usernote_delete(request, pk):
    note = _note_repo.get_or_404(pk, request.user)
    if request.method == "POST":
        note.delete()
        return redirect("users:usernote_list")
    return render(request, "users/usernote_confirm_delete.html", {"note": note})


@login_required
def mypage(request):
    user = request.user
    goals = _goal_repo.find_by_user(user)
    # 통계 데이터 가져오기
    today = datetime.date.today()
    calculator = StatsCalculator(user, today)
    daily_stats = get_daily_stats_data(user, today, calculator)
    weekly_stats = get_weekly_stats_data(user, today, calculator)
    monthly_stats = get_monthly_stats_data(user, today, calculator)
    # 목표별 달성률 계산
    _goal_progress_service.attach_progress(
        goals,
        daily_stats=daily_stats,
        weekly_stats=weekly_stats,
        monthly_stats=monthly_stats,
    )
    if request.method == "POST":
        form = UserGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = user
            goal.save()
            return redirect("users:mypage")
    else:
        form = UserGoalForm()
        form.fields["period"].initial = "monthly"
    form.fields["tag"].queryset = _get_user_tag_queryset(user)
    return render(request, "users/mypage.html", {"goals": goals, "form": form})
