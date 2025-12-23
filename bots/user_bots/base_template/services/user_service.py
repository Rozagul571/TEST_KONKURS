# bots/user_bots/base_template/services/user_service.py
"""
Optimized user service with bulk operations
"""
import logging
import secrets
import string
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from asgiref.sync import sync_to_async
from django.db import transaction, models
from django.db.models import Q, F
from django.utils import timezone

from django_app.core.models import Participant, Competition, BotSetUp, Referral
from shared.utils import generate_referral_code
from shared.constants import COMPETITION_STATUSES

logger = logging.getLogger(__name__)


class UserService:
    """High-performance user service with bulk operations"""

    def __init__(self):
        self._batch_size = 100

    async def get_or_create_participant(self, user_data: Dict[str, Any], bot_id: int) -> Tuple[Participant, bool]:
        @sync_to_async
        @transaction.atomic
        def _create_participant():
            try:
                telegram_id = user_data.get('telegram_id')
                if not telegram_id:
                    raise ValueError("telegram_id is required")
                username = user_data.get('username', '')[:64]
                first_name = user_data.get('first_name', '')[:64]
                last_name = user_data.get('last_name', '')[:64]
                phone_number = user_data.get('phone_number')
                bot = BotSetUp.objects.get(id=bot_id, is_active=True)
                competition = Competition.objects.get(bot=bot, status=COMPETITION_STATUSES['ACTIVE'])
                participant = Participant.objects.filter(telegram_id=telegram_id, competition=competition).first()
                if participant:
                    update_fields = []
                    model_fields = [f.name for f in Participant._meta.get_fields()]
                    defaults = {
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone_number': phone_number,
                        'language_code': user_data.get('language_code', 'uz'),
                        'is_premium': user_data.get('is_premium', False),
                        'is_bot': user_data.get('is_bot', False),
                        'joined_at': timezone.now()
                    }
                    for field in model_fields:
                        if field in defaults and field != 'telegram_id':
                            old_value = getattr(participant, field, None)
                            new_value = defaults[field]
                            if old_value != new_value:
                                setattr(participant, field, new_value)
                                update_fields.append(field)
                    if update_fields:
                        participant.save(update_fields=update_fields)
                    return participant, False
                referral_code = self._generate_unique_referral_code(competition.id)
                participant = Participant.objects.create(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    language_code=user_data.get('language_code', 'uz'),
                    is_premium=user_data.get('is_premium', False),
                    is_bot=user_data.get('is_bot', False),
                    competition=competition,
                    referral_code=referral_code,
                    current_points=0,
                    is_participant=True,
                    joined_at=timezone.now()
                )
                logger.info(f"Participant created: {telegram_id}")
                return participant, True
            except Exception as e:
                logger.error(f"Create participant error: {e}", exc_info=True)
                raise
        return await _create_participant()

    def _generate_unique_referral_code(self, competition_id: int, length: int = 8) -> str:
        """Generate unique referral code for competition"""
        max_attempts = 10
        for _ in range(max_attempts):
            code = generate_referral_code(length)

            # Check if code already exists for this competition
            exists = Participant.objects.filter(
                competition_id=competition_id,
                referral_code=code
            ).exists()

            if not exists:
                return code

        # If all attempts fail, use timestamp-based code
        return f"ref{int(timezone.now().timestamp()) % 1000000}"

    async def get_participant_by_code(self, code: str, bot_id: int) -> Optional[Participant]:
        """Get participant by referral code"""

        @sync_to_async
        def _get_participant():
            try:
                return Participant.objects.get(
                    referral_code=code,
                    competition__bot_id=bot_id,
                    is_participant=True
                )
            except Participant.DoesNotExist:
                return None
            except Exception as e:
                logger.error(f"Get participant by code error: {e}")
                return None

        return await _get_participant()

    async def get_participant_by_user_id(self, user_id: int, bot_id: int) -> Optional[Participant]:
        """Get participant by user ID"""

        @sync_to_async
        def _get_participant():
            try:
                return Participant.objects.get(
                    telegram_id=user_id,
                    competition__bot_id=bot_id,
                    is_participant=True
                )
            except Participant.DoesNotExist:
                return None
            except Exception as e:
                logger.error(f"Get participant by user id error: {e}")
                return None

        return await _get_participant()

    async def create_referral(self, referrer: Participant, referred: Participant) -> Optional[Referral]:
        """Create referral record"""

        @sync_to_async
        @transaction.atomic
        def _create_referral():
            try:
                # Check if referral already exists
                existing = Referral.objects.filter(
                    referrer=referrer,
                    referred=referred
                ).first()

                if existing:
                    return existing

                # Create new referral
                referral = Referral.objects.create(
                    referrer=referrer,
                    referred=referred,
                    competition=referrer.competition,
                    is_premium=referred.is_premium,
                    status='completed'
                )

                return referral

            except Exception as e:
                logger.error(f"Create referral error: {e}")
                return None

        return await _create_referral()

    async def get_user_referrals(self, user_id: int, bot_id: int) -> List[Dict[str, Any]]:
        """Get user's referrals"""

        @sync_to_async
        def _get_referrals():
            try:
                referrals = Referral.objects.filter(
                    referrer__telegram_id=user_id,
                    competition__bot_id=bot_id
                ).select_related('referred').order_by('-created_at')

                result = []
                for ref in referrals:
                    result.append({
                        'id': ref.id,
                        'referred_user_id': ref.referred.telegram_id,
                        'referred_username': ref.referred.username,
                        'referred_full_name': f"{ref.referred.first_name} {ref.referred.last_name}".strip(),
                        'is_premium': ref.is_premium,
                        'points_earned': ref.points_earned,
                        'created_at': ref.created_at.isoformat(),
                        'status': ref.status
                    })

                return result
            except Exception as e:
                logger.error(f"Get referrals error: {e}")
                return []

        return await _get_referrals()

    async def get_participant_stats(self, participant_id: int) -> Dict[str, Any]:
        """Get participant statistics"""

        @sync_to_async
        def _get_stats():
            try:
                participant = Participant.objects.get(id=participant_id)

                # Get referral count
                referral_count = Referral.objects.filter(
                    referrer_id=participant_id,
                    status='completed'
                ).count()

                # Get premium referral count
                premium_count = Referral.objects.filter(
                    referrer_id=participant_id,
                    is_premium=True,
                    status='completed'
                ).count()

                return {
                    'participant_id': participant.id,
                    'user_id': participant.telegram_id,
                    'username': participant.username,
                    'full_name': f"{participant.first_name} {participant.last_name}".strip(),
                    'referral_code': participant.referral_code,
                    'current_points': participant.current_points,
                    'referral_count': referral_count,
                    'premium_referral_count': premium_count,
                    'joined_at': participant.joined_at.isoformat() if participant.joined_at else None,
                    'last_active': participant.updated_at.isoformat() if participant.updated_at else None
                }
            except Exception as e:
                logger.error(f"Get participant stats error: {e}")
                return {}

        return await _get_stats()

    async def bulk_create_participants(self, participants_data: List[Dict[str, Any]], bot_id: int) -> List[Participant]:
        """Bulk create participants (for batch processing)"""

        @sync_to_async
        @transaction.atomic
        def _bulk_create():
            try:
                participants_to_create = []
                existing_telegram_ids = set()

                # Get existing participants
                telegram_ids = [p.get('telegram_id') for p in participants_data if p.get('telegram_id')]
                if telegram_ids:
                    existing_participants = Participant.objects.filter(telegram_id__in=telegram_ids, competition__bot_id=bot_id)
                    existing_telegram_ids = set(existing_participants.values_list('telegram_id', flat=True))

                # Prepare new participants
                bot = BotSetUp.objects.get(id=bot_id, is_active=True)
                competition = Competition.objects.get(bot=bot, status=COMPETITION_STATUSES['ACTIVE'])
                now = timezone.now()
                for p_data in participants_data:
                    telegram_id = p_data.get('telegram_id')
                    if not telegram_id or telegram_id in existing_telegram_ids:
                        continue

                    participant = Participant(
                        telegram_id=telegram_id,
                        username=(p_data.get('username') or '')[:64],
                        first_name=(p_data.get('first_name') or '')[:64],
                        last_name=(p_data.get('last_name') or '')[:64],
                        phone_number=p_data.get('phone_number'),
                        language_code=p_data.get('language_code', 'uz'),
                        is_premium=p_data.get('is_premium', False),
                        is_bot=p_data.get('is_bot', False),
                        competition=competition,
                        referral_code=self._generate_unique_referral_code(competition.id),
                        current_points=0,
                        is_participant=True,
                        joined_at=now
                    )
                    participants_to_create.append(participant)

                # Bulk create
                if participants_to_create:
                    created_participants = Participant.objects.bulk_create(participants_to_create)
                    logger.info(f"Bulk created {len(created_participants)} participants")
                    return created_participants

                return []

            except Exception as e:
                logger.error(f"Bulk create participants error: {e}", exc_info=True)
                return []

        return await _bulk_create()