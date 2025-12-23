#bots/user_bots/base_template/handlers/menu_handler.py
"""
Complete menu handlers for all main menu options - TO'G'RILANGAN
"""
import logging
from typing import Dict, Any
from aiogram import Bot

from bots.user_bots.base_template.services.competition_service import CompetitionService
from bots.user_bots.base_template.services.user_service import UserService
from bots.user_bots.base_template.services.point_service import PointService
from bots.user_bots.base_template.services.prize_service import PrizeService
from bots.user_bots.base_template.services.rating_service import RatingService
from bots.user_bots.base_template.services.invitation_service import InvitationService
from shared.redis_client import redis_client
from shared.utils import format_points, truncate_text, get_prize_emoji
from shared.constants import RATE_LIMITS, CACHE_KEYS

logger = logging.getLogger(__name__)


class MenuHandlers:
    """Complete menu handlers for user bot"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.competition_service = CompetitionService()
        self.user_service = UserService()
        self.point_service = PointService(bot_id)
        self.prize_service = PrizeService(bot_id)
        self.rating_service = RatingService(bot_id)
        self.invitation_service = InvitationService(bot_id)

    async def handle_konkurs_qatnashish(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Konkursda qatnashish' button"""
        user_id = message['from']['id']

        try:
            # Rate limit check
            if await self._check_rate_limit(user_id, 'menu_konkurs'):
                await bot.send_message(user_id, "🚫 Biroz kuting...")
                return

            # Get participant
            participant = await self.user_service.get_participant_by_user_id(user_id, self.bot_id)
            if not participant:
                await bot.send_message(
                    user_id,
                    "❌ Avval /start ni bosing va konkursda ro'yxatdan o'ting!",
                    parse_mode="Markdown"
                )
                return

            # Get competition settings
            settings = await self.competition_service.get_competition_settings(self.bot_id)
            if not settings:
                await bot.send_message(user_id, "❌ Sozlamalar topilmadi")
                return

            # Generate invitation post
            invitation_text = await self.invitation_service.generate_invitation_post(
                settings, participant
            )

            # Create keyboard
            bot_username = settings.get('bot_username', '').replace('@', '')
            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

            from bots.user_bots.base_template.keyboards.inline import get_invitation_keyboard
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
                f"👆 *Taklif postini do'stlaringizga ulashing!*\n\n"
                f"🔗 *Sizning taklif havolangiz:*\n`{referral_link}`\n\n"
                "Har bir siz orqali ro'yxatdan o'tgan do'stingiz uchun sizga ballar beriladi!"
            )

            await bot.send_message(
                user_id,
                instruction,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle konkurs qatnashish error: {e}")
            await bot.send_message(user_id, "❌ Xatolik yuz berdi")

    async def handle_sovgalar(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Sovg'alar' button"""
        user_id = message['from']['id']

        try:
            # Rate limit check
            if await self._check_rate_limit(user_id, 'menu_sovgalar'):
                await bot.send_message(user_id, "🚫 Biroz kuting...")
                return

            # Get prizes
            prizes = await self.prize_service.get_prizes()

            if not prizes:
                text = (
                    "🎁 *Sovg'alar hozircha belgilanmagan.*\n\n"
                    "Admin tez orada konkurs sovrinlarini belgilaydi."
                )
                await bot.send_message(user_id, text, parse_mode="Markdown")
                return

            # Format prizes text
            text = "🎁 *KONKURS SOVG'ALARI* 🎁\n\n"

            for prize in prizes:
                emoji = get_prize_emoji(prize['place'])
                place_text = f"{prize['place']}-o'rin"

                # Format prize display
                if prize['type'] == 'number' and prize.get('prize_amount'):
                    amount = f"{int(float(prize['prize_amount'])):,} soʻm"
                    if prize.get('prize_name'):
                        display_text = f"{prize['prize_name']} ({amount})"
                    else:
                        display_text = f"{amount}"
                elif prize.get('prize_name'):
                    display_text = prize['prize_name']
                else:
                    display_text = place_text

                text += f"{emoji} *{place_text}:* {display_text}\n"

                if prize.get('description'):
                    desc = truncate_text(prize['description'], 100)
                    text += f"   📝 {desc}\n"

                text += "\n"

            # Add motivation
            text += "🏆 *G'olib bo'lish uchun ko'proq ball yig'ing!*\n"
            text += "🚀 Do'stlaringizni taklif qiling va ballaringizni oshiring!"

            await bot.send_message(
                user_id,
                text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle sovgalar error: {e}")
            await bot.send_message(user_id, "❌ Xatolik yuz berdi")

    async def handle_ballarim(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Ballarim' button"""
        user_id = message['from']['id']

        try:
            # Rate limit check
            if await self._check_rate_limit(user_id, 'menu_ballarim'):
                await bot.send_message(user_id, "🚫 Biroz kuting...")
                return

            # Get participant
            participant = await self.user_service.get_participant_by_user_id(user_id, self.bot_id)
            if not participant:
                await bot.send_message(
                    user_id,
                    "❌ Avval /start ni bosing va konkursda ro'yxatdan o'ting!",
                    parse_mode="Markdown"
                )
                return

            # Get points stats
            stats = await self.point_service.get_user_stats(participant)

            # Format points text
            text = f"📊 *BALLARIM: {format_points(participant.current_points)} ball*\n\n"

            # Level information
            if 'level_info' in stats:
                level_info = stats['level_info']
                text += f"⭐ *Daraja:* {level_info['level_name']} (Daraja {level_info['level']})\n"
                text += f"📈 *Keyingi darajaga:* {format_points(level_info['points_to_next'])} ball qoldi\n"
                text += f"⏳ *Progress:* {level_info['progress_percentage']}%\n\n"

            # Points breakdown
            text += "💰 *Ballar tafsiloti:*\n"
            text += f"• 📢 Kanallar: {format_points(stats.get('channel_points', 0))} ball\n"
            text += f"• 👥 Referrallar: {format_points(stats.get('referral_points', 0))} ball\n"
            text += f"• ⭐ Premium bonus: {format_points(stats.get('premium_points', 0))} ball\n"
            text += f"• 📝 Boshqa: {format_points(stats.get('other_points', 0))} ball\n\n"

            # Premium status
            if stats.get('has_premium'):
                text += "⭐ *Siz Premium foydalanuvchisiz!* Ikki baravar ko'p ball olasiz.\n\n"

            # Motivation
            text += "🚀 *Ko'proq ball yig'ish uchun:*\n"
            text += "1. Do'stlaringizni taklif qiling\n"
            text += "2. Kunlik topshiriqlarni bajar\n"
            text += "3. Postlarni ulashing\n"
            text += "4. Aktiv bo'ling!"

            await bot.send_message(
                user_id,
                text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle ballarim error: {e}")
            await bot.send_message(user_id, "❌ Xatolik yuz berdi")

    async def handle_reyting(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Reyting' button"""
        user_id = message['from']['id']

        try:
            # Rate limit check
            if await self._check_rate_limit(user_id, 'menu_reyting'):
                await bot.send_message(user_id, "🚫 Biroz kuting...")
                return

            # Get rating text
            rating_text = await self.rating_service.get_rating_text(user_id)

            await bot.send_message(
                user_id,
                rating_text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle reyting error: {e}")
            await bot.send_message(user_id, "❌ Xatolik yuz berdi")

    async def handle_shartlar(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Shartlar' button"""
        user_id = message['from']['id']

        try:
            # Rate limit check
            if await self._check_rate_limit(user_id, 'menu_shartlar'):
                await bot.send_message(user_id, "🚫 Biroz kuting...")
                return

            # Get competition settings
            settings = await self.competition_service.get_competition_settings(self.bot_id)
            if not settings:
                await bot.send_message(user_id, "❌ Sozlamalar topilmadi")
                return

            # Get rules text
            rules_text = settings.get('rules_text', '')
            if not rules_text:
                rules_text = (
                    "📜 *KONKURS QOIDALARI*\n\n"
                    "1. Barcha majburiy kanallarga obuna bo'ling\n"
                    "2. Do'stlaringizni taklif qiling va ballar yig'ing\n"
                    "3. Har bir taklif qilgan do'stingiz uchun ballar olasiz\n"
                    "4. Premium foydalanuvchilar 2x ko'p ball oladi\n"
                    "5. Eng ko'p ball to'plagan TOP 10 sovrinlarni oladi\n"
                    "6. Har bir qoidani buzish diskvalifikatsiyaga olib kelishi mumkin\n\n"
                    "🚀 Ko'proq odam taklif qiling va g'olib bo'ling!"
                )

            text = f"📜 *KONKURS QOIDALARI*\n\n{rules_text}"

            await bot.send_message(
                user_id,
                text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle shartlar error: {e}")
            await bot.send_message(user_id, "❌ Xatolik yuz berdi")

    async def _check_rate_limit(self, user_id: int, action: str) -> bool:
        """Check rate limit for menu actions"""
        try:
            key = CACHE_KEYS['rate_limit'].format(self.bot_id, user_id, action)
            limit_config = RATE_LIMITS.get('message', {'limit': 30, 'window': 60})

            return await redis_client.check_rate_limit(
                key,
                limit_config['limit'],
                limit_config['window']
            )
        except Exception as e:
            logger.error(f"Menu rate limit check error: {e}")
            return False