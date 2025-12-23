# bots/user_bots/base_template/shared/utils.py
"""
Utility functions - TO'G'RILANGAN
"""
import re
import json
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import secrets
import string

logger = logging.getLogger(__name__)


def get_display_name(user):
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.last_name:
        return user.last_name
    elif user.username:
        return f"@{user.username}"
    else:
        return f"User {user.telegram_id}"



def extract_user_data(message: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user data from Telegram message"""
    try:
        from_user = message.get('from', {})

        return {
            'telegram_id': from_user.get('id'),
            'username': from_user.get('username', ''),
            'first_name': from_user.get('first_name', ''),
            'last_name': from_user.get('last_name', ''),
            'full_name': f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip(),
            'language_code': from_user.get('language_code', 'uz'),
            'is_premium': from_user.get('is_premium', False),
            'is_bot': from_user.get('is_bot', False),
            'chat_id': message.get('chat', {}).get('id'),
        }
    except Exception as e:
        logger.error(f"Extract user data error: {e}")
        return {}


def extract_referral_code(text: str) -> Optional[str]:
    """Extract referral code from /start command"""
    if not text:
        return None

    parts = text.split()
    for part in parts:
        if part.startswith('ref_'):
            return part.replace('ref_', '')

    return None


def get_prize_emoji(place: int) -> str:
    """Get emoji for prize place"""
    emoji_map = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
        7: "7️⃣",
        8: "8️⃣",
        9: "9️⃣",
        10: "🔟"
    }
    return emoji_map.get(place, "🎁")


def format_points(points: int) -> str:
    """Format points with comma separator"""
    return f"{points:,}"


def format_currency(amount: float) -> str:
    """Format currency amount"""
    return f"{amount:,.0f} soʻm"


def generate_referral_code(length: int = 8) -> str:
    """Generate unique referral code"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def calculate_time_remaining(end_time: datetime) -> Dict[str, int]:
    """Calculate time remaining until end time"""
    now = datetime.now()

    if end_time <= now:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0}

    delta = end_time - now

    return {
        'days': delta.days,
        'hours': delta.seconds // 3600,
        'minutes': (delta.seconds % 3600) // 60,
        'seconds': delta.seconds % 60
    }
