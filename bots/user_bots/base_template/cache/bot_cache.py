# bots/user_bots/base_template/cache/bot_cache.py
"""
Bot cache module - Redis cached bot settings
Vazifasi: Bot sozlamalarini cache qilish
"""
import logging
from typing import Optional, Dict, Any

from shared.redis_client import redis_client
from shared.constants import CACHE_TTL

logger = logging.getLogger(__name__)


class BotCache:
    """Bot settings cache manager"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def get_settings(self) -> Optional[Dict[str, Any]]:
        """
        Settings ni cache dan olish

        Returns:
            Settings dict yoki None
        """
        try:
            if not redis_client.is_connected():
                return None

            data = await redis_client.get_bot_settings(self.bot_id)
            if data:
                logger.debug(f"Cache hit for bot {self.bot_id}")
                return data

            return None

        except Exception as e:
            logger.error(f"Get settings cache error: {e}")
            return None

    async def set_settings(self, settings: Dict[str, Any], ttl: int = None):
        """
        Settings ni cache ga saqlash

        Args:
            settings: Settings dict
            ttl: Time to live (sekundlarda)
        """
        try:
            if not redis_client.is_connected():
                return False

            if ttl is None:
                ttl = CACHE_TTL.get('bot_settings', 300)

            await redis_client.set_bot_settings(self.bot_id, settings, ttl)
            logger.debug(f"Settings cached for bot {self.bot_id}")
            return True

        except Exception as e:
            logger.error(f"Set settings cache error: {e}")
            return False

    async def clear_settings(self):
        """Settings cache ni tozalash"""
        try:
            if not redis_client.is_connected():
                return False

            await redis_client.set_bot_settings(self.bot_id, None, 1)
            logger.debug(f"Settings cache cleared for bot {self.bot_id}")
            return True

        except Exception as e:
            logger.error(f"Clear settings cache error: {e}")
            return False

    async def get_competition_info(self) -> Optional[Dict[str, Any]]:
        """Competition info ni olish"""
        try:
            settings = await self.get_settings()
            if not settings:
                return None

            return {
                'id': settings.get('id'),
                'name': settings.get('name', ''),
                'description': settings.get('description', ''),
                'rules_text': settings.get('rules_text', ''),
                'bot_username': settings.get('bot_username', ''),
                'channels': settings.get('channels', []),
                'prizes': settings.get('prizes', []),
                'status': settings.get('status', 'draft')
            }

        except Exception as e:
            logger.error(f"Get competition info error: {e}")
            return None