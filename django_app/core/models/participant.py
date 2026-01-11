# django_app/core/models/participant.py
"""
Participant modeli - Konkursda qatnashuvchilar
Vazifasi: Har bir konkurs uchun alohida participant yozuvi
"""
from django.db import models
from django.utils import timezone
from .user import User
from .competition import Competition
from .base import TimestampMixin


class Participant(TimestampMixin):
    """
    Konkurs ishtirokchisi modeli.

    Attributes:
        user: Telegram foydalanuvchisi (User modeliga FK)
        competition: Qaysi konkursda qatnashayotgani
        is_participant: Ro'yxatdan o'tganmi (kanallarni tekshirganidan keyin True)
        current_points: Joriy ballar soni
        referral_code: Taklif qilish uchun unikal kod
        referred_by: Kim taklif qilgani (self FK)
        channels_joined: Qo'shilgan kanallar ro'yxati (JSON)
        is_blocked: Bloklangan yoki yo'q
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participants')
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='participants')
    is_participant = models.BooleanField(default=False)
    current_points = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=100, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    channels_joined = models.JSONField(default=list, blank=True)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'competition')
        db_table = 'core_participant'
        verbose_name = 'Ishtirokchi'
        verbose_name_plural = 'Ishtirokchilar'

    def __str__(self):
        return f"{self.user} @ {self.competition.name}"

    @property
    def telegram_id(self):
        """User telegram_id ni qaytarish"""
        return self.user.telegram_id if self.user else None

    @property
    def username(self):
        """User username ni qaytarish"""
        return self.user.username if self.user else None

    @property
    def first_name(self):
        """User first_name ni qaytarish"""
        return self.user.first_name if self.user else None

    @property
    def last_name(self):
        """User last_name ni qaytarish"""
        return self.user.last_name if self.user else None

    @property
    def full_name(self):
        """User full name ni qaytarish"""
        if self.user:
            return f"{self.user.first_name or ''} {self.user.last_name or ''}".strip() or self.user.username or str(
                self.user.telegram_id)
        return "Unknown"

    @property
    def is_premium(self):
        """User premium statusini qaytarish"""
        return self.user.is_premium if self.user else False

    def add_points(self, points: int, reason: str):
        """Ishtirokchiga ball qo'shish"""
        self.current_points += points
        self.save(update_fields=['current_points', 'updated_at'])
        # Point yozuvini yaratish
        from .point import Point
        Point.objects.create(participant=self, earned_points=points, reason=reason)