import importlib


def test_prod_settings_explicitly_define_cookie_security_contract():
    prod_settings = importlib.import_module("lifeDiary.settings.prod")

    assert prod_settings.SESSION_COOKIE_SECURE is True
    assert prod_settings.CSRF_COOKIE_SECURE is True
    assert prod_settings.SESSION_COOKIE_HTTPONLY is True
    assert prod_settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert prod_settings.CSRF_COOKIE_SAMESITE == "Lax"


def test_prod_settings_define_password_reset_timeout():
    prod_settings = importlib.import_module("lifeDiary.settings.prod")

    assert prod_settings.PASSWORD_RESET_TIMEOUT == 60 * 60 * 3
