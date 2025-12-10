import os
import json
import logging
from redis import Redis
import asyncio

logger = logging.getLogger(__name__)


# FIX: Async Redis client
class AsyncQueue:
    def __init__(self):
        self.redis = None
        self._connect()

    def _connect(self):
        """Redis ga ulanish"""
        try:
            self.redis = Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True,
                socket_connect_timeout=3
            )
            self.redis.ping()
            logger.info("✅ Queue Redis ga ulandi")
        except Exception as e:
            logger.warning(f"⚠️ Queue Redis ga ulanish xatosi: {e}")
            self.redis = None

    def push_update(self, bot_id: int, update_data: dict):
        """Update ni Redis queue ga yuboradi"""
        try:
            if not self.redis:
                self._connect()
                if not self.redis:
                    logger.error("Redis ulanishi mavjud emas")
                    return False

            self.redis.lpush(f"bot_queue:{bot_id}", json.dumps(update_data))
            logger.debug(f"Update bot {bot_id} uchun queue ga yuborildi")
            return True
        except Exception as e:
            logger.error(f"Queue push xatosi: {e}")
            # Reconnect urinib ko'rish
            self.redis = None
            return False

    def get_update(self, bot_id: int):
        """Queue dan update olish"""
        try:
            if not self.redis:
                self._connect()
                if not self.redis:
                    return None

            data = self.redis.rpop(f"bot_queue:{bot_id}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Queue get xatosi: {e}")
            return None


# Global queue instance
queue = AsyncQueue()


# Oldingi funksiyani saqlash
def push_update(bot_id: int, update_data: dict):
    """Eski interface uchun wrapper"""
    return queue.push_update(bot_id, update_data)