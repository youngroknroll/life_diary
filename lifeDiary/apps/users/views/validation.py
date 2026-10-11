import re
from django.http import JsonResponse
from django.utils.translation import gettext
from django.views.decorators.http import require_GET
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from ..repositories import UserAccountRepository
from .. import login_protection

_user_repo = UserAccountRepository()


_USERNAME_RE = re.compile(r"^[\w.@+\-]+$")


_USERNAME_MAX_LENGTH = 30


def _get_rate_limit_retry_message():
    return gettext("잠시 후 다시 시도해주세요.")


@require_GET
def check_username_view(request):
    """signup blur 시 username 중복/형식 비동기 검증."""
    if login_protection.is_rate_limited(
        request,
        "check-username",
        "VALIDATION_RATE_LIMIT_MAX_ATTEMPTS",
        "VALIDATION_RATE_LIMIT_WINDOW_SECONDS",
    ):
        return JsonResponse({"available": False, "message": _get_rate_limit_retry_message()})
    username = (request.GET.get("username") or "").strip()
    if not username:
        return JsonResponse({"available": False, "message": gettext("사용자명을 입력해주세요.")})
    if len(username) > _USERNAME_MAX_LENGTH:
        return JsonResponse(
            {"available": False, "message": gettext("사용자명은 30자 이하여야 합니다.")}
        )
    if not _USERNAME_RE.match(username):
        return JsonResponse(
            {"available": False, "message": gettext("영문자, 숫자, @/./+/-/_ 만 가능합니다.")}
        )
    if _user_repo.username_exists(username):
        return JsonResponse(
            {"available": False, "message": gettext("이미 사용 중인 사용자명입니다.")}
        )
    return JsonResponse({"available": True, "message": gettext("사용 가능합니다.")})


@require_GET
def check_email_view(request):
    """signup blur 시 email 형식/중복 비동기 검증."""
    if login_protection.is_rate_limited(
        request,
        "check-email",
        "VALIDATION_RATE_LIMIT_MAX_ATTEMPTS",
        "VALIDATION_RATE_LIMIT_WINDOW_SECONDS",
    ):
        return JsonResponse({"available": False, "message": _get_rate_limit_retry_message()})
    email = (request.GET.get("email") or "").strip()
    if not email:
        return JsonResponse({"available": False, "message": gettext("이메일을 입력해주세요.")})
    try:
        validate_email(email)
    except DjangoValidationError:
        return JsonResponse(
            {"available": False, "message": gettext("올바른 이메일 형식이 아닙니다.")}
        )
    if _user_repo.email_exists(email):
        return JsonResponse(
            {"available": False, "message": gettext("이미 사용 중인 이메일입니다.")}
        )
    return JsonResponse({"available": True, "message": gettext("사용 가능합니다.")})
