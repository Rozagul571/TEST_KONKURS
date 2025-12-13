# bots/user_bots/base_template/services/user_service.py
from asgiref.sync import sync_to_async
import secrets
import string

from pydantic import json

from django_app.core.models import User, Participant, Competition, Referral
from fastapi_app.cache import redis_client as redis

class UserService:
    """
    Purpose: Manages user/participant data and referrals.
    What it does: Creates users/participants, generates referral codes, handles anti-cheat.
    Why: Supports participant onboarding and referral system, TZ Step 3.
    """
    async def get_or_create_user(self, user_data: dict):
        """Creates or updates a user in the DB."""
        user, created = await sync_to_async(User.objects.get_or_create)(
            telegram_id=user_data['telegram_id'],
            defaults={
                "username": user_data['username'],
                "full_name": user_data['full_name'] or "",
                "is_premium": user_data.get('is_premium', False)
            }
        )
        if not created:
            user.username = user_data['username']
            user.full_name = user_data['full_name'] or ""
            user.is_premium = user_data.get('is_premium', False)
            await sync_to_async(user.save)()
        return user

    async def get_or_create_user_from_message(self, message: dict, competition_id: int):
        """Extracts user data from message and creates user."""
        user_data = {
            'telegram_id': message['from']['id'],
            'username': message['from']['username'] or "",
            'full_name': message['from']['first_name'] or "",
            'is_premium': message['from'].get('is_premium', False)
        }
        return await self.get_or_create_user(user_data)

    async def get_or_create_participant(self, user, competition_id):
        """Creates or gets a participant with a unique referral code."""
        competition = await sync_to_async(Competition.objects.get)(id=competition_id)
        participant, created = await sync_to_async(Participant.objects.get_or_create)(
            user=user,
            competition=competition,
            defaults={'referral_code': self.generate_referral_code()}
        )
        return participant

    def generate_referral_code(self, length=8):
        """Generates a unique referral code."""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

    async def save_referral(self, bot_id: int, user_id: int, ref_code: str):
        """Saves a referral to Redis for batch processing."""
        referrer = await self.get_participant_by_code(ref_code, bot_id)
        if referrer:
            referral_data = {
                'referrer': referrer.user.id,
                'referred': user_id,
                'competition': bot_id
            }
            await redis.lpush(f"referrals:{bot_id}", json.dumps(referral_data))

    async def get_participant_by_code(self, code: str, bot_id: int):
        """Fetches a participant by referral code."""
        return await sync_to_async(Participant.objects.get)(
            referral_code=code, competition_id=bot_id
        )

    async def get_referral_code(self, user_id: int):
        """Gets or generates a unique referral code for a user."""
        code = await redis.get(f"user_referral:{user_id}")
        if code:
            return code.decode()
        code = self.generate_referral_code()
        await redis.set(f"user_referral:{user_id}", code)
        return code

    async def anti_cheat_rate_limit(self, bot_id: int, user_id: int, action: str, limit_sec: int = 5):
        """Implements rate limiting to prevent abuse."""
        key = f"limit:{bot_id}:{user_id}:{action}"
        if await redis.exists(key):
            return True  # Rate limit hit
        await redis.set(key, 1, ex=limit_sec)
        return False