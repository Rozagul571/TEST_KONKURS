# bots/user_bots/base_template/services/point_service.py
from asgiref.sync import sync_to_async
from django_app.core.models.point import Point
from django_app.core.models.pointrule import PointAction

class PointService:
    """Point servisi. Vazifasi: Ball qoidalari va stats olish. Misol: get_user_stats - tafsilotlar qaytaradi."""
    def __init__(self, competition_data):
        self.competition_data = competition_data

    @sync_to_async
    def get_point_rules(self):
        return {rule.action_type: rule.points for rule in self.competition_data['point_rules']}

    @sync_to_async
    def get_user_stats(self, participant):
        points = Point.objects.filter(participant=participant)
        total_points = participant.current_points
        referral_points = sum(p.earned_points for p in points if p.reason in [PointAction.REFERRAL, PointAction.PREMIUM_REFERRAL])
        channel_points = sum(p.earned_points for p in points if p.reason == PointAction.CHANNEL_JOIN)
        other_points = total_points - (referral_points + channel_points)
        return {'total_points': total_points, 'referral_points': referral_points, 'channel_points': channel_points, 'other_points': other_points}