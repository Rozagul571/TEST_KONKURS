# django_app/core/models/channel.py
from django.db import models
from .base import TimestampMixin

class ChannelType(models.TextChoices):
    """Kanal turlari. Vazifasi: Channel type ni cheklash. Misol: CHANNEL = 'channel' - majburiy kanal uchun."""
    CHANNEL = 'channel', "Channel"
    GROUP = 'group', "Group"

class Channel(TimestampMixin):
    """Kanal modeli. Vazifasi: Majburiy kanallarni saqlash. Misol: channel_username='@news' - user obuna bo'ladi."""
    channel_username = models.CharField(max_length=200, unique=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    type = models.CharField(max_length=20, choices=ChannelType.choices, default=ChannelType.CHANNEL)

    def __str__(self):
        return self.channel_username or self.title

    class Meta:
        db_table = 'core_channel'