from html.parser import HTMLParser
import re

import pytest
from django.conf import settings

from apps.dashboard.services import build_time_headers, validate_slot_indexes
from apps.tags.models import Category, Tag


class TestDashboardServices:
    def test_build_time_headers(self):
        assert build_time_headers() == ["10분", "20분", "30분", "40분", "50분", "60분"] * 2

    def test_validate_slot_indexes_accepts_valid_list(self):
        assert validate_slot_indexes([0, 1, 143])

    def test_validate_slot_indexes_rejects_invalid_values(self):
        assert not validate_slot_indexes([0, -1, 144])


def _extract_element(html, element_id):
    """주어진 id의 element 내부 HTML만 반환."""

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


@pytest.fixture
def dash_user_with_tags(ko_client, make_user):
    user = make_user(username="dashuser")
    ko_client.force_login(user)
    cat_passive = Category.objects.get(slug="passive")
    cat_invest = Category.objects.get(slug="investment")
    Tag.objects.create(
        user=user, name="투자태그", color="#111111",
        is_default=False, category=cat_invest,
    )
    Tag.objects.create(
        user=user, name="수동태그", color="#222222",
        is_default=False, category=cat_passive,
    )
    return ko_client, user


@pytest.mark.django_db
class TestDashboardIndexRendering:
    def test_dashboard_renders_category_headers(self, dash_user_with_tags):
        client, _ = dash_user_with_tags
        resp = client.get("/dashboard/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "수동적 소비시간" in content
        assert "투자시간" in content

    def test_dashboard_renders_tags_under_correct_category(self, dash_user_with_tags):
        client, _ = dash_user_with_tags
        resp = client.get("/dashboard/")
        content = resp.content.decode()
        start = content.index('id="tagContainer"')
        section = content[start:start + 5000]

        idx_passive_header = section.index("수동적 소비시간")
        idx_passive_tag = section.index("수동태그")
        idx_invest_header = section.index("투자시간")
        idx_invest_tag = section.index("투자태그")

        assert idx_passive_header < idx_passive_tag
        assert idx_passive_tag < idx_invest_header
        assert idx_invest_header < idx_invest_tag

    def test_sidebar_category_headers_use_separator_not_color_dot(self, dash_user_with_tags):
        client, _ = dash_user_with_tags
        resp = client.get("/dashboard/")
        section = _extract_element(resp.content.decode(), "tagContainer")
        passive_header_start = section.index("tag-category-header")
        passive_tag_start = section.index("수동태그")
        passive_header = section[passive_header_start:passive_tag_start]
        normalized_header = re.sub(r"\s+", " ", passive_header)

        assert "- 수동적 소비시간" in normalized_header
        assert "background-color: #222222" not in passive_header
        assert "background-color: #222222" in section[passive_tag_start:]

    def test_sidebar_tag_list_uses_compact_wrapping_row_layout(self, dash_user_with_tags):
        client, _ = dash_user_with_tags
        resp = client.get("/dashboard/")
        section = _extract_element(resp.content.decode(), "tagContainer")
        css_path = settings.BASE_DIR / "apps/core/static/core/css/style.css"
        css_source = css_path.read_text()
        css_block = re.search(
            r"\.quick-input-tag-list \{(?P<body>.*?)\}",
            css_source,
            re.DOTALL,
        ).group("body")

        assert "quick-input-tag-list" in section
        assert '<div class="d-grid gap-1">' not in section
        assert "flex-wrap: wrap;" in css_block
        assert "flex-direction: column;" not in css_block

    def test_dashboard_legend_badges_are_clickable(self, dash_user_with_tags):
        client, _ = dash_user_with_tags
        resp = client.get("/dashboard/")
        section = _extract_element(resp.content.decode(), "tagLegend")
        assert "<button" in section
        assert "data-tag-id=" in section
        assert "data-tag-color=" in section
        assert "data-tag-name=" in section

    def test_sidebar_tag_buttons_use_data_attrs_no_inline_onclick(self, dash_user_with_tags):
        client, _ = dash_user_with_tags
        resp = client.get("/dashboard/")
        section = _extract_element(resp.content.decode(), "tagContainer")
        assert "data-tag-color=" in section
        assert "data-tag-name=" in section
        assert "onclick=" not in section

    def test_sidebar_tag_button_escapes_hostile_name(self, dash_user_with_tags):
        client, user = dash_user_with_tags
        cat = Category.objects.get(slug="proactive")
        Tag.objects.create(
            user=user,
            name="x');alert(1);//",
            color="#AABBCC",
            is_default=False,
            category=cat,
        )
        resp = client.get("/dashboard/")
        section = _extract_element(resp.content.decode(), "tagContainer")
        assert "onclick" not in section
        assert "<script" not in section

    def test_dashboard_renders_mobile_bottom_sheet_structure(self, dash_user_with_tags):
        client, _ = dash_user_with_tags
        resp = client.get("/dashboard/")
        content = resp.content.decode()

        assert 'id="quickInputSheetBackdrop"' in content
        assert 'id="quickInputSheet"' in content
        assert 'aria-labelledby="quickInputSheetTitle"' in content
        assert 'id="quickInputSheetTitle"' in content
        assert "data-dashboard-sheet-close" in content


class TestDashboardJavaScriptAssets:
    def test_touchmove_prevent_default_is_guarded_by_cancelable(self):
        js_path = settings.BASE_DIR / "apps/dashboard/static/dashboard/js/dashboard.js"
        source = js_path.read_text()

        assert "if (event.cancelable) {" in source
        assert "event.preventDefault();" in source

    def test_mobile_touch_drag_does_not_cancel_vertical_time_slot_gesture(self):
        js_path = settings.BASE_DIR / "apps/dashboard/static/dashboard/js/dashboard.js"
        source = js_path.read_text()

        assert "dy > dx" not in source
        assert source.index("event.preventDefault();") < source.index("document.elementFromPoint")

    def test_mobile_sheet_close_moves_focus_before_hiding_dialog(self):
        js_path = settings.BASE_DIR / "apps/dashboard/static/dashboard/js/dashboard.js"
        source = js_path.read_text()
        close_body = source[
            source.index("function closeQuickInputSheet()"):
            source.index("// ── 슬롯 선택 ──")
        ]

        assert close_body.index("focus({ preventScroll: true })") < close_body.index(
            "sheet.setAttribute('aria-hidden', 'true')"
        )

    def test_mobile_sheet_height_is_anchored_to_one_am_slot(self):
        js_path = settings.BASE_DIR / "apps/dashboard/static/dashboard/js/dashboard.js"
        source = js_path.read_text()

        assert '[data-slot-index="6"]' in source
        assert "--quick-input-sheet-max-height" in source

    def test_mobile_sheet_css_uses_dynamic_height_cap(self):
        css_path = settings.BASE_DIR / "apps/core/static/core/css/style.css"
        source = css_path.read_text()

        assert "var(--quick-input-sheet-max-height, min(82vh, 680px))" in source

    def test_time_grid_prevents_text_selection(self):
        css_path = settings.BASE_DIR / "apps/core/static/core/css/style.css"
        source = css_path.read_text()

        assert ".navbar-utility-controls" in source
        assert "user-select: none;" in source
        assert "-webkit-user-select: none;" in source
