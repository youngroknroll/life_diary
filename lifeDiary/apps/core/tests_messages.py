"""LocalizableMessage 타입 + render_message 태그 단위 테스트."""

from unittest.mock import patch

import pytest
from django.template import Context, Template
from django.utils.translation import gettext_lazy as _

from apps.core.messages import LocalizableMessage
from apps.core.templatetags import i18n_messages


@pytest.fixture(autouse=True)
def _reset_catalog_cache():
    i18n_messages._clear_caches()
    yield
    i18n_messages._clear_caches()


class TestLocalizableMessage:
    def test_default_severity_is_info(self):
        msg = LocalizableMessage(code="x.y")
        assert msg.severity == "info"
        assert msg.params == {}

    def test_to_dict_round_trips(self):
        msg = LocalizableMessage(
            code="stats.feedback.goal_achieved",
            params={"name": "운동", "hours": 5},
            severity="positive",
        )
        assert msg.to_dict() == {
            "code": "stats.feedback.goal_achieved",
            "params": {"name": "운동", "hours": 5},
            "severity": "positive",
        }

    def test_is_immutable(self):
        msg = LocalizableMessage(code="x.y")
        with pytest.raises(Exception):
            msg.code = "z"  # frozen=True


class TestRenderMessage:
    def _patch_catalog(self, catalog: dict, enum_labels: dict | None = None):
        i18n_messages._TEMPLATES_CACHE.update(catalog)
        if enum_labels:
            for k, v in enum_labels.items():
                i18n_messages._ENUM_LABELS_CACHE.setdefault(k, {}).update(v)

    def _render(self, msg):
        # 캐시 로드 우회: _load_catalogs를 no-op로 패치
        with patch.object(i18n_messages, "_load_catalogs", lambda: None):
            return i18n_messages.render_message(msg)

    def test_renders_object(self):
        self._patch_catalog({"x.greeting": _("안녕 %(name)s")})
        msg = LocalizableMessage(code="x.greeting", params={"name": "Alice"})
        assert self._render(msg) == "안녕 Alice"

    def test_renders_dict(self):
        self._patch_catalog({"x.greeting": _("안녕 %(name)s")})
        assert self._render({"code": "x.greeting", "params": {"name": "Bob"}}) == "안녕 Bob"

    def test_resolves_enum_param(self):
        self._patch_catalog(
            {"x.period_msg": _("%(period)s 요약입니다")},
            enum_labels={"period": {"daily": _("오늘"), "weekly": _("이번주")}},
        )
        msg = LocalizableMessage(code="x.period_msg", params={"period": "daily"})
        assert self._render(msg) == "오늘 요약입니다"

    def test_missing_code_returns_placeholder(self):
        result = self._render(LocalizableMessage(code="nonexistent.code"))
        assert "missing message" in result
        assert "nonexistent.code" in result

    def test_none_input_returns_empty(self):
        assert self._render(None) == ""

    def test_template_tag_loads_in_template(self):
        self._patch_catalog({"x.hi": _("Hi %(name)s")})
        with patch.object(i18n_messages, "_load_catalogs", lambda: None):
            template = Template("{% load i18n_messages %}{% render_message msg %}")
            output = template.render(Context({"msg": {"code": "x.hi", "params": {"name": "Tom"}}}))
        assert output == "Hi Tom"

    def test_handles_missing_param_gracefully(self):
        """params에 없는 키를 템플릿이 요구하면 raw 템플릿 반환."""
        self._patch_catalog({"x.needs_name": _("Hi %(name)s")})
        msg = LocalizableMessage(code="x.needs_name", params={})
        result = self._render(msg)
        # KeyError 발생 시 raw template 반환 (안전 폴백)
        assert "Hi" in result
