from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext, ngettext
from django.views.decorators.http import require_http_methods, require_GET

import json
import logging

from pydantic import ValidationError

from django.utils import timezone

from apps.tags.repositories import TagRepository
from apps.tags.use_cases import ListFrequentTagsUseCase
from .commands import (
    DeleteTimeBlocksCommand,
    RestoreTimeBlocksCommand,
    UpsertTimeBlocksCommand,
)
from .repositories import TimeBlockRepository
from .day_window import annotate_future, current_slot_index
from .services import (
    build_slot_rows,
    build_time_headers,
    hours_to_refresh,
    serialize_rows,
)
from .undo import pop_snapshot, save_snapshot
from .use_cases import (
    DeleteTimeBlocksUseCase,
    RestoreTimeBlocksUseCase,
    UpsertTimeBlocksUseCase,
)

from apps.core.utils import (
    safe_date_parse,
    calculate_time_statistics,
    success_response,
    error_response,
    TOTAL_SLOTS_PER_DAY,
)

_time_block_repo = TimeBlockRepository()
_tag_repo = TagRepository()
_list_frequent_tags = ListFrequentTagsUseCase()
_upsert_use_case = UpsertTimeBlocksUseCase(writer=_time_block_repo, tags=_tag_repo)
_delete_use_case = DeleteTimeBlocksUseCase(writer=_time_block_repo)
_restore_use_case = RestoreTimeBlocksUseCase(writer=_time_block_repo, tags=_tag_repo)


def _read_day(user, target_date):
    slot_data = {
        block.slot_index: {"tag": block.tag, "memo": block.memo, "id": block.id}
        for block in _time_block_repo.find_by_date(user, target_date)
    }
    stats = calculate_time_statistics(len(slot_data))

    return build_slot_rows(slot_data), {
        "logged_minutes": stats["total_minutes"],
        "fill_percentage": stats["fill_percentage"],
    }


def _mutation_payload(request, target_date, slot_indexes, previous_state, extra=None):
    rows, stats = _read_day(request.user, target_date)
    token = save_snapshot(
        request.session,
        {"date": target_date.isoformat(), "slots": previous_state},
        now=timezone.now(),
    )

    return {
        **(extra or {}),
        "runs": serialize_rows(rows, hours_to_refresh(slot_indexes)),
        "stats": stats,
        "undo_token": token,
    }


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
        _mutation_payload(
            request,
            cmd.target_date,
            cmd.slot_indexes,
            result.previous_state,
            extra={
                "created_count": result.created,
                "updated_count": result.updated,
                "total_count": len(cmd.slot_indexes),
                "tag": {
                    "id": result.tag_id,
                    "name": result.tag_name,
                    "color": result.tag_color,
                },
            },
        ),
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
        _mutation_payload(
            request,
            cmd.target_date,
            cmd.slot_indexes,
            result.previous_state,
            extra={
                "deleted_count": result.deleted,
                "requested_count": result.requested,
            },
        ),
    )


@login_required
@require_http_methods(["POST"])
def time_block_undo_api(request):
    """되돌릴 대상은 오직 세션 스냅샷에서만 온다.

    요청 본문의 날짜나 슬롯을 읽으면 오래된 스냅샷을 엉뚱한 날짜에 덮어쓸
    수 있다.
    """
    logger = logging.getLogger(__name__)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response(gettext("올바른 JSON 형식이 아닙니다."), "INVALID_JSON")

    snapshot = pop_snapshot(
        request.session, data.get("undo_token") or "", now=timezone.now()
    )
    if snapshot is None:
        return error_response(
            gettext("되돌릴 수 있는 시간이 지났습니다."), "UNDO_UNAVAILABLE", 404
        )

    try:
        cmd = RestoreTimeBlocksCommand(
            target_date=snapshot["date"], slots=snapshot["slots"]
        )
    except ValidationError as exc:
        return error_response(exc.errors()[0]["msg"], "VALIDATION_ERROR")

    try:
        _restore_use_case.execute(cmd, request.user)
    except PermissionError as exc:
        return error_response(str(exc), "TAG_NOT_FOUND", 404)
    except Exception:
        logger.exception("되돌리기 중 오류")
        return error_response(
            gettext("되돌리는 중 오류가 발생했습니다."), "SERVER_ERROR", 500
        )

    rows, stats = _read_day(request.user, cmd.target_date)

    return success_response(
        gettext("되돌렸습니다."),
        {
            "runs": serialize_rows(
                rows, hours_to_refresh([slot.slot_index for slot in cmd.slots])
            ),
            "stats": stats,
        },
    )
