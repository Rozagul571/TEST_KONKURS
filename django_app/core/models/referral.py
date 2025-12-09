# django_app/core/models/referral.py
from django.db import models
from .user import User
from .competition import Competition
from .base import TimestampMixin

class Referral(TimestampMixin):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referrals")
    referred = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invited_by")
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="referrals")

    class Meta:
        unique_together = ("referrer", "referred", "competition")
        db_table = 'core_referral'

    def __str__(self):
        return f"{self.referred} <- {self.referrer} ({self.competition.name})"