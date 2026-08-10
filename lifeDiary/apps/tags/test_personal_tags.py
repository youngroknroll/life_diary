"""모든 태그는 누군가의 것이다.

공유 기본 태그를 폐지한 뒤의 계약을 고정한다. 스키마가 바뀐 다음에는 공유
태그를 만들 수 없으므로, 데이터 이관 자체가 아니라 이관이 끝난 뒤 성립해야
하는 성질을 검사한다.
"""

import pytest
from django.db import IntegrityError

from apps.tags.models import Category, Tag
from apps.tags.repositories import TagRepository


@pytest.fixture
def repo():
    return TagRepository()


@pytest.fixture
def owner(make_user):
    return make_user(username="owner")


@pytest.fixture
def stranger(make_user):
    return make_user(username="stranger")


def make_tag(user, name):
    return Tag.objects.create(
        user=user, name=name, category=Category.objects.get(slug="investment")
    )


class TestTagAlwaysHasAnOwner:
    def test_creating_an_ownerless_tag_fails(self, db):
        with pytest.raises(IntegrityError):
            Tag.objects.create(
                user=None, name="공용", category=Category.objects.get(slug="sleep")
            )

    def test_model_has_no_shared_flag(self, db):
        assert not hasattr(Tag, "is_default")

    def test_str_names_the_owner(self, owner):
        assert str(make_tag(owner, "회의")) == "owner - 회의"


class TestAccessIsOwnershipOnly:
    def test_only_own_tags_are_accessible(self, repo, owner, stranger):
        mine = make_tag(owner, "회의")
        make_tag(stranger, "학습")

        assert list(repo.find_accessible(owner)) == [mine]

    def test_another_users_tag_is_not_reachable_by_id(self, repo, owner, stranger):
        theirs = make_tag(stranger, "학습")

        assert repo.find_by_id_accessible(theirs.id, owner) is None

    def test_duplicate_check_ignores_other_users(self, repo, owner, stranger):
        make_tag(stranger, "학습")

        assert not repo.exists_duplicate(owner, "학습")

    def test_same_name_is_allowed_across_users(self, owner, stranger):
        make_tag(owner, "회의")
        make_tag(stranger, "회의")

        assert Tag.objects.filter(name="회의").count() == 2

    def test_same_name_is_rejected_for_one_user(self, owner):
        make_tag(owner, "회의")

        with pytest.raises(IntegrityError):
            make_tag(owner, "회의")


class TestSuperuserHasNoTagPrivilege:
    def test_superuser_cannot_reach_another_users_tag(self, repo, make_user, stranger):
        admin = make_user(username="admin", is_superuser=True, is_staff=True)
        theirs = make_tag(stranger, "학습")

        from django.http import Http404

        with pytest.raises(Http404):
            repo.get_for_owner_or_404(theirs.id, admin)
