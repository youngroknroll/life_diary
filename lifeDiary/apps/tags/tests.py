import json
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase, Client
from django.contrib.auth.models import User

from apps.tags.domain_services import TagPolicyService
from apps.tags.models import Category, Tag
from apps.tags.repositories import CategoryRepository, TagRepository


# === Domain Service Tests (No DB) ===


class TagPolicyServiceTests(SimpleTestCase):
    def test_can_manage_default_tag_only_for_superuser(self):
        service = TagPolicyService()
        admin = SimpleNamespace(is_superuser=True)
        user = SimpleNamespace(is_superuser=False)
        default_tag = SimpleNamespace(is_default=True, user=None)

        self.assertTrue(service.can_manage(admin, default_tag))
        self.assertFalse(service.can_manage(user, default_tag))

    def test_can_manage_user_owned_tag(self):
        service = TagPolicyService()
        owner = SimpleNamespace(is_superuser=False, username="owner")
        other = SimpleNamespace(is_superuser=False, username="other")
        tag = SimpleNamespace(is_default=False, user=owner)

        self.assertTrue(service.can_manage(owner, tag))
        self.assertFalse(service.can_manage(other, tag))


# === Category Model Tests ===


class CategoryModelTests(TestCase):
    """시드 데이터가 마이그레이션으로 이미 존재하므로, 별도 slug로 테스트"""

    def test_category_creation(self):
        cat = Category.objects.create(
            name="테스트카테고리",
            slug="test_cat",
            description="테스트용",
            color="#123456",
            display_order=99,
        )
        self.assertEqual(cat.name, "테스트카테고리")
        self.assertEqual(cat.slug, "test_cat")
        self.assertEqual(str(cat), "테스트카테고리")

    def test_category_unique_slug(self):
        Category.objects.create(name="테스트A", slug="test_a", color="#111111", display_order=90)
        with self.assertRaises(Exception):
            Category.objects.create(name="테스트B", slug="test_a", color="#222222", display_order=91)

    def test_category_unique_name(self):
        Category.objects.create(name="테스트C", slug="test_c", color="#333333", display_order=92)
        with self.assertRaises(Exception):
            Category.objects.create(name="테스트C", slug="test_d", color="#444444", display_order=93)

    def test_category_ordering(self):
        """시드 5개 + 새로 추가한 것이 display_order 순으로 정렬"""
        Category.objects.create(name="Z카테고리", slug="z_cat", color="#555555", display_order=99)
        Category.objects.create(name="A카테고리", slug="a_cat", color="#666666", display_order=0)
        cats = list(Category.objects.values_list("slug", flat=True))
        # display_order: 0(a_cat), 1(passive), 2(proactive), 3(investment), 4(basic_life), 5(sleep), 99(z_cat)
        self.assertEqual(cats[0], "a_cat")
        self.assertEqual(cats[-1], "z_cat")


# === Tag with Category Tests ===


class TagCategoryTests(TestCase):
    def setUp(self):
        self.category = Category.objects.get(slug="investment")
        self.user = User.objects.create_user("testuser", password="test1234")

    def test_tag_with_category(self):
        tag = Tag.objects.create(
            user=self.user,
            name="독서",
            color="#FF5733",
            category=self.category,
        )
        self.assertEqual(tag.category, self.category)
        self.assertEqual(tag.category.slug, "investment")

    def test_tag_category_protect_on_delete(self):
        """카테고리에 태그가 있으면 삭제 불가 (PROTECT)"""
        Tag.objects.create(
            user=self.user,
            name="독서",
            color="#FF5733",
            category=self.category,
        )
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_category_reverse_relation(self):
        Tag.objects.create(user=self.user, name="독서", color="#FF5733", category=self.category)
        Tag.objects.create(user=self.user, name="공부", color="#33FF57", category=self.category)
        self.assertEqual(self.category.tags.count(), 2)


# === CategoryRepository Tests ===


class CategoryRepositoryTests(TestCase):
    def setUp(self):
        self.repo = CategoryRepository()

    def test_find_all(self):
        cats = self.repo.find_all()
        self.assertEqual(cats.count(), 5)
        self.assertEqual(cats[0].slug, "passive")

    def test_find_by_slug(self):
        cat = self.repo.find_by_slug("investment")
        self.assertEqual(cat.name, "투자시간")

    def test_find_by_slug_not_found(self):
        cat = self.repo.find_by_slug("nonexistent")
        self.assertIsNone(cat)


# === TagRepository with Category Tests ===


class TagRepositoryCategoryTests(TestCase):
    def setUp(self):
        self.repo = TagRepository()
        self.cat_invest = Category.objects.get(slug="investment")
        self.cat_passive = Category.objects.get(slug="passive")
        self.user = User.objects.create_user("testuser", password="test1234")

    def test_create_with_category(self):
        tag = self.repo.create(
            user=self.user,
            name="독서",
            color="#FF5733",
            is_default=False,
            category=self.cat_invest,
        )
        self.assertEqual(tag.category, self.cat_invest)

    def test_find_accessible_includes_category(self):
        self.repo.create(
            user=self.user,
            name="독서",
            color="#FF5733",
            is_default=False,
            category=self.cat_invest,
        )
        tags = self.repo.find_accessible(self.user)
        self.assertEqual(tags.first().category.slug, "investment")

    def test_find_by_category(self):
        self.repo.create(
            user=self.user, name="독서", color="#FF5733", is_default=False, category=self.cat_invest
        )
        self.repo.create(
            user=self.user, name="SNS", color="#33FF57", is_default=False, category=self.cat_passive
        )
        tags = self.repo.find_by_category(self.user, self.cat_invest)
        self.assertEqual(tags.count(), 1)
        self.assertEqual(tags.first().name, "독서")


# === Seed Data Migration Tests ===


class SeedCategoryTests(TestCase):
    """마이그레이션으로 시드된 카테고리 검증"""

    def test_five_categories_seeded(self):
        """5개 카테고리가 시드되어 있어야 한다 (테스트 DB는 마이그레이션 적용됨)"""
        self.assertEqual(Category.objects.count(), 5)

    def test_category_slugs(self):
        expected = {"passive", "proactive", "investment", "basic_life", "sleep"}
        actual = set(Category.objects.values_list("slug", flat=True))
        self.assertEqual(actual, expected)

    def test_display_order(self):
        cats = list(Category.objects.values_list("slug", flat=True))
        self.assertEqual(cats, ["passive", "proactive", "investment", "basic_life", "sleep"])


# === API Tests ===


class CategoryAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("testuser", password="test1234")
        self.client.login(username="testuser", password="test1234")

    def test_get_categories(self):
        resp = self.client.get("/api/categories/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["categories"]), 5)
        first = data["categories"][0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("slug", first)
        self.assertIn("color", first)
        self.assertIn("description", first)

    def test_get_categories_requires_login(self):
        self.client.logout()
        resp = self.client.get("/api/categories/")
        self.assertNotEqual(resp.status_code, 200)


class TagCreateWithCategoryAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("testuser", password="test1234")
        self.client.login(username="testuser", password="test1234")
        self.category = Category.objects.get(slug="investment")

    def test_create_tag_with_category(self):
        resp = self.client.post(
            "/api/tags/",
            data=json.dumps({
                "name": "독서",
                "color": "#FF5733",
                "category_id": self.category.id,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["tag"]["category_id"], self.category.id)

    def test_create_tag_without_category_fails(self):
        resp = self.client.post(
            "/api/tags/",
            data=json.dumps({"name": "독서", "color": "#FF5733"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_create_tag_invalid_category_fails(self):
        resp = self.client.post(
            "/api/tags/",
            data=json.dumps({
                "name": "독서",
                "color": "#FF5733",
                "category_id": 9999,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_tag_list_includes_category(self):
        Tag.objects.create(
            user=self.user, name="독서", color="#FF5733", category=self.category
        )
        resp = self.client.get("/api/tags/")
        data = resp.json()
        tag = data["tags"][0]
        self.assertIn("category_id", tag)
        self.assertEqual(tag["category_id"], self.category.id)
