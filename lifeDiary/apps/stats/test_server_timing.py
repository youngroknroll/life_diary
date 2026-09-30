import importlib
import re
from datetime import date

import pytest
from django.conf import settings as django_settings
from django.core.cache import cache
from django.db import connection

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


def test_stats_response_server_timing_reports_cache_hit_on_repeat_view(
    client, recorded_user, settings
):
    settings.STATS_SERVER_TIMING_ENABLED = True
    settings.CACHES = {
        "default": {"BACKEND": LOCMEM_CACHE_BACKEND, "LOCATION": "server-timing-repeat-view"}
    }
    cache.clear()
    client.force_login(recorded_user)
    client.get(STATS_PATH)

    response = client.get(STATS_PATH)

    timing = SERVER_TIMING_FORMAT.fullmatch(response["Server-Timing"])
    assert timing is not None, response["Server-Timing"]
    assert timing["cache"] == "hit"


def test_stats_response_omits_server_timing_when_disabled(
    client, recorded_user, settings
):
    settings.STATS_SERVER_TIMING_ENABLED = False
    client.force_login(recorded_user)

    response = client.get(STATS_PATH)

    assert response.status_code == 200
    assert "Server-Timing" not in response


def test_anonymous_stats_redirect_omits_server_timing(client, db, settings):
    settings.STATS_SERVER_TIMING_ENABLED = True

    response = client.get(STATS_PATH)

    assert response.status_code == 302
    assert "Server-Timing" not in response


def test_server_timing_header_excludes_user_and_query_content(
    client, make_user, settings
):
    settings.STATS_SERVER_TIMING_ENABLED = True
    user = make_user(username="leakcheck_owner", email="leakcheck@example.com")
    client.force_login(user)

    response = client.get("/stats/?date=2026-03-07")

    header = response["Server-Timing"]
    assert SERVER_TIMING_FORMAT.fullmatch(header), header
    for private in (
        "leakcheck_owner",
        "leakcheck@example.com",
        "2026-03-07",
        "SELECT",
        "FROM",
        "stats:",
    ):
        assert private not in header, private


def test_stats_page_still_renders_when_server_timing_measurement_fails(
    client, recorded_user, settings, monkeypatch
):
    settings.STATS_SERVER_TIMING_ENABLED = True
    client.force_login(recorded_user)

    def unavailable_wrapper(wrapper):
        raise RuntimeError("query instrumentation unavailable")

    monkeypatch.setattr(connection, "execute_wrapper", unavailable_wrapper)

    response = client.get(STATS_PATH)

    assert response.status_code == 200
    assert "stats/index.html" in [template.name for template in response.templates]
    assert "Server-Timing" not in response
