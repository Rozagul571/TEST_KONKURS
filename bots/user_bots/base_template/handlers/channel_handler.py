# bots/user_bots/handlers/channel_handler.py
"""
Obuna bo'ldim tugmasi handleri
"""

import logging
from typing import Dict, Any
from aiogram import Bot

from bots.user_bots.base_template.cache.bot_cache import BotCache
from bots.user_bots.base_template.keyboards import get_channels_keyboard
from bots.user_bots.base_template.services import PointService
from bots.user_bots.base_template.services.registration_service import RegistrationService
from shared.redis_client import redis_client


logger = logging.getLogger(__name__)


class ChannelHandler:
    """Channel handler - 'Obuna bo'ldim' tugmasi"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.bot_cache = BotCache(bot_id)
        self.registration_service = RegistrationService(bot_id)
        self.point_service = PointService(bot_id)

    async def handle_check_subscription(self, callback: Dict[str, Any], bot: Bot) -> None:
        """'Obuna bo'ldim' tugmasi bosilganda"""
        try:
            user_id = callback['from']['id']
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']

            # 1. Check channels
            channels_status = await self._check_channels(user_id, bot)

            if not channels_status['all_joined']:
                # Update message with remaining channels
                await self._update_channels_message(
                    user_id, chat_id, message_id, bot, channels_status
                )

                await bot.answer_callback_query(
                    callback['id'],
                    text=f"❌ Yana {len(channels_status['not_joined'])} ta kanalga obuna bo'lish kerak!",
                    show_alert=True
                )
                return

            # 2. All channels joined - complete registration
            await self._complete_registration(user_id, callback, bot)

            await bot.answer_callback_query(
                callback['id'],
                text="✅ Barcha kanallarga obuna bo'ldingiz!",
                show_alert=True
            )

        except Exception as e:
            logger.error(f"Check subscription error: {e}")
            await bot.answer_callback_query(
                callback['id'],
                text="❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
                show_alert=True
            )

    async def _check_channels(self, user_id: int, bot: Bot) -> Dict[str, Any]:
        """Kanallarni tekshirish"""
        channels = await self.bot_cache.get_channels()

        not_joined = []
        for channel in channels:
            try:
                member = await bot.get_chat_member(
                    chat_id=f"@{channel['channel_username']}",
                    user_id=user_id
                )

                if member.status not in ['member', 'administrator', 'creator']:
                    not_joined.append(channel)

            except Exception as e:
                logger.warning(f"Channel check error: {e}")
                not_joined.append(channel)

        return {
            'all_joined': len(not_joined) == 0,
            'not_joined': not_joined,
            'total': len(channels)
        }

    async def _update_channels_message(self, user_id: int, chat_id: int, message_id: int,
                                       bot: Bot, channels_status: Dict) -> None:
        """Kanallar xabarini yangilash"""
        keyboard = get_channels_keyboard(channels_status['not_joined'])

        remaining = len(channels_status['not_joined'])
        text = f"⚠️ *Hali {remaining} ta kanalga obuna bo'lmagansiz!*\n\n"

        for channel in channels_status['not_joined'][:5]:
            text += f"• @{channel['channel_username']}\n"

        if remaining > 5:
            text += f"• ... va yana {remaining - 5} ta\n"

        text += "\n👇 *Har bir kanal tugmasini bosing va obuna bo'ling*"

        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def _complete_registration(self, user_id: int, callback: Dict, bot: Bot) -> None:
        """Ro'yxatdan o'tishni yakunlash"""
        try:
            # Extract user data from callback
            user_data = {
                'telegram_id': user_id,
                'username': callback['from'].get('username', ''),
                'first_name': callback['from'].get('first_name', ''),
                'last_name': callback['from'].get('last_name', ''),
                'full_name': f"{callback['from'].get('first_name', '')} {callback['from'].get('last_name', '')}".strip(),
                'is_premium': callback['from'].get('is_premium', False)
            }

            # Check pending referral
            ref_key = f"pending_referral:{self.bot_id}:{user_id}"
            referrer_id = None

            if redis_client.is_connected():
                referrer_id = redis_client.client.get(ref_key)

            referrer = None
            if referrer_id:
                referrer = await self.registration_service.get_participant_by_id(int(referrer_id))

            # Register user
            participant = await self.registration_service.register_user(
                user_data=user_data,
                referrer=referrer
            )

            if not participant:
                raise Exception("Failed to register user")

            # Add channel points
            await self.point_service.add_channel_points(
                participant=participant,
                is_premium=user_data['is_premium']
            )

            # Clear pending referral
            if redis_client.is_connected() and referrer_id:
                redis_client.client.delete(ref_key)

            # Update message
            await bot.edit_message_text(
                chat_id=callback['message']['chat']['id'],
                message_id=callback['message']['message_id'],
                text="🎉 *Barcha kanallarga obuna bo'ldingiz! Ro'yxatdan o'tish yakunlandi!*",
                parse_mode="Markdown"
            )

            # Send success message
            await self._send_success_message(user_id, bot, participant)

        except Exception as e:
            logger.error(f"Complete registration error: {e}")
            raise

    async def _send_success_message(self, user_id: int, bot: Bot, participant) -> None:
        """Muvaffaqiyat xabarini yuborish"""
        # This uses the same logic as StartHandler._send_success_message
        from bots.user_bots.base_template.handlers.start_handler import StartHandler
        handler = StartHandler(self.bot_id)
        await handler._send_success_message(user_id, bot, participant)