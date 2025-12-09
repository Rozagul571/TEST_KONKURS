# bots/user_bots/base_template/services/user_service.py
from asgiref.sync import sync_to_async
import secrets
import string
from django_app.core.models.user import User
from django_app.core.models.participant import Participant
from django_app.core.models.competition import Competition
from django_app.core.models.referral import Referral

class UserService:
    """User servisi. Vazifasi: User va participant yaratish. Misol: get_or_create_participant - referral code beradi."""
    @sync_to_async
    def get_or_create_user(self, user_data: dict):
        user, created = User.objects.get_or_create(
            telegram_id=user_data['telegram_id'],
            defaults={
                "username": user_data['username'],
                "full_name": user_data['first_name'] or "",
                "is_premium": user_data.get('is_premium', False)
            }
        )
        if not created:
            user.username = user_data['username']
            user.full_name = user_data['first_name'] or ""
            user.is_premium = user_data.get('is_premium', False)
            user.save()
        return user

    async def get_or_create_user_from_message(self, message, competition: dict):
        user_data = {
            'telegram_id': message.from_user.id,
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'is_premium': getattr(message.from_user, 'is_premium', False)
        }
        return await self.get_or_create_user(user_data)

    @sync_to_async
    def get_or_create_participant(self, user, competition_data):
        competition = Competition.objects.get(id=competition_data['id'])
        participant, created = Participant.objects.get_or_create(
            user=user,
            competition=competition,
            defaults={'referral_code': self.generate_referral_code()}
        )
        return participant

    def generate_referral_code(self, length=8):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @sync_to_async
    def check_referral(self, referral_code: str, competition_data):
        return Participant.objects.filter(referral_code=referral_code, competition_id=competition_data['id']).first()

    @sync_to_async
    def create_referral(self, referrer, referred, competition_data):
        competition = Competition.objects.get(id=competition_data['id'])
        referral, created = Referral.objects.get_or_create(
            referrer=referrer.user,
            referred=referred.user,
            competition=competition
        )
        return referral