# bots/user_bots/base_template/handlers/channel_handler.py
"""
Obuna bo'ldim tugmasi handleri - TO'G'RILANGAN
Vazifasi: Foydalanuvchi "A'zo bo'ldim" tugmasini bosganda kanal obunasini tekshirish
"""
import logging
from typing import Dict, Any, Optional
from aiogram import Bot

from bots.user_bots.base_template.cache.bot_cache import BotCache
from bots.user_bots.base_template.keyboards.inline import get_channels_keyboard
from bots.user_bots.base_template.services.point_service import PointService
from bots.user_bots.base_template.services.registration_service import RegistrationService
from bots.user_bots.base_template.services.channel_service import ChannelService
from shared.redis_client import redis_client
from shared.constants import MESSAGES

logger = logging.getLogger(__name__)


class ChannelHandler:
    """A'zo bo'ldim tugmasi handleri"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.bot_cache = BotCache(bot_id)
        self.registration_service = RegistrationService(bot_id)
        self.point_service = PointService(bot_id)

    async def handle_check_subscription(self, callback: Dict[str, Any], bot: Bot) -> None:
        """
        'A'zo bo'ldim' tugmasi bosilganda kanal tekshiruvi

        Args:
            callback: Telegram callback_query dict
            bot: Aiogram Bot instance

        Note: settings argument olib tashlandi - cache dan olinadi
        """
        user_id = callback['from']['id']
        chat_id = callback['message']['chat']['id']
        message_id = callback['message']['message_id']

        try:
            # Settings ni cache dan olish
            settings = await self.bot_cache.get_settings()
            if not settings:
                # Cache da yo'q bo'lsa DB dan olish
                from bots.user_bots.base_template.services.competition_service import CompetitionService
                comp_service = CompetitionService()
                settings = await comp_service.get_competition_settings(self.bot_id)

            if not settings:
                await bot.answer_callback_query(callback['id'], MESSAGES['settings_not_found'], show_alert=True)
                return

            # Kanal tekshiruvi
            channel_service = ChannelService(settings)
            channels_status = await channel_service.check_user_channels(user_id, bot)

            # Agar hali obuna bo'lmagan kanallar bo'lsa
            if not channels_status['all_joined']:
                not_joined = channels_status.get('not_joined', [])
                await self._update_channels_message(chat_id, message_id, bot, not_joined)
                remaining = len(not_joined)
                await bot.answer_callback_query(callback['id'], text=f"⚠️ Yana {remaining} ta kanalga obuna bo'ling!",
                                                show_alert=True)
                return

            # Hammasi obuna bo'lgan - ro'yxatdan o'tkazish
            await self._complete_registration(user_id, callback, bot, settings)
            await bot.answer_callback_query(callback['id'], "✅ Muvaffaqiyatli ro'yxatdan o'tdingiz!", show_alert=True)

        except Exception as e:
            logger.error(f"Channel handler error: {e}", exc_info=True)
            await bot.answer_callback_query(callback['id'], MESSAGES['error_occurred'], show_alert=True)

    async def _update_channels_message(self, chat_id: int, message_id: int, bot: Bot, not_joined: list):
        """
        Obuna bo'linmagan kanallarni ko'rsatish

        Args:
            chat_id: Chat ID
            message_id: Tahrirlash kerak bo'lgan xabar ID
            bot: Bot instance
            not_joined: Obuna bo'linmagan kanallar ro'yxati
        """
        try:
            keyboard = get_channels_keyboard(not_joined)
            remaining = len(not_joined)

            text = f"⚠️ Hali {remaining} ta kanalga obuna bo'lmagansiz!\n\n"
            for i, channel in enumerate(not_joined[:10], 1):
                # channel_username ni xavfsiz olish
                username = channel.get('channel_username', '') or ''
                username = username.replace('@', '').strip() if username else ''
                name = channel.get('channel_name', username) or username or 'Kanal'
                if username:
                    text += f"{i}. @{username} - {name}\n"
                else:
                    text += f"{i}. {name}\n"

            if remaining > 10:
                text += f"\n... va yana {remaining - 10} ta kanal\n"

            text += "\n👇 Har bir tugmani bosing va obuna bo'ling"

            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Update channels message error: {e}")

    async def _complete_registration(self, user_id: int, callback: Dict, bot: Bot, settings: Dict):
        """
        Ro'yxatdan o'tkazish - barcha kanallardan keyin

        Args:
            user_id: Telegram user ID
            callback: Callback query dict
            bot: Bot instance
            settings: Competition settings
        """
        try:
            # User ma'lumotlarini olish
            from_user = callback.get('from', {})
            user_data = {
                'telegram_id': user_id,
                'username': from_user.get('username', ''),
                'first_name': from_user.get('first_name', ''),
                'last_name': from_user.get('last_name', ''),
                'is_premium': from_user.get('is_premium', False)
            }

            # Pending referral ni tekshirish
            referrer = None
            state = await redis_client.get_user_state(self.bot_id, user_id)
            if state and 'referrer_id' in state:
                referrer_id = state['referrer_id']
                referrer = await self.registration_service.get_participant_by_user_id(referrer_id)

            # Finalize registration
            participant = await self.registration_service.finalize_registration(user_data, referrer)
            if not participant:
                raise Exception("Registration failed")

            # Kanal ballarini qo'shish
            channels_count = len(settings.get('channels', []))
            await self._award_channel_points(participant, user_data['is_premium'], channels_count, settings)

            # Referral ballarini qo'shish (agar mavjud bo'lsa)
            if referrer and referrer.user.telegram_id != user_id:
                await self._award_referral_points(referrer, user_data['is_premium'], settings)

            # Success message
            await bot.edit_message_text(
                chat_id=callback['message']['chat']['id'],
                message_id=callback['message']['message_id'],
                text="🎉 Tabriklaymiz! Siz konkursda muvaffaqiyatli ro'yxatdan o'tdingiz!"
            )

            # Start handler ni chaqirish (welcome + menu)
            from .start_handler import StartHandler
            start_handler = StartHandler(self.bot_id)
            mock_message = {'from': callback['from'], 'chat': {'id': user_id}, 'text': '/start registered'}
            await start_handler.send_welcome_and_menu(mock_message, bot, settings, participant)

        except Exception as e:
            logger.error(f"Complete registration error: {e}", exc_info=True)

    async def _award_channel_points(self, participant, is_premium: bool, channels_count: int, settings: Dict):
        """Kanal qo'shilish balllarini hisoblash va qo'shish"""
        try:
            point_rules = settings.get('point_rules', {})

            # Har bir kanal uchun ball
            base_points_per_channel = point_rules.get('channel_join', 1)
            base_total = base_points_per_channel * channels_count

            # Premium bonus
            if is_premium:
                premium_multiplier = point_rules.get('premium_user', 2)
                total_points = base_total * premium_multiplier
            else:
                total_points = base_total

            if total_points > 0:
                participant.add_points(total_points, 'channel_join')
                logger.info(f"Channel points awarded: user={participant.telegram_id}, points={total_points}")

        except Exception as e:
            logger.error(f"Award channel points error: {e}")

    async def _award_referral_points(self, referrer, is_premium_referred: bool, settings: Dict):
        """Referral ballarini qo'shish"""
        try:
            point_rules = settings.get('point_rules', {})

            # Oddiy referral ball
            base_referral_points = point_rules.get('referral', 5)

            # Premium referral uchun
            if is_premium_referred:
                premium_referral_points = point_rules.get('premium_ref', 0)
                if premium_referral_points > 0:
                    total_points = premium_referral_points
                else:
                    # Default: 2x
                    total_points = base_referral_points * 2
                reason = 'premium_ref'
            else:
                total_points = base_referral_points
                reason = 'referral'

            if total_points > 0:
                referrer.add_points(total_points, reason)
                logger.info(f"Referral points awarded: referrer={referrer.telegram_id}, points={total_points}")

        except Exception as e:
            logger.error(f"Award referral points error: {e}")