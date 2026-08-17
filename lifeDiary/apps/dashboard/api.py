import logging

from django.utils import timezone
from django.utils.translation import gettext, ngettext
from ninja import Router, Status
from pydantic import ValidationError as CommandValidationError

from apps.core.schemas import ErrorEnvelope, error_payload
from apps.core.utils import calculate_time_statistics
from apps.tags.repositories import TagRepository
from .commands import (
    DeleteTimeBlocksCommand,
    RestoreTimeBlocksCommand,
    UpsertTimeBlocksCommand,
)
from .repositories import TimeBlockRepository
from .schemas import (
    DeleteResultOut,
    TimeBlockDeleteIn,
    TimeBlockUpsertIn,
    UndoIn,
    UndoResultOut,
    UpsertResultOut,
)
from .services import build_slot_rows, hours_to_refresh, serialize_rows
from .undo import pop_snapshot, save_snapshot
from .use_cases import (
    DeleteTimeBlocksUseCase,
    RestoreTimeBlocksUseCase,
    UpsertTimeBlocksUseCase,
)

logger = logging.getLogger(__name__)

router = Router(tags=["time-blocks"])

_time_block_repo = TimeBlockRepository()
_tag_repo = TagRepository()
_upsert_use_case = UpsertTimeBlocksUseCase(writer=_time_block_repo, tags=_tag_repo)
_delete_use_case = DeleteTimeBlocksUseCase(writer=_time_block_repo)
_restore_use_case = RestoreTimeBlocksUseCase(writer=_time_block_repo, tags=_tag_repo)


def _error(status, message, code):
    return Status(status, error_payload(message, code))


def _command_error(exc):
    return _error(400, exc.errors()[0]["msg"], "VALIDATION_ERROR")


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


@router.post(
    "/time-blocks/",
    response={
        201: UpsertResultOut,
        400: ErrorEnvelope,
        401: ErrorEnvelope,
        404: ErrorEnvelope,
        500: ErrorEnvelope,
    },
    summary="시간 블록 저장",
    description="선택한 날짜의 슬롯(0~143)들에 태그와 메모를 기록한다. 성공 시 갱신된 구간(runs)과 하루 통계, 60초 유효한 undo_token을 돌려준다.",
)
def time_block_upsert(request, payload: TimeBlockUpsertIn):
    try:
        cmd = UpsertTimeBlocksCommand(
            user_id=request.user.id,
            target_date=payload.date,
            slot_indexes=payload.slot_indexes,
            tag_id=payload.tag_id or 0,
            memo=payload.memo,
        )
    except CommandValidationError as exc:
        return _command_error(exc)

    try:
        result = _upsert_use_case.execute(cmd, request.user)
    except PermissionError as exc:
        return _error(404, str(exc), "TAG_NOT_FOUND")
    except Exception:
        logger.exception("시간 블록 저장 중 오류")
        return _error(500, gettext("저장 중 오류가 발생했습니다."), "SERVER_ERROR")

    saved_count = len(cmd.slot_indexes)
    return Status(
        201,
        {
            "success": True,
            "message": ngettext(
                "%(count)d개의 슬롯이 저장되었습니다.",
                "%(count)d개의 슬롯이 저장되었습니다.",
                saved_count,
            )
            % {"count": saved_count},
            **_mutation_payload(
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
        },
    )


@router.delete(
    "/time-blocks/",
    response={
        200: DeleteResultOut,
        400: ErrorEnvelope,
        401: ErrorEnvelope,
        404: ErrorEnvelope,
        500: ErrorEnvelope,
    },
    summary="시간 블록 삭제",
    description="선택한 날짜의 슬롯 기록을 지운다. 지운 기록이 없으면 404를 돌려준다.",
)
def time_block_delete(request, payload: TimeBlockDeleteIn):
    try:
        cmd = DeleteTimeBlocksCommand(
            user_id=request.user.id,
            target_date=payload.date,
            slot_indexes=payload.slot_indexes,
        )
    except CommandValidationError as exc:
        return _command_error(exc)

    try:
        result = _delete_use_case.execute(cmd, request.user)
    except Exception:
        logger.exception("시간 블록 삭제 중 오류")
        return _error(500, gettext("삭제 중 오류가 발생했습니다."), "SERVER_ERROR")

    if result.deleted == 0 and result.requested > 0:
        return _error(404, gettext("삭제할 기록이 없습니다."), "NO_BLOCKS_FOUND")

    return Status(
        200,
        {
            "success": True,
            "message": ngettext(
                "%(count)d개의 슬롯이 삭제되었습니다.",
                "%(count)d개의 슬롯이 삭제되었습니다.",
                result.deleted,
            )
            % {"count": result.deleted},
            **_mutation_payload(
                request,
                cmd.target_date,
                cmd.slot_indexes,
                result.previous_state,
                extra={
                    "deleted_count": result.deleted,
                    "requested_count": result.requested,
                },
            ),
        },
    )


@router.post(
    "/time-blocks/undo/",
    response={
        200: UndoResultOut,
        400: ErrorEnvelope,
        401: ErrorEnvelope,
        404: ErrorEnvelope,
        500: ErrorEnvelope,
    },
    summary="시간 블록 변경 되돌리기",
    description="저장·삭제 응답의 undo_token으로 직전 변경을 되돌린다. 되돌릴 대상은 요청 본문이 아니라 세션 스냅샷에서만 온다. 토큰은 60초 뒤 만료되고 한 번만 쓸 수 있다.",
)
def time_block_undo(request, payload: UndoIn):
    snapshot = pop_snapshot(request.session, payload.undo_token, now=timezone.now())
    if snapshot is None:
        return _error(
            404, gettext("되돌릴 수 있는 시간이 지났습니다."), "UNDO_UNAVAILABLE"
        )

    try:
        cmd = RestoreTimeBlocksCommand(
            target_date=snapshot["date"], slots=snapshot["slots"]
        )
    except CommandValidationError as exc:
        return _command_error(exc)

    try:
        _restore_use_case.execute(cmd, request.user)
    except PermissionError as exc:
        return _error(404, str(exc), "TAG_NOT_FOUND")
    except Exception:
        logger.exception("되돌리기 중 오류")
        return _error(500, gettext("되돌리는 중 오류가 발생했습니다."), "SERVER_ERROR")

    rows, stats = _read_day(request.user, cmd.target_date)

    return Status(
        200,
        {
            "success": True,
            "message": gettext("되돌렸습니다."),
            "runs": serialize_rows(
                rows, hours_to_refresh([slot.slot_index for slot in cmd.slots])
            ),
            "stats": stats,
        },
    )
