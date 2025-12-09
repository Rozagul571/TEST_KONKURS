# bots/user_bots/base_template/buttons/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🎁 Sovg'alar"), KeyboardButton(text="📊 Ballarim"))
    builder.row(KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="📜 Shartlar"))
    return builder.as_markup(resize_keyboard=True)