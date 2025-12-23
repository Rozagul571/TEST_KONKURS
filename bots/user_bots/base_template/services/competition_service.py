#bots/user_bots/base_template/services/competition_service.py
"""
High-performance competition service with Redis caching
"""
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from asgiref.sync import sync_to_async

from shared.redis_client import redis_client
from django_app.core.models import Competition, BotSetUp, Channel, PointRule, Prize
from shared.constants import COMPETITION_STATUSES

logger = logging.getLogger(__name__)


class CompetitionService:
    """Competition service with intelligent caching"""

    CACHE_TTL = 300  # 5 minutes

    def __init__(self):
        self._cache_hits = 0
        self._cache_misses = 0

    async def get_competition_settings(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """
        Get competition settings with multi-layer caching
        1. Redis cache (fast)
        2. Database with optimized queries
        3. Default fallback
        """
        # 1. Try Redis cache
        settings = await self._get_from_redis(bot_id)
        if settings:
            self._cache_hits += 1
            return settings

        self._cache_misses += 1

        # 2. Fetch from database
        settings = await self._fetch_from_database(bot_id)

        # 3. If not found, use defaults
        if not settings:
            settings = self._get_default_settings(bot_id)

        # 4. Cache in Redis
        if settings:
            await self._cache_to_redis(bot_id, settings)

        return settings

    async def _get_from_redis(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get from Redis cache"""
        try:
            if not redis_client.is_connected():
                return None

            key = f"competition:{bot_id}"
            data = await redis_client.get_bot_settings(bot_id)

            if data:
                logger.debug(f"Redis cache hit for bot {bot_id}")
                return data

        except Exception as e:
            logger.error(f"Redis get error: {e}")

        return None

    async def _cache_to_redis(self, bot_id: int, settings: Dict[str, Any]):
        """Cache to Redis"""
        try:
            if redis_client.is_connected():
                await redis_client.set_bot_settings(bot_id, settings, self.CACHE_TTL)
        except Exception as e:
            logger.error(f"Redis cache error: {e}")

    @sync_to_async
    def _fetch_from_database(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Fetch from database with optimized queries"""
        try:
            # Single query with all relations
            competition = Competition.objects.select_related(
                'bot', 'bot__owner'
            ).prefetch_related(
                'channels',
                'point_rules',
                'prize_set'
            ).filter(
                bot_id=bot_id,
                bot__is_active=True
            ).first()

            if not competition:
                logger.warning(f"Competition not found for bot {bot_id}")
                return None

            # Get all related data efficiently
            channels_data = []
            for channel in competition.channels.all():
                channels_data.append({
                    'id': channel.id,
                    'channel_username': channel.channel_username,
                    'channel_name': channel.channel_name,
                    'type': channel.type,
                    'is_required': channel.is_required
                })

            point_rules_data = {}
            for rule in competition.point_rules.all():
                point_rules_data[rule.action_type] = rule.points

            prizes_data = []
            for prize in competition.prize_set.all():
                prizes_data.append({
                    'place': prize.place,
                    'prize_name': prize.prize_name,
                    'prize_amount': float(prize.prize_amount) if prize.prize_amount else None,
                    'type': prize.type,
                    'description': prize.description,
                    'image_url': prize.image_url
                })

            return {
                'id': competition.id,
                'bot_id': bot_id,
                'name': competition.name,
                'description': competition.description,
                'rules_text': competition.rules_text,
                'status': competition.status,
                'start_at': competition.start_at.isoformat() if competition.start_at else None,
                'end_at': competition.end_at.isoformat() if competition.end_at else None,
                'bot_username': competition.bot.bot_username if competition.bot else '',
                'owner_id': competition.bot.owner.telegram_id if competition.bot and competition.bot.owner else None,
                'channels': channels_data,
                'point_rules': point_rules_data,
                'prizes': prizes_data,
                'max_participants': competition.max_participants,
                'min_points_to_win': competition.min_points_to_win,
                'is_published': competition.is_published,
                'created_at': competition.created_at.isoformat(),
                'updated_at': competition.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Database fetch error for bot {bot_id}: {e}", exc_info=True)
            return None

    def _get_default_settings(self, bot_id: int) -> Dict[str, Any]:
        """Get default settings"""
        return {
            'id': 0,
            'bot_id': bot_id,
            'name': f'Konkurs {bot_id}',
            'description': '',
            'rules_text': '',
            'status': COMPETITION_STATUSES['DRAFT'],
            'bot_username': '',
            'owner_id': None,
            'channels': [],
            'point_rules': {},
            'prizes': [],
            'max_participants': 0,
            'min_points_to_win': 0,
            'is_published': False
        }

    async def get_channel_usernames(self, bot_id: int) -> List[str]:
        """Get channel usernames for bot"""
        settings = await self.get_competition_settings(bot_id)
        if not settings:
            return []

        usernames = []
        for channel in settings.get('channels', []):
            username = channel.get('channel_username', '').replace('@', '')
            if username:
                usernames.append(username)

        return usernames

    async def get_active_competitions(self) -> List[int]:
        """Get list of active competition bot IDs"""
        try:
            @sync_to_async
            def _get_active():
                return list(Competition.objects.filter(
                    status=COMPETITION_STATUSES['ACTIVE'],
                    bot__is_active=True
                ).values_list('bot_id', flat=True))

            return await _get_active()
        except Exception as e:
            logger.error(f"Get active competitions error: {e}")
            return []

    async def update_cache(self, bot_id: int):
        """Force update cache for bot"""
        try:
            # Clear cache
            if redis_client.is_connected():
                await redis_client.set_bot_settings(bot_id, None, 1)

            # Reload from database
            settings = await self._fetch_from_database(bot_id)
            if settings:
                await self._cache_to_redis(bot_id, settings)
                logger.info(f"Cache updated for bot {bot_id}")

        except Exception as e:
            logger.error(f"Update cache error: {e}")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate': (self._cache_hits / (self._cache_hits + self._cache_misses) * 100)
                        if (self._cache_hits + self._cache_misses) > 0 else 0
        }