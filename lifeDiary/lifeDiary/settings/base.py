"""Django settings for lifeDiary project.

dev.py 와 prod.py 가 공유하는 값. 환경이 갈리는 값(DEBUG, 호스트, DB, 캐시,
메일, axes 활성화)은 각 모듈이 정한다. desktop.py 는 이 파일을 쓰지 않는다.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path

from django.contrib.messages import constants as message_constants
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "ninja",
    "apps.dashboard",
    "apps.stats",
    "apps.tags",
    "apps.users",
    "apps.core",
    "axes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1
LOGIN_REDIRECT_URL = "home"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
SOCIALACCOUNT_LOGIN_ON_GET = True
# 일반 가입은 약관 동의가 필수다. 자동 가입은 그 단계를 건너뛰므로 끈다.
SOCIALACCOUNT_AUTO_SIGNUP = False
# 이메일 확인은 users 의 6자리 코드가 담당한다. allauth 의 링크 확인 메일은
# 중복이고, account URL 을 닫은 뒤로는 보낼 수도 없다.
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_FORMS = {"signup": "apps.users.social_forms.SocialSignupForm"}
SOCIALACCOUNT_ADAPTER = "apps.users.adapters.LifeDiarySocialAccountAdapter"
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {
            "access_type": "online",
            "prompt": "select_account",
        },
    }
}

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True

LOGIN_RECAPTCHA_ENABLED = False
LOGIN_RECAPTCHA_FAILURE_LIMIT = 5
LOGIN_RECAPTCHA_CACHE_TIMEOUT = 60 * 60
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY", "")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")

GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")
GOOGLE_SITE_VERIFICATION = os.getenv("GOOGLE_SITE_VERIFICATION", "")

EMAIL_VERIFICATION_ENABLED = True
EMAIL_VERIFICATION_CODE_TTL_SECONDS = 600
EMAIL_VERIFICATION_MAX_ATTEMPTS = 3
EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS = 60
EMAIL_VERIFICATION_MAX_SENDS_PER_WINDOW = 5
EMAIL_VERIFICATION_SEND_WINDOW_SECONDS = 60 * 60
PASSWORD_RESET_SESSION_TTL_SECONDS = 600

ROOT_URLCONF = "lifeDiary.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "lifeDiary.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Django 기본 ERROR 태그는 "error" 인데 Bootstrap 에는 .alert-error 가 없다.
MESSAGE_TAGS = {message_constants.ERROR: "danger"}


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "ko-kr"

LANGUAGES = [
    ("ko", "한국어"),
    ("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
# STATICFILES_STORAGE 는 Django 5.1에서 제거됐다. manifest 스토리지는
# prod.py 의 STORAGES 가 담당한다.
STATIC_URL = "static/"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

