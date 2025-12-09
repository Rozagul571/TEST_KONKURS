# django_app/core/models/pointrule.py
from django.db import models
from .competition import Competition

class PointAction(models.TextChoices):
    """Ball harakatlari. Vazifasi: Ball berish turini cheklash. Misol: REFERRAL = 'referral' - referal uchun ball."""
    REFERRAL = "referral", "Referral"
    CHANNEL_JOIN = "channel_join", "Channel Join"
    PREMIUM_REFERRAL = "premium_ref", "Premium Referral"
    PREMIUM_USER = "premium_user", "Premium User Join"

class PointRule(models.Model):
    """Ball qoidalari. Vazifasi: Har bir action uchun ball miqdorini saqlash. Misol: action_type=REFERRAL, points=5 - admin belgilaydi."""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='point_rules')
    action_type = models.CharField(max_length=50, choices=PointAction.choices)
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ('competition', 'action_type')
        db_table = 'core_pointrule'

    def __str__(self):
        return f"{self.get_action_type_display()} ({self.points} ball)"