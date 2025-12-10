# bots/user_bots/base_template/handlers/channels.py
from aiogram import Bot

from django_app.core.services.point_calculator import PointCalculator
from fastapi_app.cache import get_bot_settings
from bots.user_bots.base_template.services import UserService
# from .services.point_calculator import PointCalculator

async def check_subscription(callback: dict, settings: dict, bot: Bot):
    """
    Purpose: Handles 'check_subscription' callback for channel verification.
    What it does: Checks if user joined all channels, awards points if complete.
    """
    user_id = callback['from']['id']
    bot_id = callback['bot_id']

    # Check rate limit
    user_service = UserService()
    if await user_service.anti_cheat_rate_limit(bot_id, user_id, 'check_subscription'):
        await bot.answer_callback_query(callback['id'], text="Iltimos, biroz kuting!")
        return

    # Check channel memberships
    not_joined = []
    for channel in settings['channels']:
        try:
            member = await bot.get_chat_member(channel['channel_username'], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(channel)
        except:
            not_joined.append(channel)

    if not not_joined:
        # All channels joined
        user_data = {
            'telegram_id': user_id,
            'username': callback['from']['username'] or "",
            'full_name': callback['from']['first_name'] or "",
            'is_premium': callback['from'].get('is_premium', False)
        }
        user = await user_service.get_or_create_user(user_data)
        participant = await user_service.get_or_create_participant(user, settings['id'])

        point_calculator = PointCalculator(settings)
        points = await point_calculator.calculate_channel_points(user_id, user.is_premium)
        await point_calculator.add_points_to_participant(participant, points, 'channel_join')

        await bot.edit_message_text(
            chat_id=callback['message']['chat']['id'],
            message_id=callback['message']['message_id'],
            text="🎉 Barcha kanallarga obuna bo‘ldingiz! Konkursda qatnashishingiz mumkin."
        )
        await bot.answer_callback_query(callback['id'], text="Muvaffaqiyatli!")
    else:
        # Show remaining channels
        buttons = []
        for channel in not_joined:
            username = channel['channel_username'].replace('@', '')
            buttons.append({
                "text": channel['channel_username'],
                "url": f"https://t.me/{username}"
            })
        buttons.append({"text": "✅ Obuna bo‘ldim", "callback_data": "check_subscription"})
        keyboard = {"inline_keyboard": [buttons]}

        await bot.edit_message_reply_markup(
            chat_id=callback['message']['chat']['id'],
            message_id=callback['message']['message_id'],
            reply_markup=keyboard
        )
        await bot.answer_callback_query(
            callback['id'],
            text=f"Yana {len(not_joined)} ta kanalga obuna bo‘lish kerak!"
        )

async def check_channels(bot: Bot, user_id: int, channels: list) -> bool:
    """
    Purpose: Checks if a user is subscribed to all required channels.
    What it does: Queries Telegram API for membership status.
    Why: Validates channel subscriptions, TZ Step 3.
    """
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel['channel_username'], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True