from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import json
from typing import Dict, Any

from shared.redis_client import redis_client
from bots.user_bots.base_template.services import UserService
from asgiref.sync import sync_to_async
import django

logger = logging.getLogger(__name__)


async def start_handler(message: Dict[str, Any], settings: Dict[str, Any], bot: Bot):
    """
    /start handler for B bots - Fully working version
    """
    try:
        user_id = message['from']['id']
        bot_id = settings.get('id', 0)

        logger.info(f"🚀 /start from user {user_id} for bot {bot_id}")

        # 1. Kanallarni tekshirish (cached)
        channels_joined = await _check_channels_cached(bot, user_id, settings.get('channels', []))

        if not channels_joined['all_joined']:
            # Kanallarni ko'rsatish
            await _show_channels(message, bot, channels_joined['not_joined_channels'])
            return

        # 2. Referralni tekshirish
        ref_code = None
        if 'text' in message:
            parts = message['text'].split()
            if len(parts) > 1:
                ref_code = parts[1]

        # 3. User yaratish yoki olish
        user_service = UserService()
        user_data = {
            'telegram_id': user_id,
            'username': message['from'].get('username', ''),
            'full_name': f"{message['from'].get('first_name', '')} {message['from'].get('last_name', '')}".strip(),
            'is_premium': message['from'].get('is_premium', False)
        }

        user = await user_service.get_or_create_user(user_data)

        # 4. Participant yaratish yoki olish
        participant = await user_service.get_or_create_participant(user, bot_id)

        # 5. Referralni qayta ishlash
        if ref_code and len(ref_code) > 3:
            await _process_referral(bot_id, user_id, ref_code, participant)

        # 6. Ball berish (channel join uchun)
        from django_app.core.services.point_calculator import PointCalculator

        point_calculator = PointCalculator(settings)
        points = await point_calculator.calculate_channel_points(
            user_id,
            user.is_premium
        )

        await point_calculator.add_points_to_participant(
            participant,
            points,
            'channel_join'
        )

        # 7. Welcome message yuborish
        await _send_welcome_message(message, bot, settings, user_data)

        logger.info(f"✅ /start completed for user {user_id}")

    except Exception as e:
        logger.error(f"Start handler error: {e}", exc_info=True)
        await bot.send_message(
            message['from']['id'],
            "❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
        )


async def _check_channels_cached(bot: Bot, user_id: int, channels: list) -> Dict[str, Any]:
    """Kanallarni tekshirish (15 soniyalik cache)"""
    cache_key = f"channel_check:{bot.token}:{user_id}"

    # Cache dan olish
    if redis_client.is_connected():
        cached = redis_client.client.get(cache_key)
        if cached:
            return json.loads(cached)

    # Tekshirish
    not_joined = []
    for channel in channels:
        try:
            username = channel.get('channel_username', '').replace('@', '')
            if not username:
                continue

            member = await bot.get_chat_member(f"@{username}", user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(channel)
        except Exception as e:
            logger.error(f"Channel check error: {e}")
            not_joined.append(channel)

    result = {
        'all_joined': len(not_joined) == 0,
        'not_joined_channels': not_joined
    }

    # Cache ga saqlash (15 soniya)
    if redis_client.is_connected():
        redis_client.client.setex(cache_key, 15, json.dumps(result))

    return result


async def _show_channels(message: Dict, bot: Bot, channels: list):
    """Obuna bo'lish kerak bo'lgan kanallarni ko'rsatish"""
    keyboard = []

    for channel in channels:
        username = channel.get('channel_username', '').replace('@', '')
        if username:
            keyboard.append([InlineKeyboardButton(
                text=f"📢 {channel.get('channel_username')}",
                url=f"https://t.me/{username}"
            )])

    keyboard.append([InlineKeyboardButton(
        text="✅ Obuna bo'ldim",
        callback_data="check_subscription"
    )])

    await bot.send_message(
        message['from']['id'],
        "🎯 *Konkursda qatnashish uchun quyidagi kanallarga obuna bo'ling:*\n\n"
        "Har bir kanalga obuna bo'lgach, ✅ tugmasini bosing.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


async def _process_referral(bot_id: int, user_id: int, ref_code: str, participant):
    """Referralni qayta ishlash"""
    try:
        from bots.user_bots.base_template.services import UserService

        user_service = UserService()
        referrer = await user_service.get_participant_by_code(ref_code, bot_id)

        if referrer and referrer.user.telegram_id != user_id:
            # Redis ga referral ma'lumotini saqlash
            referral_data = {
                'bot_id': bot_id,
                'referrer_id': referrer.user.telegram_id,
                'referred_id': user_id,
                'timestamp': django.utils.timezone.now().isoformat()
            }

            if redis_client.is_connected():
                redis_client.client.lpush(
                    f"referral_queue:{bot_id}",
                    json.dumps(referral_data)
                )

            logger.info(f"Referral saved: {referrer.user.telegram_id} -> {user_id}")

    except Exception as e:
        logger.error(f"Process referral error: {e}")


async def _send_welcome_message(message: Dict, bot: Bot, settings: Dict, user_data: Dict):
    """Welcome message yuborish"""
    from bots.user_bots.base_template.buttons.reply import get_main_menu_keyboard

    welcome_text = (
        f"🎉 *Xush kelibsiz, {user_data['full_name']}!*\n\n"
        f"🏆 *Konkurs:* {settings.get('name', 'Konkurs')}\n"
        f"📝 *Tavsif:* {settings.get('description', '')[:100]}...\n\n"
        "✅ *Siz konkursda muvaffaqiyatli ro'yxatdan o'tdingiz!*\n\n"
        "👇 *Quyidagi menyu orqali konkursda ishtirok eting:*"
    )

    await bot.send_message(
        message['from']['id'],
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )