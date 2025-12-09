# bots/user_bots/base_template/handlers/start.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
import os

router = Router()

@sync_to_async
def get_active_competition_by_bot_id(bot_id: int):
    """USER Bot uchun faol competition ma'lumotlarini olish. O'ZGARTIRILGAN: bot_id bilan, token emas."""
    from django_app.core.models.bot import BotSetUp
    from django_app.core.models.competition import Competition
    bot = BotSetUp.objects.filter(id=bot_id, status='running', is_active=True).first()
    if bot and bot.competition:
        competition = bot.competition
        return {
            'id': competition.id,
            'name': competition.name,
            'description': competition.description or "Tavsif yo'q",
            'channels': [
                {
                    'id': ch.id,
                    'channel_username': ch.channel_username,
                    'title': ch.title
                }
                for ch in competition.channels.all()
            ],
            'rules_text': competition.rules_text,
            'welcome_image': competition.welcome_image.url if competition.welcome_image else None,
            'end_at': competition.end_at,
            'point_rules': {rule.action_type: rule.points for rule in competition.point_rules.all()},
            'prizes': [{'place': p.place, 'prize_name': p.prize_name, 'prize_amount': p.prize_amount, 'type': p.type} for p in competition.prize_set.all()],
        }
    return None

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        # Bot ID ni env dan olish (subprocess da)
        bot_id = int(os.getenv('BOT_ID', 0))  # O'ZGARTIRILGAN: BOT_ID env
        print(f"🟢 START: {user_id} @{username} bot_id: {bot_id}")
        # Competition topish
        competition = await get_active_competition_by_bot_id(bot_id)
        if not competition:
            await message.answer("❌ Konkurs topilmadi yoki ishlamayapti!")
            return
        # Welcome text
        welcome_text = f"""
👋 Assalomu alaykum <b>{first_name or username}</b>!
🏆 <b>Konkurs:</b> {competition['name']}
📝 <b>Tavsif:</b> {competition['description']}
😎 <b>Konkursda qatnashish uchun kanallarga obuna bo'ling:</b>
        """
        try:
            photo_url = competition['welcome_image'] if competition['welcome_image'] else "https://via.placeholder.com/600x300/0088cc/FFFFFF?text=Konkurs+Bot"
            await message.answer_photo(
                photo=photo_url,
                caption=welcome_text,
                parse_mode="HTML"
            )
        except:
            await message.answer(welcome_text, parse_mode="HTML")
        # Kanallarni ko'rsatish
        await show_channels(message, competition)
    except Exception as e:
        print(f"❌ Start handler xatosi: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

async def show_channels(message: Message, competition: dict):
    """Kanallarni inline buttonlar bilan ko'rsatish"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    channels = competition.get('channels', [])
    for channel in channels:
        channel_username = channel['channel_username'].replace('@', '')
        builder.add(InlineKeyboardButton(
            text=f"📢 {channel['channel_username']}",
            url=f"https://t.me/{channel_username}"
        ))
    builder.add(InlineKeyboardButton(
        text="✅ Obuna bo'ldim",
        callback_data="check_subscription"
    ))
    builder.adjust(1)
    channels_text = "📢 <b>Majburiy kanallar:</b>\n\n"
    for channel in channels:
        channels_text += f"• {channel['channel_username']}\n"
    channels_text += "\nHar bir kanalga obuna bo'lgach, \"✅ Obuna bo'ldim\" tugmasini bosing."
    await message.answer(channels_text, reply_markup=builder.as_markup(), parse_mode="HTML")
