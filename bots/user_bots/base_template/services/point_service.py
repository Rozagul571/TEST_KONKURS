# bots/user_bots/base_template/services/point_service.py
"""
Point service - Ballarni hisoblash va statistikalar (OPTIMIZED)
Vazifasi: Foydalanuvchi ballarini hisoblash va statistika
"""
import logging
from typing import Dict, Any, Optional
from asgiref.sync import sync_to_async
from django.db.models import Sum, Case, When, Value, IntegerField
from django.db.models.functions import Coalesce

from django_app.core.models import Participant, Point
from django_app.core.models.pointrule import PointAction
from shared.utils import format_points

logger = logging.getLogger(__name__)


class PointService:
    """Point service with optimized queries"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def get_user_stats(self, participant: Participant) -> Dict[str, Any]:
        """
        Foydalanuvchi statistikasini olish (OPTIMIZED)

        Args:
            participant: Participant object

        Returns:
            Stats dict
        """
        try:
            points_breakdown = await self._get_points_breakdown(participant.id)

            return {
                'total_points': participant.current_points,
                'formatted_total': format_points(participant.current_points),
                'referral_points': points_breakdown.get('referral', 0),
                'channel_points': points_breakdown.get('channel_join', 0),
                'premium_points': points_breakdown.get('premium_bonus', 0),
                'other_points': points_breakdown.get('other', 0),
                'has_premium': participant.is_premium
            }
        except Exception as e:
            logger.error(f"Get user stats error: {e}")
            return self._get_default_stats()

    async def _get_points_breakdown(self, participant_id: int) -> Dict[str, int]:
        """
        Ballarni sabablarga ajratish (optimized single query)

        Args:
            participant_id: Participant ID

        Returns:
            Breakdown dict
        """

        @sync_to_async
        def _get_breakdown():
            try:
                # Single query with conditional aggregation
                points = Point.objects.filter(participant_id=participant_id)

                breakdown = points.aggregate(
                    referral_points=Coalesce(Sum(
                        Case(
                            When(reason__in=[PointAction.REFERRAL, PointAction.PREMIUM_REFERRAL], then='earned_points'),
                            default=Value(0),
                            output_field=IntegerField()
                        )
                    ), 0),
                    channel_points=Coalesce(Sum(
                        Case(
                            When(reason=PointAction.CHANNEL_JOIN, then='earned_points'),
                            default=Value(0),
                            output_field=IntegerField()
                        )
                    ), 0),
                    premium_points=Coalesce(Sum(
                        Case(
                            When(reason=PointAction.PREMIUM_USER, then='earned_points'),
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
                    'other': max(0, other_points)
                }

            except Exception as e:
                logger.error(f"Get points breakdown error: {e}")
                return {'referral': 0, 'channel_join': 0, 'premium_bonus': 0, 'other': 0}

        return await _get_breakdown()

    def _get_default_stats(self) -> Dict[str, Any]:
        """Default stats"""
        return {
            'total_points': 0,
            'formatted_total': '0',
            'referral_points': 0,
            'channel_points': 0,
            'premium_points': 0,
            'other_points': 0,
            'has_premium': False
        }

    async def get_user_ranking(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Foydalanuvchi reytingdagi o'rnini olish

        Args:
            user_id: Telegram user ID

        Returns:
            Ranking info dict
        """

        @sync_to_async
        def _get_ranking():
            try:
                participant = Participant.objects.select_related('user').get(
                    user__telegram_id=user_id,
                    competition__bot_id=self.bot_id,
                    is_participant=True
                )

                # Count participants with more points
                higher_count = Participant.objects.filter(
                    competition=participant.competition,
                    is_participant=True,
                    current_points__gt=participant.current_points
                ).count()

                rank = higher_count + 1

                # Get next rank points
                next_rank_participant = Participant.objects.filter(
                    competition=participant.competition,
                    is_participant=True,
                    current_points__gt=participant.current_points
                ).order_by('current_points').first()

                points_to_next = 0
                if next_rank_participant:
                    points_to_next = next_rank_participant.current_points - participant.current_points

                # Total participants
                total = Participant.objects.filter(
                    competition=participant.competition,
                    is_participant=True
                ).count()

                return {
                    'rank': rank,
                    'points': participant.current_points,
                    'points_to_next_rank': points_to_next,
                    'total_participants': total
                }

            except Participant.DoesNotExist:
                return None
            except Exception as e:
                logger.error(f"Get user ranking error: {e}")
                return None

        return await _get_ranking()