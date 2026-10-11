"""프로덕션 설정. base.py 의 공유 값 위에 Render·Supabase 환경과 보안 강화를 얹는다."""

import os

from .base import *

# 프로덕션 환경 오버라이드
DEBUG = False

# 프로덕션 DB (Supabase PostgreSQL — Transaction Pooler port 6543)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "6543"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
}
ALLOWED_HOSTS = ["lifediary.onrender.com","www.lifediary.kr","lifediary.kr"]

# 프로덕션 보안 설정
# Render는 TLS를 프록시에서 종료하고 X-Forwarded-Proto를 전달한다.
# 이 헤더를 신뢰하지 않으면 request.is_secure()가 오판해
# SECURE_SSL_REDIRECT와 결합 시 리다이렉트 루프가 발생할 수 있다.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    "https://lifediary.onrender.com",
    "https://www.lifediary.kr",
    "https://lifediary.kr",
]
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1년
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# CSP: 현재 템플릿이 실제로 사용하는 출처만 허용하는 심층방어 헤더.
# 인라인 스크립트/핸들러와 Alpine.js가 남아 있어 'unsafe-inline'/'unsafe-eval'을
# 허용한다. nonce 기반 엄격화는 인라인 제거 작업과 함께 별도 승인 대상.
MIDDLEWARE = MIDDLEWARE + ["apps.core.middleware.ContentSecurityPolicyMiddleware"]
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
        " https://cdn.jsdelivr.net https://unpkg.com"
        " https://www.google.com https://www.gstatic.com"
        " https://www.googletagmanager.com",
        "style-src 'self' 'unsafe-inline'"
        " https://cdn.jsdelivr.net",
        "font-src 'self' data: https://cdn.jsdelivr.net",
        "img-src 'self' data:"
        " https://*.google-analytics.com https://*.googletagmanager.com",
        "connect-src 'self'"
        " https://*.google-analytics.com https://*.analytics.google.com"
        " https://*.googletagmanager.com",
        "frame-src https://www.google.com",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)

# 프로덕션 전용 세션 보안 설정
SESSION_COOKIE_AGE = 3600  # 1시간 (초 단위)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 브라우저 종료 시 세션 만료
SESSION_SAVE_EVERY_REQUEST = False  # DB session write 최소화 (Django 기본값)
PASSWORD_RESET_TIMEOUT = 60 * 60 * 3  # 3시간
AXES_ENABLED = True
# reCAPTCHA is the user-facing challenge after repeated failures; keep axes from
# returning an account-locked response before that challenge can be completed.
AXES_FAILURE_LIMIT = int(os.getenv("AXES_FAILURE_LIMIT", "1000"))
LOGIN_RECAPTCHA_ENABLED = True
LOGIN_RECAPTCHA_FAILURE_LIMIT = 5
LOGIN_RECAPTCHA_CACHE_TIMEOUT = 60 * 60
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/lifediary-cache",
        "OPTIONS": {"MAX_ENTRIES": 500},
    },
    # 브루트포스 카운터는 /tmp 파일 캐시에 두지 않는다. 재배포·cull 에 지워지면
    # reCAPTCHA 게이트가 풀린다. 테이블은 core 0001 마이그레이션이 만든다.
    "security": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "lifediary_security_cache",
        "OPTIONS": {"MAX_ENTRIES": 10000},
    },
}

STATS_SERVER_TIMING_ENABLED = (
    os.getenv("STATS_SERVER_TIMING_ENABLED", "").lower() == "true"
)

# manifest 해시 + whitenoise 압축·장기 캐시. prod 에만 둔다: pytest 는
# DEBUG=False 로 강제되므로 dev 에 manifest 를 두면 collectstatic 없이는
# 템플릿의 {% static %} 해석이 깨진다. 배포 빌드의 collectstatic 은 반드시
# prod 설정으로 실행되어야 한다(아니면 manifest 부재로 기동 후 500).
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Email (production: Gmail SMTP)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# 500 응답의 트레이스백을 메일로 받는다. 외부 추적 서비스 없이 Gmail SMTP 를
# 그대로 쓴다. 따로 주소를 주지 않으면 발신 계정 자신(운영 문의 메일함)으로
# 보낸다. 둘 다 비어 있으면 ADMINS 가 비어 콘솔 로그만 남는다.
ERROR_REPORT_EMAIL = os.getenv("ERROR_REPORT_EMAIL", EMAIL_HOST_USER)
ADMINS = [("LifeDiary", ERROR_REPORT_EMAIL)] if ERROR_REPORT_EMAIL else []

# Production error visibility: keep DEBUG=False, but send server-side errors
# and framework warnings/errors to the deployment console.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "mail_admins": {
            "class": "django.utils.log.AdminEmailHandler",
            "level": "ERROR",
            "include_html": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
