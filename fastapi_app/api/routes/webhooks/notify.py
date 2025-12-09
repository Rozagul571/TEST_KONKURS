from fastapi import APIRouter, Request, HTTPException
from aiogram import Bot
import os
from asgiref.sync import sync_to_async
from django_app.core.models.bot import BotSetUp
from bots.main_bot.utils.message_texts import get_competition_complete_message
from bots.main_bot.buttons.inline import get_contact_admin_keyboard
import logging

logger = logging.getLogger(__name__)
router = APIRouter()  # No prefix here – main.py handles it

@router.post("/")  # Change to "/" – prefix in main.py makes it /api/webhooks/handle-user-completed
async def handle_user_completed(request: Request):
    """User notification handler."""
    try:
        data = await request.json()
        user_tg_id = data["user_tg_id"]
        competition_name = data["competition_name"]
        description = data["description"]
        bot_username = await sync_to_async(get_bot_username)(user_tg_id)
        text = get_competition_complete_message(bot_username, competition_name, description)
        keyboard = await get_contact_admin_keyboard()
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        await bot.send_message(chat_id=user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
        await bot.session.close()
        logger.info(f"User notification sent to {user_tg_id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Notification error: {str(e)}")
        raise HTTPException(500, str(e))

def get_bot_username(user_tg_id):
    bot = BotSetUp.objects.filter(owner__telegram_id=user_tg_id, is_active=True).order_by('-created_at').first()
    return bot.bot_username if bot else "topilmadi"