#bots/main_bot/services/notification_service.py
from asgiref.sync import sync_to_async
from aiogram import Bot
from django.conf import settings
from bots.main_bot.buttons.inline import get_bot_management_keyboard
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Barcha notification textlari va yuborish logikasi shu yerda"""
    def __init__(self):
        self.main_bot_token = settings.TELEGRAM_BOT_TOKEN
        self.super_admin_id = getattr(settings, 'SUPER_ADMIN_TELEGRAM_ID', None)

    async def send_superadmin_new_bot(self, user, bot_username: str, admin_username: str, bot_id: int):
        """Yangi bot yaratilganda superadmin ga xabar"""
        if not self.main_bot_token or not self.super_admin_id:
            return

        full_display = f"{user.first_name or ''} {user.last_name or 'Nomalum'}"
        if user.username:
            full_display += f" @{user.username}"

        text = (
            f"🔔 <b>Yangi Bot Tayyor!</b>\n\n"
            f"👤 <b>Admin:</b> {full_display.strip()}\n"
            f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
            f"🤖 <b>Bot:</b> @{bot_username}\n"
            f"🔑 <b>Admin login:</b> <code>{admin_username}</code>\n\n"
            "⏳ <b>Status:</b> Pending - Tasdiqlang yoki rad eting"
        )

        keyboard = get_bot_management_keyboard(bot_id)
        bot = Bot(token=self.main_bot_token)
        try:
            await bot.send_message(int(self.super_admin_id), text=text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Superadmin notification error: {e}")
        finally:
            await bot.session.close()

    async def send_user_competition_completed(self, user_tg_id: int, bot_username: str, competition_name: str, description: str):
        """User konkurs to'ldirganda xabar"""
        if not self.main_bot_token:
            return

        text = (
            f"🎉 <b>Konkurs muvaffaqiyatli yaratildi!</b>\n\n"
            f"🤖 <b>Sizning botingiz:</b> @{bot_username}\n"
            f"🏆 <b>Konkurs nomi:</b> {competition_name}\n"
            f"📝 <b>Tavsif:</b> {description}\n\n"
            "✅ <b>Barcha kerakli ma'lumotlar to'ldirildi!</b>\n"
            "⏳ <b>Status:</b> Pending - SuperAdmin tasdiqlashini kuting\n"
            "🚀 <b>Run qilish uchun SuperAdmin bilan bog'lanish</b> 👇"
        )

        keyboard = get_bot_management_keyboard(0)
        bot = Bot(token=self.main_bot_token)
        try:
            await bot.send_message(user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.error(f"User {user_tg_id} notification error: {e}")
        finally:
            await bot.session.close()

    async def send_bot_run_to_owner(self, owner_tg_id: int, bot_username: str, bot_id: int):
        """Bot run bo'lganda owner ga xabar"""
        if not self.main_bot_token:
            return

        text = (
            f"🎉 <b>Bot ishga tushdi!</b>\n\n"
            f"🤖 <b>Bot:</b> @{bot_username}\n"
            f"🆔 <b>ID:</b> {bot_id}\n"
            f"🔗 <b>Link:</b> https://t.me/{bot_username}\n\n"
            "✅ <b>Status:</b> Ishga tushdi\n"
            "📊 Endi ishtirokchilar qatnasha boshlashi mumkin!"
        )

        bot = Bot(token=self.main_bot_token)
        try:
            await bot.send_message(owner_tg_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Owner {owner_tg_id} run notification error: {e}")
        finally:
            await bot.session.close()

    async def send_bot_run_to_superadmin(self, bot_username: str, bot_id: int):
        """Bot run bo'lganda superadmin ga xabar"""
        if not self.main_bot_token or not self.super_admin_id:
            return

        text = (
            f"✅ <b>Bot ishga tushdi!</b>\n\n"
            f"🤖 <b>Bot:</b> @{bot_username}\n"
            f"🆔 <b>ID:</b> {bot_id}\n"
            f"🔗 <b>Link:</b> https://t.me/{bot_username}\n\n"
            "📊 Endi ishtirokchilar qatnashishni boshlaydi!"
        )

        bot = Bot(token=self.main_bot_token)
        try:
            await bot.send_message(int(self.super_admin_id), text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Superadmin run notification error: {e}")
        finally:
            await bot.session.close()