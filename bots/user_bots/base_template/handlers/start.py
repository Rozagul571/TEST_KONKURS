# bots/user_bots/base_template/handlers/start.py
from aiogram import Bot
from django_app.core.services.point_calculator import PointCalculator
from fastapi_app.cache import get_bot_settings
from .channels import check_channels
from ..services import UserService


async def start_handler(message: dict, settings: dict, bot: Bot):
    """
    Purpose: Handles /start command for B bots.
    What it does: Checks channels, processes referrals, awards points, sends welcome message.
    Why: Onboards participants, TZ Step 3.
    """
    user_id = message['from']['id']
    bot_id = message['bot_id']  # Set by worker

    # Check rate limit (anti-cheat)
    user_service = UserService()
    if await user_service.anti_cheat_rate_limit(bot_id, user_id, 'start'):
        await bot.send_message(user_id, "Iltimos, biroz kuting va qayta urining!")
        return

    # Check channel subscriptions
    if not await check_channels(bot, user_id, settings['channels']):
        await bot.send_message(user_id, "Iltimos, barcha kanallarga obuna bo‘ling!")
        return

    # Process referral if provided
    ref_code = message['text'].split()[-1] if len(message['text'].split()) > 1 else None
    if ref_code:
        await user_service.save_referral(bot_id, user_id, ref_code)

    # Create user and participant
    user_data = {
        'telegram_id': user_id,
        'username': message['from']['username'] or "",
        'full_name': message['from']['first_name'] or "",
        'is_premium': message['from'].get('is_premium', False)
    }
    user = await user_service.get_or_create_user(user_data)
    participant = await user_service.get_or_create_participant(user, settings['id'])

    # Award points for joining channels
    point_calculator = PointCalculator(settings)
    points = await point_calculator.calculate_channel_points(user_id, user.is_premium)
    await point_calculator.add_points_to_participant(participant, points, 'channel_join')

    # Send welcome message
    welcome_text = (
        f"Xush kelibsiz, {user_data['full_name']}!\n"
        f"Konkurs: {settings['name']}\n"
        f"Tavsif: {settings['description']}\n"
        f"Endi qatnashishingiz mumkin!"
    )
    await bot.send_message(user_id, welcome_text)