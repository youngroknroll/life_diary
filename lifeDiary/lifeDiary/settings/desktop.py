"""Desktop app settings.

Loaded when running LifeDiary as a packaged desktop app via
``desktop/launcher.py``. Bases on dev.py and overrides paths/middleware
to suit a local single-user environment.
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _user_data_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path.home() / ".local" / "share"
    path = base / "LifeDiary"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_or_create_secret_key(data_dir: Path) -> str:
    key_path = data_dir / "secret_key"
    if key_path.exists():
        return key_path.read_text(encoding="utf-8").strip()
    new_key = secrets.token_urlsafe(50)
    key_path.write_text(new_key, encoding="utf-8")
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    return new_key


USER_DATA_DIR = _user_data_dir()

SECRET_KEY = _load_or_create_secret_key(USER_DATA_DIR)

DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
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
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

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


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(USER_DATA_DIR / "db.sqlite3"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "ko-kr"

LANGUAGES = [
    ("ko", "한국어"),
    ("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True


STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATIC_URL = "static/"

if hasattr(sys, "_MEIPASS"):
    STATIC_ROOT = os.path.join(sys._MEIPASS, "staticfiles")
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": str(USER_DATA_DIR / ".cache"),
        "OPTIONS": {"MAX_ENTRIES": 500},
    }
}


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@lifediary.local"


SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
