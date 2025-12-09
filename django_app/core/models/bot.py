from django.db import models
from cryptography.fernet import Fernet
import os
from django.utils import timezone
from .user import User
from .base import TimestampMixin

FERNET_KEY = os.getenv("FERNET_KEY")
if FERNET_KEY:
    FERNET_KEY = FERNET_KEY.encode()
    cipher = Fernet(FERNET_KEY)
else:
    cipher = None

def encrypt_token(token):
    if not cipher:
        raise RuntimeError("FERNET_KEY not configured")
    return cipher.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token):
    if not cipher:
        raise RuntimeError("FERNET_KEY not configured")
    return cipher.decrypt(encrypted_token.encode()).decode()

class BotStatus(models.TextChoices):
    """Bot statuslari. Vazifasi: Bot holatini cheklash. Misol: RUNNING = 'running' - bot ishlayotganida ishlatiladi."""
    DRAFT = "draft", "Draft"  # O'ZGARTIRILGAN: DRAFT qo'shildi
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    STOPPED = "stopped", "Stopped"
    REJECTED = "rejected", "Rejected"

class BotSetUp(TimestampMixin):
    """Bot setup modeli. Vazifasi: User bot token va statusini saqlash. Misol: owner=User(1), bot_username='@mybot' - B bot yaratishda ishlatiladi."""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bots')
    bot_username = models.CharField(max_length=255, unique=True)
    encrypted_token = models.TextField()
    status = models.CharField(max_length=20, default=BotStatus.DRAFT, choices=BotStatus.choices)  # O'ZGARTIRILGAN: Default DRAFT
    is_active = models.BooleanField(default=False)  # O'ZGARTIRILGAN: Faqat bitta aktiv bot uchun
    process_id = models.CharField(max_length=255, null=True, blank=True)  # Subprocess PID

    def save(self, *args, **kwargs):
        if self.encrypted_token and not self.encrypted_token.startswith("gAAAA"):
            self.encrypted_token = encrypt_token(self.encrypted_token)
        super().save(*args, **kwargs)

    def get_token(self):
        return decrypt_token(self.encrypted_token)

    def __str__(self):
        return f"@{self.bot_username}"

    class Meta:
        db_table = 'bot_setup'
        verbose_name = 'Bot Sozlash'
        verbose_name_plural = 'Bot Sozlashlar'