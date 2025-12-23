#bots/user_bots/base_template/handlers/start_handler.py
"""
COMPLETE START HANDLER - TZ Requirements Fully Implemented
Sequence:
1. Rate limit check
2. Parse referral code
3. Check channel subscriptions
4. Create user/participant
5. Award points (channel + referral + premium)
6. Send welcome message
7. Send invitation post
8. Show main menu
"""
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from aiogram import Bot

from bots.user_bots.base_template.services.competition_service import CompetitionService
from bots.user_bots.base_template.services.user_service import UserService
from bots.user_bots.base_template.services.channel_service import ChannelService
from bots.user_bots.base_template.services.point_calculator import PointCalculator
from bots.user_bots.base_template.services.prize_service import PrizeService
from bots.user_bots.base_template.services.rating_service import RatingService
from bots.user_bots.base_template.keyboards.inline import (
    get_channels_keyboard,
    get_invitation_keyboard,
    get_post_generate_keyboard
)
from bots.user_bots.base_template.keyboards.reply import get_main_menu_keyboard
from shared.redis_client import redis_client
from shared.anti_cheat import get_anti_cheat_engine
from shared.utils import extract_user_data, extract_referral_code, truncate_text
from shared.constants import RATE_LIMITS, CACHE_KEYS

logger = logging.getLogger(__name__)


class StartHandler:
    """Complete start handler implementing all TZ requirements"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.competition_service = CompetitionService()
        self.user_service = UserService()
        self.channel_service = None
        self.point_calculator = None
        self.prize_service = PrizeService(bot_id)
        self.rating_service = RatingService(bot_id)
        self.anti_cheat = get_anti_cheat_engine(bot_id)

    async def handle_start(self, message: Dict[str, Any], bot: Bot) -> None:
        """
        Main start handler - Full TZ implementation
        """
        user_id = message['from']['id']
        text = message.get('text', '')

        try:
            logger.info(f"🚀 /start from user {user_id} in bot {self.bot_id}")

            # 1. Rate limit check
            if await self._check_rate_limit(user_id):
                await bot.send_message(
                    user_id,
                    "🚫 Juda tez so'rov yuborayapsiz. Iltimos, 1 daqiqa kuting.",
                    parse_mode="Markdown"
                )
                return

            # 2. Get competition settings
            settings = await self.competition_service.get_competition_settings(self.bot_id)
            if not settings:
                await bot.send_message(
                    user_id,
                    "❌ Bot sozlamalari topilmadi. Admin bilan bog'laning.",
                    parse_mode="Markdown"
                )
                return

            # Initialize services
            self.channel_service = ChannelService(settings)
            self.point_calculator = PointCalculator(settings)

            # 3. Parse referral code
            ref_code = extract_referral_code(text)
            referrer = None
            if ref_code:
                referrer = await self.user_service.get_participant_by_code(ref_code, self.bot_id)
                if referrer:
                    await self._save_pending_referral(user_id, referrer.user.telegram_id)
                    logger.info(f"Referral detected: {referrer.user.telegram_id} -> {user_id}")

            # 4. Check channel subscriptions
            channels_status = await self.channel_service.check_user_channels(user_id, bot)

            if not channels_status['all_joined']:
                # Show channels for subscription
                await self._show_channels_for_subscription(message, bot, channels_status, settings)
                return

            # 5. Complete registration
            await self._complete_registration(message, bot, settings, referrer)

        except Exception as e:
            logger.error(f"Start handler error: {e}", exc_info=True)
            await bot.send_message(
                user_id,
                "❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
                parse_mode="Markdown"
            )

    async def _check_rate_limit(self, user_id: int) -> bool:
        """Check rate limit for start command - TO'G'RILANGAN"""
        try:
            from shared.constants import CACHE_KEYS, RATE_LIMITS

            # Formatni to'g'ri ishlatish
            key = CACHE_KEYS['rate_limit'].format(
                bot_id=str(self.bot_id),
                user_id=str(user_id),
                action='start'
            )

            # Redis client mavjudligini tekshirish
            from shared.redis_client import redis_client
            if not redis_client or not redis_client.is_connected():
                logger.warning("Redis not connected, skipping rate limit")
                return False

            return await redis_client.check_rate_limit(
                key,
                RATE_LIMITS.get('start', {}).get('limit', 3),
                RATE_LIMITS.get('start', {}).get('window', 60)
            )
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False

    async def _save_pending_referral(self, user_id: int, referrer_id: int):
        """Save pending referral to Redis"""
        try:
            key = CACHE_KEYS['referral_pending'].format(self.bot_id, user_id)
            await redis_client.set_user_state(
                self.bot_id, user_id,
                {'referrer_id': referrer_id},
                3600
            )
        except Exception as e:
            logger.error(f"Save pending referral error: {e}")

    async def _show_channels_for_subscription(self, message: Dict, bot: Bot,
                                            channels_status: Dict, settings: Dict):
        """Show channels that need subscription"""
        try:
            user_id = message['from']['id']
            not_joined = channels_status.get('not_joined', [])
            request_needed = channels_status.get('request_needed', [])

            # Prepare message text
            text = "🎯 *Konkursda qatnashish uchun quyidagi kanallarga obuna bo'ling:*\n\n"

            all_channels = not_joined + request_needed
            for i, channel in enumerate(all_channels[:10], 1):
                username = channel.get('channel_username', '').replace('@', '')
                name = channel.get('channel_name', username)
                status = channel.get('status', '')

                if status == 'request_needed':
                    text += f"{i}. @{username} - {name} 📨 *(Request kerak)*\n"
                else:
                    text += f"{i}. @{username} - {name}\n"

            if len(all_channels) > 10:
                text += f"... va yana {len(all_channels) - 10} ta kanal\n"

            text += "\n📋 *Qadamlar:*\n"
            text += "1. Har bir kanal tugmasini bosing\n"
            text += "2. Kanallarga o'ting va 'Join' tugmasini bosing\n"
            text += "3. Barchasiga obuna bo'lgach, ✅ tugmasini qayta bosing\n\n"
            text += "⚠️ *Eslatma:* Faqat barcha kanallarga obuna bo'lganingizdan so'ng konkursda qatnashishingiz mumkin!"

            # Create keyboard
            keyboard = get_channels_keyboard(all_channels)

            # Send message
            await bot.send_message(
                user_id,
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Show channels error: {e}")

    async def _complete_registration(self, message: Dict, bot: Bot,
                                   settings: Dict, referrer: Any):
        """Complete user registration"""
        user_id = message['from']['id']

        try:
            # 1. Extract user data
            user_data = extract_user_data(message)

            # 2. Create or get user
            user, user_created = await self.user_service.get_or_create_user(user_data)

            # 3. Create or get participant
            participant, participant_created = await self.user_service.get_or_create_participant(
                user, self.bot_id
            )

            # 4. Get pending referral if exists
            pending_referrer_id = await self._get_pending_referral(user_id)
            if pending_referrer_id and not referrer:
                referrer = await self.user_service.get_participant_by_user_id(
                    pending_referrer_id, self.bot_id
                )

            # 5. Award points
            points_summary = await self._award_registration_points(
                participant, user.is_premium, referrer
            )

            # 6. Send registration messages
            await self._send_registration_messages(
                user_id, bot, settings, user, participant, points_summary
            )

            logger.info(f"✅ Registration completed for user {user_id}: {points_summary}")

        except Exception as e:
            logger.error(f"Complete registration error: {e}", exc_info=True)
            raise

    async def _get_pending_referral(self, user_id: int) -> Optional[int]:
        """Get pending referral from Redis"""
        try:
            state = await redis_client.get_user_state(self.bot_id, user_id)
            if state and 'referrer_id' in state:
                return state['referrer_id']
        except Exception as e:
            logger.error(f"Get pending referral error: {e}")

        return None

    async def _award_registration_points(self, participant, is_premium: bool,
                                       referrer: Any) -> Dict[str, Any]:
        """Award all registration points"""
        summary = {
            'channel_points': 0,
            'referral_points': 0,
            'total_points': 0,
            'is_premium': is_premium,
            'has_referrer': referrer is not None
        }

        try:
            # Award channel points
            channels_count = len(self.channel_service.channels)
            channel_points, channel_breakdown = await self.point_calculator.calculate_channel_points(
                participant.user.telegram_id, is_premium, channels_count
            )

            if channel_points > 0:
                await self.point_calculator.add_points_to_participant(
                    participant, channel_points, 'channel_join', channel_breakdown
                )
                summary['channel_points'] = channel_points

            # Award referral points (to referrer)
            if referrer and referrer.user.telegram_id != participant.user.telegram_id:
                referral_points, referral_breakdown = await self.point_calculator.calculate_referral_points(
                    referrer.user.telegram_id, is_premium
                )

                if referral_points > 0:
                    await self.point_calculator.add_points_to_participant(
                        referrer, referral_points,
                        'premium_ref' if is_premium else 'referral',
                        referral_breakdown
                    )
                    summary['referral_points'] = referral_points

                    # Create referral record
                    await self.user_service.create_referral(referrer, participant)

            summary['total_points'] = summary['channel_points'] + summary['referral_points']

        except Exception as e:
            logger.error(f"Award registration points error: {e}")

        return summary

    async def _send_registration_messages(self, user_id: int, bot: Bot, settings: Dict,
                                        user, participant, points_summary: Dict):
        """Send all registration messages"""
        # 1. Welcome message
        await self._send_welcome_message(user_id, bot, settings, user, points_summary)

        # 2. Invitation post
        await self._send_invitation_post(user_id, bot, settings, participant)

        # 3. Main menu
        await self._send_main_menu(user_id, bot)

    async def _send_welcome_message(self, user_id: int, bot: Bot, settings: Dict,
                                  user, points_summary: Dict):
        """Send welcome message"""
        try:
            user_name = user.get('full_name', user.get('first_name', 'Do\'stim'))

            text = f"🎉 *Tabriklaymiz, {user_name}!*\n\n"
            text += f"✅ *Siz \"{settings.get('name', 'Konkurs')}\" konkursida muvaffaqiyatli ro'yxatdan o'tdingiz!*\n\n"

            # Points summary
            if points_summary['total_points'] > 0:
                text += "🎁 *Sizga ballar berildi:*\n"

                if points_summary['channel_points'] > 0:
                    text += f"• Kanallarga obuna bo'lganingiz uchun: {points_summary['channel_points']} ball\n"

                if points_summary['referral_points'] > 0:
                    text += f"• Referral orqali kelganingiz uchun (referral egasiga): {points_summary['referral_points']} ball\n"

                text += f"💰 *Jami berilgan ballar:* {points_summary['total_points']} ball\n\n"

            # Competition description
            description = settings.get('description', '')
            if description:
                short_desc = truncate_text(description, 150)
                text += f"📝 *Konkurs haqida:* {short_desc}\n\n"

            # Premium status
            if points_summary['is_premium']:
                text += "⭐ *Siz Premium foydalanuvchisiz!* Ikki baravar ko'p ball olasiz.\n\n"

            text += "👇 *Taklif postini oling va do'stlaringizni taklif qilishni boshlang!*"

            # Send message
            await bot.send_message(
                user_id,
                text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Send welcome message error: {e}")

    async def _send_invitation_post(self, user_id: int, bot: Bot, settings: Dict,
                                  participant):
        """Send invitation post"""
        try:
            # Generate invitation text
            invitation_text = await self._generate_invitation_text(settings, participant)

            # Generate keyboard with referral link
            bot_username = settings.get('bot_username', '').replace('@', '')
            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"
            keyboard = get_invitation_keyboard(referral_link)

            # Send invitation post
            await bot.send_message(
                user_id,
                invitation_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

            # Send instruction
            instruction = (
                "👆 *Yuqoridagi postni do'stlaringizga ulashing!*\n\n"
                f"🔗 *Sizning taklif havolangiz:*\n`{referral_link}`\n\n"
                "Har bir taklif qilgan do'stingiz uchun sizga ballar beriladi!"
            )

            await bot.send_message(
                user_id,
                instruction,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Send invitation post error: {e}")

    async def _generate_invitation_text(self, settings: Dict, participant) -> str:
        """Generate invitation post text"""
        from shared.utils import get_prize_emoji

        bot_username = settings.get('bot_username', '').replace('@', '')
        referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

        text = "🎉 *DO'STLARINGIZNI TAKLIF QILING VA BALLAR YIG'ING!*\n\n"
        text += f"🏆 *Konkurs:* {settings.get('name', 'Konkurs')}\n\n"

        # Description
        description = settings.get('description', '')
        if description:
            short_desc = truncate_text(description, 120)
            text += f"📝 *Tavsif:* {short_desc}\n\n"

        # Prizes (top 3)
        prizes = await self.prize_service.get_prizes()
        if prizes:
            text += "🎁 *Asosiy sovrinlar:*\n"
            for prize in prizes[:3]:
                emoji = get_prize_emoji(prize['place'])

                if prize['type'] == 'number' and prize.get('prize_amount'):
                    amount = f"{int(float(prize['prize_amount'])):,} soʻm"
                    if prize.get('prize_name'):
                        display_text = f"{prize['prize_name']} ({amount})"
                    else:
                        display_text = amount
                elif prize.get('prize_name'):
                    display_text = prize['prize_name']
                else:
                    display_text = f"{prize['place']}-o'rin"

                text += f"{emoji} {display_text}\n"

            text += "\n"

        # Rules preview
        rules_text = settings.get('rules_text', '')
        if rules_text:
            short_rules = truncate_text(rules_text, 100)
            text += f"📜 *Qoidalar:* {short_rules}\n\n"

        # Referral link
        text += f"🔗 *Mening taklif havolam:*\n`{referral_link}`\n\n"
        text += "👇 *Ishtirok etish uchun havolani bosing yoki tugmalardan foydalaning!*"

        return text

    async def _send_main_menu(self, user_id: int, bot: Bot):
        """Send main menu"""
        try:
            text = (
                "👇 *ASOSIY MENYU*\n\n"
                "Quyidagi tugmalar orqali konkursda ishtirok eting va ballar yig'ing:\n\n"
                "• 🎁 *Sovg'alar* - Konkurs sovrinlarini ko'rish\n"
                "• 📊 *Ballarim* - Ballaringiz va statistikangiz\n"
                "• 🏆 *Reyting* - Top 10 va o'rningiz\n"
                "• 📜 *Shartlar* - Konkurs qoidalari\n"
                "• 🚀 *Konkursda qatnashish* - Taklif postini qayta olish"
            )

            await bot.send_message(
                user_id,
                text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Send main menu error: {e}")