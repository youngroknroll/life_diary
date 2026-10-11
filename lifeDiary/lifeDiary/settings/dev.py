"""로컬 개발 설정. pytest 도 이 모듈을 쓴다(pytest.ini)."""

import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

AXES_ENABLED = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(BASE_DIR / ".cache"),
        "OPTIONS": {"MAX_ENTRIES": 500},
    },
    # 로그인 실패·복구·가입 검증 카운터. 통계 캐시의 cull 에 밀려나지 않게 따로 둔다.
    "security": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(BASE_DIR / ".cache" / "security"),
        "OPTIONS": {"MAX_ENTRIES": 10000},
    },
}

# Email (development: print to console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@lifediary.local")
