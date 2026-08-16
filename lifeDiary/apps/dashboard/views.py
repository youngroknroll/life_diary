from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext
from django.views.decorators.http import require_GET

from apps.core.utils import (
    TOTAL_SLOTS_PER_DAY,
    calculate_time_statistics,
    safe_date_parse,
)
from apps.tags.repositories import TagRepository
from apps.tags.use_cases import ListFrequentTagsUseCase

from .day_window import annotate_future, current_slot_index
from .repositories import TimeBlockRepository
from .services import build_slot_rows, build_time_headers

_time_block_repo = TimeBlockRepository()
_tag_repo = TagRepository()
_list_frequent_tags = ListFrequentTagsUseCase()


@login_required
@require_GET
def dashboard_view(request):
    """
    메인 대시보드 - Django 템플릿 기반으로 초기 데이터 렌더링
    """
    selected_date = safe_date_parse(request.GET.get("date"))

    # 시간 블록 데이터 조회
    time_blocks = _time_block_repo.find_by_date(request.user, selected_date)
    slot_data = {
        block.slot_index: {"tag": block.tag, "memo": block.memo, "id": block.id}
        for block in time_blocks
    }

    now = timezone.localtime()
    current_slot = current_slot_index(selected_date, now)
    slot_rows = annotate_future(build_slot_rows(slot_data), current_slot)

    user_tags = _tag_repo.find_accessible_ordered(request.user)

    # 통계 계산 (core 유틸리티 사용)
    stats = calculate_time_statistics(len(slot_data))

    context = {
        "page_title": gettext("대시보드"),
        "selected_date": selected_date,
        "slot_rows": slot_rows,
        "is_today": current_slot is not None,
        "now_time": now,
        "frequent_tags": _list_frequent_tags.execute(request.user),
        "has_tag_usage": _list_frequent_tags.has_usage(request.user),
        "user_tags": user_tags,
        "total_slots": TOTAL_SLOTS_PER_DAY,
        "filled_slots": len(slot_data),
        "empty_slots": TOTAL_SLOTS_PER_DAY - len(slot_data),
        "fill_percentage": stats["fill_percentage"],
        "total_hours": stats["hours"],
        "remaining_minutes": stats["remaining_minutes"],
        "time_headers": build_time_headers(),
    }

    return render(request, "dashboard/index.html", context)
