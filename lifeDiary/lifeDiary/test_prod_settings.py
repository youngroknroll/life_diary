import importlib


def test_prod_settings_disable_debug_and_use_resend(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "test-secret")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_dummy")
    monkeypatch.setenv("DEFAULT_FROM_EMAIL", "LifeDiary <noreply@example.com>")

    prod_settings = importlib.import_module("lifeDiary.settings.prod")
    prod_settings = importlib.reload(prod_settings)

    assert prod_settings.DEBUG is False
    assert prod_settings.EMAIL_BACKEND == "apps.core.email_backends.ResendEmailBackend"
    assert prod_settings.RESEND_API_KEY == "re_test_dummy"
    assert prod_settings.DEFAULT_FROM_EMAIL == "LifeDiary <noreply@example.com>"
