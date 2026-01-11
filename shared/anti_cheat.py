# shared/anti_cheat.py
"""
Anti-cheat engine for detecting fraudulent activities
Vazifasi: Firibgarlikni aniqlash va oldini olish
"""
import time
import logging
from typing import Dict, Any

from shared.redis_client import redis_client
from shared.constants import RATE_LIMITS

logger = logging.getLogger(__name__)


class AntiCheatEngine:
    """Anti-cheat engine for detecting fraudulent activities"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def check_rate_limit(self, user_id: int, action: str, limits: Dict[str, Dict[str, int]] = None) -> bool:
        """
        Foydalanuvchi harakatini rate limit tekshirish

        Args:
            user_id: Telegram user ID
            action: Harakat turi (start, message, callback, etc.)
            limits: Limitlar dict (optional, default RATE_LIMITS)

        Returns:
            True agar blocked (limit oshgan)
        """
        if limits is None:
            limits = RATE_LIMITS

        if action not in limits:
            return False

        limit_config = limits[action]
        limit = limit_config.get('limit', 5)
        window = limit_config.get('window', 60)

        key = f"rate_limit:{self.bot_id}:{user_id}:{action}"

        if not redis_client.is_connected():
            return False

        is_blocked = await redis_client.check_rate_limit(key, limit, window)

        if is_blocked:
            logger.warning(f"Rate limit hit: bot={self.bot_id}, user={user_id}, action={action}")

        return is_blocked

    async def detect_bot_patterns(self, user_id: int, update: Dict) -> Dict[str, Any]:
        """
        Bot-like pattern larni aniqlash

        Args:
            user_id: Telegram user ID
            update: Telegram update dict

        Returns:
            Dict: is_suspicious, reasons, score
        """
        suspicious = {
            'is_suspicious': False,
            'reasons': [],
            'score': 0
        }

        if not redis_client.is_connected():
            return suspicious

        try:
            # User state olish
            user_state = await redis_client.get_user_state(self.bot_id, user_id)
            current_time = time.time()

            if user_state:
                last_action_time = user_state.get('last_action_time', 0)
                time_diff = current_time - last_action_time

                # Juda tez harakatlar (100ms dan kam)
                if time_diff < 0.1:
                    suspicious['score'] += 30
                    suspicious['reasons'].append('action_too_fast')

                # Takroriy harakatlar
                action_type = update.get('type', 'unknown')
                action_count = user_state.get(f"action_count:{action_type}", 0)
                if action_count > 10:
                    suspicious['score'] += 20
                    suspicious['reasons'].append('repetitive_actions')

            # User state yangilash
            new_state = user_state or {}
            new_state['last_action_time'] = current_time
            action_type = update.get('type', 'unknown')
            new_state[f"action_count:{action_type}"] = new_state.get(f"action_count:{action_type}", 0) + 1

            await redis_client.set_user_state(self.bot_id, user_id, new_state, 300)

            if suspicious['score'] > 40:
                suspicious['is_suspicious'] = True
                logger.warning(f"Suspicious activity: bot={self.bot_id}, user={user_id}, score={suspicious['score']}")

        except Exception as e:
            logger.error(f"Detect bot patterns error: {e}")

        return suspicious

    async def check_join_spam(self, user_id: int) -> bool:
        """
        Join/check subscription spam tekshirish

        Args:
            user_id: Telegram user ID

        Returns:
            True agar spam
        """
        key = f"join_check:{self.bot_id}:{user_id}"
        limit_config = RATE_LIMITS.get('join_check', {'limit': 5, 'window': 15})

        if not redis_client.is_connected():
            return False

        is_spam = await redis_client.check_rate_limit(key, limit_config['limit'], limit_config['window'])

        if is_spam:
            logger.warning(f"Join check spam: bot={self.bot_id}, user={user_id}")

        return is_spam

    async def validate_referral(self, referrer_id: int, referred_id: int) -> Dict[str, Any]:
        """
        Referral ni validatsiya qilish

        Args:
            referrer_id: Taklif qilgan user ID
            referred_id: Taklif qilingan user ID

        Returns:
            Dict: valid, reasons, warning
        """
        validation = {
            'valid': True,
            'reasons': [],
            'warning': None
        }

        # O'zini o'zi taklif qilish
        if referrer_id == referred_id:
            validation['valid'] = False
            validation['reasons'].append('self_referral')
            return validation

        if not redis_client.is_connected():
            return validation

        try:
            # Referral chain uzunligi
            chain_key = f"ref_chain:{self.bot_id}:{referrer_id}"
            if redis_client.client:
                chain_length = redis_client.client.incr(chain_key)
                redis_client.client.expire(chain_key, 86400)  # 24 soat

                if chain_length > 100:  # Juda ko'p referral
                    validation['warning'] = 'High referral count detected'

            # Duplicate referral
            ref_key = f"ref_dup:{self.bot_id}:{referred_id}"
            if redis_client.client and redis_client.client.exists(ref_key):
                validation['valid'] = False
                validation['reasons'].append('duplicate_referral')
            elif redis_client.client:
                redis_client.client.setex(ref_key, 86400, '1')

        except Exception as e:
            logger.error(f"Validate referral error: {e}")

        return validation

    async def get_user_risk_score(self, user_id: int) -> int:
        """
        Foydalanuvchi risk balini hisoblash

        Args:
            user_id: Telegram user ID

        Returns:
            Risk score (0-100)
        """
        score = 0

        if not redis_client.is_connected():
            return score

        try:
            # Harakat chastotasi
            action_key = f"user_actions:{self.bot_id}:{user_id}"
            if redis_client.client:
                action_count = redis_client.client.get(action_key)
                if action_count and int(action_count) > 100:
                    score += 30

        except Exception as e:
            logger.error(f"Get user risk score error: {e}")

        return score


def get_anti_cheat_engine(bot_id: int) -> AntiCheatEngine:
    """Factory function"""
    return AntiCheatEngine(bot_id)