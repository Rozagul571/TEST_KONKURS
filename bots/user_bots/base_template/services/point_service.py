# bots/user_bots/base_template/services/point_service.py
"""
Point service - Ballarni hisoblash va statistikalar (OPTIMIZED)
"""
import logging
from typing import Dict, Any, Optional
from asgiref.sync import sync_to_async
from django.db.models import Sum

from django_app.core.models import Participant, Point
from django_app.core.models.pointrule import PointAction
from shared.utils import format_points

logger = logging.getLogger(__name__)


class PointService:
    """Point service with optimized queries"""

    def __init__(self, competition_id: int):
        self.competition_id = competition_id

    async def get_user_stats(self, participant: Participant) -> Dict[str, Any]:
        """Foydalanuvchi statistikasini olish (OPTIMIZED)"""
        try:
            # Get points breakdown in single query
            points_breakdown = await self._get_points_breakdown(participant.id)

            # Calculate level
            level_info = await self._calculate_level(participant.current_points)

            return {
                'total_points': participant.current_points,
                'formatted_total': format_points(participant.current_points),
                'referral_points': points_breakdown.get('referral', 0),
                'channel_points': points_breakdown.get('channel_join', 0),
                'premium_points': points_breakdown.get('premium_bonus', 0),
                'other_points': points_breakdown.get('other', 0),
                'level_info': level_info,
                'has_premium': participant.user.is_premium if participant.user else False
            }

        except Exception as e:
            logger.error(f"Get user stats error: {e}")
            return self._get_default_stats()

    async def _get_points_breakdown(self, participant_id: int) -> Dict[str, int]:
        """Ballarni sabablarga ajratish (optimized)"""

        @sync_to_async
        def _get_breakdown():
            try:
                # Single query for all points with aggregation
                from django.db.models import Case, When, Value, IntegerField
                from django.db.models.functions import Coalesce

                points = Point.objects.filter(participant_id=participant_id)

                # Use conditional aggregation for better performance
                breakdown = points.aggregate(
                    referral_points=Coalesce(Sum(
                        Case(
                            When(reason__in=[PointAction.REFERRAL, PointAction.PREMIUM_REFERRAL],
                                 then='earned_points'),
                            default=Value(0),
                            output_field=IntegerField()
                        )
                    ), 0),
                    channel_points=Coalesce(Sum(
                        Case(
                            When(reason=PointAction.CHANNEL_JOIN,
                                 then='earned_points'),
                            default=Value(0),
                            output_field=IntegerField()
                        )
                    ), 0),
                    premium_points=Coalesce(Sum(
                        Case(
                            When(reason=PointAction.PREMIUM_USER,
                                 then='earned_points'),
                            default=Value(0),
                            output_field=IntegerField()
                        )
                    ), 0),
                    total_points=Coalesce(Sum('earned_points'), 0)
                )

                other_points = breakdown['total_points'] - (
                        breakdown['referral_points'] +
                        breakdown['channel_points'] +
                        breakdown['premium_points']
                )

                return {
                    'referral': breakdown['referral_points'],
                    'channel_join': breakdown['channel_points'],
                    'premium_bonus': breakdown['premium_points'],
                    'other': other_points if other_points > 0 else 0
                }

            except Exception as e:
                logger.error(f"Get points breakdown error: {e}")
                return {'referral': 0, 'channel_join': 0, 'premium_bonus': 0, 'other': 0}

        return await _get_breakdown()

    async def _calculate_level(self, total_points: int) -> Dict[str, Any]:
        """Calculate user level based on points"""
        # Level progression
        points_for_level = [
            0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500,
            6600, 7800, 9100, 10500, 12000, 13600, 15300, 17100, 19000
        ]

        current_level = 0
        points_to_next = 0
        progress_percentage = 0

        for i in range(len(points_for_level) - 1):
            if total_points >= points_for_level[i] and total_points < points_for_level[i + 1]:
                current_level = i
                points_in_level = points_for_level[i + 1] - points_for_level[i]
                points_earned_in_level = total_points - points_for_level[i]
                points_to_next = points_for_level[i + 1] - total_points
                progress_percentage = (points_earned_in_level / points_in_level) * 100
                break

        if total_points >= points_for_level[-1]:
            current_level = len(points_for_level) - 1
            points_to_next = 0
            progress_percentage = 100

        level_names = [
            "Beginner", "Novice", "Regular", "Active", "Dedicated",
            "Expert", "Master", "Champion", "Legend", "Elite",
            "Hero", "Superhero", "Titan", "Immortal", "God",
            "Ultimate", "Supreme", "Divine", "Eternal", "Infinity"
        ]

        return {
            'level': current_level,
            'level_name': level_names[min(current_level, len(level_names) - 1)],
            'total_points': total_points,
            'points_to_next': points_to_next,
            'progress_percentage': round(progress_percentage, 1),
            'next_level_points': points_for_level[min(current_level + 1, len(points_for_level) - 1)]
        }

    def _get_default_stats(self) -> Dict[str, Any]:
        """Default stats"""
        return {
            'total_points': 0,
            'formatted_total': '0',
            'referral_points': 0,
            'channel_points': 0,
            'premium_points': 0,
            'other_points': 0,
            'level_info': {
                'level': 0,
                'level_name': 'Beginner',
                'points_to_next': 100,
                'progress_percentage': 0
            },
            'has_premium': False
        }

    async def get_user_ranking(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user ranking information"""

        @sync_to_async
        def _get_ranking():
            try:
                # Get user's rank and points
                participant = Participant.objects.select_related('user').get(
                    user__telegram_id=user_id,
                    competition_id=self.competition_id
                )

                # Count participants with more points
                higher_count = Participant.objects.filter(
                    competition_id=self.competition_id,
                    current_points__gt=participant.current_points
                ).count()

                rank = higher_count + 1

                # Get next rank points
                next_rank_participant = Participant.objects.filter(
                    competition_id=self.competition_id,
                    current_points__gt=participant.current_points
                ).order_by('current_points').first()

                points_to_next = 0
                if next_rank_participant:
                    points_to_next = next_rank_participant.current_points - participant.current_points

                return {
                    'rank': rank,
                    'points': participant.current_points,
                    'points_to_next_rank': points_to_next,
                    'total_participants': Participant.objects.filter(
                        competition_id=self.competition_id
                    ).count()
                }

            except Participant.DoesNotExist:
                return None
            except Exception as e:
                logger.error(f"Get user ranking error: {e}")
                return None

        return await _get_ranking()