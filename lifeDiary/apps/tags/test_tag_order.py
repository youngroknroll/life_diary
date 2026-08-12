"""사용자가 정한 태그 순서.

시안 6a 는 태그를 카테고리로 묶은 행 리스트로 보여 주고 행을 옮길 수 있게
한다. 순서는 카테고리 안에서만 움직인다 — 카테고리를 넘기면 색과 과거
통계까지 소급해 바뀌므로 그것은 편집 화면의 일이다.
"""

import json

import pytest

from apps.tags.models import Category, Tag
from apps.tags.ordering import assign_display_order
from apps.tags.repositories import TagRepository
from apps.tags.use_cases import ReorderTagsUseCase


@pytest.fixture
def user(make_user):
    return make_user(username="orderuser")


@pytest.fixture
def repo():
    return TagRepository()


@pytest.fixture
def use_case():
    return ReorderTagsUseCase()


def make_tag(user, name, slug="investment", **kwargs):
    return Tag.objects.create(
        user=user, name=name, category=Category.objects.get(slug=slug), **kwargs
    )


class TestOrderedListing:
    def test_display_order_decides_order_inside_a_category(self, repo, user):
        """사용자가 정한 순서가 이름순을 이긴다."""
        make_tag(user, "가나다", display_order=2)
        make_tag(user, "마바사", display_order=0)
        make_tag(user, "라마바", display_order=1)

        names = [tag.name for tag in repo.find_accessible_ordered(user)]

        assert names == ["마바사", "라마바", "가나다"]


class TestNumbering:
    """마이그레이션의 첫 번호 매기기와 사용자의 순서 변경이 쓰는 같은 규칙."""

    def test_numbers_the_given_order_from_zero(self, user):
        tags = [make_tag(user, name) for name in ["다", "가", "나"]]

        assign_display_order(tags)

        assert [tag.display_order for tag in tags] == [0, 1, 2]

    def test_each_category_counts_from_zero_again(self, user):
        work = make_tag(user, "회의", slug="investment")
        rest = make_tag(user, "여가", slug="passive")
        work_two = make_tag(user, "학습", slug="investment")

        assign_display_order([work, rest, work_two])

        assert (work.display_order, work_two.display_order) == (0, 1)
        assert rest.display_order == 0

    def test_reports_only_the_tags_whose_number_moved(self, user):
        first = make_tag(user, "가", display_order=0)
        second = make_tag(user, "나", display_order=5)

        changed = assign_display_order([first, second])

        assert changed == [second]


class TestReorder:
    def test_saves_the_received_order(self, use_case, repo, user):
        make_tag(user, "가")
        make_tag(user, "나")
        make_tag(user, "다")
        ids = [tag.id for tag in repo.find_accessible_ordered(user)]

        use_case.execute(user, [ids[2], ids[0], ids[1]])

        names = [tag.name for tag in repo.find_accessible_ordered(user)]
        assert names == ["다", "가", "나"]

    def test_never_moves_a_tag_between_categories(self, use_case, user):
        """순서를 바꾸는 동작은 색도 통계 분류도 건드리지 않는다."""
        work = make_tag(user, "회의", slug="investment")
        rest = make_tag(user, "여가", slug="passive")

        use_case.execute(user, [rest.id, work.id])

        work.refresh_from_db()
        rest.refresh_from_db()
        assert work.category.slug == "investment"
        assert rest.category.slug == "passive"

    def test_rejects_a_list_missing_some_of_my_tags(self, use_case, user):
        kept = make_tag(user, "가")
        make_tag(user, "나")

        with pytest.raises(ValueError):
            use_case.execute(user, [kept.id])

    def test_rejects_another_users_tag(self, use_case, user, make_user):
        mine = make_tag(user, "가")
        theirs = make_tag(make_user(username="stranger"), "남의것")

        with pytest.raises(ValueError):
            use_case.execute(user, [mine.id, theirs.id])

    def test_rejects_a_repeated_id(self, use_case, user):
        first = make_tag(user, "가")
        make_tag(user, "나")

        with pytest.raises(ValueError):
            use_case.execute(user, [first.id, first.id])

    def test_leaves_the_order_untouched_when_it_refuses(self, use_case, repo, user):
        make_tag(user, "가")
        make_tag(user, "나")
        before = [tag.id for tag in repo.find_accessible_ordered(user)]

        with pytest.raises(ValueError):
            use_case.execute(user, [before[1]])

        assert [tag.id for tag in repo.find_accessible_ordered(user)] == before


ENDPOINT = "/api/tags/order/"


class TestReorderEndpoint:
    def test_saves_the_order(self, auth_client, repo):
        make_tag(auth_client.user, "가")
        make_tag(auth_client.user, "나")
        ids = [tag.id for tag in repo.find_accessible_ordered(auth_client.user)]

        resp = auth_client.patch(
            ENDPOINT,
            data=json.dumps({"tag_ids": [ids[1], ids[0]]}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert [
            tag.name for tag in repo.find_accessible_ordered(auth_client.user)
        ] == ["나", "가"]

    def test_rejects_a_tag_that_is_not_mine(self, auth_client, make_user):
        mine = make_tag(auth_client.user, "가")
        theirs = make_tag(make_user(username="stranger"), "남의것")

        resp = auth_client.patch(
            ENDPOINT,
            data=json.dumps({"tag_ids": [mine.id, theirs.id]}),
            content_type="application/json",
        )

        assert resp.status_code == 400

    def test_rejects_a_broken_body(self, auth_client):
        make_tag(auth_client.user, "가")

        resp = auth_client.patch(
            ENDPOINT, data="{", content_type="application/json"
        )

        assert resp.status_code == 400

    def test_rejects_a_non_number_id(self, auth_client):
        make_tag(auth_client.user, "가")

        resp = auth_client.patch(
            ENDPOINT,
            data=json.dumps({"tag_ids": ["앗"]}),
            content_type="application/json",
        )

        assert resp.status_code == 400

    def test_requires_login(self, client):
        resp = client.patch(
            ENDPOINT,
            data=json.dumps({"tag_ids": []}),
            content_type="application/json",
        )

        assert resp.status_code != 200

    def test_refuses_other_methods(self, auth_client):
        assert auth_client.get(ENDPOINT).status_code == 405
