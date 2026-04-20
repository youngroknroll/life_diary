from django.conf import settings


def pytest_configure(config):
    if settings.configured:
        return
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "apps.core",
            "apps.dashboard",
            "apps.tags",
            "apps.users",
            "apps.stats",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            }
        },
        USE_TZ=False,
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
