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

# 프로덕션 DB (Supabase PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
ALLOWED_HOSTS = ["lifediary.onrender.com"]

# 프로덕션 보안 설정
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1년
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 프로덕션 전용 세션 보안 설정
SESSION_COOKIE_AGE = 3600  # 1시간 (초 단위)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # 브라우저 종료 시 세션 만료
SESSION_SAVE_EVERY_REQUEST = True  # 매 요청마다 세션 저장 (활성화 시간 갱신)
