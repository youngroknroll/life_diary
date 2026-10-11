from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth import logout
from django.utils.translation import gettext
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import (
    UserGoalForm,
)
from ..account_deletion import request_account_deletion
from apps.tags.models import Category
from ..use_cases import (
    GetMyPageUseCase,
)
from .goals import goal_data_from_form, save_goal, user_tag_queryset

_mypage_use_case = GetMyPageUseCase()


@login_required
def mypage(request):
    user = request.user
    form = UserGoalForm(request.POST or None)
    form.fields["tag"].queryset = user_tag_queryset(user)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if request.method == "POST":
        if form.is_valid():
            save_goal.execute(goal_data_from_form(form), user)
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
            "settings_tags": user_tag_queryset(user).select_related("category"),
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
