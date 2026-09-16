from django.contrib import admin

from api.models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "platform",
        "version",
        "version_code",
        "update_type",
        "is_silent",
        "is_active",
        "created_at",
    )
    list_filter = ("platform", "update_type", "is_active", "is_silent")
    search_fields = ("version", "version_code", "changelog")
    ordering = ("-version_code", "-created_at")
    list_editable = ("is_active", "is_silent")
    fieldsets = (
        (None, {
            "fields": (
                "platform",
                "version",
                "version_code",
                "update_type",
            ),
        }),
        ("下载与日志", {
            "fields": ("download_url", "changelog"),
        }),
        ("状态控制", {
            "fields": ("is_silent", "is_active"),
        }),
    )
