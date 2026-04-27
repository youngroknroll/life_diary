"""LocalizableMessage 렌더링 템플릿 태그.

앱별 `messages.py`의 `CATALOG` (코드 → lazy 번역 문자열) 와
선택적 `ENUM_LABELS` (params 안 enum 키 → lazy 번역 라벨) 을 자동 수집하여 사용한다.
"""

import importlib
from django import template
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

register = template.Library()

_TEMPLATES_CACHE: dict = {}
_ENUM_LABELS_CACHE: dict = {}


def _load_catalogs() -> None:
    """모든 설치된 앱의 messages 모듈에서 CATALOG / ENUM_LABELS 수집."""
    if _TEMPLATES_CACHE:
        return
    for app_config in apps.get_app_configs():
        try:
            module = importlib.import_module(f"{app_config.name}.messages")
        except ModuleNotFoundError:
            continue
        catalog = getattr(module, "CATALOG", {})
        for code, lazy_text in catalog.items():
            if code in _TEMPLATES_CACHE:
                raise ImproperlyConfigured(f"Duplicate message code: {code}")
            _TEMPLATES_CACHE[code] = lazy_text
        enum_labels = getattr(module, "ENUM_LABELS", {})
        for param_name, mapping in enum_labels.items():
            existing = _ENUM_LABELS_CACHE.setdefault(param_name, {})
            existing.update(mapping)


def _resolve_template(code: str):
    _load_catalogs()
    if code not in _TEMPLATES_CACHE:
        return _("[missing message: %(code)s]") % {"code": code}
    return _TEMPLATES_CACHE[code]


def _resolve_enum_params(params: dict) -> dict:
    _load_catalogs()
    resolved = {}
    for key, value in params.items():
        labels = _ENUM_LABELS_CACHE.get(key)
        if labels and value in labels:
            resolved[key] = labels[value]
        else:
            resolved[key] = value
    return resolved


@register.simple_tag
def render_message(msg) -> str:
    """LocalizableMessage 객체 또는 dict({code, params, severity})를 번역된 문자열로 렌더링."""
    if msg is None:
        return ""
    if isinstance(msg, dict):
        code = msg.get("code", "")
        params = dict(msg.get("params") or {})
    else:
        code = getattr(msg, "code", "")
        params = dict(getattr(msg, "params", None) or {})
    template_text = _resolve_template(code)
    resolved_params = _resolve_enum_params(params)
    try:
        return str(template_text) % resolved_params
    except (KeyError, ValueError, TypeError):
        return str(template_text)


# 테스트용: 카탈로그 캐시 초기화
def _clear_caches() -> None:
    _TEMPLATES_CACHE.clear()
    _ENUM_LABELS_CACHE.clear()
