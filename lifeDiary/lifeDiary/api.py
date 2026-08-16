import json

from django.utils.translation import gettext
from ninja import NinjaAPI, Swagger
from ninja.errors import AuthenticationError, HttpError, ValidationError
from ninja.security import django_auth

from apps.core.schemas import error_payload
from apps.tags.api import router as tags_router

api = NinjaAPI(
    title="LifeDiary API",
    version="1.0.0",
    description="10분 슬롯 기록과 태그 관리를 위한 내부 JSON API",
    auth=django_auth,
    docs=Swagger(),
)


@api.exception_handler(AuthenticationError)
def on_authentication_error(request, exc):
    return api.create_response(
        request,
        error_payload(gettext("로그인이 필요합니다."), "UNAUTHORIZED"),
        status=401,
    )


@api.exception_handler(ValidationError)
def on_validation_error(request, exc):
    message = exc.errors[0]["msg"] if exc.errors else gettext("요청이 올바르지 않습니다.")
    return api.create_response(
        request, error_payload(message, "VALIDATION_ERROR"), status=400
    )


# ninja는 본문 파싱 실패를 HttpError(400)로 감싼다(__cause__에 원인 보존).
@api.exception_handler(HttpError)
def on_http_error(request, exc):
    if isinstance(exc.__cause__, json.JSONDecodeError):
        return api.create_response(
            request,
            error_payload(gettext("올바른 JSON 형식이 아닙니다."), "INVALID_JSON"),
            status=400,
        )
    return api.create_response(
        request, {"detail": str(exc)}, status=exc.status_code
    )


api.add_router("", tags_router)
