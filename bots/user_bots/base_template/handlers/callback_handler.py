# bots/user_bots/base_template/handlers/callback_handler.py
"""
Callback handler for inline buttons
"""
import logging
from typing import Dict, Any
from aiogram import Bot

from bots.user_bots.base_template.services.channel_service import ChannelService
from shared.redis_client import redis_client
from shared.constants import CACHE_KEYS, RATE_LIMITS
from bots.user_bots.base_template.keyboards.inline import get_channels_keyboard

logger = logging.getLogger(__name__)

class CallbackHandler:
    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def handle_check_subscription(self, callback: Dict[str, Any], settings: Dict[str, Any], bot: Bot):
        user_id = callback['from']['id']

        try:
            # Rate limit
            if await self._check_rate_limit(user_id, 'check_subscription'):
                await bot.answer_callback_query(callback['id'], "Birozdan keyin urinib koring", show_alert=True)
                return

            # Chanel check
            channel_service = ChannelService(settings)
            channels_status = await channel_service.check_user_channels(user_id, bot)

            if not channels_status['all_joined']:
                await self._update_channels_message(user_id, callback, bot, channels_status['not_joined'], settings)
                return

            # Hammasi obuna bo‘lingan – ro‘yxatdan o‘tkazish
            await self._complete_subscription(user_id, callback, bot)

        except Exception as e:
            logger.error(f"Handle check subscription error: {e}")
            await bot.answer_callback_query(callback['id'], "Xatolik yuz berdi.", show_alert=True)

    async def _check_rate_limit(self, user_id: int, action: str) -> bool:
        """Foydalanuvchi harakatini rate limit """
        key = CACHE_KEYS['rate_limit'].format(self.bot_id, user_id, action)
        limit_config = RATE_LIMITS.get('join_check', {'limit': 4, 'window': 15})
        return await redis_client.check_rate_limit(key, limit_config['limit'], limit_config['window'])

    async def _update_channels_message(self, user_id: int, callback: Dict, bot: Bot, not_joined: list, settings: Dict):
        """Obuna bo‘linmagan kanallarni yangilash"""
        keyboard = get_channels_keyboard(not_joined)
        remaining = len(not_joined)
        text = f"⚠️ Hali {remaining} ta kanalga obuna bo‘lmagansiz!\n\n"
        for channel in not_joined[:5]:
            text += f"• @{channel.get('channel_username', '').replace('@', '')}\n"
        if remaining > 5:
            text += f"• ... va yana {remaining - 5} ta\n"
        text += "\n👇 Har bir tugmani bosing va obuna bo‘ling"

        await bot.edit_message_text(
            chat_id=callback['message']['chat']['id'],
            message_id=callback['message']['message_id'],
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

        await bot.answer_callback_query(callback['id'], f"Yana {remaining} ta kanal kerak!", show_alert=True)

    async def _complete_subscription(self, user_id: int, callback: Dict, bot: Bot):
        """Obuna tugagach – /start ni chaqirish"""
        try:
            success_text = "🎉 Barcha kanallarga obuna bo‘ldingiz! Ro‘yxatdan o‘tish yakunlanmoqda..."
            await bot.edit_message_text(
                chat_id=callback['message']['chat']['id'],
                message_id=callback['message']['message_id'],
                text=success_text,
                parse_mode="Markdown"
            )

            await bot.answer_callback_query(callback['id'], "✅ Muvaffaqiyatli!", show_alert=True)

            # Start handlerni chaqirish
            from .start_handler import StartHandler
            start_handler = StartHandler(self.bot_id)
            mock_message = {
                'from': callback['from'],
                'chat': {'id': user_id},
                'text': '/start'
            }
            await start_handler.handle_start(mock_message, bot)

        except Exception as e:
            logger.error(f"Complete subscription error: {e}")
            await bot.answer_callback_query(callback['id'], "Xatolik. /start ni qayta bosing.", show_alert=True)