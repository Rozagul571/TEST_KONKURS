# bots/user_bots/base_template/buttons/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_channels_keyboard(channels):
    """Kanallar keyboard. Vazifasi: Obuna bo'lmagan kanallarni chiqarish. Misol: Button '@kanal' url bilan."""
    keyboard = InlineKeyboardBuilder()
    for channel in channels:
        channel_username = channel.channel_username.replace('@', '')
        keyboard.button(text=f"📢 {channel.channel_username}", url=f"https://t.me/{channel_username}")
    keyboard.button(text="✅ Obuna bo'ldim", callback_data="check_subscription")
    keyboard.adjust(1)
    return keyboard.as_markup()