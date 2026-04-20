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
def tag_badge(color, text_color, name):
    """이름 포함 전체 배지. 호출: {% tag_badge tag.color tag.text_color tag.name %}"""
    return format_html(
        '<span class="badge" style="background-color: {}; color: {};">{}</span>',
        color,
        text_color,
        name,
    )
