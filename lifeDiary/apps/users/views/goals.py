from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from ..forms import (
    UserGoalForm,
)
from ..goal_deadline import deadline_state
from ..models import UserGoal
from ..repositories import GoalRepository
from apps.tags.repositories import TagRepository
from apps.stats.aggregation.goal_progress import (
    build_goal_progress_rows,
    with_deadline_states,
)
from ..use_cases import (
    DeleteGoalUseCase,
    GoalData,
    SaveGoalUseCase,
)

_goal_repo = GoalRepository()
_tag_repo = TagRepository()
save_goal = SaveGoalUseCase(tags=_tag_repo)
_delete_goal = DeleteGoalUseCase()


def user_tag_queryset(user):
    """사용자 태그 쿼리셋"""
    return _tag_repo.find_accessible(user)


def goal_data_from_form(form: UserGoalForm) -> GoalData:
    cleaned = form.cleaned_data
    return GoalData(
        tag_id=cleaned["tag"].id,
        period=cleaned["period"],
        target_hours=cleaned["target_hours"],
        due_date=cleaned["due_date"],
    )


def _submitted_goal_values(request):
    """거절된 폼이 사용자가 입력한 값을 그대로 들고 있게 한다 — 저장된 값으로
    되돌리면 무엇을 잘못 넣었는지 화면에서 사라진다."""
    return {
        "tag": request.POST.get("tag", ""),
        "period": request.POST.get("period", ""),
        "target_hours": request.POST.get("target_hours", ""),
        "due_date": request.POST.get("due_date", ""),
        "no_due_date": "no_due_date" in request.POST,
    }


def _goal_page_context(
    request,
    add_error="",
    row_error="",
    error_goal_id=None,
    error_field="",
    keep_values=False,
):
    submitted = _submitted_goal_values(request) if keep_values else None
    today = timezone.localdate()
    goals = _goal_repo.find_by_user(request.user)
    return {
        "goals": goals,
        "goal_items": [(goal, deadline_state(goal.due_date, today)) for goal in goals],
        "goal_progress_rows": with_deadline_states(
            build_goal_progress_rows(request.user, today), today
        ),
        "assignable_tags": user_tag_queryset(request.user),
        "period_choices": UserGoal.PERIOD_CHOICES,
        "add_error": add_error,
        "row_error": row_error,
        "error_goal_id": error_goal_id,
        "error_field": error_field,
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


def _first_form_error(form) -> tuple[str, str]:
    """행 안에 한 줄로 보여줄 오류와 그 필드 이름. 둘을 한 번에 꺼내야
    화면이 표시하는 칸과 문구가 어긋나지 않는다."""
    for field, errors in form.errors.items():
        if errors:
            return field, errors[0]
    return "", ""


@login_required
def usergoal_list(request):
    return render(request, "users/goals.html", _goal_page_context(request))


@login_required
def usergoal_create(request):
    if request.method != "POST":
        return redirect("users:usergoal_list")

    form = UserGoalForm(request.POST, user=request.user)
    form.fields["tag"].queryset = user_tag_queryset(request.user)
    if form.is_valid():
        save_goal.execute(goal_data_from_form(form), request.user)
        return _goal_mutation_done(request)
    error_field, message = _first_form_error(form)
    return _goal_mutation_failed(request, add_error=message, error_field=error_field)


@login_required
def usergoal_update(request, pk):
    goal = _goal_repo.get_or_404(pk, request.user)
    if request.method != "POST":
        return redirect("users:usergoal_list")

    form = UserGoalForm(request.POST, instance=goal, user=request.user)
    form.fields["tag"].queryset = user_tag_queryset(request.user)
    if form.is_valid():
        save_goal.execute(goal_data_from_form(form), request.user, goal_id=pk)
        return _goal_mutation_done(request)
    error_field, message = _first_form_error(form)
    return _goal_mutation_failed(
        request, row_error=message, error_goal_id=pk, error_field=error_field
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
