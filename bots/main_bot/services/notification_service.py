# bots/main_bot/services/notification_service.py
"""
Barcha notification textlari va yuborish logikasi shu yerda
Vazifasi: Telegram xabarlarini yuborish
"""
import os
import logging
from aiogram import Bot

from bots.main_bot.buttons.inline import get_bot_management_keyboard
from shared.constants import MESSAGES

logger = logging.getLogger(__name__)


class NotificationService:
    """Barcha notification logikasi"""

    def __init__(self):
        self.main_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.super_admin_id = os.getenv('SUPER_ADMIN_TELEGRAM_ID')

    async def send_superadmin_new_bot(self, user, bot_username: str, admin_username: str, bot_id: int):
        """
        Yangi bot yaratilganda superadmin ga xabar

        Args:
            user: User object
            bot_username: Bot username
            admin_username: Admin panel login
            bot_id: Bot ID
        """
        if not self.main_bot_token or not self.super_admin_id:
            logger.warning("Main bot token or super admin ID not configured")
            return

        try:
            # User display name
            full_display = f"{user.first_name or ''} {user.last_name or 'Nomalum'}".strip()
            if user.username:
                full_display += f" @{user.username}"

            text = MESSAGES['superadmin_new_bot'].format(
                full_name=full_display,
                telegram_id=user.telegram_id,
                bot_username=bot_username,
                admin_username=admin_username
            )

            keyboard = get_bot_management_keyboard(bot_id)

            bot = Bot(token=self.main_bot_token)
            await bot.send_message(int(self.super_admin_id), text=text, reply_markup=keyboard, parse_mode="HTML")
            await bot.session.close()

            logger.info(f"Superadmin notified about new bot: {bot_username}")

        except Exception as e:
            logger.error(f"Superadmin notification error: {e}")

    async def send_user_competition_completed(self, user_tg_id: int, bot_username: str, competition_name: str,
                                              description: str):
        """
        User konkurs to'ldirganda xabar

        Args:
            user_tg_id: User telegram ID
            bot_username: Bot username
            competition_name: Konkurs nomi
            description: Konkurs tavsifi
        """
        if not self.main_bot_token:
            return

        try:
            text = MESSAGES['competition_completed'].format(
                bot_username=bot_username,
                name=competition_name,
                description=description
            )

            from bots.main_bot.buttons.inline import get_contact_admin_keyboard
            keyboard = await get_contact_admin_keyboard()

            bot = Bot(token=self.main_bot_token)
            await bot.send_message(user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
            await bot.session.close()

            logger.info(f"User {user_tg_id} notified about competition completion")

        except Exception as e:
            logger.error(f"User {user_tg_id} notification error: {e}")

    async def send_bot_run_to_owner(self, owner_tg_id: int, bot_username: str, bot_id: int):
        """
        Bot run bo'lganda owner ga xabar

        Args:
            owner_tg_id: Owner telegram ID
            bot_username: Bot username
            bot_id: Bot ID
        """
        if not self.main_bot_token:
            return

        try:
            text = MESSAGES['bot_running'].format(
                bot_username=bot_username,
                bot_id=bot_id
            )

            bot = Bot(token=self.main_bot_token)
            await bot.send_message(chat_id=owner_tg_id, text=text, parse_mode="HTML")
            await bot.session.close()

            logger.info(f"Owner {owner_tg_id} notified about bot running")

        except Exception as e:
            logger.error(f"Owner notification error: {e}")

    async def send_bot_run_to_superadmin(self, bot_username: str, bot_id: int):
        """
        Bot run bo'lganda superadmin ga xabar

        Args:
            bot_username: Bot username
            bot_id: Bot ID
        """
        if not self.main_bot_token or not self.super_admin_id:
            return

        try:
            text = f"✅ <b>Bot ishga tushdi!</b>\n\n🤖 <b>Bot:</b> @{bot_username}\n🆔 <b>ID:</b> {bot_id}\n🔗 <b>Link:</b> https://t.me/{bot_username}\n\n📊 Endi ishtirokchilar qatnashishni boshlaydi!"

            bot = Bot(token=self.main_bot_token)
            await bot.send_message(chat_id=int(self.super_admin_id), text=text, parse_mode="HTML")
            await bot.session.close()

        except Exception as e:
            logger.error(f"Superadmin run notification error: {e}")

    async def send_custom_message(self, user_id: int, text: str, parse_mode: str = "HTML", reply_markup=None):
        """
        Custom xabar yuborish

        Args:
            user_id: Telegram user ID
            text: Xabar matni
            parse_mode: Parse mode
            reply_markup: Keyboard
        """
        if not self.main_bot_token:
            return False

        try:
            bot = Bot(token=self.main_bot_token)
            await bot.send_message(chat_id=user_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
            await bot.session.close()
            return True
        except Exception as e:
            logger.error(f"Send custom message error: {e}")
            return False