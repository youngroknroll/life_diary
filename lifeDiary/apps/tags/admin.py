from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "color_display", "display_order"]
    ordering = ["display_order"]

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 3px; color: white; font-weight: bold;">{}</span>',
            obj.color,
            obj.color,
        )

    color_display.short_description = "색상"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "user", "is_default", "color_display", "created_at"]
    list_filter = ["category", "is_default", "user", "created_at"]
    search_fields = ["name", "user__username"]
    ordering = ["category__display_order", "is_default", "user", "name"]
    list_per_page = 25

    fieldsets = (
        (None, {"fields": ("name", "color", "category", "is_default")}),
        (
            "사용자 정보",
            {
                "fields": ("user",),
                "classes": ("collapse",),
                "description": "기본 태그인 경우 사용자를 비워두세요.",
            },
        ),
        (
            "시간 정보",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border-radius: 3px; color: white; font-weight: bold;">{}</span>',
            obj.color,
            obj.color,
        )

    color_display.short_description = "색상"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "category")
