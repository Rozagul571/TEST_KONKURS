# shared/rate_limiter.py
"""
Rate limiter for API calls
"""

import time
import logging
from typing import Dict, Any
from shared.redis_client import redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for anti-spam"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

        # Rate limits configuration
        self.limits = {
            'start': {'limit': 3, 'window': 60},  # 3 /start per minute
            'message': {'limit': 30, 'window': 60},  # 30 messages per minute
            'callback': {'limit': 20, 'window': 60},  # 20 callbacks per minute
            'check_subscription': {'limit': 5, 'window': 15},  # 5 checks per 15 seconds
        }

    async def is_limited(self, user_id: int, action: str) -> bool:
        """Check if user is rate limited"""
        if action not in self.limits:
            return False

        limit_config = self.limits[action]
        key = f"rate_limit:{self.bot_id}:{user_id}:{action}"

        if not redis_client.is_connected():
            return False

        try:
            # Use Redis INCR for rate limiting
            current = redis_client.client.incr(key)

            # Set expiry on first increment
            if current == 1:
                redis_client.client.expire(key, limit_config['window'])

            return current > limit_config['limit']

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False