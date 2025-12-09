from fastapi import APIRouter, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from asgiref.sync import sync_to_async
from django_app.core.models import BotSetUp
from cryptography.fernet import Fernet
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Bitta universal dispatcher — barcha B botlar uchun
dp = Dispatcher()
from bots.user_bots.base_template.handlers.start import router as start_router
from bots.user_bots.base_template.handlers.channels import router as channels_router
from bots.user_bots.base_template.handlers.main_menu import router as menu_router
dp.include_router(start_router)
dp.include_router(channels_router)
dp.include_router(menu_router)

@router.post("/user/{bot_id}")
async def universal_webhook(bot_id: int, update: Update):
    """Barcha B botlar uchun bitta webhook"""
    try:
        bot_setup = await sync_to_async(BotSetUp.objects.get)(
            id=bot_id,
            status='running'
        )
        token = Fernet(os.getenv("FERNET_KEY").encode()).decrypt(
            bot_setup.encrypted_token.encode()
        ).decode()

        bot = Bot(token=token)
        await dp.feed_update(bot=bot, update=update)
        await bot.session.close()
        return {"ok": True}
    except Exception as e:
        logger.error(f"B bot {bot_id} xatosi: {e}")
        raise HTTPException(500, "Ichki xato")