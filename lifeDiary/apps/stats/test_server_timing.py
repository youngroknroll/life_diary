import importlib
import re
from datetime import date

import pytest
from django.conf import settings as django_settings
from django.core.cache import cache

from apps.dashboard.models import TimeBlock
from apps.stats.use_cases import GetStatsContextUseCase
from apps.tags.models import Category, Tag

LOCMEM_CACHE_BACKEND = "django.core.cache.backends.locmem.LocMemCache"
DUMMY_CACHE_BACKEND = "django.core.cache.backends.dummy.DummyCache"
STATS_DATE = date(2026, 4, 15)
STATS_PATH = f"/stats/?date={STATS_DATE.isoformat()}"
SERVER_TIMING_FORMAT = re.compile(
    r'cache;desc="(?P<cache>hit|miss)", ctx;dur=\d+\.\d, db;dur=\d+\.\d, '
    r'db-count;desc="(?P<queries>\d+) queries"'
)


@pytest.fixture
def recorded_user(make_user):
    user = make_user(username="timing_user")
    category = Category.objects.create(
        name="타이밍", slug="timing_cat", color="#112233", display_order=998
    )
    tag = Tag.objects.create(user=user, name="work", color="#abcdef", category=category)
    TimeBlock.objects.create(user=user, date=STATS_DATE, slot_index=0, tag=tag, memo="")
    return user


def test_second_stats_context_lookup_is_a_cache_hit(recorded_user, settings):
    settings.CACHES = {
        "default": {"BACKEND": LOCMEM_CACHE_BACKEND, "LOCATION": "server-timing-use-case"}
    }
    cache.clear()

    first = GetStatsContextUseCase().execute(recorded_user, STATS_DATE)
    second = GetStatsContextUseCase().execute(recorded_user, STATS_DATE)

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.context == first.context


def test_dev_settings_leave_server_timing_disabled():
    assert getattr(django_settings, "STATS_SERVER_TIMING_ENABLED", False) is False


def test_desktop_settings_leave_server_timing_disabled(monkeypatch, tmp_path):
    # desktop 설정은 import 할 때 홈 아래에 데이터 폴더와 secret_key 를 만든다.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    desktop_settings = importlib.import_module("lifeDiary.settings.desktop")
    desktop_settings = importlib.reload(desktop_settings)

    assert getattr(desktop_settings, "STATS_SERVER_TIMING_ENABLED", False) is False
    assert desktop_settings.USER_DATA_DIR.is_relative_to(tmp_path)


def test_stats_response_reports_server_timing_when_enabled(
    client, recorded_user, settings
):
    settings.STATS_SERVER_TIMING_ENABLED = True
    assert settings.CACHES["default"]["BACKEND"] == DUMMY_CACHE_BACKEND
    client.force_login(recorded_user)

    response = client.get(STATS_PATH)

    assert "Server-Timing" in response
    timing = SERVER_TIMING_FORMAT.fullmatch(response["Server-Timing"])
    assert timing is not None, response["Server-Timing"]
    assert timing["cache"] == "miss"
    assert int(timing["queries"]) > 0
