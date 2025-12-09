# # django_app/core/services/point_calculator.py
# from asgiref.sync import sync_to_async
#
# from django_app.core.models import PointAction, Point
#
#
# class PointCalculator:
#     """Ball hisoblash servisi. Vazifasi: Ballarni hisoblash (modeldan ajratilgan). Misol: calculate_channel_points(user_id, competition) - kanallar uchun ball."""
#     def __init__(self, competition):
#         self.competition = competition
#
#     @sync_to_async
#     def get_point_for_action(self, action_type):
#         rule = self.competition['point_rules'].get(action_type, 0)
#         return rule
#
#     async def calculate_channel_points(self, user_id, is_premium):
#         points = await self.get_point_for_action(PointAction.CHANNEL_JOIN)
#         if is_premium:
#             points *= 2
#         return points * len(self.competition['channels'])
#
#     async def calculate_referral_points(self, is_premium_referred):
#         if is_premium_referred:
#             return await self.get_point_for_action(PointAction.PREMIUM_REFERRAL)
#         return await self.get_point_for_action(PointAction.REFERRAL)
#
#     @sync_to_async
#     def add_points_to_participant(self, participant, points, reason):
#         participant.current_points += points
#         participant.save()
#         Point.objects.create(participant=participant, earned_points=points, reason=reason)