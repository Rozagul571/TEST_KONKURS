# bots/user_bots/base_template/handlers/start_handler.py
"""
COMPLETE START HANDLER - FINAL VERSION
Vazifasi: /start buyrug'ini handle qilish
"""
import logging
from typing import Dict, Any, Optional
from aiogram import Bot

from bots.user_bots.base_template.services.competition_service import CompetitionService
from bots.user_bots.base_template.services.registration_service import RegistrationService
from bots.user_bots.base_template.services.channel_service import ChannelService
from bots.user_bots.base_template.services.prize_service import PrizeService
from bots.user_bots.base_template.keyboards.inline import get_channels_keyboard, get_invitation_keyboard
from bots.user_bots.base_template.keyboards.reply import get_main_menu_keyboard
from shared.redis_client import redis_client
from shared.utils import extract_user_data, extract_referral_code, truncate_text, get_prize_emoji, \
    clean_channel_username
from shared.constants import MESSAGES, RATE_LIMITS, CACHE_KEYS

logger = logging.getLogger(__name__)


class StartHandler:
    """Start handler for user bots"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.competition_service = CompetitionService()
        self.registration_service = RegistrationService(bot_id)
        self.prize_service = PrizeService(bot_id)

    async def handle_start(self, message: Dict[str, Any], bot: Bot) -> None:
        """
        Main /start handler

        Flow:
        1. Rate limit tekshirish
        2. Settings olish
        3. Referral tekshirish
        4. Kanal tekshirish
        5. Ro'yxatdan o'tkazish (agar barcha kanallar joined)
        6. Welcome va menu yuborish
        """
        user_id = message['from']['id']
        text = message.get('text', '')

        try:
            logger.info(f"/start from user {user_id}")

            # Rate limit (Redis)
            if await self._check_rate_limit(user_id):
                await bot.send_message(user_id, MESSAGES['rate_limited'])
                return

            # Settings olish (cache -> DB)
            settings = await self.competition_service.get_competition_settings(self.bot_id)
            if not settings:
                await bot.send_message(user_id, MESSAGES['settings_not_found'])
                return

            # Agar registered flag bilan kelgan bo'lsa (channel_handler dan)
            if 'registered' in text:
                participant = await self.registration_service.get_participant_by_user_id(user_id)
                if participant:
                    await self.send_welcome_and_menu(message, bot, settings, participant)
                return

            # Referral parse
            ref_code = extract_referral_code(text)
            referrer = None
            if ref_code:
                referrer = await self.registration_service.get_participant_by_code(ref_code)
                if referrer and referrer.user.telegram_id != user_id:
                    await self._save_pending_referral(user_id, referrer.user.telegram_id)
                    logger.info(f"Referral saved: user={user_id}, referrer={referrer.user.telegram_id}")

            # Mavjud participant tekshirish
            existing_participant = await self.registration_service.get_participant_by_user_id(user_id)
            if existing_participant:
                # Allaqachon ro'yxatdan o'tgan - menu ko'rsatish
                await self.send_welcome_and_menu(message, bot, settings, existing_participant)
                return

            # Channel service init
            channel_service = ChannelService(settings)

            # Kanal tekshirish
            channels_status = await channel_service.check_user_channels(user_id, bot)

            if not channels_status['all_joined']:
                # Kanallarni ko'rsatish
                await self._show_channels_for_subscription(user_id, bot, channels_status, settings)
                return

            # Barcha kanallarga joined - ro'yxatdan o'tkazish
            user_data = extract_user_data(message)
            participant = await self.registration_service.finalize_registration(user_data, referrer)

            if not participant:
                await bot.send_message(user_id, MESSAGES['error_occurred'])
                return

            # Kanal ballari
            await self._award_channel_points(participant, user_data.get('is_premium', False), settings)

            # Referral ballari (agar mavjud bo'lsa)
            if referrer and referrer.user.telegram_id != user_id:
                await self._award_referral_points(referrer, user_data.get('is_premium', False), settings)

            # Welcome va menu
            await self.send_welcome_and_menu(message, bot, settings, participant)

        except Exception as e:
            logger.error(f"/start error user {user_id}: {e}", exc_info=True)
            await bot.send_message(user_id, MESSAGES['error_occurred'])

    async def _check_rate_limit(self, user_id: int) -> bool:
        """Rate limit tekshirish"""
        if not redis_client.is_connected():
            return False
        key = CACHE_KEYS['rate_limit'].format(bot_id=self.bot_id, user_id=user_id, action='start')
        limit_config = RATE_LIMITS.get('start', {'limit': 5, 'window': 60})
        return await redis_client.check_rate_limit(key, limit_config['limit'], limit_config['window'])

    async def _save_pending_referral(self, user_id: int, referrer_id: int):
        """Pending referral ni cache ga saqlash"""
        if not redis_client.is_connected():
            return
        await redis_client.set_user_state(self.bot_id, user_id, {'referrer_id': referrer_id}, 3600)

    async def _show_channels_for_subscription(self, user_id: int, bot: Bot, channels_status: Dict, settings: Dict):
        """Kanallarni obuna uchun ko'rsatish"""
        try:
            not_joined = channels_status.get('not_joined', [])
            all_channels = settings.get('channels', []) if not not_joined else not_joined

            # Text yaratish
            text = MESSAGES['channels_intro']

            if all_channels:
                for i, channel in enumerate(all_channels[:10], 1):
                    raw_username = channel.get('channel_username') or ''
                    username = clean_channel_username(raw_username)
                    name = channel.get('channel_name') or channel.get('title') or username or 'Kanal'

                    if username:
                        text += f"{i}. @{username} - {name}\n"
                    else:
                        text += f"{i}. {name}\n"

                if len(all_channels) > 10:
                    text += f"\n... va yana {len(all_channels) - 10} ta kanal\n"

            text += "\n📋 *Qadamlar:*\n"
            text += "1. Har bir kanal tugmasini bosing\n"
            text += "2. Kanallarga o'ting va 'Join' tugmasini bosing\n"
            text += "3. Barchasiga obuna bo'lgach, ✅ tugmasini qayta bosing\n\n"
            text += "⚠️ *Eslatma:* Faqat barcha kanallarga obuna bo'lganingizdan so'ng konkursda qatnashishingiz mumkin!"

            keyboard = get_channels_keyboard(all_channels)

            await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Show channels error: {e}", exc_info=True)
            # Fallback
            await bot.send_message(
                user_id,
                "Konkursda qatnashish uchun majburiy kanallarga obuna bo'ling. Keyin /start ni qayta bosing.",
                reply_markup=get_channels_keyboard([])
            )

    async def send_welcome_and_menu(self, message: Dict, bot: Bot, settings: Dict, participant):
        """Welcome xabar va menu yuborish"""
        user_id = message['from']['id']

        try:
            # 1. Welcome message
            await self._send_welcome_message(user_id, bot, settings, participant)

            # 2. Taklif posti
            await self._send_invitation_post(user_id, bot, settings, participant)

            # 3. Main menu
            await self._send_main_menu(user_id, bot)

        except Exception as e:
            logger.error(f"Send welcome and menu error: {e}", exc_info=True)

    async def _send_welcome_message(self, user_id: int, bot: Bot, settings: Dict, participant):
        """Welcome xabar yuborish"""
        try:
            name = participant.full_name or participant.first_name or 'Do\'stim'
            text = MESSAGES['welcome_registered'].format(name=name)

            # Admin rules qo'shish
            rules_text = settings.get('rules_text', '')
            if rules_text:
                text += rules_text

            await bot.send_message(user_id, text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Welcome message error: {e}")

    async def _send_invitation_post(self, user_id: int, bot: Bot, settings: Dict, participant):
        """Taklif posti yuborish"""
        try:
            invitation_text = await self._generate_invitation_text(settings, participant)

            bot_username = clean_channel_username(settings.get('bot_username', ''))
            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

            keyboard = get_invitation_keyboard(referral_link)

            await bot.send_message(user_id, invitation_text, reply_markup=keyboard, parse_mode="Markdown")
            await bot.send_message(user_id, MESSAGES['invitation_share_instruction'])

        except Exception as e:
            logger.error(f"Invitation post error: {e}")

    async def _generate_invitation_text(self, settings: Dict, participant) -> str:
        """Taklif posti textini generatsiya qilish"""
        try:
            bot_username = clean_channel_username(settings.get('bot_username', ''))
            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

            text = MESSAGES['invitation_header']
            text += MESSAGES['invitation_competition'].format(name=settings.get('name', 'Konkurs'))

            # Description
            description = settings.get('description', '')
            if description:
                text += MESSAGES['invitation_description'].format(description=truncate_text(description, 120))

            # Prizes (top 3)
            prizes = await self.prize_service.get_prizes()
            if prizes:
                text += MESSAGES['invitation_prizes']
                for prize in prizes[:3]:
                    emoji = get_prize_emoji(prize['place'])
                    display_text = prize.get('display_text', f"{prize['place']}-o'rin")
                    text += f"{emoji} {display_text}\n"
                text += "\n"

            # Rules preview
            rules_text = settings.get('rules_text', '')
            if rules_text:
                text += MESSAGES['invitation_rules'].format(rules=truncate_text(rules_text, 100))

            # Referral link
            text += MESSAGES['invitation_link'].format(link=referral_link)
            text += MESSAGES['invitation_cta']

            return text

        except Exception as e:
            logger.error(f"Generate invitation text error: {e}")
            return "🎉 Do'stlaringizni taklif qiling va ballar yig'ing!"

    async def _send_main_menu(self, user_id: int, bot: Bot):
        """Main menu yuborish"""
        try:
            text = MESSAGES['main_menu_intro']
            await bot.send_message(user_id, text, reply_markup=get_main_menu_keyboard())
        except Exception as e:
            logger.error(f"Main menu error: {e}")

    async def _award_channel_points(self, participant, is_premium: bool, settings: Dict):
        """Kanal qo'shilish ballarini hisoblash va qo'shish"""
        try:
            point_rules = settings.get('point_rules', {})
            channels_count = len(settings.get('channels', []))

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