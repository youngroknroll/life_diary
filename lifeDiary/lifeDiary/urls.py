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
from django.contrib.auth.decorators import user_passes_test
from . import views

# 관리자만 admin 패널 접근 가능하도록 제한
admin.site.login = user_passes_test(lambda u: u.is_superuser, login_url="/")(
    admin.site.login
)

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("admin/", admin.site.urls),
    path("", views.index, name="home"),
    # Page URLs
    path("dashboard/", include("apps.dashboard.urls")),
    path("stats/", include("apps.stats.urls")),
    path("tags/", include("apps.tags.urls")),
    path("accounts/", include("apps.users.urls")),
    # API URLs
    path("api/", include("apps.dashboard.api_urls")),
    path("api/", include("apps.tags.api_urls")),
]
