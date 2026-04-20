import pytest


@pytest.fixture(autouse=True)
def _use_dummy_cache(settings):
    """테스트 구간 동안 파일 기반 캐시 대신 DummyCache 사용."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }
