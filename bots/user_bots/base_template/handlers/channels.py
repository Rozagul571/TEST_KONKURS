# bots/user_bots/base_template/handlers/channels.py
import os
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from .start import get_active_competition_by_bot_id  # FIX: get_active_competition_by_token -> get_active_competition_by_bot_id
from ..buttons.reply import get_main_menu_keyboard  # reply.py dan
from ..services.user_service import UserService
from ..services.channel_service import ChannelService
from django_app.core.services.point_calculator import PointCalculator

router = Router()

@router.callback_query(F.data == "check_subscription")
async def check_subscription(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    bot = callback.bot
    bot_id = int(os.getenv('BOT_ID', 0))  # bot_id env dan
    competition = await get_active_competition_by_bot_id(bot_id)  # FIX: token emas, bot_id
    if not competition:
        await callback.answer("❌ Konkurs topilmadi!")
        return
    channel_service = ChannelService(competition)
    status = await channel_service.check_user_channels_status(user_id, bot)
    if status['all_joined']:
        await process_successful_join(callback, competition, user_id)
    else:
        await show_remaining_channels(callback, status['not_joined_channels'])


async def process_successful_join(callback: CallbackQuery, competition: dict, user_id: int):
    user_service = UserService()
    user = await user_service.get_or_create_user_from_message(callback.message, competition)
    participant = await user_service.get_or_create_participant(user, competition)
    if not participant:
        await callback.answer("❌ Xatolik yuz berdi!")
        return
    point_calculator = PointCalculator(competition)
    total_points = await point_calculator.calculate_channel_points(user_id, user.is_premium)
    await point_calculator.add_points_to_participant(participant, total_points, 'channel_join')
    success_text = f"🎉 Tabriklaymiz! Siz barcha kanallarga obuna bo'ldingiz.\n✅ Sizga {total_points} ball berildi!\n🚀 Endi konkursda qatnashishingiz mumkin!"
    await callback.message.edit_text(success_text, parse_mode="HTML")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu_keyboard())
    await callback.answer("✅ Muvaffaqiyatli!")

async def show_remaining_channels(callback: CallbackQuery, not_joined_channels: list):
    builder = InlineKeyboardBuilder()
    for channel in not_joined_channels:
        channel_username = channel['channel_username'].replace('@', '')
        builder.add(InlineKeyboardButton(text=f"📢 {channel['channel_username']}", url=f"https://t.me/{channel_username}"))
    builder.add(InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_subscription"))
    builder.adjust(1)
    remaining_text = f"❌ Hali {len(not_joined_channels)} ta kanalga obuna bo'lmagansiz!\nQuyidagi kanallarga obuna bo'ling va \"✅ Obuna bo'ldim\" tugmasini bosing:"
    await callback.message.edit_text(remaining_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer(f"Hali {len(not_joined_channels)} ta kanal qoldi!")