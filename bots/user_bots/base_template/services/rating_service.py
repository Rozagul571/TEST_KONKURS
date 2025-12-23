#bots/user_bots/base_template/services/rating_service.py
"""
Rating service - TOP 10 ni tez ko'rsatish (OPTIMIZED)
Redis cache + Window functions
"""

import logging
import json
from typing import List, Dict, Any
from asgiref.sync import sync_to_async
from django.utils import asyncio

from shared.redis_client import redis_client
from shared.utils import get_prize_emoji, format_points
from shared.constants import CACHE_KEYS

logger = logging.getLogger(__name__)


class RatingService:
    """High-performance rating service with caching"""

    def __init__(self, competition_id: int):
        self.competition_id = competition_id
        self.cache_ttl = 30  # 30 seconds

    async def get_rating_text(self, user_id: int) -> str:
        """Optimized rating text generator with caching"""
        try:
            # Check cache first
            cache_key = CACHE_KEYS['rating_cache'].format(self.competition_id, user_id)

            if redis_client.is_connected():
                cached = await redis_client.get_user_state(self.competition_id, user_id)
                if cached and 'rating' in cached:
                    logger.debug(f"Cache hit for rating: bot={self.competition_id}, user={user_id}")
                    return cached['rating']

            # Generate rating
            rating_text = await self._generate_rating_text(user_id)

            # Cache result
            if redis_client.is_connected() and rating_text:
                await redis_client.set_user_state(
                    self.competition_id, user_id,
                    {'rating': rating_text},
                    self.cache_ttl
                )

            return rating_text

        except Exception as e:
            logger.error(f"Get rating text error: {e}")
            return self._get_default_rating()

    async def _generate_rating_text(self, user_id: int) -> str:
        """Generate rating text with optimized queries"""
        try:
            # Get top 10 and user rank in parallel
            top_10_task = self._get_top_10()
            user_rank_task = self._get_user_rank(user_id)

            top_10, user_rank = await asyncio.gather(top_10_task, user_rank_task)

            return self._format_rating(top_10, user_rank, user_id)

        except Exception as e:
            logger.error(f"Generate rating error: {e}")
            return self._get_default_rating()

    async def _get_top_10(self) -> List[Dict]:
        """Get top 10 participants (optimized with window function)"""

        @sync_to_async
        def _get_top():
            try:
                from django_app.core.models import Participant
                from django.db.models import F, Window
                from django.db.models.functions import RowNumber

                participants = Participant.objects.filter(
                    competition_id=self.competition_id,
                    is_participant=True
                ).select_related('user').annotate(
                    rank=Window(
                        expression=RowNumber(),
                        order_by=F('current_points').desc()
                    )
                ).values(
                    'rank',
                    'user__telegram_id',
                    'user__username',
                    'user__full_name',
                    'current_points'
                ).order_by('rank')[:10]

                return list(participants)

            except Exception as e:
                logger.error(f"Get top 10 error: {e}")
                return []

        return await _get_top()

    async def _get_user_rank(self, user_id: int) -> Dict[str, Any]:
        """Get user rank (optimized)"""

        @sync_to_async
        def _get_rank():
            try:
                from django_app.core.models import Participant

                # Get user's points first
                participant = Participant.objects.filter(
                    competition_id=self.competition_id,
                    user__telegram_id=user_id,
                    is_participant=True
                ).select_related('user').first()

                if not participant:
                    return {'rank': None, 'points': 0, 'participant': None}

                # Count participants with more points
                higher_count = Participant.objects.filter(
                    competition_id=self.competition_id,
                    is_participant=True,
                    current_points__gt=participant.current_points
                ).count()

                return {
                    'rank': higher_count + 1,
                    'points': participant.current_points,
                    'participant': participant
                }

            except Exception as e:
                logger.error(f"Get user rank error: {e}")
                return {'rank': None, 'points': 0, 'participant': None}

        return await _get_rank()

    def _format_rating(self, top_10: List[Dict], user_rank: Dict, user_id: int) -> str:
        """Format rating text"""
        if not top_10:
            return "🏆 *TOP 10 Reyting*\n\nHozircha hech kim ball to'plamagan.\n🚀 Birinchi bo'ling!"

        text = "🏆 *TOP 10 Reyting* 🏆\n\n"

        # TOP 10
        for participant in top_10:
            rank = participant['rank']
            full_name = participant['user__full_name'] or 'Foydalanuvchi'
            username = participant['user__username'] or ''
            points = participant['current_points']

            emoji = get_prize_emoji(rank)

            # Format display name
            if username:
                display_name = f"{full_name} (@{username})"
            else:
                display_name = full_name

            text += f"{emoji} *{rank}-o'rin:* {display_name} - {format_points(points)} ball\n"

        text += "\n" + "─" * 30 + "\n\n"

        # User rank
        if user_rank['rank']:
            if user_rank['rank'] <= 10:
                text += f"✅ *Siz {user_rank['rank']}-o'rindasiz!* - {format_points(user_rank['points'])} ball\n"
            else:
                text += f"🎯 *Siz:* {user_rank['rank']}-o'rinda - {format_points(user_rank['points'])} ball\n"

                if top_10 and len(top_10) >= 10:
                    points_needed = top_10[9]['current_points'] - user_rank['points']
                    if points_needed > 0:
                        text += f"🔝 *TOP 10 uchun {format_points(points_needed)} ball kerak!*\n"
        else:
            text += "❌ *Siz hali reytingda emassiz.* /start ni bosib ro'yxatdan o'ting!\n"

        # Total participants info
        try:
            total_participants = Participant.objects.filter(
                competition_id=self.competition_id,
                is_participant=True
            ).count()

            if user_rank['rank'] and total_participants > 0:
                percentage = (user_rank['rank'] / total_participants) * 100
                text += f"📊 *Jami ishtirokchilar:* {total_participants} ta (Siz {percentage:.1f}% ichidasiz)\n"
        except:
            pass

        text += f"\n🚀 *Ko'proq ball yig'ish uchun do'stlaringizni taklif qiling!*"

        return text

    def _get_default_rating(self) -> str:
        """Default rating text"""
        return "🏆 *TOP 10 Reyting*\n\nXatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."

    async def update_cache(self, user_id: int):
        """Force update rating cache for user"""
        try:
            cache_key = CACHE_KEYS['rating_cache'].format(self.competition_id, user_id)

            if redis_client.is_connected():
                # Clear cache
                await redis_client.set_user_state(self.competition_id, user_id, None, 1)

                # Regenerate and cache
                rating_text = await self._generate_rating_text(user_id)
                if rating_text:
                    await redis_client.set_user_state(
                        self.competition_id, user_id,
                        {'rating': rating_text},
                        self.cache_ttl
                    )
                    logger.info(f"Rating cache updated for user {user_id}")

        except Exception as e:
            logger.error(f"Update rating cache error: {e}")