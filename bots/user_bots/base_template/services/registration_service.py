# bots/user_bots/services/registration_service.py
"""
Registration service - Transaction bilan ishlaydi
"""

import logging
from typing import Dict, Any, Optional
from asgiref.sync import sync_to_async
from django.db import transaction

from django_app.core.models import User, Participant, Competition, BotSetUp

logger = logging.getLogger(__name__)


class RegistrationService:
    """Optimized registration service"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def register_user(self, user_data: Dict, referrer=None) -> Optional[Participant]:
        """User ni ro'yxatdan o'tkazish (transaction bilan)"""
        try:
            return await self._register_with_transaction(user_data, referrer)
        except Exception as e:
            logger.error(f"Register user error: {e}")
            return None

    @sync_to_async
    @transaction.atomic
    def _register_with_transaction(self, user_data: Dict, referrer) -> Participant:
        """Transaction bilan ro'yxatdan o'tkazish"""
        try:
            # 1. Get or create user
            user, created = User.objects.get_or_create(
                telegram_id=user_data['telegram_id'],
                defaults={
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'full_name': user_data['full_name'],
                    'language_code': user_data['language_code'],
                    'is_premium': user_data['is_premium'],
                    'is_bot': user_data['is_bot']
                }
            )

            # Update user if exists
            if not created:
                user.username = user_data['username']
                user.full_name = user_data['full_name']
                user.is_premium = user_data['is_premium']
                user.save(update_fields=['username', 'full_name', 'is_premium'])

            # 2. Get competition
            bot = BotSetUp.objects.get(id=self.bot_id, is_active=True)
            competition = Competition.objects.get(bot=bot)

            # 3. Create participant
            participant, p_created = Participant.objects.get_or_create(
                user=user,
                competition=competition,
                defaults={
                    'referral_code': self._generate_referral_code(),
                    'current_points': 0,
                    'is_participant': True
                }
            )

            # 4. If referred, create referral record
            if referrer:
                from django_app.core.models import Referral
                Referral.objects.create(
                    referrer=referrer,
                    referred=participant,
                    is_premium=user.is_premium
                )

            logger.info(f"✅ User registered: {user.telegram_id} for bot {self.bot_id}")
            return participant

        except Exception as e:
            logger.error(f"Registration transaction error: {e}")
            raise

    def _generate_referral_code(self, length: int = 8) -> str:
        """Generate unique referral code"""
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))