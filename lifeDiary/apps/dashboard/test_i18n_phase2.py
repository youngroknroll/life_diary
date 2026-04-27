"""Phase 2 (dashboard) i18n 검증 테스트."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardEnglishTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="dash-en-user", password="testpass-Long-9!"
        )

    def setUp(self):
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"
        self.client.force_login(self.user)

    def test_dashboard_renders_english_stats_labels(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertContains(response, "Total slots")
        self.assertContains(response, "Logged slots")
        self.assertContains(response, "Logged rate")
        self.assertContains(response, "Total time logged")
        self.assertNotContains(response, "총 슬롯")

    def test_dashboard_renders_english_sidebar(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertContains(response, "Entry")
        self.assertContains(response, "Select a tag")
        self.assertContains(response, "New tag")
        self.assertContains(response, "Memo (optional)")
        self.assertContains(response, "Save")

    def test_dashboard_title_uses_blocktrans(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertContains(response, "Dashboard -")
        self.assertContains(response, "| Life Diary")

    def test_dashboard_post_invalid_json_returns_english(self):
        response = self.client.post(
            "/api/time-blocks/", "not json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON format.", response.json()["message"])
