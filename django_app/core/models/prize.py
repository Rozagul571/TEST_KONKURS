# django_app/core/models/prize.py
from django.db import models
from .competition import Competition

class PrizeType(models.TextChoices):
    """Sovrin turlari. Vazifasi: Sovrin type ni cheklash (text yoki pul). Misol: TEXT = 'text' - 'iPhone' uchun, NUMBER = 'number' - pul uchun."""
    TEXT = 'text', "Text"
    NUMBER = 'number', "Number"

class Prize(models.Model):
    """Sovrin modeli. Vazifasi: Sovrinlarni saqlash. Misol: place=1, prize_name='iPhone', type=TEXT - admin tanlaydi."""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="prize_set")
    place = models.PositiveIntegerField()
    prize_name = models.CharField(max_length=200, null=True, blank=True)
    prize_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    type = models.CharField(max_length=20, choices=PrizeType.choices, default=PrizeType.TEXT)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("competition", "place")
        db_table = 'core_prize'

    def __str__(self):
        return f"{self.prize_name or self.place} ({self.prize_amount or ''})"