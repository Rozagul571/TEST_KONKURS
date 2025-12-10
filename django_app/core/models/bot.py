# django_app/core/models/bot.py

from django.db import models
from cryptography.fernet import Fernet
import os
from django.utils import timezone
from .user import User
from .base import TimestampMixin

# FIX: Global cipher o'rniga har chaqirilganda yangilash
def get_cipher():
    FERNET_KEY = os.getenv("FERNET_KEY")
    if not FERNET_KEY:
        raise RuntimeError("FERNET_KEY not configured")
    return Fernet(FERNET_KEY.encode())

def encrypt_token(token):
    cipher = get_cipher()
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    cipher = get_cipher()
    return cipher.decrypt(encrypted_token.encode()).decode()

class BotStatus(models.TextChoices):
    """Bot statuslari. Vazifasi: Bot holatini cheklash."""
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    STOPPED = "stopped", "Stopped"
    REJECTED = "rejected", "Rejected"

class BotSetUp(TimestampMixin):
    """Bot setup modeli."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bots')
    bot_username = models.CharField(max_length=255, unique=True)
    encrypted_token = models.TextField()
    status = models.CharField(max_length=20, default=BotStatus.DRAFT, choices=BotStatus.choices)
    is_active = models.BooleanField(default=False)
    process_id = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        # FIX: Token encrypt qilish
        if self.encrypted_token and not self.encrypted_token.startswith("gAAAA"):
            try:
                self.encrypted_token = encrypt_token(self.encrypted_token)
            except Exception as e:
                raise ValueError(f"Token encrypt qilish xatosi: {e}")
        super().save(*args, **kwargs)

    def get_token(self):
        """Token decrypt qilish (sync versiya)"""
        try:
            return decrypt_token(self.encrypted_token)
        except Exception as e:
            raise ValueError(f"Token decrypt qilish xatosi: {e}")

    @classmethod
    def get_token_async(cls, encrypted_token):
        """Async kontekstda ishlatish uchun token decrypt"""
        from asgiref.sync import sync_to_async
        return sync_to_async(decrypt_token)(encrypted_token)

    def __str__(self):
        return f"@{self.bot_username}"

    class Meta:
        db_table = 'bot_setup'
        verbose_name = 'Bot Sozlash'
        verbose_name_plural = 'Bot Sozlashlar'