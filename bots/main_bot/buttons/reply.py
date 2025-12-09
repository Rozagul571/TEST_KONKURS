# bots/main_bot/buttons/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async
from django_app.core.models.bot import BotSetUp

async def main_menu_keyboard(user):
    """Main menu reply keyboard. Vazifasi: /setup_bot va boshqa tugmalar. Misol: Agar pending bot bo'lsa, 'Botni ishga tushirish' chiqadi."""
    kb = [[KeyboardButton(text="/setup_bot")]]
    bots = await sync_to_async(list)(BotSetUp.objects.filter(owner=user, status="pending"))
    if bots:
        kb.append([KeyboardButton(text="Botni ishga tushirish")])
    kb.append([KeyboardButton(text="⬅️ Orqaga qaytish")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)