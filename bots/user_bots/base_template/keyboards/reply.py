# bots/user_bots/base_template/keyboards/reply.py
"""
Reply keyboards for user bot
Vazifasi: Asosiy menu tugmalari
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from shared.constants import BUTTON_TEXTS


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Asosiy menu keyboard

    Layout:
    [Konkursda qatnashish]
    [Sovg'alar] [Ballarim]
    [Reyting] [Shartlar]

    Returns:
        ReplyKeyboardMarkup
    """
    builder = ReplyKeyboardBuilder()

    buttons = [
        KeyboardButton(text=BUTTON_TEXTS['konkurs_qatnashish']),
        KeyboardButton(text=BUTTON_TEXTS['sovgalar']),
        KeyboardButton(text=BUTTON_TEXTS['ballarim']),
        KeyboardButton(text=BUTTON_TEXTS['reyting']),
        KeyboardButton(text=BUTTON_TEXTS['shartlar']),
    ]

    builder.add(*buttons)
    builder.adjust(1, 2, 2)  # Birinchi qatorda 1, keyin 2, 2

    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Bekor qilish keyboard

    Returns:
        ReplyKeyboardMarkup
    """
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """
    Telefon raqam so'rash keyboard

    Returns:
        ReplyKeyboardMarkup
    """
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# from aiogram.utils.keyboard import ReplyKeyboardBuilder
#
# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
# from aiogram.utils.keyboard import ReplyKeyboardBuilder
# def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
#     builder = ReplyKeyboardBuilder()
#     builder.row(KeyboardButton(text="Konkursda qatnashish"))
#     builder.row(KeyboardButton(text="🎁 Sovg'alar"), KeyboardButton(text="📊 Ballarim"))
#     builder.row(KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="📜 Shartlar"))
#     return builder.as_markup(resize_keyboard=True)