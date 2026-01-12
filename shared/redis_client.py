# shared/redis_client.py
"""
Redis client - OPTIONAL (fallback bilan)
Agar Redis yo'q bo'lsa ham bot ishlaydi
"""
import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed - running without Redis")


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._client = None
        self._connected = False
        self._connect()

    def _connect(self):
        if not REDIS_AVAILABLE:
            return

        try:
            url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._client = redis.from_url(url, decode_responses=True, socket_timeout=5)
            self._client.ping()
            self._connected = True
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - running without Redis")
            self._connected = False

    def is_connected(self) -> bool:
        if not self._connected or not self._client:
            return False
        try:
            self._client.ping()
            return True
        except:
            self._connected = False
            return False

    # =============== QUEUE METHODS ===============

    async def push_update(self, bot_id: int, update: dict) -> bool:
        """Update ni queue ga qo'shish"""
        if not self.is_connected():
            return False
        try:
            key = f"bot_queue:{bot_id}"
            self._client.rpush(key, json.dumps(update))
            return True
        except Exception as e:
            logger.error(f"Push update error: {e}")
            return False

    async def pop_update(self, bot_id: int) -> Optional[Dict]:
        """Queue dan update olish"""
        if not self.is_connected():
            return None
        try:
            key = f"bot_queue:{bot_id}"
            data = self._client.lpop(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Pop update error: {e}")
            return None

    async def get_queue_length(self, bot_id: int) -> int:
        """Queue uzunligini olish"""
        if not self.is_connected():
            return 0
        try:
            return self._client.llen(f"bot_queue:{bot_id}")
        except:
            return 0

    # =============== SETTINGS METHODS ===============

    async def get_bot_settings(self, bot_id: int) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            data = self._client.get(f"bot_settings:{bot_id}")
            return json.loads(data) if data else None
        except:
            return None

    async def set_bot_settings(self, bot_id: int, settings: Dict, ttl: int = 300) -> bool:
        if not self.is_connected():
            return False
        try:
            if settings:
                self._client.setex(f"bot_settings:{bot_id}", ttl, json.dumps(settings))
            else:
                self._client.delete(f"bot_settings:{bot_id}")
            return True
        except:
            return False

    # =============== USER STATE METHODS ===============

    async def get_user_state(self, bot_id: int, user_id: int) -> Optional[Dict]:
        if not self.is_connected():
            return None
        try:
            data = self._client.get(f"user_state:{bot_id}:{user_id}")
            return json.loads(data) if data else None
        except:
            return None

    async def set_user_state(self, bot_id: int, user_id: int, state: Dict, ttl: int = 600) -> bool:
        if not self.is_connected():
            return False
        try:
            self._client.setex(f"user_state:{bot_id}:{user_id}", ttl, json.dumps(state))
            return True
        except:
            return False

    # =============== CACHE METHODS ===============

    async def clear_bot_cache(self, bot_id: int):
        """Bot cache ni tozalash"""
        if not self.is_connected():
            return
        try:
            self._client.delete(f"bot_settings:{bot_id}")
            self._client.delete(f"bot_queue:{bot_id}")
        except:
            pass


# Global instance
redis_client = RedisClient()