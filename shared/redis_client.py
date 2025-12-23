# shared/redis_client.py
"""
Optimized Redis client with connection pooling and error handling
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from redis import Redis, ConnectionPool, RedisError

logger = logging.getLogger(__name__)


class RedisClient:
    """
    High-performance Redis client
    - Singleton
    - Connection pool
    - Async + Sync support
    """

    _instance = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None

    # =========================
    # SINGLETON
    # =========================
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    # =========================
    # INIT
    # =========================
    def _initialize(self):
        """Initialize Redis connection pool"""
        try:
            max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", 100))

            self._pool = ConnectionPool(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                password=os.getenv("REDIS_PASSWORD"),
                decode_responses=True,
                max_connections=max_connections,
                socket_keepalive=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # test connection
            self.client.ping()

            logger.info("✅ Redis connection pool initialized successfully")

        except RedisError as e:
            logger.error(f"❌ Redis initialization failed: {e}", exc_info=True)
            self._pool = None
            self._client = None

    # =========================
    # CORE ACCESS
    # =========================
    def get_client(self) -> Redis:
        """Create new redis client from pool"""
        if not self._pool:
            raise RedisError("Redis pool not initialized")
        return Redis(connection_pool=self._pool)

    @property
    def client(self) -> Redis:
        """
        Cached Redis client
        Used by batch processors & sync code
        """
        if self._client is None:
            self._client = self.get_client()
        return self._client

    def is_connected(self) -> bool:
        try:
            return self.client.ping()
        except Exception:
            return False

    # =====================================================
    # ASYNC METHODS (FastAPI / Webhooks / Workers)
    # =====================================================
    async def set_bot_settings(
        self,
        bot_id: int,
        settings: Dict[str, Any],
        expire: int = 300,
    ) -> bool:
        try:
            key = f"bot_settings:{bot_id}"
            self.client.setex(key, expire, json.dumps(settings))
            return True
        except Exception as e:
            logger.error(f"Set bot settings error: {e}")
            return False

    async def get_bot_settings(self, bot_id: int) -> Optional[Dict[str, Any]]:
        try:
            key = f"bot_settings:{bot_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Get bot settings error: {e}")
            return None

    async def push_update(self, bot_id: int, update: Dict[str, Any]) -> bool:
        try:
            queue_key = f"bot_queue:{bot_id}"
            self.client.lpush(queue_key, json.dumps(update))

            length = self.client.llen(queue_key)
            if length > 1000:
                logger.warning(f"Queue overflow bot={bot_id}, size={length}")

            return True
        except Exception as e:
            logger.error(f"Push update error: {e}")
            return False

    async def pop_update(self, bot_id: int) -> Optional[Dict[str, Any]]:
        try:
            queue_key = f"bot_queue:{bot_id}"
            data = self.client.rpop(queue_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Pop update error: {e}")
            return None

    async def set_user_state(
        self,
        bot_id: int,
        user_id: int,
        state: Dict[str, Any],
        expire: int = 600,
    ):
        try:
            key = f"user_state:{bot_id}:{user_id}"
            self.client.setex(key, expire, json.dumps(state))
        except Exception as e:
            logger.error(f"Set user state error: {e}")

    async def get_user_state(
        self,
        bot_id: int,
        user_id: int,
    ) -> Optional[Dict[str, Any]]:
        try:
            key = f"user_state:{bot_id}:{user_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Get user state error: {e}")
            return None

    async def increment_counter(
        self,
        key: str,
        amount: int = 1,
        expire: int = 3600,
    ) -> int:
        try:
            pipe = self.client.pipeline()
            pipe.incrby(key, amount)
            pipe.expire(key, expire)
            result = pipe.execute()
            return result[0]
        except Exception as e:
            logger.error(f"Increment counter error: {e}")
            return 0

    async def get_queue_length(self, bot_id: int) -> int:
        try:
            return self.client.llen(f"bot_queue:{bot_id}")
        except Exception as e:
            logger.error(f"Get queue length error: {e}")
            return 0

    # =====================================================
    # SYNC METHODS (BatchProcessor / Celery / Threads)
    # =====================================================
    def rpop_sync(self, key: str):
        try:
            return self.client.rpop(key)
        except Exception as e:
            logger.error(f"RPOP error: {e}")
            return None

    def keys_sync(self, pattern: str) -> List[str]:
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"KEYS error: {e}")
            return []

    def get_sync(self, key: str):
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"GET error: {e}")
            return None

    def delete_sync(self, key: str) -> int:
        try:
            return self.client.delete(key)
        except Exception as e:
            logger.error(f"DELETE error: {e}")
            return 0

    def cleanup_old_data(self, pattern: str = "temp:*", older_than: int = 86400):
        try:
            for key in self.client.keys(pattern):
                ttl = self.client.ttl(key)
                if ttl == -1 or ttl > older_than:
                    self.client.delete(key)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")



redis_client = RedisClient()