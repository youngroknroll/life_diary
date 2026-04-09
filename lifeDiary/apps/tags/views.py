import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
import json

from .repositories import TagRepository
from .domain_services import _tag_policy_service
from apps.dashboard.repositories import TimeBlockRepository
from apps.core.utils import serialize_for_js

_tag_repo = TagRepository()
_time_block_repo = TimeBlockRepository()

# Create your views here.


@login_required
def index(request):
    tags = _tag_repo.find_accessible_ordered(request.user)
    context = {
        "tags": tags,
        "tags_json": serialize_for_js(
            [
                {
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "is_default": tag.is_default,
                }
                for tag in tags
            ]
        ),
    }
    return render(request, "tags/index.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def tag_list_create(request):
    """
    태그 목록 조회 (GET) 또는 새 태그 생성 (POST)
    """
    if request.method == "GET":
        # 사용자가 사용 가능한 모든 태그 조회 (기존 get_tags 로직)
        try:
            tags = _tag_repo.find_accessible(request.user).order_by("is_default", "name")

            tag_list = [
                {
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "is_default": tag.is_default,
                    "can_edit": _tag_policy_service.can_edit(request.user, tag),
                    "can_delete": _tag_policy_service.can_delete(request.user, tag),
                }
                for tag in tags
            ]

            return JsonResponse({"success": True, "tags": tag_list})
        except Exception:
            logging.getLogger(__name__).exception("태그 조회 중 오류")
            return JsonResponse(
                {"success": False, "message": "태그 조회 중 오류가 발생했습니다."}, status=500
            )

    elif request.method == "POST":
        # 새 태그 생성 (기존 create_tag 로직)
        try:
            data = json.loads(request.body)
            name = data.get("name", "").strip()
            color = data.get("color", "").strip()
            is_default = data.get("is_default", False)

            try:
                _tag_policy_service.validate_create_default(request.user, is_default)
            except PermissionError as e:
                return JsonResponse({"success": False, "message": str(e)}, status=403)

            if not name or not color:
                return JsonResponse(
                    {"success": False, "message": "태그명과 색상을 입력해주세요."},
                    status=400,
                )

            # 중복 확인
            if _tag_repo.exists_duplicate(request.user, name):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "이미 같은 이름의 태그가 존재합니다.",
                    },
                    status=400,
                )

            tag = _tag_repo.create(request.user, name, color, is_default)

            return JsonResponse(
                {
                    "success": True,
                    "message": f"태그가 생성되었습니다.",
                    "tag": {
                        "id": tag.id,
                        "name": tag.name,
                        "color": tag.color,
                        "is_default": tag.is_default,
                    },
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "잘못된 형식의 요청입니다."}, status=400
            )
        except Exception:
            logging.getLogger(__name__).exception("태그 생성 중 오류")
            return JsonResponse(
                {"success": False, "message": "태그 생성 중 오류가 발생했습니다."}, status=500
            )


@login_required
@require_http_methods(["PUT", "DELETE"])
def tag_detail_update_delete(request, tag_id):
    """
    특정 태그 수정 (PUT) 또는 삭제 (DELETE)
    """
    # 태그 객체 가져오기 (권한 확인 포함)
    tag = _tag_repo.get_for_owner_or_404(tag_id, request.user)

    if request.method == "PUT":
        # 태그 수정 (기존 update_tag 로직)
        try:
            data = json.loads(request.body)
            name = data.get("name", "").strip()
            color = data.get("color", "").strip()
            requested_is_default = data.get("is_default", tag.is_default)
            try:
                _tag_policy_service.validate_default_flip(
                    request.user, tag, requested_is_default
                )
            except PermissionError as e:
                return JsonResponse({"success": False, "message": str(e)}, status=403)
            is_default = requested_is_default

            if not name or not color:
                return JsonResponse(
                    {"success": False, "message": "태그명과 색상을 입력해주세요."},
                    status=400,
                )

            # 중복 확인 (자신 제외)
            if _tag_repo.exists_duplicate(request.user, name, exclude_id=tag.id):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "이미 같은 이름의 태그가 존재합니다.",
                    },
                    status=400,
                )

            tag.name = name
            tag.color = color
            tag.is_default = is_default
            tag.user = None if is_default else request.user
            _tag_repo.save(tag)

            return JsonResponse(
                {
                    "success": True,
                    "message": "태그가 수정되었습니다.",
                    "tag": {
                        "id": tag.id,
                        "name": tag.name,
                        "color": tag.color,
                        "is_default": tag.is_default,
                    },
                }
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "message": "잘못된 형식의 요청입니다."}, status=400
            )
        except Exception:
            logging.getLogger(__name__).exception("태그 수정 중 오류")
            return JsonResponse(
                {"success": False, "message": "태그 수정 중 오류가 발생했습니다."}, status=500
            )

    elif request.method == "DELETE":
        # 태그 삭제 (기존 delete_tag 로직)
        try:
            # 기본 태그는 사용 중이면 삭제 불가
            if tag.is_default and _time_block_repo.is_tag_in_use(tag):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "이 기본 태그는 사용 중이어서 삭제할 수 없습니다.",
                    },
                    status=400,
                )

            tag_name = tag.name
            _tag_repo.delete(tag)

            return JsonResponse(
                {"success": True, "message": f'"{tag_name}" 태그가 삭제되었습니다.'}
            )

        except Exception:
            logging.getLogger(__name__).exception("태그 삭제 중 오류")
            return JsonResponse(
                {"success": False, "message": "태그 삭제 중 오류가 발생했습니다."}, status=500
            )
