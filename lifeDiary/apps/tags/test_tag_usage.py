"""태그 목록의 누적 기록.

태그마다 얼마나 쌓였는지 보이지 않으면 안 쓰는 태그가 계속 늘어나고,
지울 때 무엇이 사라지는지도 알 수 없다.
"""

from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.tags.models import Category, Tag
from apps.tags.use_cases import ListTagsUseCase


TARGET = date(2026, 8, 1)


@pytest.fixture
def user(make_user):
    return make_user(username="usageuser")


@pytest.fixture
def focus(user):
    return Tag.objects.create(
        user=user, name="집중", is_default=False,
        category=Category.objects.get(slug="investment"),
    )


def record(user, tag, count, on_date=TARGET, first_slot=0):
    for offset in range(count):
        TimeBlock.objects.create(
            user=user, date=on_date, slot_index=first_slot + offset, tag=tag
        )


def find(rows, name):
    return next(row for row in rows if row.name == name)


@pytest.mark.django_db
class TestTagUsage:
    def test_an_unused_tag_reports_zero(self, user, focus):
        rows = ListTagsUseCase().execute(user)

        assert find(rows, "집중").block_count == 0
        assert find(rows, "집중").total_hours == 0.0

    def test_each_block_counts_ten_minutes(self, user, focus):
        record(user, focus, count=6)

        row = find(ListTagsUseCase().execute(user), "집중")

        assert row.block_count == 6
        assert row.total_hours == 1.0

    def test_usage_spans_every_date(self, user, focus):
        record(user, focus, count=3)
        record(user, focus, count=3, on_date=date(2026, 7, 20))

        assert find(ListTagsUseCase().execute(user), "집중").block_count == 6

    def test_another_users_records_do_not_count(self, user, focus, make_user):
        stranger = make_user(username="stranger")
        record(stranger, focus, count=6)

        assert find(ListTagsUseCase().execute(user), "집중").block_count == 0

    def test_usage_is_reported_per_tag(self, user, focus):
        other = Tag.objects.create(
            user=user, name="여가", is_default=False,
            category=Category.objects.get(slug="passive"),
        )
        record(user, focus, count=6)
        record(user, other, count=3, first_slot=20)

        rows = ListTagsUseCase().execute(user)

        assert find(rows, "집중").block_count == 6
        assert find(rows, "여가").block_count == 3


@pytest.mark.django_db
class TestTagListEndpoint:
    def test_usage_reaches_the_client(self, client, user, focus):
        client.force_login(user)
        record(user, focus, count=6)

        payload = client.get("/api/tags/").json()
        row = next(t for t in payload["tags"] if t["name"] == "집중")

        assert row["block_count"] == 6
        assert row["total_hours"] == 1.0
