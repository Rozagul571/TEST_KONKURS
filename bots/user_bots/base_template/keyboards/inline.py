#bots/user_bots/base_template/keyboards/inline.py
"""
Inline keyboards for user bot - TO'G'RILANGAN
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_channels_keyboard(channels: list) -> InlineKeyboardMarkup:
    """
    Kanallar uchun inline keyboard
    Har bir kanal uchun URL button
    """
    builder = InlineKeyboardBuilder()

    for channel in channels:
        channel_username = channel.get('channel_username', '')
        channel_name = channel.get('channel_name', channel_username)

        if channel_username.startswith('@'):
            channel_username = channel_username[1:]

        if channel_username:
            url = f"https://t.me/{channel_username}"

            builder.add(
                InlineKeyboardButton(
                    text=f"📢 {channel_name}",
                    url=url
                )
            )

    # Check button
    builder.add(
        InlineKeyboardButton(
            text="✅ Obuna bo'ldim",
            callback_data="check_subscription"
        )
    )

    builder.adjust(1)  # Har biri alohida qatorda
    return builder.as_markup()


def get_post_generate_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """
    Taklif posti uchun inline keyboard
    """
    builder = InlineKeyboardBuilder()

    # Taklif linki
    builder.add(
        InlineKeyboardButton(
            text="🔗 Taklif havolasini nusxalash",
            url=referral_link
        )
    )

    # Ishtirok etish
    builder.add(
        InlineKeyboardButton(
            text="🚀 Ishtirok etish",
            url=referral_link
        )
    )

    builder.adjust(1)  # Har biri alohida qatorda
    return builder.as_markup()


def get_invitation_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """
    Taklif qilish uchun inline keyboard
    """
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(
            text="👥 Do'stlarni taklif qilish",
            url=referral_link
        )
    )

    builder.add(
        InlineKeyboardButton(
            text="📢 Postni ulashish",
            callback_data="share_post"
        )
    )

    builder.adjust(1)
    return builder.as_markup()