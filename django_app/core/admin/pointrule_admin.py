# django_app/core/admin/pointrule_admin.py
from django.contrib import admin
from django.http import HttpRequest
from ..models.pointrule import PointRule
from ..models.user import User

@admin.register(PointRule)
class PointRuleAdmin(admin.ModelAdmin):
    list_display = ("action_type", "points", "competition_display")
    list_filter = ("action_type",)
    def competition_display(self, obj):
        return obj.competition.name if obj.competition else "-"
    competition_display.short_description = "Konkurs"
    def get_queryset(self, request: HttpRequest):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            return qs.filter(competition__creator=admin_user)
        except:
            return qs.none()
    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return request.user.is_staff
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            return obj.competition.creator == admin_user
        except:
            return False
    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return request.user.is_staff
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            return obj.competition.creator == admin_user
        except:
            return False
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser