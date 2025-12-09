# django_app/core/models/winner.py
from django.db import models
from .competition import Competition
from .participant import Participant
from .base import TimestampMixin

class Winner(TimestampMixin):
    """G'olib modeli. Vazifasi: G'oliblarni saqlash. Misol: place=1, participant=Participant(1) - konkurs tugaganda avto to'ldiriladi."""
    place = models.PositiveIntegerField()
    awarded_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    payment_proof_url = models.URLField(null=True, blank=True)

    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='winners')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='wins')

    class Meta:
        unique_together = ('competition', 'place')
        db_table = 'core_winner'

    def __str__(self):
        return f"{self.competition} - {self.participant} ({self.place})"