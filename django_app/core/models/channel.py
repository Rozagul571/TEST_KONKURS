# django_app/core/models/channel.py
from django.db import models
from .base import TimestampMixin

class ChannelType(models.TextChoices):
    CHANNEL = 'channel', "Channel"
    GROUP = 'group', "Group"

class Channel(TimestampMixin):
    channel_username = models.CharField(max_length=200, unique=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    type = models.CharField(max_length=20, choices=ChannelType.choices, default=ChannelType.CHANNEL)
    is_required = models.BooleanField(default=True)
    def __str__(self):
        return self.channel_username or self.title

    class Meta:
        db_table = 'core_channel'