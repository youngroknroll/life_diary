import pytest


@pytest.fixture(autouse=True)
def _use_dummy_cache(settings):
    """테스트 구간 동안 파일 기반 캐시 대신 DummyCache 사용."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
    settings.AXES_ENABLED = False
    settings.AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
    ]


@pytest.fixture
def en_client(client):
    """영어 locale 강제 client."""
    client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
    return client


@pytest.fixture
def ko_client(client):
    """한국어 locale 강제 client."""
    client.defaults["HTTP_ACCEPT_LANGUAGE"] = "ko"
    return client


@pytest.fixture
def make_user(db, django_user_model):
    """user factory — 호출마다 새 user 생성."""
    counter = {"n": 0}

    def _make(username=None, password="pass-Long-9!", **kwargs):
        counter["n"] += 1
        return django_user_model.objects.create_user(
            username=username or f"u{counter['n']}",
            password=password,
            **kwargs,
        )

    return _make


@pytest.fixture
def auth_client(client, make_user):
    """기본 user로 로그인된 client."""
    user = make_user()
    client.force_login(user)
    client.user = user
    return client


@pytest.fixture
def auth_en_client(en_client, make_user):
    """영어 locale + 로그인."""
    user = make_user()
    en_client.force_login(user)
    en_client.user = user
    return en_client
