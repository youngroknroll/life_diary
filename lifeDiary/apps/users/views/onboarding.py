"""가입 직후 온보딩 화면 뷰."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext

from apps.dashboard.day_window import annotate_future, current_slot_index
from apps.dashboard.repositories import TimeBlockRepository
from apps.dashboard.services import build_slot_rows, build_time_headers
from apps.tags.repositories import TagRepository

_tag_repo = TagRepository()
_time_block_repo = TimeBlockRepository()


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
