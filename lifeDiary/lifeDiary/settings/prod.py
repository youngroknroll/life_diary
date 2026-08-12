"""
Django settings for lifeDiary project.

프로덕션 환경 설정
- dev.py의 개발 설정을 프로덕션용으로 오버라이드
- 보안 강화 및 프로덕션 최적화

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/
"""

from .dev import *

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
ALLOWED_HOSTS = ["lifediary.onrender.com","lifediary.kr"]

# 프로덕션 보안 설정
# Render는 TLS를 프록시에서 종료하고 X-Forwarded-Proto를 전달한다.
# 이 헤더를 신뢰하지 않으면 request.is_secure()가 오판해
# SECURE_SSL_REDIRECT와 결합 시 리다이렉트 루프가 발생할 수 있다.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://lifediary.onrender.com"]
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
        " https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://unpkg.com"
        " https://www.google.com https://www.gstatic.com",
        "style-src 'self' 'unsafe-inline'"
        " https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "font-src 'self' data: https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
        "img-src 'self' data:",
        "connect-src 'self'",
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
    }
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

# Production error visibility: keep DEBUG=False, but send server-side errors
# and framework warnings/errors to the deployment console.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
