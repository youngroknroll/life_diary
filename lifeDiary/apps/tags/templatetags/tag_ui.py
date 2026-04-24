from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def tag_dot(color):
    """색상 점 배지. 호출: {% tag_dot tag.color %}"""
    return format_html(
        '<span class="badge me-2" style="background-color: {};">&nbsp;</span>',
        color,
    )


@register.simple_tag
def tag_badge(color, text_color, name, clickable=False, tag_id=None):
    """
    이름 포함 전체 배지.
    - 기본: {% tag_badge tag.color tag.text_color tag.name %}
    - 클릭 가능: {% tag_badge tag.color tag.text_color tag.name clickable=True tag_id=tag.id %}
      → <button>으로 렌더링되고 클릭 시 selectTag(id, color, name) 호출.
    """
    if clickable and tag_id is not None:
        return format_html(
            '<button type="button" class="badge btn-tag-legend" '
            'data-tag-id="{}" data-tag-color="{}" data-tag-name="{}" '
            'style="background-color: {}; color: {}; border: 0;">{}</button>',
            tag_id,
            color,
            name,
            color,
            text_color,
            name,
        )
    return format_html(
        '<span class="badge" style="background-color: {}; color: {};">{}</span>',
        color,
        text_color,
        name,
    )
