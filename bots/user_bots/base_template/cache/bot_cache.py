#bots/user_bots/base_template/cache/bot_cache.py
"""
Bot cache module - Redis cached bot settings
"""
import logging
import json
from typing import Optional, Dict, Any
from shared.redis_client import redis_client

logger = logging.getLogger(__name__)


class BotCache:
    """Bot settings cache manager"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def get_settings(self) -> Optional[Dict[str, Any]]:
        """Get bot settings from cache"""
        try:
            if not redis_client.is_connected():
                return None

            key = f"bot_settings:{self.bot_id}"
            data = await redis_client.get_bot_settings(self.bot_id)

            if data:
                logger.debug(f"Cache hit for bot {self.bot_id}")
                return data

            return None

        except Exception as e:
            logger.error(f"Get settings cache error: {e}")
            return None

    async def set_settings(self, settings: Dict[str, Any], ttl: int = 300):
        """Set bot settings to cache"""
        try:
            if not redis_client.is_connected():
                return False

            await redis_client.set_bot_settings(self.bot_id, settings, ttl)
            logger.debug(f"Settings cached for bot {self.bot_id}")
            return True

        except Exception as e:
            logger.error(f"Set settings cache error: {e}")
            return False

    async def clear_settings(self):
        """Clear bot settings from cache"""
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
        """Get competition info from cache"""
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