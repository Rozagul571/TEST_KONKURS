#django_app/core/admin/channel_admin.py
from django.contrib import admin
from ..models.channel import Channel

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("channel_username", "title", "type")
    search_fields = ("channel_username", "title")
    list_filter = ("type",)

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # def get_queryset(self, request: HttpRequest):
    #     qs = super().get_queryset(request)
    #     if request.user.is_superuser:
    #         return qs
    #     try:
    #         telegram_id = int(request.user.username.split('_')[-1])
    #         admin_user = User.objects.get(telegram_id=telegram_id)
    #         return qs.filter(competitions__creator=admin_user).distinct()
    #     except:
    #         return qs.none()