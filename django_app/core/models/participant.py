# django_app/core/models/participant.py
from django.db import models
from django.utils import timezone
from .user import User
from .competition import Competition
from .base import TimestampMixin

class Participant(TimestampMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participants')
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='participants')
    is_participant = models.BooleanField(default=False)
    current_points = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=100, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    channels_joined = models.JSONField(default=list, blank=True)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'competition')
        db_table = 'core_participant'

    def __str__(self):
        return f"{self.user} @ {self.competition.name}"

    def add_points(self, points, reason):
        self.current_points += points
        self.save()
        from .point import Point
        Point.objects.create(participant=self, earned_points=points, reason=reason)