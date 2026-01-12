# django_app/core/models/prize.py
"""
Prize Model - O'zbekcha verbose_name va Type choices
"""
from django.db import models


class PrizeType(models.TextChoices):
    """Prize turi"""
    NUMBER = 'number', 'Pul'  # Pul mukofoti
    TEXT = 'text', 'Matn'  # Boshqa sovg'alar (iPhone, mashina..)


class Prize(models.Model):
    """Konkurs sovg'alari"""

    competition = models.ForeignKey(
        'Competition',
        on_delete=models.CASCADE,
        verbose_name="Konkurs"
    )

    place = models.PositiveIntegerField(
        verbose_name="O'rin",
        help_text="Nechanchi o'rin uchun sovg'a"
    )

    prize_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Sovg'a nomi",
        help_text="Sovg'a nomi (ixtiyoriy)"
    )

    prize_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Pul miqdori",
        help_text="Pul mukofoti (faqat 'Pul' turi uchun)"
    )

    type = models.CharField(
        max_length=10,
        choices=PrizeType.choices,
        default=PrizeType.NUMBER,
        verbose_name="Turi",
        help_text="'Pul' - pul mukofoti, 'Matn' - boshqa sovg'a"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Tavsif",
        help_text="Sovg'a tavsifi (faqat 'Matn' turi uchun, masalan: iPhone 15 Pro)"
    )

    class Meta:
        verbose_name = "Sovg'a"
        verbose_name_plural = "Sovg'alar"
        ordering = ['place']
        unique_together = ['competition', 'place']

    def __str__(self):
        if self.type == PrizeType.TEXT and self.description:
            return f"{self.place}-o'rin: {self.description}"
        elif self.prize_amount:
            return f"{self.place}-o'rin: {self.prize_amount:,.0f} so'm"
        elif self.prize_name:
            return f"{self.place}-o'rin: {self.prize_name}"
        return f"{self.place}-o'rin"

    def get_display_text(self) -> str:
        """Sovg'ani ko'rsatish uchun text"""
        if self.type == PrizeType.TEXT:
            return self.description or self.prize_name or "Sovg'a"
        else:
            if self.prize_amount:
                if self.prize_name:
                    return f"{self.prize_name} - {self.prize_amount:,.0f} so'm"
                return f"{self.prize_amount:,.0f} so'm"
            return self.prize_name or "Sovg'a"