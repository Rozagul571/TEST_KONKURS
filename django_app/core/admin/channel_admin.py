# django_app/core/admin/channel_admin.py
"""
Channel Admin - Faqat o'z konkursidagi kanallarni ko'rish
"""
from django.contrib import admin
from django.http import HttpRequest

from ..models import User
from ..models.channel import Channel


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    """
    Channel admin - har bir admin faqat o'z konkursidagi kanallarni ko'radi
    """
    list_display = ("channel_username", "title", "type", "get_competitions")
    search_fields = ("channel_username", "title")
    list_filter = ("type",)

    def get_competitions(self, obj):
        """Kanal qaysi konkurslarda ishlatilayotganini ko'rsatish"""
        competitions = obj.competitions.all()
        if competitions:
            return ", ".join([c.name for c in competitions[:3]])
        return "-"

    get_competitions.short_description = "Konkurslar"

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

    def get_queryset(self, request: HttpRequest):
        """
        Faqat o'z konkursidagi kanallarni ko'rsatish

        SuperAdmin: Barcha kanallar
        Admin: Faqat o'z competition dagi kanallar
        """
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        # Admin faqat o'z kanallarini ko'radi
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            # Faqat o'z competition ga bog'langan kanallar
            return qs.filter(competitions__creator=admin_user).distinct()
        except (ValueError, User.DoesNotExist):
            return qs.none()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """ManyToMany fieldlar uchun filterlash"""
        if db_field.name == "competitions" and not request.user.is_superuser:
            try:
                from ..models.competition import Competition
                telegram_id = int(request.user.username.split('_')[-1])
                admin_user = User.objects.get(telegram_id=telegram_id)
                kwargs["queryset"] = Competition.objects.filter(creator=admin_user)
            except:
                pass
        return super().formfield_for_manytomany(db_field, request, **kwargs)