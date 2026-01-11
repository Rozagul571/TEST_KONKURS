# bots/user_bots/base_template/services/user_service.py
"""
Optimized user service with bulk operations
Vazifasi: Participant va User operatsiyalari
"""
import logging
import secrets
import string
from typing import Dict, Any, Optional, List, Tuple
from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from django_app.core.models import Participant, Competition, BotSetUp, Referral, User
from shared.utils import generate_referral_code
from shared.constants import COMPETITION_STATUSES

logger = logging.getLogger(__name__)


class UserService:
    """High-performance user service"""

    def __init__(self):
        self._batch_size = 100

    async def get_participant_by_user_id(self, user_id: int, bot_id: int) -> Optional[Participant]:
        """
        User ID bo'yicha participant olish

        Args:
            user_id: Telegram user ID
            bot_id: Bot ID

        Returns:
            Participant yoki None
        """

        @sync_to_async
        def _get_participant():
            try:
                return Participant.objects.select_related('user', 'competition').get(
                    user__telegram_id=user_id,
                    competition__bot_id=bot_id,
                    is_participant=True
                )
            except Participant.DoesNotExist:
                return None
            except Exception as e:
                logger.error(f"Get participant by user id error: {e}")
                return None

        return await _get_participant()

    async def get_participant_by_code(self, code: str, bot_id: int) -> Optional[Participant]:
        """
        Referral kod bo'yicha participant olish

        Args:
            code: Referral kod
            bot_id: Bot ID

        Returns:
            Participant yoki None
        """

        @sync_to_async
        def _get_participant():
            try:
                return Participant.objects.select_related('user', 'competition').get(
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

    async def get_or_create_participant(self, user_data: Dict[str, Any], bot_id: int) -> Tuple[
        Optional[Participant], bool]:
        """
        Participant olish yoki yaratish

        Args:
            user_data: User ma'lumotlari
            bot_id: Bot ID

        Returns:
            Tuple (Participant, created)
        """

        @sync_to_async
        @transaction.atomic
        def _create_participant():
            try:
                telegram_id = user_data.get('telegram_id')
                if not telegram_id:
                    raise ValueError("telegram_id is required")

                # User olish/yaratish
                user, user_created = User.objects.get_or_create(
                    telegram_id=telegram_id,
                    defaults={
                        'username': (user_data.get('username') or '')[:255],
                        'first_name': (user_data.get('first_name') or '')[:64],
                        'last_name': (user_data.get('last_name') or '')[:64],
                        'is_premium': user_data.get('is_premium', False),
                    }
                )

                # Bot va Competition olish
                bot = BotSetUp.objects.get(id=bot_id, is_active=True)
                competition = Competition.objects.get(bot=bot)

                # Participant tekshirish
                participant = Participant.objects.filter(user=user, competition=competition).first()

                if participant:
                    # Mavjud - yangilash kerak bo'lsa
                    return participant, False

                # Yangi yaratish
                referral_code = self._generate_unique_code(competition.id)
                participant = Participant.objects.create(
                    user=user,
                    competition=competition,
                    referral_code=referral_code,
                    current_points=0,
                    is_participant=True
                )

                logger.info(f"Participant created: {telegram_id}")
                return participant, True

            except Exception as e:
                logger.error(f"Create participant error: {e}", exc_info=True)
                return None, False

        return await _create_participant()

    def _generate_unique_code(self, competition_id: int, length: int = 8) -> str:
        """Unikal referral kod generatsiya qilish"""
        max_attempts = 10
        for _ in range(max_attempts):
            code = generate_referral_code(length)
            exists = Participant.objects.filter(competition_id=competition_id, referral_code=code).exists()
            if not exists:
                return code
        # Fallback
        return f"ref{int(timezone.now().timestamp()) % 1000000}"

    async def create_referral(self, referrer: Participant, referred: Participant) -> Optional[Referral]:
        """
        Referral yaratish

        Args:
            referrer: Taklif qilgan
            referred: Taklif qilingan

        Returns:
            Referral yoki None
        """

        @sync_to_async
        @transaction.atomic
        def _create_referral():
            try:
                # Mavjud bo'lsa olish
                existing = Referral.objects.filter(
                    referrer=referrer.user,
                    referred=referred.user,
                    competition=referrer.competition
                ).first()

                if existing:
                    return existing

                # Yangi yaratish
                referral = Referral.objects.create(
                    referrer=referrer.user,
                    referred=referred.user,
                    competition=referrer.competition
                )

                return referral

            except Exception as e:
                logger.error(f"Create referral error: {e}")
                return None

        return await _create_referral()

    async def get_user_referrals(self, user_id: int, bot_id: int) -> List[Dict[str, Any]]:
        """Foydalanuvchi referrallarini olish"""

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
                        'created_at': ref.created_at.isoformat()
                    })
                return result

            except Exception as e:
                logger.error(f"Get referrals error: {e}")
                return []

        return await _get_referrals()

    async def get_participant_stats(self, participant_id: int) -> Dict[str, Any]:
        """Participant statistikasini olish"""

        @sync_to_async
        def _get_stats():
            try:
                participant = Participant.objects.select_related('user').get(id=participant_id)

                # Referral count
                referral_count = Referral.objects.filter(referrer=participant.user,
                                                         competition=participant.competition).count()

                return {
                    'participant_id': participant.id,
                    'user_id': participant.user.telegram_id,
                    'username': participant.user.username,
                    'full_name': participant.full_name,
                    'referral_code': participant.referral_code,
                    'current_points': participant.current_points,
                    'referral_count': referral_count,
                    'created_at': participant.created_at.isoformat() if participant.created_at else None
                }

            except Exception as e:
                logger.error(f"Get participant stats error: {e}")
                return {}

        return await _get_stats()