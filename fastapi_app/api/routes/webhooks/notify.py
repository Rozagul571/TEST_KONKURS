# fastapi_app/api/routes/webhooks/notify.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aiogram import Bot
import os
from asgiref.sync import sync_to_async
from django_app.core.models.bot import BotSetUp
from bots.main_bot.utils.message_texts import get_competition_complete_message
from bots.main_bot.buttons.inline import get_contact_admin_keyboard
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class NotificationPayload(BaseModel):
    user_tg_id: int
    competition_name: str
    description: str

@router.post("/handle-user-completed")
async def handle_user_completed(payload: NotificationPayload):
    try:
        # FIX: Bot topish – order_by bilan
        bot_username = await sync_to_async(get_bot_username)(payload.user_tg_id)
        text = get_competition_complete_message(bot_username, payload.competition_name, payload.description)
        keyboard = await get_contact_admin_keyboard()
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=payload.user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        await bot.session.close()
        logger.info(f"Notification {payload.user_tg_id} ga yuborildi")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Notification xatosi: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# def get_bot_username(user_tg_id):
#     bot = BotSetUp.objects.filter(owner__telegram_id=user_tg_id, is_active=True).order_by('-created_at').first()
#     return bot.bot_username if bot else "topilmadi"
# FIX: Yangi async funksiya
@sync_to_async
def get_bot_username_async(user_tg_id):
    """Sync funksiyani async ga o'giradi"""
    return get_bot_username(user_tg_id)

def get_bot_username(user_tg_id):
    bot = BotSetUp.objects.filter(owner__telegram_id=user_tg_id, is_active=True).order_by('-created_at').first()
    return bot.bot_username if bot else "topilmadi"