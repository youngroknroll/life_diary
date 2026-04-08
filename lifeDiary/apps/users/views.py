from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UserGoal, UserNote
from .forms import UserGoalForm, UserNoteForm
from apps.tags.models import Tag
from apps.stats.logic import (
    get_daily_stats_data,
    get_weekly_stats_data,
    get_monthly_stats_data,
    StatsCalculator,
)
from apps.core.utils import calculate_goal_percent

import datetime


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
            form.save()
            messages.success(request, "회원가입이 완료되었습니다. 로그인해주세요.")
            return redirect("users:login")
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
    goals = UserGoal.objects.filter(user=request.user).select_related("tag")
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
    form.fields["tag"].queryset = Tag.objects.filter(
        user=request.user
    ) | Tag.objects.filter(is_default=True)
    return render(request, "users/usergoal_form.html", {"form": form, "mode": "create"})


@login_required
def usergoal_update(request, pk):
    goal = get_object_or_404(UserGoal, pk=pk, user=request.user)
    if request.method == "POST":
        form = UserGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            return redirect("users:mypage")
    else:
        form = UserGoalForm(instance=goal)
    form.fields["tag"].queryset = Tag.objects.filter(
        user=request.user
    ) | Tag.objects.filter(is_default=True)
    return render(request, "users/usergoal_form.html", {"form": form, "mode": "update"})


@login_required
@require_http_methods(["GET", "POST"])
def usergoal_delete(request, pk):
    goal = get_object_or_404(UserGoal, pk=pk, user=request.user)
    if request.method == "POST":
        goal.delete()
        return redirect("users:mypage")
    return render(request, "users/usergoal_confirm_delete.html", {"goal": goal})


@login_required
def usernote_list(request):
    notes = UserNote.objects.filter(user=request.user).order_by("-created_at")
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
    note = get_object_or_404(UserNote, pk=pk, user=request.user)
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
    note = get_object_or_404(UserNote, pk=pk, user=request.user)
    if request.method == "POST":
        note.delete()
        return redirect("users:usernote_list")
    return render(request, "users/usernote_confirm_delete.html", {"note": note})


@login_required
def mypage(request):
    user = request.user
    goals = UserGoal.objects.filter(user=user).select_related("tag")
    # 통계 데이터 가져오기
    today = datetime.date.today()
    calculator = StatsCalculator(user, today)
    daily_stats = get_daily_stats_data(user, today, calculator)
    weekly_stats = get_weekly_stats_data(user, today, calculator)
    monthly_stats = get_monthly_stats_data(user, today, calculator)
    # 목표별 달성률 계산
    for goal in goals:
        goal.actual, goal.percent = calculate_goal_percent(
            goal,
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
    form.fields["tag"].queryset = Tag.objects.filter(user=user) | Tag.objects.filter(
        is_default=True
    )
    return render(request, "users/mypage.html", {"goals": goals, "form": form})
