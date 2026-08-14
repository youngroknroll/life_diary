"""내보내기 엔드포인트 — 무엇을 내주고 무엇을 막는가."""

from datetime import date

import pytest
from django.contrib.messages import get_messages

from apps.dashboard.models import TimeBlock
from apps.tags.models import Category, Tag


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
ENDPOINT = "/stats/export/"
INDEX_URL = "/stats/"


def record(user, tag, on_date, slots=1, first_slot=0):
    for offset in range(slots):
        TimeBlock.objects.create(
            user=user, date=on_date, slot_index=first_slot + offset, tag=tag
        )


@pytest.fixture
def tag(auth_client):
    return Tag.objects.create(
        user=auth_client.user, name="집중",
        category=Category.objects.get(slug="investment"),
    )


class TestExportEndpoint:
    def test_returns_a_workbook(self, auth_client, tag):
        record(auth_client.user, tag, date(2026, 8, 5))

        resp = auth_client.get(ENDPOINT, {"month": "2026-08"})

        assert resp.status_code == 200
        assert resp["Content-Type"] == XLSX
        assert "lifediary-2026-08.xlsx" in resp["Content-Disposition"]
        assert resp.content[:2] == b"PK"        # xlsx 는 zip 이다

    def test_a_month_without_records_is_refused(self, auth_client, tag):
        record(auth_client.user, tag, date(2026, 8, 5))

        resp = auth_client.get(ENDPOINT, {"month": "2026-07"})

        assert resp.status_code == 302
        assert resp["Location"] == INDEX_URL
        assert len(get_messages(resp.wsgi_request)) == 1

    def test_a_broken_month_is_refused(self, auth_client, tag):
        record(auth_client.user, tag, date(2026, 8, 5))

        for params in [{"month": "말도안됨"}, {"month": "2026-13"}, {}]:
            resp = auth_client.get(ENDPOINT, params)
            assert resp.status_code == 302
            assert resp["Location"] == INDEX_URL

    def test_requires_login(self, client):
        assert client.get(ENDPOINT, {"month": "2026-08"}).status_code != 200

    def test_cannot_reach_another_users_month(self, auth_client, tag, make_user):
        """남의 달을 주소로 요청해도 내 기록 기준으로만 판단한다."""
        stranger = make_user(username="viewstranger")
        stranger_tag = Tag.objects.create(
            user=stranger, name="남의것",
            category=Category.objects.get(slug="passive"),
        )
        record(stranger, stranger_tag, date(2026, 7, 1))
        record(auth_client.user, tag, date(2026, 8, 5))

        assert auth_client.get(ENDPOINT, {"month": "2026-07"}).status_code == 302
