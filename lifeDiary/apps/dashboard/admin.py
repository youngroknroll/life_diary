from django.contrib import admin
from django.utils.html import format_html

from .models import TimeBlock

# Register your models here.


@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "get_time_range", "tag_display", "memo_preview"]
    list_filter = ["user", "date", "tag__name", "created_at"]
    search_fields = ["user__username", "tag__name", "memo"]
    ordering = ["-date", "slot_index"]
    date_hierarchy = "date"
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("user", "date", "slot_index", "tag")}),
        (
            "추가 정보",
            {
                "fields": ("memo",),
            },
        ),
        (
            "시간 정보",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")

    def memo_preview(self, obj):
        """메모 미리보기."""
        if obj.memo:
            return obj.memo[:50] + "..." if len(obj.memo) > 50 else obj.memo
        return "-"

    memo_preview.short_description = "메모"

    def tag_display(self, obj):
        """태그를 색상과 함께 표시."""
        return format_html(
            '<span style="background-color: {}; padding: 2px 8px; border-radius: 3px; '
            'color: white; font-size: 0.8em;">{}</span>',
            obj.tag.color,
            obj.tag.name,
        )

    tag_display.short_description = "태그"

    def get_queryset(self, request):
        """쿼리 최적화."""
        return super().get_queryset(request).select_related("user", "tag")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """태그 선택 시 사용자별로 필터링."""
        if db_field.name == "tag" and hasattr(request, "_obj_"):
            kwargs["queryset"] = db_field.related_model.objects.filter(
                user=request._obj_.user
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """폼 커스터마이징."""
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)
