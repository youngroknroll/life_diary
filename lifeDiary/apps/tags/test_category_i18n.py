import pytest
from django.urls import reverse
from django.utils import translation

from apps.tags.models import Category


@pytest.mark.django_db
class TestCategoryI18n:
    @pytest.fixture(autouse=True)
    def _seed(self):
        Category.objects.update_or_create(
            slug="passive",
            defaults={
                "name": "수동적 소비시간",
                "description": "비계획적 소비",
                "color": "#888888",
                "display_order": 1,
            },
        )

    def test_display_name_korean(self):
        cat = Category.objects.get(slug="passive")
        with translation.override("ko"):
            assert cat.display_name == "수동적 소비시간"

    def test_display_name_english(self):
        cat = Category.objects.get(slug="passive")
        with translation.override("en"):
            assert cat.display_name == "Passive consumption"

    def test_category_list_api_returns_translated_name(self, auth_client):
        response = auth_client.get(reverse("tags_api:category_list"))
        assert response.status_code == 200
        # Korean default
        names = [c["name"] for c in response.json()["categories"]]
        assert "수동적 소비시간" in names

    def test_category_list_api_returns_english_when_en(self, auth_en_client):
        response = auth_en_client.get(reverse("tags_api:category_list"))
        assert response.status_code == 200
        names = [c["name"] for c in response.json()["categories"]]
        assert "Passive consumption" in names
