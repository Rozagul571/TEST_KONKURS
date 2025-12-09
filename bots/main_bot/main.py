import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
import django
from aiogram.exceptions import TelegramBadRequest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")
django.setup()
from bots.main_bot.api.webhook import router
from fastapi import FastAPI

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(router, prefix="/api/webhooks")

from .handlers.start import router as start_router
from .handlers.setup import router as setup_router
from .handlers.bot_management import router as bot_management_router

async def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN topilmadi!")
        return
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(setup_router)
    dp.include_router(bot_management_router)
    logger.info("Bot ishga tushdi!")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, handle_signals=False, close_bot_session=True)
    except TelegramBadRequest as e:
        logger.error(f"Telegram xato: {str(e)}")
    except Exception as e:
        logger.error(f"Bot xato: {str(e)}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())