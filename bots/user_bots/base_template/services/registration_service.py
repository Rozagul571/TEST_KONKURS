# bots/user_bots/base_template/services/registration_service.py
"""
Registration Service - Foydalanuvchini ro'yxatdan o'tkazish
MUHIM: User faqat barcha kanallarga qo'shilgandan keyin DB ga yoziladi
"""
import logging
from typing import Dict, Any, Optional
from asgiref.sync import sync_to_async
from django.db import transaction

logger = logging.getLogger(__name__)


class RegistrationService:
    """Ro'yxatdan o'tkazish service"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def register_user(
            self,
            user_data: Dict[str, Any],
            referral_code: Optional[str],
            settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Foydalanuvchini ro'yxatdan o'tkazish

        Args:
            user_data: telegram_id, username, first_name, last_name, is_premium
            referral_code: Referrer kodi (agar mavjud bo'lsa)
            settings: Competition settings

        Returns:
            {
                success: bool,
                participant: Participant,
                channel_points: int,
                referral_bonus: int,
                already_registered: bool
            }
        """
        try:
            return await self._register_atomic(user_data, referral_code, settings)
        except Exception as e:
            logger.error(f"Registration error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @sync_to_async
    @transaction.atomic
    def _register_atomic(
            self,
            user_data: Dict[str, Any],
            referral_code: Optional[str],
            settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atomic transaction ichida ro'yxatdan o'tkazish"""
        from django_app.core.models import User, Participant, Competition, Referral, Point
        from django_app.core.models.pointrule import PointAction
        import secrets
        import string

        telegram_id = user_data.get("telegram_id")

        # Competition olish
        try:
            competition = Competition.objects.get(bot_id=self.bot_id)
        except Competition.DoesNotExist:
            logger.error(f"Competition not found for bot {self.bot_id}")
            return {"success": False, "error": "Competition not found"}

        # User olish yoki yaratish
        user, user_created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": user_data.get("username", "")[:255],
                "first_name": user_data.get("first_name", "")[:64],
                "last_name": user_data.get("last_name", "")[:64],
                "is_premium": user_data.get("is_premium", False)
            }
        )

        # User mavjud bo'lsa yangilash
        if not user_created:
            user.username = user_data.get("username", "") or user.username
            user.first_name = user_data.get("first_name", "") or user.first_name
            user.last_name = user_data.get("last_name", "") or user.last_name
            user.is_premium = user_data.get("is_premium", False)
            user.save()

        # Participant mavjudmi tekshirish
        existing = Participant.objects.filter(user=user, competition=competition).first()
        if existing and existing.is_participant:
            return {
                "success": True,
                "participant": existing,
                "already_registered": True,
                "channel_points": 0,
                "referral_bonus": 0
            }

        # Yangi referral kod yaratish
        def generate_code(length=8):
            alphabet = string.ascii_letters + string.digits
            return ''.join(secrets.choice(alphabet) for _ in range(length))

        new_referral_code = generate_code()
        while Participant.objects.filter(competition=competition, referral_code=new_referral_code).exists():
            new_referral_code = generate_code()

        # Participant yaratish
        participant = Participant.objects.create(
            user=user,
            competition=competition,
            referral_code=new_referral_code,
            current_points=0,
            is_participant=True
        )

        # Point rules
        point_rules = settings.get("point_rules", {})
        channel_points_per = point_rules.get("channel_join", 1)
        referral_points = point_rules.get("referral", 5)
        premium_referral_points = point_rules.get("premium_referral", 10)

        total_points = 0
        channel_points_earned = 0
        referral_bonus = 0

        # 1. KANAL BALLARI
        channels = settings.get("channels", [])
        if channels:
            channel_points_earned = len(channels) * channel_points_per
            total_points += channel_points_earned

            # Point yozuvi
            Point.objects.create(
                participant=participant,
                earned_points=channel_points_earned,
                reason=PointAction.CHANNEL_JOIN,
                description=f"{len(channels)} kanal uchun"
            )

        # 2. REFERRAL BALL (taklif qilingan odamga bonus)
        # Premium user bo'lsa ko'proq ball
        if user.is_premium:
            referral_bonus = premium_referral_points
        else:
            referral_bonus = referral_points

        # Referral bonus - o'ziga
        # (Ixtiyoriy - taklif qilingan odamga ham ball berish)
        # total_points += referral_bonus
        # Point.objects.create(
        #     participant=participant,
        #     earned_points=referral_bonus,
        #     reason=PointAction.REFERRAL,
        #     description="Taklif orqali kirdi"
        # )

        # 3. REFERRER GA BALL (taklif qilgan odamga)
        if referral_code:
            referrer = Participant.objects.filter(
                competition=competition,
                referral_code=referral_code,
                is_participant=True
            ).first()

            if referrer and referrer.user.telegram_id != telegram_id:
                # Referral yaratish
                Referral.objects.get_or_create(
                    referrer=referrer.user,
                    referred=user,
                    competition=competition
                )

                # Referrer ga ball
                points_for_referrer = premium_referral_points if user.is_premium else referral_points

                referrer.current_points += points_for_referrer
                referrer.save()

                Point.objects.create(
                    participant=referrer,
                    earned_points=points_for_referrer,
                    reason=PointAction.REFERRAL,
                    description=f"@{user.username or telegram_id} ni taklif qildi"
                )

                logger.info(
                    f"Referrer {referrer.user.telegram_id} got +{points_for_referrer} points for referring {telegram_id}")

        # Participant ballarini yangilash
        participant.current_points = total_points
        participant.save()

        logger.info(f"User {telegram_id} registered with {total_points} points")

        return {
            "success": True,
            "participant": participant,
            "channel_points": channel_points_earned,
            "referral_bonus": referral_bonus,
            "already_registered": False
        }


# # bots/user_bots/base_template/services/registration_service.py
# """
# Registration Service - Foydalanuvchini ro'yxatdan o'tkazish
# MUHIM: User faqat barcha kanallarga qo'shilgandan keyin DB ga yoziladi
# """
# import logging
# from typing import Dict, Any, Optional
# from asgiref.sync import sync_to_async
# from django.db import transaction
#
# logger = logging.getLogger(__name__)
#
#
# class RegistrationService:
#     """Ro'yxatdan o'tkazish service"""
#
#     def __init__(self, bot_id: int):
#         self.bot_id = bot_id
#
#     async def register_user(
#             self,
#             user_data: Dict[str, Any],
#             referral_code: Optional[str],
#             settings: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """
#         Foydalanuvchini ro'yxatdan o'tkazish
#
#         Args:
#             user_data: telegram_id, username, first_name, last_name, is_premium
#             referral_code: Referrer kodi (agar mavjud bo'lsa)
#             settings: Competition settings
#
#         Returns:
#             {
#                 success: bool,
#                 participant: Participant,
#                 channel_points: int,
#                 referral_bonus: int,
#                 already_registered: bool
#             }
#         """
#         try:
#             return await self._register_atomic(user_data, referral_code, settings)
#         except Exception as e:
#             logger.error(f"Registration error: {e}", exc_info=True)
#             return {"success": False, "error": str(e)}
#
#     @sync_to_async
#     @transaction.atomic
#     def _register_atomic(
#             self,
#             user_data: Dict[str, Any],
#             referral_code: Optional[str],
#             settings: Dict[str, Any]
#     ) -> Dict[str, Any]:
#         """Atomic transaction ichida ro'yxatdan o'tkazish"""
#         from django_app.core.models import User, Participant, Competition, Referral, Point
#         from django_app.core.models.pointrule import PointAction
#         import secrets
#         import string
#
#         telegram_id = user_data.get("telegram_id")
#
#         # Competition olish
#         try:
#             competition = Competition.objects.get(bot_id=self.bot_id)
#         except Competition.DoesNotExist:
#             logger.error(f"Competition not found for bot {self.bot_id}")
#             return {"success": False, "error": "Competition not found"}
#
#         # User olish yoki yaratish
#         user, user_created = User.objects.get_or_create(
#             telegram_id=telegram_id,
#             defaults={
#                 "username": user_data.get("username", "")[:255],
#                 "first_name": user_data.get("first_name", "")[:64],
#                 "last_name": user_data.get("last_name", "")[:64],
#                 "is_premium": user_data.get("is_premium", False)
#             }
#         )
#
#         # User mavjud bo'lsa yangilash
#         if not user_created:
#             user.username = user_data.get("username", "") or user.username
#             user.first_name = user_data.get("first_name", "") or user.first_name
#             user.last_name = user_data.get("last_name", "") or user.last_name
#             user.is_premium = user_data.get("is_premium", False)
#             user.save()
#
#         # Participant mavjudmi tekshirish
#         existing = Participant.objects.filter(user=user, competition=competition).first()
#         if existing and existing.is_participant:
#             return {
#                 "success": True,
#                 "participant": existing,
#                 "already_registered": True,
#                 "channel_points": 0,
#                 "referral_bonus": 0
#             }
#
#         # Yangi referral kod yaratish
#         def generate_code(length=8):
#             alphabet = string.ascii_letters + string.digits
#             return ''.join(secrets.choice(alphabet) for _ in range(length))
#
#         new_referral_code = generate_code()
#         while Participant.objects.filter(competition=competition, referral_code=new_referral_code).exists():
#             new_referral_code = generate_code()
#
#         # Participant yaratish
#         participant = Participant.objects.create(
#             user=user,
#             competition=competition,
#             referral_code=new_referral_code,
#             current_points=0,
#             is_participant=True
#         )
#
#         # Point rules
#         point_rules = settings.get("point_rules", {})
#         channel_points_per = point_rules.get("channel_join", 1)
#         referral_points = point_rules.get("referral", 5)
#         premium_referral_points = point_rules.get("premium_referral", 10)
#
#         total_points = 0
#         channel_points_earned = 0
#         referral_bonus = 0
#
#         # 1. KANAL BALLARI
#         channels = settings.get("channels", [])
#         if channels:
#             channel_points_earned = len(channels) * channel_points_per
#             total_points += channel_points_earned
#
#             # Point yozuvi
#             Point.objects.create(
#                 participant=participant,
#                 earned_points=channel_points_earned,
#                 reason=PointAction.CHANNEL_JOIN,
#                 description=f"{len(channels)} kanal uchun"
#             )
#
#         # 2. REFERRAL BALL (taklif qilingan odamga bonus)
#         # Premium user bo'lsa ko'proq ball
#         if user.is_premium:
#             referral_bonus = premium_referral_points
#         else:
#             referral_bonus = referral_points
#
#         # Referral bonus - o'ziga
#         # (Ixtiyoriy - taklif qilingan odamga ham ball berish)
#         # total_points += referral_bonus
#         # Point.objects.create(
#         #     participant=participant,
#         #     earned_points=referral_bonus,
#         #     reason=PointAction.REFERRAL,
#         #     description="Taklif orqali kirdi"
#         # )
#
#         # 3. REFERRER GA BALL (taklif qilgan odamga)
#         if referral_code:
#             referrer = Participant.objects.filter(
#                 competition=competition,
#                 referral_code=referral_code,
#                 is_participant=True
#             ).first()
#
#             if referrer and referrer.user.telegram_id != telegram_id:
#                 # Referral yaratish
#                 Referral.objects.get_or_create(
#                     referrer=referrer.user,
#                     referred=user,
#                     competition=competition
#                 )
#
#                 # Referrer ga ball
#                 points_for_referrer = premium_referral_points if user.is_premium else referral_points
#
#                 referrer.current_points += points_for_referrer
#                 referrer.save()
#
#                 Point.objects.create(
#                     participant=referrer,
#                     earned_points=points_for_referrer,
#                     reason=PointAction.REFERRAL,
#                     description=f"@{user.username or telegram_id} ni taklif qildi"
#                 )
#
#                 logger.info(
#                     f"Referrer {referrer.user.telegram_id} got +{points_for_referrer} points for referring {telegram_id}")
#
#         # Participant ballarini yangilash
#         participant.current_points = total_points
#         participant.save()
#
#         logger.info(f"User {telegram_id} registered with {total_points} points")
#
#         return {
#             "success": True,
#             "participant": participant,
#             "channel_points": channel_points_earned,
#             "referral_bonus": referral_bonus,
#             "already_registered": False
#         }