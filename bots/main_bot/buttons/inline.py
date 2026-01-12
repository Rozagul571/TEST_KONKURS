# bots/main_bot/buttons/inline.py
"""
Main bot inline keyboards
Vazifasi: A bot uchun inline tugmalar
"""
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async

from django_app.core.models.system import SystemSettings
from shared.constants import BUTTON_TEXTS


async def get_contact_admin_keyboard() -> InlineKeyboardMarkup:
    """
    Admin kontakt keyboard
    Vazifasi: User admin bilan bog'lanish tugmasi
    """
    keyboard = InlineKeyboardBuilder()
    admin_data = await sync_to_async(SystemSettings.get)()
    url = admin_data.get_telegram_url()
    keyboard.button(text=BUTTON_TEXTS['admin_contact'], url=url)
    return keyboard.as_markup()


def get_admin_panel_keyboard(admin_url: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=BUTTON_TEXTS['admin_panel'], url=admin_url)
    return keyboard.as_markup()


def get_bot_management_keyboard(bot_id: int) -> InlineKeyboardMarkup:

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=BUTTON_TEXTS['run_bot'], callback_data=f"run_bot:{bot_id}")
    keyboard.button(text=BUTTON_TEXTS['stop_bot'], callback_data=f"stop_bot:{bot_id}")
    keyboard.button(text=BUTTON_TEXTS['reject_bot'], callback_data=f"reject_bot:{bot_id}")
    keyboard.adjust(3)
    return keyboard.as_markup()