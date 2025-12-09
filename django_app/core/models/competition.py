from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from .bot import BotSetUp  # O'ZGARTIRILGAN: BotSetUp import
from .user import User
from .base import TimestampMixin

class CompetitionStatus(models.TextChoices):
    """Konkurs statuslari. Vazifasi: Konkurs holatini cheklash. Misol: ACTIVE = 'active' - konkurs ishlayotganida."""
    DRAFT = "draft", "Draft"  # O'ZGARTIRILGAN: DRAFT qo'shildi
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    FINISHED = "finished", "Finished"
    CANCELED = "canceled", "Canceled"

class Competition(TimestampMixin):
    """Konkurs modeli. Vazifasi: Konkurs ma'lumotlarini saqlash. Misol: name='Yangi Konkurs', channels=[Channel(1)] - admin to'ldiradi."""
    bot = models.OneToOneField(BotSetUp, on_delete=models.CASCADE, related_name="competition", null=True, blank=True)  # O'ZGARTIRILGAN: OneToOneField, unique bog'lanish
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_competitions", null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)  # O'ZGARTIRILGAN: Celery uchun null=True
    status = models.CharField(max_length=50, choices=CompetitionStatus.choices, default=CompetitionStatus.DRAFT)  # O'ZGARTIRILGAN: Default DRAFT
    channels = models.ManyToManyField('Channel', related_name="competitions", blank=True)
    rules_text = models.TextField(blank=True, null=True)
    welcome_image = models.ImageField(upload_to='welcome_images/', null=True, blank=True)
    is_published = models.BooleanField(default=False)
    notification_sent = models.BooleanField(default=False)

    def clean(self):
        if self.bot and Competition.objects.filter(bot=self.bot).exclude(id=self.id).exists():  # O'ZGARTIRILGAN: Sizning yechim – bot ga bog'liq, pk emas
            raise ValidationError("Bu bot uchun konkurs allaqachon yaratilgan.")  # O'ZGARTIRILGAN: Bitta bot ga bitta konkurs

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'core_competition'
        verbose_name = 'Konkurs'
        verbose_name_plural = 'Konkurslar'
        ordering = ['-created_at']