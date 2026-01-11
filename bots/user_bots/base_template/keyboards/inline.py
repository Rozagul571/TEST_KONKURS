# bots/user_bots/base_template/keyboards/inline.py
"""
Inline keyboards for user bot - TO'G'RILANGAN
Vazifasi: Barcha inline tugmalar bir joyda
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict, Any

from shared.constants import BUTTON_TEXTS
from shared.utils import clean_channel_username


def get_channels_keyboard(channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Kanallar uchun inline keyboard yaratish

    Args:
        channels: Kanallar ro'yxati (channel_username, channel_name keraklari bilan)

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Agar channels bo'sh bo'lsa ham A'zo bo'ldim buttoni chiqsin
    if not channels:
        builder.add(InlineKeyboardButton(text=BUTTON_TEXTS['azo_boldim'], callback_data="check_subscription"))
        return builder.as_markup()

    # Har bir kanal uchun button
    for channel in channels:
        # Username ni xavfsiz olish va tozalash
        raw_username = channel.get('channel_username') or channel.get('username', '')
        username = clean_channel_username(raw_username)

        if not username:
            continue

        # Kanal nomini olish
        channel_name = channel.get('channel_name') or channel.get('title') or f"@{username}"

        # URL button
        url = f"https://t.me/{username}"
        builder.add(InlineKeyboardButton(text=f"📢 {channel_name}", url=url))

    # A'zo bo'ldim tugmasi
    builder.add(InlineKeyboardButton(text=BUTTON_TEXTS['azo_boldim'], callback_data="check_subscription"))

    # Har bir button alohida qatorda
    builder.adjust(1)

    return builder.as_markup()


def get_invitation_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """
    Taklif qilish uchun inline keyboard

    Args:
        referral_link: Referral havolasi

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text=BUTTON_TEXTS['taklif_qilish'], url=referral_link))
    builder.add(InlineKeyboardButton(text=BUTTON_TEXTS['postni_ulashish'], switch_inline_query=referral_link))

    builder.adjust(1)
    return builder.as_markup()


def get_post_generate_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """
    Taklif posti uchun inline keyboard

    Args:
        referral_link: Referral havolasi

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    builder.add(InlineKeyboardButton(text="🔗 Taklif havolasi", url=referral_link))
    builder.add(InlineKeyboardButton(text="🚀 Ishtirok etish", url=referral_link))

    builder.adjust(1)
    return builder.as_markup()


def get_share_keyboard(referral_link: str, bot_username: str) -> InlineKeyboardMarkup:
    """
    Ulashish uchun keyboard

    Args:
        referral_link: Referral havolasi
        bot_username: Bot username

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()

    # Share button (switch_inline_query orqali)
    share_text = f"🎉 Konkursda qatnashing va sovg'alar yuting! {referral_link}"
    builder.add(InlineKeyboardButton(text="📤 Do'stlarga ulashish", switch_inline_query=share_text))
    builder.add(InlineKeyboardButton(text="🔗 Havolani nusxalash", callback_data="copy_link"))

    builder.adjust(1)
    return builder.as_markup()


def get_rating_keyboard() -> InlineKeyboardMarkup:
    """
    Reyting uchun keyboard (refresh button)

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_rating"))
    return builder.as_markup()


def get_back_keyboard(callback_data: str = "back_to_menu") -> InlineKeyboardMarkup:
    """
    Orqaga qaytish tugmasi

    Args:
        callback_data: Callback data

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=callback_data))
    return builder.as_markup()


def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "cancel") -> InlineKeyboardMarkup:
    """
    Tasdiqlash keyboard

    Args:
        confirm_data: Tasdiqlash callback data
        cancel_data: Bekor qilish callback data

    Returns:
        InlineKeyboardMarkup
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Ha", callback_data=confirm_data))
    builder.add(InlineKeyboardButton(text="❌ Yo'q", callback_data=cancel_data))
    builder.adjust(2)
    return builder.as_markup()