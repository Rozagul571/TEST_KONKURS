# bots/user_bots/base_template/main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from .handlers.channels import router as channels_router
from .handlers.main_menu import router as menu_router
from .handlers.start import router as start_router

async def start_user_bot(token: str):
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(channels_router)
    dp.include_router(menu_router)
    await dp.start_polling(bot)