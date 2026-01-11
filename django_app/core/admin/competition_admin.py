# django_app/core/admin/competition_admin.py
"""
Competition Admin - TO'G'RILANGAN
Vazifasi: Konkursni boshqarish, o'chirilganda bog'liq narsalar ham o'chsin
"""
from django.contrib import admin
from django.http import HttpRequest
from django.contrib import messages
from django.template.loader import render_to_string
import requests
import os

from ..models.competition import Competition
from ..models.pointrule import PointRule
from ..models.prize import Prize
from ..models.user import User
from ..models.bot import BotSetUp, BotStatus
from bots.main_bot.services.notification_service import NotificationService
from asgiref.sync import async_to_sync


class CompetitionChannelInline(admin.TabularInline):
    model = Competition.channels.through
    extra = 1
    verbose_name = "Kanal"
    verbose_name_plural = "Kanallar"

    def get_queryset(self, request):
        """Faqat o'z kanallarini ko'rsatish"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Competition filter qilinganidan keyin bu avtomatik filter bo'ladi
        return qs


class PointRuleInline(admin.StackedInline):
    model = PointRule
    extra = 1
    verbose_name = "Ball Qoidasi"
    verbose_name_plural = "Ball Qoidalari"
    fields = ('action_type', 'points')


class PrizeInline(admin.TabularInline):
    model = Prize
    extra = 1
    verbose_name = "Sovrin"
    verbose_name_plural = "Sovrinlar"
    fields = ('place', 'prize_name', 'prize_amount', 'type', 'description')


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "bot_username", "creator_display", "completion_status")
    list_filter = ("status",)
    search_fields = ("name", "description")
    inlines = [CompetitionChannelInline, PointRuleInline, PrizeInline]
    exclude = ("bot", "is_published", "notification_sent")
    readonly_fields = ("creator",)

    def get_fields(self, request, obj=None):
        fields = ['name', 'description', 'start_at', 'end_at', 'rules_text']
        if request.user.is_superuser:
            fields.append('status')
        return fields

    def get_queryset(self, request: HttpRequest):
        """Faqat o'z konkurslarini ko'rsatish"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            return qs.filter(bot__owner=admin_user, bot__is_active=True)
        except:
            return qs.none()

    def bot_username(self, obj):
        return obj.bot.bot_username if obj.bot else "-"
    bot_username.short_description = "Bot Username"

    def creator_display(self, obj):
        if obj.creator:
            name = f"{obj.creator.first_name or ''} {obj.creator.last_name or ''}".strip()
            return name or "Noma'lum"
        return "-"
    creator_display.short_description = "Egasi"

    def completion_status(self, obj):
        is_complete = self.is_complete(obj)
        context = {'is_complete': is_complete, 'missing': self.get_missing_fields(obj)}
        return render_to_string('admin/core/competition/completion_status.html', context)
    completion_status.short_description = "Holati"

    def save_model(self, request, obj, form, change):
        # Creator o'rnatish
        if not obj.creator_id:
            try:
                telegram_id = int(request.user.username.split('_')[-1])
                admin_user = User.objects.get(telegram_id=telegram_id)
                obj.creator = admin_user
            except:
                pass

        # Bot bog'lash
        if not obj.bot and obj.creator:
            active_bot = BotSetUp.objects.filter(owner=obj.creator, is_active=True).first()
            if active_bot:
                obj.bot = active_bot

        notification_was_sent_before = obj.notification_sent if change else False
        super().save_model(request, obj, form, change)

        # To'liq bo'lsa notification
        is_complete_now = self.is_complete(obj)
        if is_complete_now and not notification_was_sent_before and obj.status == 'draft':
            obj.status = 'pending'
            if obj.bot:
                obj.bot.status = BotStatus.PENDING
                obj.bot.save()
            obj.save(update_fields=['status'])

            success = self.send_completion_notification(obj)
            if success:
                obj.notification_sent = True
                obj.save(update_fields=['notification_sent'])
                messages.success(request, "✅ SuperAdmin ga notification yuborildi!")
                async_to_sync(self.send_superadmin_complete_notification)(obj)

    async def send_superadmin_complete_notification(self, competition):
        """SuperAdmin ga notification yuborish"""
        user = competition.creator
        bot_username = competition.bot.bot_username if competition.bot else "Noma'lum"
        admin_username = f"admin_{user.telegram_id}"
        bot_id = competition.bot.id if competition.bot else 0
        service = NotificationService()
        await service.send_superadmin_new_bot(user, bot_username, admin_username, bot_id)

    def is_complete(self, obj):
        """Konkurs to'liqmi tekshirish"""
        return all([
            bool(obj.name and obj.name.strip()),
            bool(obj.description and obj.description.strip()),
            obj.channels.exists(),
            obj.point_rules.exists(),
            obj.prize_set.exists(),
            bool(obj.rules_text and obj.rules_text.strip()),
            bool(obj.start_at),
            bool(obj.end_at)
        ])

    def get_missing_fields(self, obj):
        """Yetishmayotgan maydonlar"""
        missing = []
        if not obj.name:
            missing.append('Nomi')
        if not obj.description:
            missing.append('Tavsif')
        if not obj.channels.exists():
            missing.append('Kanallar')
        if not obj.point_rules.exists():
            missing.append('Ball qoidalari')
        if not obj.prize_set.exists():
            missing.append('Sovrinlar')
        if not obj.rules_text:
            missing.append('Shartlar')
        if not obj.start_at:
            missing.append('Boshlanish vaqti')
        if not obj.end_at:
            missing.append('Tugash vaqti')
        return ', '.join(missing)

    def send_completion_notification(self, competition):
        """FastAPI ga notification yuborish"""
        try:
            fastapi_url = os.getenv('FASTAPI_URL',)
            payload = {
                "user_tg_id": competition.creator.telegram_id,
                "competition_name": competition.name,
                "description": competition.description or "Tavsif yo'q"
            }
            response = requests.post(
                f"{fastapi_url}/api/webhooks/handle-user-completed",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            return False

    def delete_model(self, request, obj):
        """
        Competition o'chirilganda bog'liq narsalarni tozalash
        - Redis cache
        - Bot status
        """
        bot_id = obj.bot.id if obj.bot else None

        # Redis cache tozalash
        if bot_id:
            try:
                from shared.redis_client import redis_client
                import asyncio
                asyncio.get_event_loop().run_until_complete(redis_client.clear_bot_cache(bot_id))
            except:
                pass

        # Bot statusini o'zgartirish
        if obj.bot:
            obj.bot.status = BotStatus.DRAFT
            obj.bot.save()

        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Bulk delete uchun"""
        for obj in queryset:
            self.delete_model(request, obj)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            active_bot = BotSetUp.objects.filter(owner=admin_user, is_active=True).first()
            return Competition.objects.filter(bot=active_bot).count() == 0
        except:
            return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            return obj.creator == admin_user
        except:
            return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        try:
            telegram_id = int(request.user.username.split('_')[-1])
            admin_user = User.objects.get(telegram_id=telegram_id)
            return obj.creator == admin_user
        except:
            return False

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff