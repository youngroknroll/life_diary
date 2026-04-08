import logging

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.db import models
from django.db.models import Q
import json

from .models import Tag
from apps.dashboard.models import TimeBlock
from apps.core.utils import serialize_for_js

# Create your views here.


@login_required
def index(request):
    tags = Tag.objects.filter(Q(user=request.user) | Q(is_default=True)).order_by(
        "-is_default", "name"
    )
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
            tags = Tag.objects.filter(
                Q(is_default=True) | Q(user=request.user)
            ).order_by("is_default", "name")

            tag_list = [
                {
                    "id": tag.id,
                    "name": tag.name,
                    "color": tag.color,
                    "is_default": tag.is_default,
                    "can_edit": not tag.is_default or request.user.is_superuser,
                    "can_delete": not tag.is_default or request.user.is_superuser,
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

            if is_default and not request.user.is_superuser:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "기본 태그는 관리자만 생성할 수 있습니다.",
                    },
                    status=403,
                )

            if not name or not color:
                return JsonResponse(
                    {"success": False, "message": "태그명과 색상을 입력해주세요."},
                    status=400,
                )

            # 중복 확인
            if Tag.objects.filter(
                Q(user=request.user, name=name) | Q(is_default=True, name=name)
            ).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": "이미 같은 이름의 태그가 존재합니다.",
                    },
                    status=400,
                )

            tag = Tag.objects.create(
                user=None if is_default else request.user,
                name=name,
                color=color,
                is_default=is_default,
            )

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
    if request.user.is_superuser:
        tag = get_object_or_404(Tag, id=tag_id)
    else:
        tag = get_object_or_404(Tag, id=tag_id, user=request.user, is_default=False)

    if request.method == "PUT":
        # 태그 수정 (기존 update_tag 로직)
        try:
            data = json.loads(request.body)
            name = data.get("name", "").strip()
            color = data.get("color", "").strip()
            is_default = data.get("is_default", tag.is_default)

            if is_default and not request.user.is_superuser:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "기본 태그는 관리자만 설정할 수 있습니다.",
                    },
                    status=403,
                )

            if not name or not color:
                return JsonResponse(
                    {"success": False, "message": "태그명과 색상을 입력해주세요."},
                    status=400,
                )

            # 중복 확인 (자신 제외)
            if (
                Tag.objects.filter(
                    Q(user=request.user, name=name) | Q(is_default=True, name=name)
                )
                .exclude(id=tag.id)
                .exists()
            ):
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
            tag.save()

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
            if tag.is_default and TimeBlock.objects.filter(tag=tag).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": "이 기본 태그는 사용 중이어서 삭제할 수 없습니다.",
                    },
                    status=400,
                )

            tag_name = tag.name
            tag.delete()

            return JsonResponse(
                {"success": True, "message": f'"{tag_name}" 태그가 삭제되었습니다.'}
            )

        except Exception:
            logging.getLogger(__name__).exception("태그 삭제 중 오류")
            return JsonResponse(
                {"success": False, "message": "태그 삭제 중 오류가 발생했습니다."}, status=500
            )
