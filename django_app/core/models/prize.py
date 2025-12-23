from django.db import models
from .competition import Competition

class PrizeType(models.TextChoices):
    TEXT = 'text', "Text"
    NUMBER = 'number', "Number"

class Prize(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="prize_set")
    place = models.PositiveIntegerField()
    prize_name = models.CharField(max_length=200, null=True, blank=True)
    prize_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    type = models.CharField(max_length=20, choices=PrizeType.choices, default=PrizeType.NUMBER)
    description = models.TextField(blank=True, null=True)
    class Meta:
        unique_together = ("competition", "place")
        db_table = 'core_prize'
    def __str__(self):
        return f"{self.prize_name or self.place} ({self.prize_amount or ''})"