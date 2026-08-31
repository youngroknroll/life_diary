"""
URL configuration for lifeDiary project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from allauth.urls import build_provider_urlpatterns
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.views.i18n import JavaScriptCatalog
from . import views
from .api import api

# 관리자만 admin 패널 접근 가능하도록 제한
admin.site.login = user_passes_test(lambda u: u.is_superuser, login_url="/")(
    admin.site.login
)

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "robots.txt",
        # 홈만 색인 허용(2026-08-31 결정). /static/ 은 색인이 아니라 홈
        # 렌더링 평가용 자산 크롤 허용이다. RFC 9309 최장 일치 규칙.
        lambda request: HttpResponse(
            "User-agent: *\nAllow: /$\nAllow: /static/\nDisallow: /\n"
            f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}\n",
            content_type="text/plain",
        ),
        name="robots-txt",
    ),
    path(
        "sitemap.xml",
        # robots.txt 가 홈만 색인 허용하므로 sitemap 도 홈 하나만 담는다.
        lambda request: HttpResponse(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{request.build_absolute_uri('/')}</loc></url>\n"
            "</urlset>\n",
            content_type="application/xml",
        ),
        name="sitemap-xml",
    ),
    path(
        "favicon.ico",
        # 링크 미리보기 크롤러와 구형 브라우저는 <link> 태그 대신 루트
        # 경로를 직접 요청한다. manifest 해시 조회 없이 원본 경로로 보낸다.
        RedirectView.as_view(url=settings.STATIC_URL + "core/img/favicon-32.png"),
        name="favicon",
    ),
    path(
        "jsi18n/",
        JavaScriptCatalog.as_view(
            packages=[
                "apps.core",
                "apps.dashboard",
                "apps.stats",
                "apps.tags",
                "apps.users",
            ]
        ),
        name="javascript-catalog",
    ),
    path("admin/", admin.site.urls),
    path("", views.index, name="home"),
    path("privacy/", views.privacy_policy, name="privacy"),
    path("terms/", views.terms_of_service, name="terms"),
    # Page URLs
    path("dashboard/", include("apps.dashboard.urls")),
    path("stats/", include("apps.stats.urls")),
    path("tags/", include("apps.tags.urls")),
    path("accounts/", include("apps.users.urls")),
    # allauth.urls 전체 대신 소셜 경로만 연다. account URL 을 열어 두면 링크
    # 방식 비밀번호 재설정이 코드 방식 옆에 그대로 살아 있게 된다.
    path("accounts/3rdparty/", include("allauth.socialaccount.urls")),
    path("accounts/", include(build_provider_urlpatterns())),
    # allauth 내부가 reverse("account_login") 을 쓴다. 해석은 위의 users 로그인이
    # 먼저 가져가고, 이 항목은 이름만 채운다.
    path(
        "accounts/login/",
        RedirectView.as_view(pattern_name="users:login"),
        name="account_login",
    ),
    # API URLs
    path("api/", api.urls),
]
