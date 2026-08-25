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

from django.contrib import admin
from django.urls import path, include
from allauth.urls import build_provider_urlpatterns
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
        lambda request: HttpResponse(
            "User-agent: *\nDisallow: /\n",
            content_type="text/plain",
        ),
        name="robots-txt",
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
    # API URLs
    path("api/", api.urls),
]
