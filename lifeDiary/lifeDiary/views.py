from django.conf import settings
from django.shortcuts import render
from django.http import HttpRequest


def _public_page_context() -> dict:
    """공개 페이지에만 노출되는 검색 색인·웹 분석 컨텍스트."""
    return {
        "ga_measurement_id": settings.GA_MEASUREMENT_ID,
        "google_site_verification": settings.GOOGLE_SITE_VERIFICATION,
    }


def index(request: HttpRequest):
    """
    메인 홈페이지
    """
    context = {
        **_public_page_context(),
        "project_name": "라이프 다이어리",
        "project_description": "복잡한 입력 없이 하루를 단순하게 기록하고 돌아보는 서비스입니다.",
        "features": [
            {
                "icon": "fas fa-pen",
                "title": "기록하기",
                "description": "오늘 한 일을 가볍게 남깁니다.",
            },
            {
                "icon": "fas fa-tags",
                "title": "정리하기",
                "description": "태그로 하루의 흐름을 구분합니다.",
            },
            {
                "icon": "fas fa-chart-simple",
                "title": "돌아보기",
                "description": "쌓인 기록에서 생활 패턴을 확인합니다.",
            },
        ],
    }
    return render(request, "index.html", context)


def privacy_policy(request: HttpRequest):
    """Public privacy policy page."""
    return render(request, "legal/privacy.html", _public_page_context())


def terms_of_service(request: HttpRequest):
    """Public terms of service page."""
    return render(request, "legal/terms.html", _public_page_context())
