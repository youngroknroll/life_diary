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
