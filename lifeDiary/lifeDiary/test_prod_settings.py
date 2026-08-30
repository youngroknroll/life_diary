import importlib


def test_prod_settings_disable_debug_and_use_gmail_smtp(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("EMAIL_HOST_USER", "logbetter.info@gmail.com")
    monkeypatch.setenv("EMAIL_HOST_PASSWORD", "app-password")
    monkeypatch.setenv("DEFAULT_FROM_EMAIL", "logbetter.info@gmail.com")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    assert prod_settings.DEBUG is False
    assert prod_settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend"
    assert prod_settings.EMAIL_HOST == "smtp.gmail.com"
    assert prod_settings.EMAIL_PORT == 587
    assert prod_settings.EMAIL_HOST_USER == "logbetter.info@gmail.com"
    assert prod_settings.EMAIL_HOST_PASSWORD == "app-password"
    assert prod_settings.EMAIL_USE_TLS is True
    assert prod_settings.DEFAULT_FROM_EMAIL == "logbetter.info@gmail.com"
    assert prod_settings.SERVER_EMAIL == "logbetter.info@gmail.com"


def test_prod_settings_send_error_logs_to_console(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    assert prod_settings.LOGGING["disable_existing_loggers"] is False
    assert prod_settings.LOGGING["handlers"]["console"] == {
        "class": "logging.StreamHandler",
    }
    assert prod_settings.LOGGING["root"] == {
        "handlers": ["console"],
        "level": "WARNING",
    }
    assert prod_settings.LOGGING["loggers"]["django.request"] == {
        "handlers": ["console"],
        "level": "ERROR",
        "propagate": False,
    }


def test_prod_settings_trust_render_proxy_ssl_header(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    assert prod_settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")


def test_prod_settings_trust_every_serving_host_for_csrf(monkeypatch):
    """CSRF 목록이 ALLOWED_HOSTS 를 따라가지 못하면 그 도메인의 POST 가 막힌다."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    origins = prod_settings.CSRF_TRUSTED_ORIGINS
    assert all(origin.startswith("https://") for origin in origins)
    assert {origin.removeprefix("https://") for origin in origins} == set(
        prod_settings.ALLOWED_HOSTS
    )


def test_prod_csp_policy_covers_required_sources(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    policy = prod_settings.CONTENT_SECURITY_POLICY
    assert "default-src 'self'" in policy
    assert "object-src 'none'" in policy
    assert "frame-ancestors 'none'" in policy
    # 현재 템플릿이 실제로 사용하는 CDN과 reCAPTCHA 출처만 허용한다.
    for host in (
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
        "https://unpkg.com",
        "https://www.google.com",
        "https://www.gstatic.com",
    ):
        assert host in policy
    assert (
        "apps.core.middleware.ContentSecurityPolicyMiddleware"
        in prod_settings.MIDDLEWARE
    )


def test_prod_settings_serve_hashed_static_files_with_whitenoise(monkeypatch):
    """Django 5.1에서 STATICFILES_STORAGE 가 제거되어 STORAGES 로만
    manifest 해시·압축·장기 캐시가 활성화된다."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    assert prod_settings.STORAGES["staticfiles"] == {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
    assert prod_settings.STORAGES["default"] == {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }


def test_prod_settings_enable_login_recaptcha_after_failures(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("RECAPTCHA_SITE_KEY", "site-key")
    monkeypatch.setenv("RECAPTCHA_SECRET_KEY", "secret-key")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    assert prod_settings.AXES_ENABLED is True
    assert prod_settings.AXES_FAILURE_LIMIT > prod_settings.LOGIN_RECAPTCHA_FAILURE_LIMIT
    assert prod_settings.LOGIN_RECAPTCHA_ENABLED is True
    assert prod_settings.LOGIN_RECAPTCHA_FAILURE_LIMIT == 5
    assert prod_settings.RECAPTCHA_SITE_KEY == "site-key"
    assert prod_settings.RECAPTCHA_SECRET_KEY == "secret-key"
