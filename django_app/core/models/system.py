# django_app/core/models/system.py
from django.db import models
from .base import TimestampMixin

class SystemSettings(TimestampMixin):
    """Tizim sozlamalari. Vazifasi: Global sozlamalarni saqlash. Misol: admin_username='@admin' - kontakt uchun."""
    admin_username = models.CharField(max_length=255, default="konkurs_system")

    class Meta:
        verbose_name = "Tizim Sozlamasi"
        verbose_name_plural = "Tizim Sozlamalari"
        db_table = 'core_systemsettings'

    def __str__(self):
        return "Tizim Sozlamalari"

    @classmethod
    def get(cls):
        obj, created = cls.objects.get_or_create(pk=1, defaults={'admin_username': 'konkurs_system'})
        return obj

    def get_telegram_url(self):
        username = self.admin_username.replace('@', '').strip()
        return f"https://t.me/{username}"

    def get_tg_protocol_url(self):
        username = self.admin_username.replace('@', '').strip()
        return f"tg://resolve?domain={username}"

    def save(self, *args, **kwargs):
        self.admin_username = self.admin_username.replace('@', '').strip()
        # Faqat bitta SystemSettings bo'lishi un
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'admin_username': 'konkurs_system'
            }
        )
        return obj