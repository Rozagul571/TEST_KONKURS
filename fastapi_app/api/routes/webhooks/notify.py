# fastapi_app/api/routes/webhooks/notify.py
"""
Notification webhooks
Vazifasi: User konkurs to'ldirganda notification yuborish
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aiogram import Bot
import os
import logging
from asgiref.sync import sync_to_async

from django_app.core.models.bot import BotSetUp
from bots.main_bot.buttons.inline import get_contact_admin_keyboard
from shared.constants import MESSAGES

logger = logging.getLogger(__name__)

router = APIRouter()


class NotificationPayload(BaseModel):
    user_tg_id: int
    competition_name: str
    description: str


@router.post("/handle-user-completed")
async def handle_user_completed(payload: NotificationPayload):
    """
    User konkurs to'ldirganda notification yuborish

    Note: bots/main_bot/services/notification_service.py dagi
    send_user_competition_completed bilan bir xil vazifani bajaradi.
    Bu endpoint FastAPI orqali chaqiriladi (admin panel dan).
    """
    try:
        bot_username = await get_bot_username_async(payload.user_tg_id)

        # Text - MESSAGES dan olish
        text = MESSAGES['competition_completed'].format(
            bot_username=bot_username,
            name=payload.competition_name,
            description=payload.description
        )

        keyboard = await get_contact_admin_keyboard()

        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=payload.user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        await bot.session.close()

        logger.info(f"Notification sent to {payload.user_tg_id}")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@sync_to_async
def get_bot_username_async(user_tg_id: int) -> str:
    """Bot username ni olish"""
    return get_bot_username(user_tg_id)


def get_bot_username(user_tg_id: int) -> str:
    """Bot username ni sync olish"""
    bot = BotSetUp.objects.filter(owner__telegram_id=user_tg_id, is_active=True).order_by('-created_at').first()
    return bot.bot_username if bot else "topilmadi"