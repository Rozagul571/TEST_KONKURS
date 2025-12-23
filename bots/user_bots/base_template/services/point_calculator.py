# bots/user_bots/base_template/services/point_calculator.py
"""
Point calculator service - TO'G'RILANGAN
"""
import logging
from typing import Dict, Any, Optional, Tuple
from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from django_app.core.models import Participant, Point
from django_app.core.models.pointrule import PointAction
from shared.utils import format_points

logger = logging.getLogger(__name__)


class PointCalculator:
    """Point calculation service"""

    def __init__(self, competition_settings: Dict[str, Any]):
        self.competition_settings = competition_settings
        self.competition_id = competition_settings.get('id')
        self.point_rules = competition_settings.get('point_rules', {})

    async def calculate_channel_points(self, user_id: int, is_premium: bool,
                                     channels_joined: int = None) -> Tuple[int, Dict[str, Any]]:
        """Calculate points for channel joining"""
        try:
            # Get base points for channel join
            base_points = self._get_rule_value(PointAction.CHANNEL_JOIN, 1)

            # Get channels count
            if channels_joined is None:
                channels_joined = len(self.competition_settings.get('channels', []))

            # Calculate total
            base_total = base_points * channels_joined

            # Apply premium multiplier
            total_points = base_total
            multiplier = 1.0
            premium_bonus = 0

            if is_premium:
                premium_multiplier = self._get_rule_value(PointAction.PREMIUM_USER, 2.0)
                multiplier = float(premium_multiplier)
                total_points = int(base_total * multiplier)
                premium_bonus = total_points - base_total

            breakdown = {
                'base_points_per_channel': base_points,
                'channels_joined': channels_joined,
                'base_total': base_total,
                'premium_multiplier': multiplier,
                'premium_bonus': premium_bonus,
                'final_total': total_points
            }

            logger.info(f"Channel points: user={user_id}, points={total_points}")

            return total_points, breakdown

        except Exception as e:
            logger.error(f"Calculate channel points error: {e}")
            return 0, {}

    async def calculate_referral_points(self, referrer_id: int, is_premium_referral: bool) -> Tuple[int, Dict[str, Any]]:
        """Calculate points for referral"""
        try:
            # Get base referral points
            base_points = self._get_rule_value(PointAction.REFERRAL, 5)

            total_points = base_points
            premium_bonus = 0

            if is_premium_referral:
                premium_points = self._get_rule_value(PointAction.PREMIUM_REFERRAL, 10)
                if premium_points:
                    total_points = premium_points
                    premium_bonus = premium_points - base_points
                else:
                    # Default: double points for premium referral
                    total_points = base_points * 2
                    premium_bonus = base_points

            breakdown = {
                'base_points': base_points,
                'is_premium_referral': is_premium_referral,
                'premium_bonus': premium_bonus,
                'final_total': total_points
            }

            logger.info(f"Referral points: referrer={referrer_id}, points={total_points}")

            return total_points, breakdown

        except Exception as e:
            logger.error(f"Calculate referral points error: {e}")
            return 5, {}

    async def add_points_to_participant(self, participant: Participant, points: int,
                                      reason: str, details: Dict[str, Any] = None) -> bool:
        """Add points to participant"""
        @sync_to_async
        @transaction.atomic
        def _add_points():
            try:
                # Update participant points
                participant.current_points += points
                participant.updated_at = timezone.now()
                participant.save(update_fields=['current_points', 'updated_at'])

                # Create point record
                point = Point.objects.create(
                    participant=participant,
                    earned_points=points,
                    reason=reason,
                    details=details or {},
                    created_at=timezone.now()
                )

                logger.info(f"Added {points} points to participant {participant.id}")
                return True

            except Exception as e:
                logger.error(f"Add points to participant error: {e}")
                return False

        return await _add_points()

    def _get_rule_value(self, action_type: str, default: Any = None) -> Any:
        """Get rule value from settings"""
        return self.point_rules.get(action_type, default)