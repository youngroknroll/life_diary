"""자주 쓰는 태그.

시안 6c 는 빈 화면에서 태그 몇 개를 바로 집어 주는 자리를 둔다. 제목은
"자주 쓰는 태그"이고, 아직 쓴 적이 없으면 만들어진 순서를 보여 준다.
"""

from datetime import date

import pytest

from apps.dashboard.models import TimeBlock
from apps.tags.models import Category, Tag
from apps.tags.repositories import TagRepository
from apps.tags.use_cases import FREQUENT_TAG_LIMIT, ListFrequentTagsUseCase


TARGET = date(2026, 8, 1)


@pytest.fixture
def use_case():
    return ListFrequentTagsUseCase()


@pytest.fixture
def user(make_user):
    return make_user(username="frequser")


def make_tag(user, name, slug="investment"):
    return Tag.objects.create(
        user=user, name=name, category=Category.objects.get(slug=slug)
    )


_next_slot = {"value": 0}


def record(user, tag, count):
    """태그마다 다른 칸에 적는다. 같은 칸은 하루에 하나뿐이다."""
    for _ in range(count):
        TimeBlock.objects.create(
            user=user, date=TARGET, slot_index=_next_slot["value"], tag=tag
        )
        _next_slot["value"] += 1


class TestWithoutUsage:
    def test_falls_back_to_the_default_order(self, use_case, user):
        """쓴 적이 없으면 태그 목록이 쓰는 순서를 그대로 따른다."""
        for name in ["집중 작업", "회의", "학습", "운동", "약속"]:
            make_tag(user, name)

        expected = [tag.name for tag in TagRepository().find_accessible_ordered(user)]

        tags = use_case.execute(user)

        assert [tag.name for tag in tags] == expected[:FREQUENT_TAG_LIMIT]

    def test_never_returns_more_than_the_limit(self, use_case, user):
        for index in range(FREQUENT_TAG_LIMIT + 3):
            make_tag(user, f"태그{index}")

        assert len(use_case.execute(user)) == FREQUENT_TAG_LIMIT

    def test_no_tags_means_no_row(self, use_case, user):
        assert use_case.execute(user) == []


class TestWithUsage:
    def test_most_used_comes_first(self, use_case, user):
        rare = make_tag(user, "회의")
        common = make_tag(user, "집중 작업")
        record(user, rare, 2)
        record(user, common, 5)

        tags = use_case.execute(user)

        assert [tag.name for tag in tags][:2] == ["집중 작업", "회의"]

    def test_unused_tags_still_fill_the_remaining_slots(self, use_case, user):
        used = make_tag(user, "집중 작업")
        make_tag(user, "회의")
        make_tag(user, "학습")
        record(user, used, 3)

        names = [tag.name for tag in use_case.execute(user)]

        assert names[0] == "집중 작업"
        assert set(names[1:]) == {"회의", "학습"}

    def test_another_users_records_do_not_count(self, use_case, user, make_user):
        stranger = make_user(username="stranger")
        mine = make_tag(user, "회의")
        theirs = make_tag(stranger, "집중 작업")
        record(stranger, theirs, 9)
        record(user, mine, 1)

        assert [tag.name for tag in use_case.execute(user)] == ["회의"]


class TestUsageFlag:
    def test_reports_whether_any_tag_has_been_used(self, use_case, user):
        tag = make_tag(user, "회의")

        assert use_case.has_usage(user) is False

        record(user, tag, 1)
        assert use_case.has_usage(user) is True
