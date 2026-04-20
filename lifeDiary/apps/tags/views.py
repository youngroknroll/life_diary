import json
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_GET

from apps.core.utils import success_response, error_response
from .repositories import CategoryRepository
from .use_cases import (
    CreateTagUseCase,
    DeleteTagUseCase,
    ListTagsUseCase,
    UpdateTagUseCase,
)

_category_repo = CategoryRepository()
_list_tags = ListTagsUseCase()
_create_tag = CreateTagUseCase()
_update_tag = UpdateTagUseCase()
_delete_tag = DeleteTagUseCase()


@login_required
def index(request):
    return render(request, "tags/index.html")


@login_required
@require_GET
def category_list(request):
    try:
        categories = _category_repo.find_all()
        return success_response(
            "카테고리 목록",
            {
                "categories": [
                    {
                        "id": cat.id,
                        "name": cat.name,
                        "slug": cat.slug,
                        "description": cat.description,
                        "color": cat.color,
                        "display_order": cat.display_order,
                    }
                    for cat in categories
                ]
            },
        )
    except Exception:
        logging.getLogger(__name__).exception("카테고리 조회 중 오류")
        return error_response("카테고리 조회 중 오류가 발생했습니다.", "SERVER_ERROR", 500)


@login_required
@require_http_methods(["GET", "POST"])
def tag_list_create(request):
    if request.method == "GET":
        try:
            tags = _list_tags.execute(request.user)
            return success_response(
                "태그 목록",
                {
                    "tags": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "color": t.color,
                            "is_default": t.is_default,
                            "category_id": t.category_id,
                            "can_edit": t.can_edit,
                            "can_delete": t.can_delete,
                        }
                        for t in tags
                    ]
                },
            )
        except Exception:
            logging.getLogger(__name__).exception("태그 조회 중 오류")
            return error_response("태그 조회 중 오류가 발생했습니다.", "SERVER_ERROR", 500)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response("잘못된 형식의 요청입니다.", "INVALID_JSON")

    try:
        tag = _create_tag.execute(
            user=request.user,
            name=data.get("name", "").strip(),
            color=data.get("color", "").strip(),
            is_default=data.get("is_default", False),
            category_id=data.get("category_id"),
        )
        return success_response("태그가 생성되었습니다.", {"tag": tag}, 201)
    except PermissionError as exc:
        return error_response(str(exc), "FORBIDDEN", 403)
    except LookupError as exc:
        return error_response(str(exc), "NOT_FOUND", 400)
    except ValueError as exc:
        return error_response(str(exc), "VALIDATION_ERROR")
    except Exception:
        logging.getLogger(__name__).exception("태그 생성 중 오류")
        return error_response("태그 생성 중 오류가 발생했습니다.", "SERVER_ERROR", 500)


@login_required
@require_http_methods(["PUT", "DELETE"])
def tag_detail_update_delete(request, tag_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response("잘못된 형식의 요청입니다.", "INVALID_JSON")

        try:
            tag = _update_tag.execute(
                user=request.user,
                tag_id=tag_id,
                name=data.get("name", "").strip(),
                color=data.get("color", "").strip(),
                is_default=data.get("is_default", False),
                category_id=data.get("category_id"),
            )
            return success_response("태그가 수정되었습니다.", {"tag": tag})
        except PermissionError as exc:
            return error_response(str(exc), "FORBIDDEN", 403)
        except LookupError as exc:
            return error_response(str(exc), "NOT_FOUND", 400)
        except ValueError as exc:
            return error_response(str(exc), "VALIDATION_ERROR")
        except Exception:
            logging.getLogger(__name__).exception("태그 수정 중 오류")
            return error_response("태그 수정 중 오류가 발생했습니다.", "SERVER_ERROR", 500)

    try:
        tag_name = _delete_tag.execute(user=request.user, tag_id=tag_id)
        return success_response(f'"{tag_name}" 태그가 삭제되었습니다.')
    except PermissionError as exc:
        return error_response(str(exc), "FORBIDDEN", 403)
    except ValueError as exc:
        return error_response(str(exc), "VALIDATION_ERROR")
    except Exception:
        logging.getLogger(__name__).exception("태그 삭제 중 오류")
        return error_response("태그 삭제 중 오류가 발생했습니다.", "SERVER_ERROR", 500)
