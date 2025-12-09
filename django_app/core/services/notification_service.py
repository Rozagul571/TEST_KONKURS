# django_app/core/services/notification_service.py
from asgiref.sync import sync_to_async
from aiogram import Bot
from django.conf import settings


class NotificationService:
    """Notification servisi. Vazifasi: Superadmin va userlarga xabar yuborish. Misol: send_superadmin_notification - yangi bot yaratilganda."""
    def __init__(self):
        self.main_bot_token = settings.TELEGRAM_BOT_TOKEN
        self.super_admin_id = getattr(settings, 'SUPER_ADMIN_TELEGRAM_ID', None)

    async def send_superadmin_notification(self, user, bot_username: str, admin_username: str, bot_id: int):
        if not self.main_bot_token or not self.super_admin_id:
            return
        from bots.main_bot.utils.message_texts import get_superadmin_notification_message
        from bots.main_bot.buttons.inline import get_bot_management_keyboard
        text = get_superadmin_notification_message(user, bot_username, admin_username)
        keyboard = get_bot_management_keyboard(bot_id)
        bot = Bot(token=self.main_bot_token)
        await bot.send_message(chat_id=int(self.super_admin_id), text=text, reply_markup=keyboard, parse_mode="HTML")
        await bot.session.close()

    async def send_user_notification(self, user_tg_id, bot_username, competition_name, description):
        bot = Bot(token=self.main_bot_token)
        from bots.main_bot.utils.message_texts import get_competition_complete_message
        from bots.main_bot.buttons.inline import get_contact_admin_keyboard
        text = get_competition_complete_message(bot_username, competition_name, description)
        keyboard = await get_contact_admin_keyboard()
        await bot.send_message(chat_id=user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        await bot.session.close()

