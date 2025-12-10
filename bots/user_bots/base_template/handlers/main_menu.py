# bots/user_bots/base_template/handlers/main_menu.py
from aiogram import Bot
from django.db.models import F
from django_app.core.models import Participant
from asgiref.sync import sync_to_async
from fastapi_app.cache import redis_client
from bots.user_bots.base_template.services.user_service import UserService

async def prizes_handler(message: dict, settings: dict, bot: Bot):
    user_id = message['from']['id']
    bot_id = message.get('bot_id', 0)
    user_service = UserService()

    if await user_service.anti_cheat_rate_limit(bot_id, user_id, 'prizes'):
        await bot.send_message(user_id, "Iltimos, biroz kuting!")
        return

    referral_code = await user_service.get_referral_code(user_id)
    bot_username = (await bot.get_me())['username']
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"

    prizes_text = "Sovg'alar:\n"
    for prize in settings.get('prizes', []):
        prizes_text += f"{prize['place']}-o‘rin: {prize['prize_name']}\n"
    prizes_text += f"\nReferral linkingiz: {referral_link}"

    await bot.send_message(user_id, prizes_text)

async def points_handler(message: dict, settings: dict, bot: Bot):
    user_id = message['from']['id']
    bot_id = message.get('bot_id', 0)

    points = int(redis_client.get(f"user_points:{bot_id}:{user_id}") or 0)
    await bot.send_message(user_id, f"Ballaringiz: {points}")

async def rating_handler(message: dict, settings: dict, bot: Bot):
    user_id = message['from']['id']
    bot_id = message.get('bot_id', 0)

    leaderboard = await sync_to_async(list)(
        Participant.objects.filter(competition_id=settings['id'])
        .order_by(F('current_points').desc())
        .values('user__username', 'current_points')[:10]
    )

    text = "Top 10:\n"
    for i, p in enumerate(leaderboard, 1):
        text += f"{i}. @{p['user__username']} - {p['current_points']} ball\n"
    await bot.send_message(user_id, text)

async def rules_handler(message: dict, settings: dict, bot: Bot):
    user_id = message['from']['id']
    await bot.send_message(user_id, settings.get('rules_text', 'Qoidalar yo‘q'))