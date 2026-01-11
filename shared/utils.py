# shared/utils.py
"""
Utility functions - Umumiy yordamchi funksiyalar
Vazifasi: Barcha modullar uchun umumiy funksiyalar
"""
import re
import logging
import secrets
import string
from typing import Dict, Any, Optional
from datetime import datetime

from shared.constants import PRIZE_EMOJIS

logger = logging.getLogger(__name__)


def get_display_name(user) -> str:
    """
    User uchun ko'rsatiladigan ism olish

    Args:
        user: User object (model yoki dict)
    """
    if isinstance(user, dict):
        first_name = user.get('first_name', '')
        last_name = user.get('last_name', '')
        username = user.get('username', '')
        telegram_id = user.get('telegram_id', user.get('id', ''))
    else:
        first_name = getattr(user, 'first_name', '') or ''
        last_name = getattr(user, 'last_name', '') or ''
        username = getattr(user, 'username', '') or ''
        telegram_id = getattr(user, 'telegram_id', '')

    if first_name and last_name:
        return f"{first_name} {last_name}"
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    elif username:
        return f"@{username}"
    else:
        return f"User {telegram_id}"


def extract_user_data(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Telegram xabaridan user ma'lumotlarini olish

    Args:
        message: Telegram message dict

    Returns:
        User ma'lumotlari dict
    """
    try:
        from_user = message.get('from', {})
        first_name = from_user.get('first_name', '') or ''
        last_name = from_user.get('last_name', '') or ''

        return {
            'telegram_id': from_user.get('id'),
            'username': from_user.get('username', '') or '',
            'first_name': first_name,
            'last_name': last_name,
            'full_name': f"{first_name} {last_name}".strip() or from_user.get('username', ''),
            'language_code': from_user.get('language_code', 'uz'),
            'is_premium': from_user.get('is_premium', False),
            'is_bot': from_user.get('is_bot', False),
            'chat_id': message.get('chat', {}).get('id'),
        }
    except Exception as e:
        logger.error(f"Extract user data error: {e}")
        return {}


def extract_referral_code(text: str) -> Optional[str]:
    """
    /start buyrug'idan referral kodini olish

    Args:
        text: /start ref_ABC123 formatidagi text

    Returns:
        Referral kodi yoki None
    """
    if not text:
        return None

    parts = text.split()
    for part in parts:
        if part.startswith('ref_'):
            return part.replace('ref_', '')
    return None


def get_prize_emoji(place: int) -> str:
    """
    O'rin uchun emoji olish

    Args:
        place: O'rin raqami (1-10)

    Returns:
        Emoji string
    """
    return PRIZE_EMOJIS.get(place, "🎁")


def format_points(points: int) -> str:
    """
    Ballarni formatlash (vergul bilan)

    Args:
        points: Ball soni

    Returns:
        Formatlangan string (1,234)
    """
    return f"{points:,}"


def format_currency(amount: float) -> str:
    """
    Pul miqdorini formatlash

    Args:
        amount: Summa

    Returns:
        Formatlangan string (1,234,567 soʻm)
    """
    return f"{amount:,.0f} soʻm"


def generate_referral_code(length: int = 8) -> str:
    """
    Unikal referral kodi generatsiya qilish

    Args:
        length: Kod uzunligi

    Returns:
        Random kod string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Textni qisqartirish

    Args:
        text: Asl text
        max_length: Maksimal uzunlik
        suffix: Qisqartirilganda qo'shiladigan qo'shimcha

    Returns:
        Qisqartirilgan text
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def escape_md(text: str) -> str:
    """
    Markdown uchun maxsus belgilarni escape qilish (Markdown V1)

    Args:
        text: Asl text

    Returns:
        Escaped text
    """
    if not text:
        return ""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text


def escape_md2(text: str) -> str:
    """
    MarkdownV2 uchun maxsus belgilarni escape qilish

    Args:
        text: Asl text

    Returns:
        Escaped text
    """
    if not text:
        return ""
    # MarkdownV2 special characters
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    result = ""
    for char in text:
        if char in escape_chars:
            result += f"\\{char}"
        else:
            result += char
    return result


def escape_html(text: str) -> str:
    """
    HTML uchun maxsus belgilarni escape qilish

    Args:
        text: Asl text

    Returns:
        Escaped text
    """
    if not text:
        return ""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def calculate_time_remaining(end_time: datetime) -> Dict[str, int]:
    """
    Tugash vaqtiga qolgan vaqtni hisoblash

    Args:
        end_time: Tugash datetime

    Returns:
        Dict: days, hours, minutes, seconds
    """
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


def format_time_remaining(end_time: datetime) -> str:
    """
    Qolgan vaqtni formatlash

    Args:
        end_time: Tugash datetime

    Returns:
        Formatlangan string
    """
    remaining = calculate_time_remaining(end_time)
    parts = []
    if remaining['days'] > 0:
        parts.append(f"{remaining['days']} kun")
    if remaining['hours'] > 0:
        parts.append(f"{remaining['hours']} soat")
    if remaining['minutes'] > 0:
        parts.append(f"{remaining['minutes']} daqiqa")
    return ", ".join(parts) if parts else "Tugadi"


def clean_channel_username(username: str) -> str:
    """
    Kanal username ni tozalash

    Args:
        username: Raw username (@channel, https://t.me/channel, etc.)

    Returns:
        Tozalangan username (channel)
    """
    if not username:
        return ""
    if not isinstance(username, str):
        username = str(username)

    # URL formatlarni tozalash
    username = username.replace('https://t.me/', '')
    username = username.replace('http://t.me/', '')
    username = username.replace('t.me/', '')
    username = username.lstrip('@')
    username = username.strip()

    return username


def validate_telegram_username(username: str) -> bool:
    """
    Telegram username validatsiyasi

    Args:
        username: Tekshiriladigan username

    Returns:
        Valid yoki yo'q
    """
    if not username:
        return False
    # Telegram username rules: 5-32 characters, a-z, 0-9, _
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
    return bool(re.match(pattern, username))


def safe_int(value: Any, default: int = 0) -> int:
    """
    Xavfsiz int ga o'tkazish

    Args:
        value: O'tkaziladigan qiymat
        default: Default qiymat

    Returns:
        int qiymat
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Xavfsiz float ga o'tkazish

    Args:
        value: O'tkaziladigan qiymat
        default: Default qiymat

    Returns:
        float qiymat
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default