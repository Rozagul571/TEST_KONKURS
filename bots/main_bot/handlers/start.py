# bots/main_bot/handlers/start.py
from aiogram import Router, F
from aiogram.types import Message
from ..utils.db_utils import get_or_create_user
from ..buttons.reply import main_menu_keyboard

router = Router()

@router.message(F.text.startswith("/start"))
async def start_handler(message: Message):
    """Userni salomlash va menu chiqarish. Misol: /start - menu chiqadi."""
    user = await get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer("Xush kelibsiz! Yangi bot yaratish uchun /setup_bot tugmasini bosing.", reply_markup=await
    main_menu_keyboard(user))