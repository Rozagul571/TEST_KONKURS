from django.contrib import admin
from ..models.user import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "username", "full_name", "role", "joined_at")
    list_filter = ("role", "is_premium")
    search_fields = ("username", "full_name", "telegram_id")
    readonly_fields = ("referral_code",)

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)
        return User.objects.none()