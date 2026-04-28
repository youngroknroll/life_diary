import json
from types import SimpleNamespace

import pytest
from django.db.models import ProtectedError
from django.template import Context, Template

from apps.tags.domain_services import TagPolicyService
from apps.tags.models import Category, Tag
from apps.tags.repositories import CategoryRepository, TagRepository


# === Domain Service Tests (No DB) ===


class TestTagPolicyService:
    def test_can_manage_default_tag_only_for_superuser(self):
        service = TagPolicyService()
        admin = SimpleNamespace(is_superuser=True)
        user = SimpleNamespace(is_superuser=False)
        default_tag = SimpleNamespace(is_default=True, user=None)
        assert service.can_manage(admin, default_tag)
        assert not service.can_manage(user, default_tag)

    def test_can_manage_user_owned_tag(self):
        service = TagPolicyService()
        owner = SimpleNamespace(is_superuser=False, username="owner")
        other = SimpleNamespace(is_superuser=False, username="other")
        tag = SimpleNamespace(is_default=False, user=owner)
        assert service.can_manage(owner, tag)
        assert not service.can_manage(other, tag)


# === Category Model Tests ===


@pytest.mark.django_db
class TestCategoryModel:
    def test_category_creation(self):
        cat = Category.objects.create(
            name="테스트카테고리",
            slug="test_cat",
            description="테스트용",
            color="#123456",
            display_order=99,
        )
        assert cat.name == "테스트카테고리"
        assert cat.slug == "test_cat"
        assert str(cat) == "테스트카테고리"

    def test_category_unique_slug(self):
        Category.objects.create(name="테스트A", slug="test_a", color="#111111", display_order=90)
        with pytest.raises(Exception):
            Category.objects.create(name="테스트B", slug="test_a", color="#222222", display_order=91)

    def test_category_unique_name(self):
        Category.objects.create(name="테스트C", slug="test_c", color="#333333", display_order=92)
        with pytest.raises(Exception):
            Category.objects.create(name="테스트C", slug="test_d", color="#444444", display_order=93)

    def test_category_ordering(self):
        Category.objects.create(name="Z카테고리", slug="z_cat", color="#555555", display_order=99)
        Category.objects.create(name="A카테고리", slug="a_cat", color="#666666", display_order=0)
        cats = list(Category.objects.values_list("slug", flat=True))
        assert cats[0] == "a_cat"
        assert cats[-1] == "z_cat"


# === Tag with Category Tests ===


@pytest.mark.django_db
class TestTagCategory:
    def test_tag_with_category(self, make_user):
        user = make_user(username="testuser")
        category = Category.objects.get(slug="investment")
        tag = Tag.objects.create(
            user=user, name="독서", color="#FF5733", category=category,
        )
        assert tag.category == category
        assert tag.category.slug == "investment"

    def test_tag_category_protect_on_delete(self, make_user):
        user = make_user(username="testuser")
        category = Category.objects.get(slug="investment")
        Tag.objects.create(user=user, name="독서", color="#FF5733", category=category)
        with pytest.raises(ProtectedError):
            category.delete()

    def test_category_reverse_relation(self, make_user):
        user = make_user(username="testuser")
        category = Category.objects.get(slug="investment")
        Tag.objects.create(user=user, name="독서", color="#FF5733", category=category)
        Tag.objects.create(user=user, name="공부", color="#33FF57", category=category)
        assert category.tags.count() == 2


# === CategoryRepository Tests ===


@pytest.mark.django_db
class TestCategoryRepository:
    def test_find_all(self):
        repo = CategoryRepository()
        cats = repo.find_all()
        assert cats.count() == 5
        assert cats[0].slug == "passive"

    def test_find_by_slug(self):
        repo = CategoryRepository()
        cat = repo.find_by_slug("investment")
        assert cat.name == "투자시간"

    def test_find_by_slug_not_found(self):
        repo = CategoryRepository()
        cat = repo.find_by_slug("nonexistent")
        assert cat is None


# === TagRepository with Category Tests ===


@pytest.mark.django_db
class TestTagRepositoryCategory:
    def test_create_with_category(self, make_user):
        repo = TagRepository()
        user = make_user(username="testuser")
        cat_invest = Category.objects.get(slug="investment")
        tag = repo.create(
            user=user, name="독서", color="#FF5733",
            is_default=False, category=cat_invest,
        )
        assert tag.category == cat_invest

    def test_find_accessible_includes_category(self, make_user):
        repo = TagRepository()
        user = make_user(username="testuser")
        cat_invest = Category.objects.get(slug="investment")
        repo.create(
            user=user, name="독서", color="#FF5733",
            is_default=False, category=cat_invest,
        )
        tags = repo.find_accessible(user)
        assert tags.first().category.slug == "investment"

    def test_find_by_category(self, make_user):
        repo = TagRepository()
        user = make_user(username="testuser")
        cat_invest = Category.objects.get(slug="investment")
        cat_passive = Category.objects.get(slug="passive")
        repo.create(user=user, name="독서", color="#FF5733", is_default=False, category=cat_invest)
        repo.create(user=user, name="SNS", color="#33FF57", is_default=False, category=cat_passive)
        tags = repo.find_by_category(user, cat_invest)
        assert tags.count() == 1
        assert tags.first().name == "독서"

    def test_find_accessible_ordered_groups_by_category_display_order(self, make_user):
        repo = TagRepository()
        user = make_user(username="testuser")
        cat_invest = Category.objects.get(slug="investment")
        cat_passive = Category.objects.get(slug="passive")
        cat_basic = Category.objects.get(slug="basic_life")
        repo.create(user=user, name="aaa-basic", color="#111111", is_default=False, category=cat_basic)
        repo.create(user=user, name="zzz-passive", color="#222222", is_default=False, category=cat_passive)
        repo.create(user=user, name="mmm-invest", color="#333333", is_default=False, category=cat_invest)

        tags = list(repo.find_accessible_ordered(user))
        user_tag_order = [t.name for t in tags if t.user_id == user.id]
        assert user_tag_order == ["zzz-passive", "mmm-invest", "aaa-basic"]


# === Template Tag Tests ===


def _render(template_str, context=None):
    return Template(template_str).render(Context(context or {}))


class TestTagBadgeTemplateTag:
    def test_tag_badge_default_non_clickable(self):
        html = _render("{% load tag_ui %}{% tag_badge '#FF0000' '#FFFFFF' '운동' %}")
        assert "<span" in html
        assert "운동" in html
        assert "onclick" not in html
        assert "<button" not in html

    def test_tag_badge_clickable_produces_button_with_data_attrs(self):
        html = _render(
            "{% load tag_ui %}"
            "{% tag_badge '#FF0000' '#FFFFFF' '운동' clickable=True tag_id=42 %}"
        )
        assert "<button" in html
        assert 'data-tag-id="42"' in html
        assert 'data-tag-color="#FF0000"' in html
        assert 'data-tag-name="운동"' in html
        assert "운동" in html
        assert "badge" in html
        assert "onclick" not in html

    def test_tag_badge_clickable_escapes_hostile_name(self):
        html = _render(
            "{% load tag_ui %}"
            "{% tag_badge '#FF0000' '#FFFFFF' name clickable=True tag_id=1 %}",
            {"name": "</button><script>alert(1)</script>"},
        )
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html


# === Seed Data Migration Tests ===


@pytest.mark.django_db
class TestSeedCategory:
    def test_five_categories_seeded(self):
        assert Category.objects.count() == 5

    def test_category_slugs(self):
        expected = {"passive", "proactive", "investment", "basic_life", "sleep"}
        actual = set(Category.objects.values_list("slug", flat=True))
        assert actual == expected

    def test_display_order(self):
        cats = list(Category.objects.values_list("slug", flat=True))
        assert cats == ["passive", "proactive", "investment", "basic_life", "sleep"]


# === API Tests ===


@pytest.mark.django_db
class TestCategoryAPI:
    def test_get_categories(self, auth_client):
        resp = auth_client.get("/api/categories/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"]
        assert len(data["categories"]) == 5
        first = data["categories"][0]
        assert "id" in first
        assert "name" in first
        assert "slug" in first
        assert "color" in first
        assert "description" in first

    def test_get_categories_requires_login(self, client):
        resp = client.get("/api/categories/")
        assert resp.status_code != 200


@pytest.mark.django_db
class TestTagCreateWithCategoryAPI:
    def test_create_tag_with_category(self, auth_client):
        category = Category.objects.get(slug="investment")
        resp = auth_client.post(
            "/api/tags/",
            data=json.dumps({
                "name": "독서",
                "color": "#FF5733",
                "category_id": category.id,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"]
        assert data["tag"]["category_id"] == category.id

    def test_create_tag_without_category_fails(self, auth_client):
        resp = auth_client.post(
            "/api/tags/",
            data=json.dumps({"name": "독서", "color": "#FF5733"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_create_tag_invalid_category_fails(self, auth_client):
        resp = auth_client.post(
            "/api/tags/",
            data=json.dumps({
                "name": "독서",
                "color": "#FF5733",
                "category_id": 9999,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_tag_list_includes_category(self, auth_client):
        category = Category.objects.get(slug="investment")
        Tag.objects.create(
            user=auth_client.user, name="독서", color="#FF5733", category=category,
        )
        resp = auth_client.get("/api/tags/")
        data = resp.json()
        tag = data["tags"][0]
        assert "category_id" in tag
        assert tag["category_id"] == category.id
