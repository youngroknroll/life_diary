import json
import logging

from django.http import Http404
from django.utils.translation import gettext
from ninja import Router, Status

from apps.core.schemas import ErrorEnvelope, MessageEnvelope, error_payload
from .repositories import CategoryRepository
from .schemas import CategoryListOut, TagIn, TagListOut, TagMutationOut
from .use_cases import (
    CreateTagUseCase,
    DeleteTagUseCase,
    ListTagsUseCase,
    UpdateTagUseCase,
)

logger = logging.getLogger(__name__)

router = Router(tags=["tags"])

_category_repo = CategoryRepository()
_list_tags = ListTagsUseCase()
_create_tag = CreateTagUseCase()
_update_tag = UpdateTagUseCase()
_delete_tag = DeleteTagUseCase()


def _error(status, message, code):
    return Status(status, error_payload(message, code))


def _tag_not_found():
    return _error(
        404, gettext("존재하지 않는 태그이거나 접근 권한이 없습니다."), "TAG_NOT_FOUND"
    )


@router.get(
    "/categories/",
    response={200: CategoryListOut, 401: ErrorEnvelope, 500: ErrorEnvelope},
    summary="카테고리 목록 조회",
    description="소비시간 5분류 카테고리를 표시 순서대로 반환한다. 이름과 설명은 요청 locale을 따른다.",
)
def category_list(request):
    try:
        categories = _category_repo.find_all()
        return Status(
            200,
            {
                "success": True,
                "message": gettext("카테고리 목록"),
                "categories": [
                    {
                        "id": cat.id,
                        "name": cat.display_name,
                        "slug": cat.slug,
                        "description": cat.display_description,
                        "color": cat.color,
                        "display_order": cat.display_order,
                    }
                    for cat in categories
                ],
            },
        )
    except Exception:
        logger.exception("카테고리 조회 중 오류")
        return _error(
            500, gettext("카테고리 조회 중 오류가 발생했습니다."), "SERVER_ERROR"
        )


@router.get(
    "/tags/",
    response={200: TagListOut, 401: ErrorEnvelope, 500: ErrorEnvelope},
    summary="내 태그 목록 조회",
    description="로그인한 사용자의 태그를 사용량(기록 슬롯 수, 누적 시간)과 함께 반환한다.",
)
def tag_list(request):
    try:
        tags = _list_tags.execute(request.user)
        return Status(
            200,
            {
                "success": True,
                "message": gettext("태그 목록"),
                "tags": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "color": t.color,
                        "category_id": t.category_id,
                        "can_edit": t.can_edit,
                        "can_delete": t.can_delete,
                        "block_count": t.block_count,
                        "total_hours": t.total_hours,
                    }
                    for t in tags
                ],
            },
        )
    except Exception:
        logger.exception("태그 조회 중 오류")
        return _error(500, gettext("태그 조회 중 오류가 발생했습니다."), "SERVER_ERROR")


@router.post(
    "/tags/",
    response={
        201: TagMutationOut,
        400: ErrorEnvelope,
        401: ErrorEnvelope,
        403: ErrorEnvelope,
        500: ErrorEnvelope,
    },
    summary="태그 생성",
    description="선택한 카테고리에 새 태그를 만든다. 태그 색상은 카테고리 색상으로 정해진다.",
)
def tag_create(request, payload: TagIn):
    try:
        tag = _create_tag.execute(
            user=request.user,
            name=payload.name.strip(),
            color=payload.color.strip(),
            category_id=payload.category_id,
        )
        return Status(
            201,
            {"success": True, "message": gettext("태그가 생성되었습니다."), "tag": tag},
        )
    except PermissionError as exc:
        return _error(403, str(exc), "FORBIDDEN")
    except LookupError as exc:
        return _error(400, str(exc), "NOT_FOUND")
    except ValueError as exc:
        return _error(400, str(exc), "VALIDATION_ERROR")
    except Exception:
        logger.exception("태그 생성 중 오류")
        return _error(500, gettext("태그 생성 중 오류가 발생했습니다."), "SERVER_ERROR")


@router.put(
    "/tags/{tag_id}/",
    response={
        200: TagMutationOut,
        400: ErrorEnvelope,
        401: ErrorEnvelope,
        403: ErrorEnvelope,
        404: ErrorEnvelope,
        500: ErrorEnvelope,
    },
    summary="태그 수정",
    description="내가 소유한 태그의 이름·카테고리를 수정한다.",
)
def tag_update(request, tag_id: int, payload: TagIn):
    try:
        tag = _update_tag.execute(
            user=request.user,
            tag_id=tag_id,
            name=payload.name.strip(),
            color=payload.color.strip(),
            category_id=payload.category_id,
        )
        return Status(
            200,
            {"success": True, "message": gettext("태그가 수정되었습니다."), "tag": tag},
        )
    except Http404:
        return _tag_not_found()
    except PermissionError as exc:
        return _error(403, str(exc), "FORBIDDEN")
    except LookupError as exc:
        return _error(400, str(exc), "NOT_FOUND")
    except ValueError as exc:
        return _error(400, str(exc), "VALIDATION_ERROR")
    except Exception:
        logger.exception("태그 수정 중 오류")
        return _error(500, gettext("태그 수정 중 오류가 발생했습니다."), "SERVER_ERROR")


@router.delete(
    "/tags/{tag_id}/",
    response={
        200: MessageEnvelope,
        400: ErrorEnvelope,
        401: ErrorEnvelope,
        403: ErrorEnvelope,
        404: ErrorEnvelope,
        500: ErrorEnvelope,
    },
    summary="태그 삭제",
    description="내가 소유한 태그를 지운다. move_to_id를 주면 그 태그로 기록을 옮기고, 없으면 해당 기록은 미기록으로 돌아간다.",
    openapi_extra={
        "requestBody": {
            "required": False,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "move_to_id": {
                                "type": "integer",
                                "nullable": True,
                                "description": "삭제할 태그의 기록을 옮겨 받을 태그 id",
                            }
                        },
                    }
                }
            },
        }
    },
)
def tag_delete(request, tag_id: int):
    try:
        move_to = _parse_move_to(request)
    except ValueError as exc:
        return _error(400, str(exc), "VALIDATION_ERROR")

    try:
        tag_name = _delete_tag.execute(
            user=request.user, tag_id=tag_id, move_to_id=move_to
        )
        return Status(
            200,
            {
                "success": True,
                "message": gettext('"%(name)s" 태그가 삭제되었습니다.')
                % {"name": tag_name},
            },
        )
    except Http404:
        return _tag_not_found()
    except PermissionError as exc:
        return _error(403, str(exc), "FORBIDDEN")
    except ValueError as exc:
        return _error(400, str(exc), "VALIDATION_ERROR")
    except Exception:
        logger.exception("태그 삭제 중 오류")
        return _error(500, gettext("태그 삭제 중 오류가 발생했습니다."), "SERVER_ERROR")


def _parse_move_to(request):
    """삭제 시 기록을 옮길 태그. 없으면 그 구간은 미기록으로 돌아간다."""
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return None

    raw = payload.get("move_to_id")
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValueError(gettext("옮길 태그를 찾을 수 없습니다."))
