import json
import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext, gettext_lazy as _
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


@login_required
def index(request):
    return render(request, "tags/index.html")


# 안내 화면의 예시일 뿐 사용자 태그가 아니다. 시안 7a 의 세 번째 열.
CATEGORY_EXAMPLE_TAGS = {
    "investment": [_("집중 작업"), _("회의"), _("학습")],
    "proactive": [_("운동"), _("약속")],
    "passive": [_("여가"), _("멍때림")],
    "basic_life": [_("식사"), _("이동")],
    "sleep": [_("수면"), _("낮잠")],
}


@login_required
@require_GET
def category_guide(request):
    """소비시간 다섯 분류 설명. 색이 무엇을 뜻하는지 읽는 화면이다."""
    categories = list(_category_repo.find_all())
    for category in categories:
        category.example_tags = CATEGORY_EXAMPLE_TAGS.get(category.slug, [])
    return render(
        request,
        "tags/category_guide.html",
        {"categories": categories},
    )


@login_required
@require_GET
def category_list(request):
    try:
        categories = _category_repo.find_all()
        return success_response(
            gettext("카테고리 목록"),
            {
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
                ]
            },
        )
    except Exception:
        logging.getLogger(__name__).exception("카테고리 조회 중 오류")
        return error_response(gettext("카테고리 조회 중 오류가 발생했습니다."), "SERVER_ERROR", 500)


@login_required
@require_http_methods(["GET", "POST"])
def tag_list_create(request):
    if request.method == "GET":
        try:
            tags = _list_tags.execute(request.user)
            return success_response(
                gettext("태그 목록"),
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
                            "block_count": t.block_count,
                            "total_hours": t.total_hours,
                        }
                        for t in tags
                    ]
                },
            )
        except Exception:
            logging.getLogger(__name__).exception("태그 조회 중 오류")
            return error_response(gettext("태그 조회 중 오류가 발생했습니다."), "SERVER_ERROR", 500)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return error_response(gettext("잘못된 형식의 요청입니다."), "INVALID_JSON")

    try:
        tag = _create_tag.execute(
            user=request.user,
            name=data.get("name", "").strip(),
            color=data.get("color", "").strip(),
            is_default=data.get("is_default", False),
            category_id=data.get("category_id"),
        )
        return success_response(gettext("태그가 생성되었습니다."), {"tag": tag}, 201)
    except PermissionError as exc:
        return error_response(str(exc), "FORBIDDEN", 403)
    except LookupError as exc:
        return error_response(str(exc), "NOT_FOUND", 400)
    except ValueError as exc:
        return error_response(str(exc), "VALIDATION_ERROR")
    except Exception:
        logging.getLogger(__name__).exception("태그 생성 중 오류")
        return error_response(gettext("태그 생성 중 오류가 발생했습니다."), "SERVER_ERROR", 500)


@login_required
@require_http_methods(["PUT", "DELETE"])
def tag_detail_update_delete(request, tag_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_response(gettext("잘못된 형식의 요청입니다."), "INVALID_JSON")

        try:
            tag = _update_tag.execute(
                user=request.user,
                tag_id=tag_id,
                name=data.get("name", "").strip(),
                color=data.get("color", "").strip(),
                is_default=data.get("is_default", False),
                category_id=data.get("category_id"),
            )
            return success_response(gettext("태그가 수정되었습니다."), {"tag": tag})
        except PermissionError as exc:
            return error_response(str(exc), "FORBIDDEN", 403)
        except LookupError as exc:
            return error_response(str(exc), "NOT_FOUND", 400)
        except ValueError as exc:
            return error_response(str(exc), "VALIDATION_ERROR")
        except Exception:
            logging.getLogger(__name__).exception("태그 수정 중 오류")
            return error_response(gettext("태그 수정 중 오류가 발생했습니다."), "SERVER_ERROR", 500)

    try:
        move_to = _parse_move_to(request)
    except ValueError as exc:
        return error_response(str(exc), "VALIDATION_ERROR")

    try:
        tag_name = _delete_tag.execute(
            user=request.user, tag_id=tag_id, move_to_id=move_to
        )
        return success_response(
            gettext('"%(name)s" 태그가 삭제되었습니다.') % {"name": tag_name}
        )
    except PermissionError as exc:
        return error_response(str(exc), "FORBIDDEN", 403)
    except ValueError as exc:
        return error_response(str(exc), "VALIDATION_ERROR")
    except Exception:
        logging.getLogger(__name__).exception("태그 삭제 중 오류")
        return error_response(gettext("태그 삭제 중 오류가 발생했습니다."), "SERVER_ERROR", 500)
