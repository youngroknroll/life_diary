"""Phase 1 (base/core) i18n 검증 테스트.

영어 locale에서 base.html / index.html / utils.py 의 핵심 문자열이 영문으로 출력되는지 확인.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import activate, deactivate

from apps.core.utils import format_time_display


class HomePageEnglishTests(TestCase):
    def setUp(self):
        # LocaleMiddleware는 Accept-Language 헤더로 locale 결정
        self.client.defaults["HTTP_ACCEPT_LANGUAGE"] = "en"

    def test_home_page_renders_english_hero(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Capture your day, simply.")
        self.assertContains(response, "Pick activities, log the flow of your day, then look back.")
        self.assertNotContains(response, "하루를 단순하게 기록하세요")

    def test_home_page_renders_english_navbar(self):
        response = self.client.get(reverse("home"))
        # 네비 항목은 아이콘 뒤에 텍스트가 붙음
        self.assertContains(response, "Home")
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Stats")
        self.assertContains(response, "Tags")
        # 한국어 네비 라벨이 사라졌는지 (브랜드 'Life Diary'와 충돌 방지: '대시보드' 등 사용)
        self.assertNotContains(response, "대시보드")
        self.assertNotContains(response, "태그 관리")

    def test_javascript_catalog_url_is_loaded(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("javascript-catalog"))

    def test_javascript_catalog_endpoint_returns_translations(self):
        response = self.client.get(reverse("javascript-catalog"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode("utf-8")
        # 카탈로그가 영문 msgstr를 포함 (msgid는 \uXXXX로 인코딩됨)
        self.assertIn("Select a category", body)
        self.assertIn("Create new tag", body)
        self.assertIn("Processing...", body)


class FormatTimeDisplayTests(TestCase):
    def test_korean_default(self):
        self.assertEqual(format_time_display(2, 30), "2시간 30분")
        self.assertEqual(format_time_display(0, 0), "0분")

    def test_english(self):
        activate("en")
        try:
            assert format_time_display(2, 30) == "2h 30m"
            assert format_time_display(2, 0) == "2h"
            assert format_time_display(0, 30) == "30m"
            assert format_time_display(0, 0) == "0m"
        finally:
            deactivate()
