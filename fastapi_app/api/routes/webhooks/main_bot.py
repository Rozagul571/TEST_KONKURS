from fastapi import APIRouter, HTTPException, Request
from aiogram import Bot
import os
import logging
from asgiref.sync import sync_to_async
from pydantic import BaseModel

from bots.main_bot.utils.message_texts import get_competition_complete_message
from bots.main_bot.buttons.inline import get_contact_admin_keyboard
from django_app.core.models.bot import BotSetUp

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationPayload(BaseModel):
    """Notification uchun model"""
    user_tg_id: int
    competition_name: str
    description: str


@router.post("/handle-user-completed")
async def handle_user_completed(payload: NotificationPayload):
    """
    User competition to'ldirganda notification yuborish
    Endpoint: POST /api/webhooks/handle-user-completed
    """
    try:
        logger.info(f"📨 Notification for user {payload.user_tg_id}")

        # Bot username ni olish
        bot_username = await get_bot_username_async(payload.user_tg_id)

        # Xabar matnini tayyorlash
        text = get_competition_complete_message(
            bot_username,
            payload.competition_name,
            payload.description
        )

        # Keyboard olish
        keyboard = await get_contact_admin_keyboard()

        # Xabar yuborish
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(
            chat_id=payload.user_tg_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await bot.session.close()

        logger.info(f"✅ Notification sent to {payload.user_tg_id}")

        return {"status": "success", "message": "Notification sent"}

    except Exception as e:
        logger.error(f"Notification error: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@sync_to_async
def get_bot_username_async(user_tg_id: int) -> str:
    """Bot username ni async tarzda olish"""
    try:
        bot = BotSetUp.objects.filter(
            owner__telegram_id=user_tg_id,
            is_active=True
        ).order_by('-created_at').first()

        return bot.bot_username if bot else "bot_topilmadi"
    except Exception as e:
        logger.error(f"Get bot username error: {e}")
        return "xatolik"