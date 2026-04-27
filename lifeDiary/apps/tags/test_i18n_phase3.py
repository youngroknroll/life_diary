"""Phase 3 (tags) i18n 검증 테스트."""

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class TagsEnglishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="tag-en-user", password="testpass-Long-9!"
        )

    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.client.force_login(self.user)

    def test_tags_index_renders_english(self):
        response = self.client.get(reverse("tags:index"))
        self.assertContains(response, "Create new tag")
        self.assertContains(response, "Loading tags...")
        self.assertContains(response, "No tags yet.")
        self.assertNotContains(response, "새 태그 생성")

    def test_tags_modal_labels_english(self):
        response = self.client.get(reverse("tags:index"))
        self.assertContains(response, "Tag name")
        self.assertContains(response, "Color")
        self.assertContains(response, "Category")

    def test_create_tag_validation_returns_english(self):
        response = self.client.post(
            "/api/tags/",
            json.dumps({"name": "", "color": "#abcdef", "category_id": 1}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Please enter a tag name and color.", response.json()["message"])

    def test_create_tag_invalid_json(self):
        response = self.client.post(
            "/api/tags/", "not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Malformed request.", response.json()["message"])
