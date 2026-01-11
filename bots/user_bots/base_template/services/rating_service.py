# bots/user_bots/base_template/services/rating_service.py
"""
Rating Service - TOP 10 reyting
USERNAME VA PROFIL LINK BILAN
"""
import logging
from typing import Dict, Any, Optional, List
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class RatingService:
    """Rating service"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def get_rating_text(self, user_id: int) -> str:
        """Reyting textini olish - HTML format"""
        try:
            top_10 = await self._get_top_10()
            user_rank = await self._get_user_rank(user_id)

            return self._format_rating(top_10, user_rank, user_id)
        except Exception as e:
            logger.error(f"Get rating error: {e}")
            return "🏆 Reyting yuklanmadi. Keyinroq urinib ko'ring."

    @sync_to_async
    def _get_top_10(self) -> List[Dict]:
        """TOP 10 ni olish"""
        try:
            from django_app.core.models import Participant

            participants = Participant.objects.filter(
                competition__bot_id=self.bot_id,
                is_participant=True
            ).select_related('user').order_by('-current_points')[:10]

            result = []
            for i, p in enumerate(participants, 1):
                result.append({
                    'rank': i,
                    'telegram_id': p.user.telegram_id,
                    'username': p.user.username or '',
                    'first_name': p.user.first_name or '',
                    'last_name': p.user.last_name or '',
                    'points': p.current_points
                })

            return result
        except Exception as e:
            logger.error(f"Get top 10 error: {e}")
            return []

    @sync_to_async
    def _get_user_rank(self, user_id: int) -> Optional[Dict]:
        """User rankini olish"""
        try:
            from django_app.core.models import Participant

            participant = Participant.objects.filter(
                competition__bot_id=self.bot_id,
                user__telegram_id=user_id,
                is_participant=True
            ).first()

            if not participant:
                return None

            higher_count = Participant.objects.filter(
                competition__bot_id=self.bot_id,
                is_participant=True,
                current_points__gt=participant.current_points
            ).count()

            return {
                'rank': higher_count + 1,
                'points': participant.current_points
            }
        except Exception as e:
            logger.error(f"Get user rank error: {e}")
            return None

    def _format_rating(self, top_10: List[Dict], user_rank: Optional[Dict], user_id: int) -> str:
        """
        Reytingni formatlash - HTML FORMAT

        Username bo'lsa: Ism (@username) - clickable link
        Username yo'q bo'lsa: Ism (tg://user?id=123456) - profil link
        """
        if not top_10:
            return "🏆 <b>TOP 10 Reyting</b>\n\nHozircha hech kim ball to'plamagan.\n🚀 Birinchi bo'ling!"

        emojis = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"}

        text = "🏆 <b>TOP 10 Reyting</b> 🏆\n\n"

        for p in top_10:
            rank = p['rank']
            emoji = emojis.get(rank, f"{rank}.")

            # Ism yaratish
            first_name = p['first_name'] or ''
            last_name = p['last_name'] or ''
            full_name = f"{first_name} {last_name}".strip()

            if not full_name:
                full_name = "Foydalanuvchi"

            # Link yaratish
            username = p['username']
            telegram_id = p['telegram_id']

            if username:
                # Username bor - @username formatda link
                display_name = f'<a href="https://t.me/{username}">{full_name}</a> (@{username})'
            else:
                # Username yo'q - tg://user?id=XXX formatda link
                display_name = f'<a href="tg://user?id={telegram_id}">{full_name}</a>'

            text += f"{emoji} <b>{rank}-o'rin:</b> {display_name} - {p['points']:,} ball\n"

        text += "\n" + "─" * 25 + "\n"

        if user_rank:
            if user_rank['rank'] <= 10:
                text += f"✨ Siz <b>{user_rank['rank']}-o'rindasiz</b> ({user_rank['points']:,} ball)"
            else:
                text += f"📊 Sizning o'rningiz: <b>{user_rank['rank']}</b> ({user_rank['points']:,} ball)"
        else:
            text += "❌ Siz hali ro'yxatdan o'tmagan"

        return text

# # bots/user_bots/base_template/services/rating_service.py
# """
# Rating service - TOP 10 ni tez ko'rsatish (OPTIMIZED)
# Vazifasi: Reyting ma'lumotlarini olish va cache qilish
# """
# import logging
# import asyncio
# from typing import List, Dict, Any
# from asgiref.sync import sync_to_async
# from django.db.models import F, Window
# from django.db.models.functions import RowNumber
#
# from django_app.core.models import Participant
# from shared.redis_client import redis_client
# from shared.utils import get_prize_emoji, format_points
# from shared.constants import MESSAGES, CACHE_KEYS, CACHE_TTL
#
# logger = logging.getLogger(__name__)
#
#
# class RatingService:
#     """High-performance rating service with caching"""
#
#     def __init__(self, bot_id: int):
#         self.bot_id = bot_id
#         self.cache_ttl = CACHE_TTL.get('rating', 30)
#
#     async def get_rating_text(self, user_id: int) -> str:
#         """
#         Optimized rating text generator with caching
#
#         Args:
#             user_id: Telegram user ID
#
#         Returns:
#             Formatlangan rating text
#         """
#         try:
#             # Cache tekshirish
#             if redis_client.is_connected():
#                 cached = await redis_client.get_user_state(self.bot_id, user_id)
#                 if cached and 'rating' in cached:
#                     logger.debug(f"Cache hit for rating: bot={self.bot_id}, user={user_id}")
#                     return cached['rating']
#
#             # Generate rating
#             rating_text = await self._generate_rating_text(user_id)
#
#             # Cache saqlash
#             if redis_client.is_connected() and rating_text:
#                 current_state = await redis_client.get_user_state(self.bot_id, user_id) or {}
#                 current_state['rating'] = rating_text
#                 await redis_client.set_user_state(self.bot_id, user_id, current_state, self.cache_ttl)
#
#             return rating_text
#
#         except Exception as e:
#             logger.error(f"Get rating text error: {e}")
#             return self._get_default_rating()
#
#     async def _generate_rating_text(self, user_id: int) -> str:
#         """Rating text generatsiya qilish"""
#         try:
#             # Parallel olish
#             top_10, user_rank = await asyncio.gather(
#                 self._get_top_10(),
#                 self._get_user_rank(user_id)
#             )
#
#             return self._format_rating(top_10, user_rank, user_id)
#
#         except Exception as e:
#             logger.error(f"Generate rating error: {e}")
#             return self._get_default_rating()
#
#     async def _get_top_10(self) -> List[Dict]:
#         """TOP 10 ni olish (optimized)"""
#
#         @sync_to_async
#         def _get_top():
#             try:
#                 participants = Participant.objects.filter(
#                     competition__bot_id=self.bot_id,
#                     is_participant=True
#                 ).select_related('user').annotate(
#                     rank=Window(
#                         expression=RowNumber(),
#                         order_by=F('current_points').desc()
#                     )
#                 ).values(
#                     'rank',
#                     'user__telegram_id',
#                     'user__username',
#                     'user__first_name',
#                     'user__last_name',
#                     'current_points'
#                 ).order_by('rank')[:10]
#
#                 return list(participants)
#
#             except Exception as e:
#                 logger.error(f"Get top 10 error: {e}")
#                 return []
#
#         return await _get_top()
#
#     async def _get_user_rank(self, user_id: int) -> Dict[str, Any]:
#         """Foydalanuvchi o'rnini olish"""
#
#         @sync_to_async
#         def _get_rank():
#             try:
#                 participant = Participant.objects.filter(
#                     competition__bot_id=self.bot_id,
#                     user__telegram_id=user_id,
#                     is_participant=True
#                 ).select_related('user').first()
#
#                 if not participant:
#                     return {'rank': None, 'points': 0, 'participant': None}
#
#                 # Count higher
#                 higher_count = Participant.objects.filter(
#                     competition__bot_id=self.bot_id,
#                     is_participant=True,
#                     current_points__gt=participant.current_points
#                 ).count()
#
#                 return {
#                     'rank': higher_count + 1,
#                     'points': participant.current_points,
#                     'participant': participant
#                 }
#
#             except Exception as e:
#                 logger.error(f"Get user rank error: {e}")
#                 return {'rank': None, 'points': 0, 'participant': None}
#
#         return await _get_rank()
#
#     def _format_rating(self, top_10: List[Dict], user_rank: Dict, user_id: int) -> str:
#         """Rating textini formatlash"""
#         if not top_10:
#             return MESSAGES['rating_empty']
#
#         text = MESSAGES['rating_header']
#
#         # TOP 10
#         for participant in top_10:
#             rank = participant['rank']
#             first_name = participant['user__first_name'] or ''
#             last_name = participant['user__last_name'] or ''
#             username = participant['user__username'] or ''
#             points = participant['current_points']
#
#             emoji = get_prize_emoji(rank)
#
#             # Display name
#             full_name = f"{first_name} {last_name}".strip() or 'Foydalanuvchi'
#             if username:
#                 display_name = f"{full_name} @{username}"
#             else:
#                 display_name = full_name
#
#             text += f"{emoji} *{rank}-o'rin:* {display_name} - {format_points(points)} ball\n"
#
#         text += "\n" + "─" * 30 + "\n"
#
#         # User rank
#         if user_rank['rank']:
#             if user_rank['rank'] <= 10:
#                 text += MESSAGES['rating_user_in_top'].format(rank=user_rank['rank'],
#                                                               points=format_points(user_rank['points']))
#             else:
#                 text += MESSAGES['rating_user_not_in_top'].format(rank=user_rank['rank'],
#                                                                   points=format_points(user_rank['points']))
#
#                 # TOP 10 ga kerakli ball
#                 if top_10 and len(top_10) >= 10:
#                     points_needed = top_10[9]['current_points'] - user_rank['points']
#                     if points_needed > 0:
#                         text += MESSAGES['rating_points_needed'].format(points=format_points(points_needed))
#         else:
#             text += MESSAGES['rating_not_registered']
#
#         # Total participants
#         try:
#             @sync_to_async
#             def _get_total():
#                 return Participant.objects.filter(
#                     competition__bot_id=self.bot_id,
#                     is_participant=True
#                 ).count()
#
#             # Note: Bu sync chaqiriladi chunki biz allaqachon async context ichidamiz
#             # Lekin bu yerda total olish uchun alohida query kerak emas
#             # top_10 dan ham olsa bo'ladi
#         except:
#             pass
#
#         text += MESSAGES['rating_motivation']
#
#         return text
#
#     def _get_default_rating(self) -> str:
#         """Default rating text"""
#         return "🏆 *TOP 10 Reyting*\n\nXatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
#
#     async def update_cache(self, user_id: int):
#         """Cache ni yangilash"""
#         try:
#             if redis_client.is_connected():
#                 # Clear old cache
#                 current_state = await redis_client.get_user_state(self.bot_id, user_id) or {}
#                 if 'rating' in current_state:
#                     del current_state['rating']
#                     await redis_client.set_user_state(self.bot_id, user_id, current_state, self.cache_ttl)
#
#             logger.info(f"Rating cache cleared for user {user_id}")
#
#         except Exception as e:
#             logger.error(f"Update rating cache error: {e}")