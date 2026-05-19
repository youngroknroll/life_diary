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
