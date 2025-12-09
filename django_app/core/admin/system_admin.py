# django_app/core/admin/system_admin.py
from django.contrib import admin
from django.utils.html import format_html
from ..models.system import SystemSettings

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("admin_username", "get_telegram_link", "updated_at")
    fields = ("admin_username",)
    readonly_fields = ("updated_at",)
    def get_telegram_link(self, obj):
        if obj.admin_username:
            username = obj.admin_username.replace('@', '').strip()
            return format_html(
                '<a href="https://t.me/{}" target="_blank" style="background-color: #0088cc; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">📨 Telegramga o\'tish</a>',
                username
            )
        return "-"
    get_telegram_link.short_description = "Telegram Link"
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists() and request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return False
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return SystemSettings.objects.none()