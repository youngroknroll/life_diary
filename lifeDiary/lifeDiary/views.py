from django.shortcuts import render
from django.http import HttpRequest


def index(request: HttpRequest):
    """
    메인 홈페이지
    """
    context = {
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
