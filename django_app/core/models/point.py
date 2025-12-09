# django_app/core/models/point.py
from django.db import models
from django.utils import timezone
from .participant import Participant
from .pointrule import PointAction
from .base import TimestampMixin

class Point(TimestampMixin):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="points")
    earned_points = models.IntegerField()
    reason = models.CharField(max_length=50, choices=PointAction.choices)

    def __str__(self):
        return f"{self.participant} +{self.earned_points} ({self.reason})"

    class Meta:
        db_table = 'core_point'