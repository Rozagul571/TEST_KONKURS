#bots/user_bots/base_template/handlers/callback_handler.py
"""
Callback handler for inline buttons - TO'G'RILANGAN
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
    """Callback handler for inline buttons"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def handle_check_subscription(self, callback: Dict[str, Any], settings: Dict[str, Any], bot: Bot):
        """Handle check subscription callback"""
        user_id = callback['from']['id']

        try:
            # Rate limit check
            if await self._check_rate_limit(user_id, 'check_subscription'):
                await bot.answer_callback_query(
                    callback['id'],
                    text="🚫 Juda tez so'rov yuborayapsiz. Iltimos, biroz kuting.",
                    show_alert=True
                )
                return

            # Check channels
            channel_service = ChannelService(settings)
            channels_status = await channel_service.check_user_channels(user_id, bot)

            # If not all joined, update message
            if not channels_status['all_joined']:
                await self._update_channels_message(user_id, callback, bot,
                                                    channels_status['not_joined'], settings)
                return

            # All channels joined - process completion
            await self._complete_subscription(user_id, callback, bot, settings)

        except Exception as e:
            logger.error(f"Handle check subscription error: {e}")
            await bot.answer_callback_query(
                callback['id'],
                text="❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
                show_alert=True
            )

    async def _check_rate_limit(self, user_id: int, action: str) -> bool:
        """Check rate limit"""
        try:
            key = CACHE_KEYS['rate_limit'].format(self.bot_id, user_id, action)
            limit_config = RATE_LIMITS.get('join_check', {'limit': 4, 'window': 15})

            return await redis_client.check_rate_limit(
                key,
                limit_config['limit'],
                limit_config['window']
            )
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False

    async def _update_channels_message(self, user_id: int, callback: Dict, bot: Bot,
                                       not_joined: list, settings: Dict):
        """Update channels message"""
        try:
            # Create keyboard
            keyboard = get_channels_keyboard(not_joined)

            # Prepare text
            remaining = len(not_joined)
            text = f"⚠️ *Hali {remaining} ta kanalga obuna bo'lmagansiz!*\n\n"
            text += f"📋 *Obuna bo'lish kerak:*\n"

            for channel in not_joined[:5]:
                username = channel.get('channel_username', '').replace('@', '')
                text += f"• @{username}\n"

            if remaining > 5:
                text += f"• ... va yana {remaining - 5} ta\n"

            text += "\n👇 *Qadamlar:*\n"
            text += "1. Har bir kanal tugmasini bosing\n"
            text += "2. Kanalga o'ting va 'Join' tugmasini bosing\n"
            text += "3. Barchasiga obuna bo'lgach, ✅ tugmasini qayta bosing"

            # Update message
            message_id = callback['message']['message_id']
            chat_id = callback['message']['chat']['id']

            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

            # Answer callback
            await bot.answer_callback_query(
                callback['id'],
                text=f"❌ Yana {remaining} ta kanalga obuna bo'lish kerak!",
                show_alert=True
            )

        except Exception as e:
            logger.error(f"Update channels message error: {e}")
            await bot.answer_callback_query(
                callback['id'],
                text="❌ Xatolik yuz berdi",
                show_alert=True
            )

    async def _complete_subscription(self, user_id: int, callback: Dict, bot: Bot, settings: Dict):
        """Complete subscription process"""
        try:
            # Update message
            message_id = callback['message']['message_id']
            chat_id = callback['message']['chat']['id']

            success_text = (
                "🎉 *Tabriklaymiz!*\n\n"
                "✅ *Barcha kanallarga obuna bo'ldingiz!*\n\n"
                "🏆 *Endi siz konkursda rasmiy ishtirokchisiz!*\n\n"
                "🔄 Ro'yxatdan o'tish yakunlanmoqda..."
            )

            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=success_text,
                parse_mode="Markdown"
            )

            # Answer callback
            await bot.answer_callback_query(
                callback['id'],
                text="✅ Barcha kanallarga obuna bo'ldingiz!",
                show_alert=True
            )

            # Now trigger the start handler to complete registration
            from .start_handler import StartHandler
            start_handler = StartHandler(self.bot_id)

            # Create a mock message for start handler
            mock_message = {
                'from': callback['from'],
                'chat': {'id': user_id},
                'text': '/start'
            }

            # Call start handler to complete registration
            await start_handler.handle_start(mock_message, bot)

        except Exception as e:
            logger.error(f"Complete subscription error: {e}")
            await bot.answer_callback_query(
                callback['id'],
                text="❌ Xatolik yuz berdi. Iltimos, /start ni qayta bosing.",
                show_alert=True
            )