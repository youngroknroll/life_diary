"""Phase 3 (tags) i18n 검증 테스트 — pytest 스타일."""

import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTagsEnglish:
    def test_tags_index_renders_english(self, auth_en_client):
        response = auth_en_client.get(reverse("tags:index"))
        body = response.content.decode()
        assert "New tag" in body
        assert "Loading tags..." in body
        assert "새 태그" not in body

    def test_tags_modal_labels_english(self, auth_en_client):
        response = auth_en_client.get(reverse("tags:index"))
        body = response.content.decode()
        assert "Name" in body
        assert "Category" in body
        assert "Create tag" in body
        assert "Up to 10 characters" in body

    def test_create_tag_validation_returns_english(self, auth_en_client):
        response = auth_en_client.post(
            "/api/tags/",
            json.dumps({"name": "", "color": "#abcdef", "category_id": 1}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "Please enter a tag name and color." in response.json()["message"]

    def test_create_tag_invalid_json(self, auth_en_client):
        response = auth_en_client.post(
            "/api/tags/", "not json", content_type="application/json"
        )
        assert response.status_code == 400
        assert "Malformed request." in response.json()["message"]
