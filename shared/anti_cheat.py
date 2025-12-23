#shared/anti_cheat.py
import time
import logging
from typing import Dict, List, Optional
from shared.redis_client import redis_client

logger = logging.getLogger(__name__)


class AntiCheatEngine:
    """Anti-cheat engine for detecting fraudulent activities"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def check_rate_limit(self, user_id: int, action: str,
                               limits: Dict[str, Dict[str, int]]) -> bool:
        """
        Check if user exceeds rate limits for specific action
        Returns: True if blocked, False if allowed
        """
        if action not in limits:
            return False

        limit_config = limits[action]
        limit = limit_config.get('limit', 5)
        window = limit_config.get('window', 60)

        key = f"rate_limit:{self.bot_id}:{user_id}:{action}"
        is_blocked = redis_client.check_rate_limit(key, limit, window)

        if is_blocked:
            logger.warning(f"Rate limit hit: bot={self.bot_id}, user={user_id}, action={action}")

        return is_blocked

    async def detect_bot_patterns(self, user_id: int, update: dict) -> Dict:
        """
        Detect bot-like patterns in user behavior
        """
        suspicious = {
            'is_suspicious': False,
            'reasons': [],
            'score': 0
        }

        # Check message timing patterns
        user_state = redis_client.get_user_state(self.bot_id, user_id)
        current_time = time.time()

        if user_state:
            last_action_time = user_state.get('last_action_time', 0)
            time_diff = current_time - last_action_time

            # Too fast actions (less than 100ms)
            if time_diff < 0.1:
                suspicious['score'] += 30
                suspicious['reasons'].append('action_too_fast')

            # Pattern detection (same action repeated)
            action_count = user_state.get(f"action_count:{update.get('type', 'unknown')}", 0)
            if action_count > 10:
                suspicious['score'] += 20
                suspicious['reasons'].append('repetitive_actions')

        # Update user state
        new_state = {
            'last_action_time': current_time,
            f"action_count:{update.get('type', 'unknown')}": (action_count or 0) + 1,
            'last_update': update
        }
        redis_client.set_user_state(self.bot_id, user_id, new_state)

        if suspicious['score'] > 40:
            suspicious['is_suspicious'] = True
            logger.warning(f"Suspicious activity detected: bot={self.bot_id}, user={user_id}")

        return suspicious

    async def check_join_spam(self, user_id: int, channel_check_count: int) -> bool:
        """
        Check for join/check subscription spam
        """
        key = f"join_check:{self.bot_id}:{user_id}"

        # Allow max 4 checks in 15 seconds
        is_spam = redis_client.check_rate_limit(key, 4, 15)

        if is_spam:
            logger.warning(f"Join check spam detected: bot={self.bot_id}, user={user_id}")

        return is_spam

    async def validate_referral(self, referrer_id: int, referred_id: int) -> Dict:
        """
        Validate referral to prevent cheating
        """
        validation = {
            'valid': True,
            'reasons': [],
            'warning': None
        }

        # Check self-referral
        if referrer_id == referred_id:
            validation['valid'] = False
            validation['reasons'].append('self_referral')

        # Check referral chain length
        chain_key = f"ref_chain:{self.bot_id}:{referrer_id}"
        chain_length = redis_client.client.incr(chain_key) if redis_client.client else 1

        if chain_length > 50:  # Too many referrals from same user
            validation['valid'] = False
            validation['reasons'].append('referral_chain_too_long')
            validation['warning'] = 'Possible referral fraud detected'

        # Check duplicate referral
        ref_key = f"ref_dup:{self.bot_id}:{referred_id}"
        if redis_client.client and redis_client.client.exists(ref_key):
            validation['valid'] = False
            validation['reasons'].append('duplicate_referral')
        elif redis_client.client:
            redis_client.client.setex(ref_key, 86400, '1')  # 24 hours

        return validation

    async def get_user_risk_score(self, user_id: int) -> int:
        """
        Calculate user risk score based on behavior
        """
        score = 0

        # Check multiple account patterns
        ip_key = f"user_ip:{self.bot_id}:{user_id}"
        # (In production, you would check IP patterns here)

        # Action frequency
        action_key = f"user_actions:{self.bot_id}:{user_id}"
        action_count = redis_client.client.get(action_key) if redis_client.client else 0

        if int(action_count or 0) > 100:
            score += 30

        return score


# Factory function
def get_anti_cheat_engine(bot_id: int) -> AntiCheatEngine:
    return AntiCheatEngine(bot_id)