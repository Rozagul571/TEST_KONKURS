#bots/user_bots/base_template/cache/user_cache.py
"""
User cache module - Redis cached user data
"""
import logging
import json
from typing import Optional, Dict, Any
from shared.redis_client import redis_client

logger = logging.getLogger(__name__)


class UserCache:
    """User data cache manager"""

    def __init__(self, bot_id: int, user_id: int):
        self.bot_id = bot_id
        self.user_id = user_id

    async def get_user_state(self) -> Optional[Dict[str, Any]]:
        """Get user state from cache"""
        try:
            return await redis_client.get_user_state(self.bot_id, self.user_id)
        except Exception as e:
            logger.error(f"Get user state error: {e}")
            return None

    async def set_user_state(self, state: Dict[str, Any], ttl: int = 300):
        """Set user state to cache"""
        try:
            await redis_client.set_user_state(self.bot_id, self.user_id, state, ttl)
            logger.debug(f"User state cached for user {self.user_id}")
        except Exception as e:
            logger.error(f"Set user state error: {e}")

    async def clear_user_state(self):
        """Clear user state from cache"""
        try:
            await redis_client.set_user_state(self.bot_id, self.user_id, None, 1)
            logger.debug(f"User state cleared for user {self.user_id}")
        except Exception as e:
            logger.error(f"Clear user state error: {e}")

    async def get_points(self) -> Optional[int]:
        """Get user points from cache"""
        try:
            if not redis_client.is_connected():
                return None

            key = f"user_points:{self.bot_id}:{self.user_id}"
            points_data = redis_client.client.get(key)
            return int(points_data) if points_data else None

        except Exception as e:
            logger.error(f"Get user points error: {e}")
            return None

    async def set_points(self, points: int, ttl: int = 60):
        """Set user points to cache"""
        try:
            if not redis_client.is_connected():
                return False

            key = f"user_points:{self.bot_id}:{self.user_id}"
            redis_client.client.setex(key, ttl, str(points))
            return True

        except Exception as e:
            logger.error(f"Set user points error: {e}")
            return False

    async def get_rating_position(self) -> Optional[int]:
        """Get user rating position from cache"""
        try:
            state = await self.get_user_state()
            if state and 'rating_position' in state:
                return state['rating_position']
            return None
        except Exception as e:
            logger.error(f"Get rating position error: {e}")
            return None

    async def set_rating_position(self, position: int, ttl: int = 60):
        """Set user rating position to cache"""
        try:
            state = await self.get_user_state() or {}
            state['rating_position'] = position
            await self.set_user_state(state, ttl)
        except Exception as e:
            logger.error(f"Set rating position error: {e}")