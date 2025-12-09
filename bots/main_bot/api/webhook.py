# bots/main_bot/api/webhooks.py
from fastapi import APIRouter, Request
from aiogram import Bot
import os
from ..buttons.inline import get_contact_admin_keyboard
from ..utils.message_texts import get_competition_complete_message
from asgiref.sync import sync_to_async
from django_app.core.models.bot import BotSetUp

router = APIRouter()

@router.post("/handle-user-completed")
async def handle_user_completed(request: Request):
    """Webhook handler. Vazifasi: Competition to'ldirilgach user ga notification yuborish. Misol: POST {user_tg_id:123} - xabar yuboriladi."""
    data = await request.json()
    user_tg_id = data["user_tg_id"]
    competition_name = data["competition_name"]
    description = data["description"]
    bot_username = await sync_to_async(get_bot_username)(user_tg_id)
    text = get_competition_complete_message(bot_username, competition_name, description)
    keyboard = await get_contact_admin_keyboard()
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    try:
        await bot.send_message(chat_id=user_tg_id, text=text, reply_markup=keyboard, parse_mode="HTML")
    finally:
        await bot.session.close()
    return {"status": "success"}

def get_bot_username(user_tg_id):
    bot = BotSetUp.objects.filter(owner__telegram_id=user_tg_id, status='pending').first()
    return bot.bot_username if bot else "topilmadi"