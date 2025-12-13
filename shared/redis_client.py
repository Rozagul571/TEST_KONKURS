import os
import json
import logging
from typing import Optional, Any
from redis import Redis, ConnectionPool
from redis.exceptions import ConnectionError

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client singleton pattern with connection pooling"""
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_redis()
        return cls._instance

    def _init_redis(self):
        """Initialize Redis connection pool"""
        try:
            self.pool = ConnectionPool(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True,
                max_connections=50,
                socket_keepalive=True,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self._client = Redis(connection_pool=self.pool)
            self._client.ping()
            logger.info("✅ Redis connection pool initialized")
        except ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._client = None

    @property
    def client(self) -> Optional[Redis]:
        """Get Redis client instance"""
        return self._client

    def is_connected(self) -> bool:
        """Check Redis connection"""
        try:
            return self._client is not None and self._client.ping()
        except:
            return False

    # Bot-specific methods
    async def set_bot_settings(self, bot_id: int, settings: dict, expire: int = 86400):
        """Cache bot settings with expiration"""
        if not self.is_connected():
            return False
        try:
            key = f"bot_settings:{bot_id}"
            return self._client.setex(key, expire, json.dumps(settings))
        except Exception as e:
            logger.error(f"Redis set_bot_settings error: {e}")
            return False

    def get_bot_settings(self, bot_id: int) -> Optional[dict]:
        """Get cached bot settings"""
        if not self.is_connected():
            return None
        try:
            key = f"bot_settings:{bot_id}"
            data = self._client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis get_bot_settings error: {e}")
            return None

    # Queue methods
    def push_update(self, bot_id: int, update: dict):
        """Push update to bot-specific queue"""
        if not self.is_connected():
            return False
        try:
            queue_key = f"bot_queue:{bot_id}"
            self._client.lpush(queue_key, json.dumps(update))
            return True
        except Exception as e:
            logger.error(f"Redis push_update error: {e}")
            return False

    def pop_update(self, bot_id: int) -> Optional[dict]:
        """Pop update from bot-specific queue"""
        if not self.is_connected():
            return None
        try:
            queue_key = f"bot_queue:{bot_id}"
            data = self._client.rpop(queue_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis pop_update error: {e}")
            return None

    # Rate limiting methods
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit is exceeded"""
        if not self.is_connected():
            return False
        try:
            current = self._client.incr(key)
            if current == 1:
                self._client.expire(key, window)
            return current > limit
        except Exception as e:
            logger.error(f"Redis check_rate_limit error: {e}")
            return False

    def set_user_state(self, bot_id: int, user_id: int, state: dict, expire: int = 300):
        """Cache user state for anti-spam"""
        if not self.is_connected():
            return
        try:
            key = f"user_state:{bot_id}:{user_id}"
            self._client.setex(key, expire, json.dumps(state))
        except Exception as e:
            logger.error(f"Redis set_user_state error: {e}")

    def get_user_state(self, bot_id: int, user_id: int) -> Optional[dict]:
        """Get cached user state"""
        if not self.is_connected():
            return None
        try:
            key = f"user_state:{bot_id}:{user_id}"
            data = self._client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Redis get_user_state error: {e}")
            return None


# Global instance
redis_client = RedisClient()