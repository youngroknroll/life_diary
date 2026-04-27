from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext, ngettext
from django.views.decorators.http import require_http_methods, require_GET

import json
import logging

from pydantic import ValidationError

from apps.tags.repositories import TagRepository
from .commands import DeleteTimeBlocksCommand, UpsertTimeBlocksCommand
from .repositories import TimeBlockRepository
from .services import build_time_headers
from .use_cases import DeleteTimeBlocksUseCase, UpsertTimeBlocksUseCase

from apps.core.utils import (
    safe_date_parse,
    calculate_time_statistics,
    success_response,
    error_response,
    TOTAL_SLOTS_PER_DAY,
    get_time_from_slot,
)

_time_block_repo = TimeBlockRepository()
_tag_repo = TagRepository()
_upsert_use_case = UpsertTimeBlocksUseCase(writer=_time_block_repo, tags=_tag_repo)
_delete_use_case = DeleteTimeBlocksUseCase(writer=_time_block_repo)


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

    # 144개 슬롯 생성 (00:00 ~ 23:50, 10분 단위)
    slots = []
    for i in range(TOTAL_SLOTS_PER_DAY):
        hour, minute = get_time_from_slot(i)
        slots.append(
            {
                "index": i,
                "hour": hour,
                "minute": minute,
                "time_str": f"{hour:02d}:{minute:02d}",
                "data": slot_data.get(i),
            }
        )

    # 사용자의 모든 태그 + 공용 기본 태그 조회 (기본 태그 우선)
    user_tags = _tag_repo.find_accessible_ordered(request.user)

    # 통계 계산 (core 유틸리티 사용)
    stats = calculate_time_statistics(len(slot_data))

    context = {
        "page_title": gettext("대시보드"),
        "selected_date": selected_date,
        "slots": slots,
        "user_tags": user_tags,
        "total_slots": len(slots),
        "filled_slots": len(slot_data),
        "fill_percentage": stats["fill_percentage"],
        "total_hours": stats["hours"],
        "remaining_minutes": stats["remaining_minutes"],
        "time_headers": build_time_headers(),
    }

    return render(request, "dashboard/index.html", context)


@login_required
@require_http_methods(["POST", "DELETE"])
def time_block_api(request):
    """
    RESTful 시간 블록 API
    POST: 시간 블록 생성/수정
    DELETE: 시간 블록 삭제
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response(gettext("올바른 JSON 형식이 아닙니다."), "INVALID_JSON")

    if request.method == "POST":
        return _handle_upsert(request, data)
    return _handle_delete(request, data)


def _handle_upsert(request, data):
    logger = logging.getLogger(__name__)
    try:
        cmd = UpsertTimeBlocksCommand(
            user_id=request.user.id,
            target_date=data.get("date"),
            slot_indexes=data.get("slot_indexes", []),
            tag_id=data.get("tag_id") or 0,
            memo=data.get("memo", ""),
        )
    except ValidationError as exc:
        return error_response(exc.errors()[0]["msg"], "VALIDATION_ERROR")

    try:
        result = _upsert_use_case.execute(cmd, request.user)
    except PermissionError as exc:
        return error_response(str(exc), "TAG_NOT_FOUND", 404)
    except Exception:
        logger.exception("시간 블록 저장 중 오류")
        return error_response(gettext("저장 중 오류가 발생했습니다."), "SERVER_ERROR", 500)

    saved_count = len(cmd.slot_indexes)
    return success_response(
        ngettext(
            "%(count)d개의 슬롯이 저장되었습니다.",
            "%(count)d개의 슬롯이 저장되었습니다.",
            saved_count,
        ) % {"count": saved_count},
        {
            "created_count": result.created,
            "updated_count": result.updated,
            "total_count": len(cmd.slot_indexes),
            "tag": {"id": result.tag_id, "name": result.tag_name, "color": result.tag_color},
        },
        201,
    )


def _handle_delete(request, data):
    logger = logging.getLogger(__name__)
    try:
        cmd = DeleteTimeBlocksCommand(
            user_id=request.user.id,
            target_date=data.get("date"),
            slot_indexes=data.get("slot_indexes", []),
        )
    except ValidationError as exc:
        return error_response(exc.errors()[0]["msg"], "VALIDATION_ERROR")

    try:
        result = _delete_use_case.execute(cmd, request.user)
    except Exception:
        logger.exception("시간 블록 삭제 중 오류")
        return error_response(gettext("삭제 중 오류가 발생했습니다."), "SERVER_ERROR", 500)

    if result.deleted == 0 and result.requested > 0:
        return error_response(gettext("삭제할 기록이 없습니다."), "NO_BLOCKS_FOUND", 404)

    return success_response(
        ngettext(
            "%(count)d개의 슬롯이 삭제되었습니다.",
            "%(count)d개의 슬롯이 삭제되었습니다.",
            result.deleted,
        ) % {"count": result.deleted},
        {"deleted_count": result.deleted, "requested_count": result.requested},
    )
