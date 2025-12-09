from django.db import models
from django.utils import timezone

class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    PARTICIPANT = "participant", "Participant"
    PREMIUM = "premium", "Premium"

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PARTICIPANT)
    joined_at = models.DateTimeField(default=timezone.now)
    referral_code = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username or str(self.telegram_id)

    class Meta:
        db_table = 'core_user'