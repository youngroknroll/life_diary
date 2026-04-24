from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase, TestCase

from apps.dashboard.services import build_time_headers, validate_slot_indexes
from apps.tags.models import Category, Tag


class DashboardServicesTests(SimpleTestCase):
    def test_build_time_headers(self):
        self.assertEqual(
            build_time_headers(),
            ["10분", "20분", "30분", "40분", "50분", "60분"] * 2,
        )

    def test_validate_slot_indexes_accepts_valid_list(self):
        self.assertTrue(validate_slot_indexes([0, 1, 143]))

    def test_validate_slot_indexes_rejects_invalid_values(self):
        self.assertFalse(validate_slot_indexes([0, -1, 144]))


class DashboardIndexRenderingTests(TestCase):
    """대시보드 index.html이 태그를 카테고리 그룹으로 렌더링하는지 검증."""

    def setUp(self):
        self.user = User.objects.create_user("dashuser", password="test1234")
        self.client = Client()
        self.client.login(username="dashuser", password="test1234")

        cat_passive = Category.objects.get(slug="passive")
        cat_invest = Category.objects.get(slug="investment")
        # 의도적으로 카테고리 순서와 역순으로 생성
        Tag.objects.create(
            user=self.user, name="투자태그", color="#111111",
            is_default=False, category=cat_invest,
        )
        Tag.objects.create(
            user=self.user, name="수동태그", color="#222222",
            is_default=False, category=cat_passive,
        )

    def test_dashboard_renders_category_headers(self):
        resp = self.client.get("/dashboard/")
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        # 사용자가 태그를 가진 카테고리 헤더가 노출
        self.assertIn("수동적 소비시간", content)
        self.assertIn("투자시간", content)

    def test_dashboard_renders_tags_under_correct_category(self):
        """카테고리 헤더가 해당 카테고리 태그보다 앞서 나타나야 한다."""
        resp = self.client.get("/dashboard/")
        content = resp.content.decode()
        # tagContainer 영역만 추출
        start = content.index('id="tagContainer"')
        section = content[start:start + 5000]

        idx_passive_header = section.index("수동적 소비시간")
        idx_passive_tag = section.index("수동태그")
        idx_invest_header = section.index("투자시간")
        idx_invest_tag = section.index("투자태그")

        # passive 헤더 → passive 태그 → invest 헤더 → invest 태그
        self.assertLess(idx_passive_header, idx_passive_tag)
        self.assertLess(idx_passive_tag, idx_invest_header)
        self.assertLess(idx_invest_header, idx_invest_tag)

    def _extract_element(self, html, element_id):
        """주어진 id의 element 내부 HTML만 반환."""
        from html.parser import HTMLParser

        class _Extractor(HTMLParser):
            def __init__(self, target_id):
                super().__init__()
                self.target_id = target_id
                self.depth = 0
                self.captured = []
                self.capturing = False

            def handle_starttag(self, tag, attrs):
                attr_dict = dict(attrs)
                if not self.capturing and attr_dict.get("id") == self.target_id:
                    self.capturing = True
                    self.depth = 1
                    return
                if self.capturing:
                    self.depth += 1
                    self.captured.append(self.get_starttag_text() or "")

            def handle_endtag(self, tag):
                if self.capturing:
                    self.depth -= 1
                    if self.depth == 0:
                        self.capturing = False
                        return
                    self.captured.append(f"</{tag}>")

            def handle_data(self, data):
                if self.capturing:
                    self.captured.append(data)

            def handle_startendtag(self, tag, attrs):
                if self.capturing:
                    self.captured.append(self.get_starttag_text() or "")

        p = _Extractor(element_id)
        p.feed(html)
        return "".join(p.captured)

    def test_dashboard_legend_badges_are_clickable(self):
        """하단 범례 배지는 data-tag-id가 포함된 button이어야 한다."""
        resp = self.client.get("/dashboard/")
        section = self._extract_element(resp.content.decode(), "tagLegend")
        self.assertIn("<button", section)
        self.assertIn("data-tag-id=", section)
        self.assertIn("data-tag-color=", section)
        self.assertIn("data-tag-name=", section)

    def test_sidebar_tag_buttons_use_data_attrs_no_inline_onclick(self):
        """사이드바 태그 버튼은 inline onclick 대신 data-tag-* 속성 사용 (XSS 방어)."""
        resp = self.client.get("/dashboard/")
        section = self._extract_element(resp.content.decode(), "tagContainer")
        self.assertIn("data-tag-color=", section)
        self.assertIn("data-tag-name=", section)
        self.assertNotIn("onclick=", section)

    def test_sidebar_tag_button_escapes_hostile_name(self):
        """악성 태그 이름이 JS 실행 컨텍스트 (onclick/script)에 들어가지 않아야 한다."""
        cat = Category.objects.get(slug="proactive")
        Tag.objects.create(
            user=self.user,
            name="x');alert(1);//",
            color="#AABBCC",
            is_default=False,
            category=cat,
        )
        resp = self.client.get("/dashboard/")
        section = self._extract_element(resp.content.decode(), "tagContainer")
        # data-attr 값 안에 '(escape된 형태로) 포함되는 것은 안전하지만,
        # JS 실행 컨텍스트(onclick, script)에 들어가서는 안 된다.
        self.assertNotIn("onclick", section)
        self.assertNotIn("<script", section)
