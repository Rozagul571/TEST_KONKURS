#bots/user_bots/base_template/services/anti_cheat_service.py
"""
Anti-cheat service for user bot
"""
import logging
import time
from typing import Dict, Any
from shared.redis_client import redis_client

logger = logging.getLogger(__name__)


class AntiCheatService:
    """Anti-cheat service for detecting fraudulent activities"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def check_rate_limit(self, user_id: int, action: str, limits: Dict[str, Dict]) -> bool:
        """Check rate limit for user action"""
        try:
            key = f"rate_limit:{self.bot_id}:{user_id}:{action}"

            if action not in limits:
                return False

            limit_config = limits[action]
            limit = limit_config.get('limit', 5)
            window = limit_config.get('window', 60)

            return await redis_client.check_rate_limit(key, limit, window)

        except Exception as e:
            logger.error(f"Check rate limit error: {e}")
            return False

    async def detect_bot_patterns(self, user_id: int, update: Dict[str, Any]) -> Dict[str, Any]:
        """Detect bot-like patterns"""
        try:
            user_state = await redis_client.get_user_state(self.bot_id, user_id)
            current_time = time.time()

            suspicious = {
                'is_suspicious': False,
                'reasons': [],
                'score': 0
            }

            if user_state:
                last_action_time = user_state.get('last_action_time', 0)
                time_diff = current_time - last_action_time

                # Too fast actions
                if time_diff < 0.1:
                    suspicious['score'] += 30
                    suspicious['reasons'].append('action_too_fast')

                # Update user state
                new_state = {
                    'last_action_time': current_time,
                    'last_update': update
                }
                await redis_client.set_user_state(self.bot_id, user_id, new_state, 300)

            if suspicious['score'] > 40:
                suspicious['is_suspicious'] = True

            return suspicious

        except Exception as e:
            logger.error(f"Detect bot patterns error: {e}")
            return {'is_suspicious': False, 'reasons': [], 'score': 0}