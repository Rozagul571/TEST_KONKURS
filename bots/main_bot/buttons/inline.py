# bots/main_bot/buttons/inline.py
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from django_app.core.models.system import SystemSettings

async def get_contact_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin kontakt keyboard. Vazifasi: User admin bilan bog'lanish tugmasi. Misol: Inline button 'Admin bilan bog'lanish'."""
    keyboard = InlineKeyboardBuilder()
    admin_data = await sync_to_async(SystemSettings.get)()
    url = admin_data.get_telegram_url()
    keyboard.button(text="👩‍💻 Admin bilan bogʻlanish", url=url)
    return keyboard.as_markup()

def get_admin_panel_keyboard(admin_url: str) -> InlineKeyboardMarkup:
    """Admin panel keyboard. Vazifasi: Panelga kirish tugmasi. Misol: 'Konkurs Paneliga Kirish'."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🚀 Konkurs Paneliga Kirish", url=admin_url)
    return keyboard.as_markup()

def get_bot_management_keyboard(bot_id: int) -> InlineKeyboardMarkup:
    """Bot management keyboard. Vazifasi: Superadmin uchun run/stop/reject. Misol: Callback 'run_bot:1'."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Run Bot", callback_data=f"run_bot:{bot_id}")
    keyboard.button(text="⏹️ Stop Bot", callback_data=f"stop_bot:{bot_id}")
    keyboard.button(text="❌ Reject Bot", callback_data=f"reject_bot:{bot_id}")
    return keyboard.as_markup()