import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import translation
from django.utils.translation import gettext

from apps.tags.models import Category, Tag
from apps.tags.name_limit import MAX_TAG_NAME_LENGTH
from apps.tags.seed_tags import SEED_TAGS, create_seed_tags


@pytest.fixture
def categories(db):
    """마이그레이션 0005 가 심어 둔 다섯 카테고리."""
    rows = list(Category.objects.all())
    assert {row.slug for row in rows} >= {slug for slug, _name in SEED_TAGS}
    return rows


@pytest.fixture
def user(db):
    return User.objects.create_user(username="seeded", password="pw-12345678")


class TestCreateSeedTags:
    def test_creates_one_tag_per_seed_entry(self, categories, user):
        created = create_seed_tags(user)

        assert len(created) == len(SEED_TAGS)
        assert Tag.objects.filter(user=user).count() == len(SEED_TAGS)

    def test_tags_belong_to_the_user(self, categories, user):
        create_seed_tags(user)

        assert not Tag.objects.filter(user__isnull=True).exists()
        assert all(tag.user_id == user.id for tag in Tag.objects.all())

    def test_tags_land_in_the_declared_category(self, categories, user):
        with translation.override("ko"):
            create_seed_tags(user)

        by_slug = {}
        for tag in Tag.objects.select_related("category"):
            by_slug.setdefault(tag.category.slug, set()).add(tag.name)

        for slug, name in SEED_TAGS:
            assert name in by_slug[slug]

    @pytest.mark.parametrize("language", [code for code, _label in settings.LANGUAGES])
    def test_names_fit_the_length_limit_in_every_language(self, language):
        """번역이 한계를 넘으면 이름이 잘려 나간다.

        영어 'Focused work' 가 'Focused wo' 로 잘리던 것을 이 검사가 잡았다.
        태그명 10자는 사용자 결정이므로, 번역이 그 안에 들어와야 한다.
        """
        with translation.override(language):
            for _slug, source in SEED_TAGS:
                translated = gettext(source)
                assert len(translated) <= MAX_TAG_NAME_LENGTH, (
                    f"{language}: {source!r} -> {translated!r} ({len(translated)}자)"
                )

    def test_running_twice_does_not_duplicate(self, categories, user):
        create_seed_tags(user)
        second = create_seed_tags(user)

        assert second == []
        assert Tag.objects.filter(user=user).count() == len(SEED_TAGS)

    def test_keeps_a_name_the_user_already_took(self, categories, user):
        slug, name = SEED_TAGS[0]
        mine = Tag.objects.create(
            user=user, name=name, category=Category.objects.get(slug="sleep")
        )

        create_seed_tags(user)

        mine.refresh_from_db()
        assert mine.category.slug == "sleep"
        assert Tag.objects.filter(user=user, name=name).count() == 1

    def test_two_users_get_independent_rows(self, categories, user):
        other = User.objects.create_user(username="other", password="pw-12345678")
        create_seed_tags(user)
        create_seed_tags(other)

        mine = Tag.objects.filter(user=user)
        theirs = Tag.objects.filter(user=other)
        assert mine.count() == theirs.count() == len(SEED_TAGS)
        assert not set(mine.values_list("id", flat=True)) & set(
            theirs.values_list("id", flat=True)
        )

        mine.first().delete()
        assert theirs.count() == len(SEED_TAGS)

    def test_missing_category_is_skipped_not_fatal(self, categories, user):
        """카테고리가 덜 심긴 환경에서도 가입은 막히지 않는다."""
        Category.objects.filter(slug="sleep").delete()

        created = create_seed_tags(user)

        assert created
        assert not Tag.objects.filter(user=user, category__slug="sleep").exists()


class TestSignupSeedsTags:
    def test_signup_gives_the_new_user_personal_tags(self, categories, client):
        response = client.post(
            "/accounts/signup/",
            {
                "username": "newcomer",
                "password1": "sian-pass-8891",
                "password2": "sian-pass-8891",
                "email": "newcomer@example.com",
                "consent": "on",
            },
        )

        assert response.status_code == 302
        newcomer = User.objects.get(username="newcomer")
        assert Tag.objects.filter(user=newcomer).count() == len(SEED_TAGS)
