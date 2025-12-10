# fastapi_app/workers/bot_worker.py
from celery import shared_task
from aiogram import Bot
import json
import logging
from django_app.core.models import BotSetUp
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)
fernet = Fernet(os.getenv("FERNET_KEY").encode())

@shared_task
def process_update(bot_id: int, update_json: str):
    try:
        update = json.loads(update_json)
        bot_setup = BotSetUp.objects.get(id=bot_id)
        token = fernet.decrypt(bot_setup.encrypted_token.encode()).decode()
        bot = Bot(token=token)

        # Bu yerda handlerlarni chaqiramiz (masalan, /start)
        if update.get("message", {}).get("text", "").startswith("/start"):
             bot.send_message(
                update["message"]["from"]["id"],
                "Xush kelibsiz! Konkursda qatnashish uchun kanallarga obuna bo‘ling."
            )

        bot.session.close()
    except Exception as e:
        logger.error(f"Worker xatosi: {e}")