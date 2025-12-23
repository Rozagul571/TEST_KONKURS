"""
Utility functions for the entire system
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


def generate_hash(data: str) -> str:
    """Generate SHA256 hash"""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def validate_username(username: str) -> bool:
    """Validate Telegram username"""
    if not username:
        return False

    # Remove @ if present
    username = username.replace('@', '')

    # Telegram username rules
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
    return bool(re.match(pattern, username))


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime string"""
    try:
        # Try ISO format
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Try other common formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%d.%m.%Y %H:%M',
                '%m/%d/%Y %H:%M:%S'
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
        except Exception:
            pass

    return None


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


def safe_json_loads(data: str) -> Optional[Dict]:
    """Safely parse JSON"""
    try:
        return json.loads(data)
    except:
        return None


def get_percentage(part: int, total: int) -> float:
    """Calculate percentage"""
    if total == 0:
        return 0.0
    return (part / total) * 100


class PerformanceTimer:
    """Performance timer context manager"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        if duration > 1.0:
            logger.warning(f"⏱️ {self.operation_name} took {duration:.2f}s")
        else:
            logger.debug(f"⏱️ {self.operation_name} took {duration:.3f}s")