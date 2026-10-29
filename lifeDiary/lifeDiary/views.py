"""공개 홈과 약관 페이지 뷰."""

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render


def _public_page_context() -> dict:
    """공개 페이지에만 노출되는 검색 색인·웹 분석 컨텍스트."""
    return {
        "ga_measurement_id": settings.GA_MEASUREMENT_ID,
        "google_site_verification": settings.GOOGLE_SITE_VERIFICATION,
    }


def index(request: HttpRequest):
    """메인 홈페이지."""
    context = {
        **_public_page_context(),
        "project_name": "라이프 다이어리",
        "project_description": "복잡한 입력 없이 하루를 단순하게 기록하고 돌아보는 서비스입니다.",
    }
    return render(request, "index.html", context)


def privacy_policy(request: HttpRequest):
    """Public privacy policy page."""
    return render(request, "legal/privacy.html", _public_page_context())


def terms_of_service(request: HttpRequest):
    """Public terms of service page."""
    return render(request, "legal/terms.html", _public_page_context())
