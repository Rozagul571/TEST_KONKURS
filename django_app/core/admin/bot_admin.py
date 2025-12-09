# django_app/core/admin/bot_admin.py
from django.contrib import admin
from django.http import HttpRequest
from ..models.bot import BotSetUp

@admin.register(BotSetUp)
class BotSetUpAdmin(admin.ModelAdmin):
    list_display = ("bot_username", "status", "owner_display", "created_at")
    list_filter = ("status",)
    search_fields = ("bot_username", "owner__full_name")
    fields = ("bot_username", "status", "owner", "encrypted_token", "admin_contact_username")
    readonly_fields = ("encrypted_token", "owner", "created_at")
    def owner_display(self, obj):
        return obj.owner.full_name if obj.owner else "-"
    owner_display.short_description = "Owner"
    def get_queryset(self, request: HttpRequest):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.none()
    def has_module_permission(self, request):
        return request.user.is_superuser
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser