from fastapi import APIRouter, Request
from aiogram import Bot
import os
from ..buttons.inline import get_contact_admin_keyboard
from ..utils.message_texts import get_competition_complete_message
from asgiref.sync import sync_to_async
from django_app.core.models.bot import BotSetUp
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/handle-user-completed")
async def handle_user_completed(request: Request):
    """Webhook handler. Vazifasi: Competition to'ldirilgach user ga notification yuborish."""
    try:
        data = await request.json()
        user_tg_id = data["user_tg_id"]
        competition_name = data["competition_name"]
        description = data["description"]

        # FIX: sync_to_async ni to'g'ri ishlatish
        bot_username = await get_bot_username_async(user_tg_id)
        text = get_competition_complete_message(bot_username, competition_name, description)
        keyboard = await get_contact_admin_keyboard()

        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        await bot.session.close()

        logger.info(f"Notification {user_tg_id} ga yuborildi")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Notification xatosi: {e}")
        return {"status": "error", "detail": str(e)}, 500


# FIX: Yangi async funksiya
@sync_to_async
def get_bot_username_async(user_tg_id):
    """Sync funksiyani async ga o'giradi"""
    bot = BotSetUp.objects.filter(owner__telegram_id=user_tg_id, is_active=True).order_by('-created_at').first()
    return bot.bot_username if bot else "topilmadi"