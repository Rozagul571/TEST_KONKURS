# bots/user_bots/base_template/handlers/menu_handler.py
"""
Complete menu handlers for all main menu options - TO'G'RILANGAN
Vazifasi: Asosiy menu tugmalarini handle qilish
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
from bots.user_bots.base_template.keyboards.inline import get_invitation_keyboard
from shared.redis_client import redis_client
from shared.utils import format_points, truncate_text, get_prize_emoji, clean_channel_username
from shared.constants import MESSAGES, RATE_LIMITS, CACHE_KEYS

logger = logging.getLogger(__name__)


class MenuHandlers:

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
            # Rate limit
            if await self._check_rate_limit(user_id, 'menu_konkurs'):
                await bot.send_message(user_id, MESSAGES['rate_limited'])
                return

            # Participant olish
            participant = await self.user_service.get_participant_by_user_id(user_id, self.bot_id)
            if not participant:
                await bot.send_message(user_id, MESSAGES['not_registered'], parse_mode="Markdown")
                return

            # Competition settings
            settings = await self.competition_service.get_competition_settings(self.bot_id)
            if not settings:
                await bot.send_message(user_id, MESSAGES['settings_not_found'])
                return

            # Taklif posti generatsiya
            invitation_text = await self.invitation_service.generate_invitation_post(settings, participant)

            # Referral link
            bot_username = clean_channel_username(settings.get('bot_username', ''))
            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

            keyboard = get_invitation_keyboard(referral_link)

            # Taklif postini yuborish
            await bot.send_message(user_id, invitation_text, reply_markup=keyboard, parse_mode="Markdown")
            await bot.send_message(user_id, MESSAGES['invitation_share_instruction'], parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Handle konkurs qatnashish error: {e}", exc_info=True)
            await bot.send_message(user_id, MESSAGES['error_occurred'])

    async def handle_konkurs_qatnashish_callback(self, callback: Dict[str, Any], bot: Bot):
        """Callback versiyasi - taklif_posti"""
        message = {'from': callback['from'], 'chat': callback['message']['chat']}
        await self.handle_konkurs_qatnashish(message, bot)
        await bot.answer_callback_query(callback['id'])

    async def handle_sovgalar(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Sovg'alar' button"""
        user_id = message['from']['id']
        try:
            # Rate limit
            if await self._check_rate_limit(user_id, 'menu_sovgalar'):
                await bot.send_message(user_id, MESSAGES['rate_limited'])
                return

            # Sovrinlarni olish
            prizes = await self.prize_service.get_prizes()
            if not prizes:
                await bot.send_message(user_id, MESSAGES['no_prizes'], parse_mode="Markdown")
                return

            # Text format
            text = MESSAGES['prizes_header']

            for prize in prizes:
                emoji = get_prize_emoji(prize['place'])
                place_text = f"{prize['place']}-o'rin"

                if prize['type'] == 'number' and prize.get('prize_amount'):
                    amount = f"{int(float(prize['prize_amount'])):,} soʻm"
                    display_text = f"{prize['prize_name']} ({amount})" if prize.get('prize_name') else amount
                elif prize.get('prize_name'):
                    display_text = prize['prize_name']
                else:
                    display_text = place_text

                text += f"{emoji} *{place_text}:* {display_text}\n"

                if prize.get('description'):
                    desc = truncate_text(prize['description'], 100)
                    text += f"   📝 {desc}\n"

                text += "\n"

            text += MESSAGES['prizes_footer']

            await bot.send_message(user_id, text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Handle sovgalar error: {e}", exc_info=True)
            await bot.send_message(user_id, MESSAGES['error_occurred'])

    async def handle_ballarim(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Ballarim' button"""
        user_id = message['from']['id']
        try:
            # Rate limit
            if await self._check_rate_limit(user_id, 'menu_ballarim'):
                await bot.send_message(user_id, MESSAGES['rate_limited'])
                return

            # Participant olish
            participant = await self.user_service.get_participant_by_user_id(user_id, self.bot_id)
            if not participant:
                await bot.send_message(user_id, MESSAGES['not_registered'], parse_mode="Markdown")
                return

            # Stats olish
            stats = await self.point_service.get_user_stats(participant)

            # Text format
            text = MESSAGES['points_header'].format(points=format_points(participant.current_points))

            text += MESSAGES['points_breakdown'].format(
                channel=format_points(stats.get('channel_points', 0)),
                referral=format_points(stats.get('referral_points', 0)),
                premium=format_points(stats.get('premium_points', 0)),
                other=format_points(stats.get('other_points', 0))
            )

            # Premium status
            if stats.get('has_premium'):
                text += MESSAGES['points_premium_status']

            # Motivation
            text += MESSAGES['points_motivation']

            await bot.send_message(user_id, text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Handle ballarim error: {e}", exc_info=True)
            await bot.send_message(user_id, MESSAGES['error_occurred'])

    async def handle_reyting(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Reyting' button"""
        user_id = message['from']['id']
        try:
            # Rate limit
            if await self._check_rate_limit(user_id, 'menu_reyting'):
                await bot.send_message(user_id, MESSAGES['rate_limited'])
                return

            # Rating text olish
            rating_text = await self.rating_service.get_rating_text(user_id)

            await bot.send_message(user_id, rating_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Handle reyting error: {e}", exc_info=True)
            await bot.send_message(user_id, MESSAGES['error_occurred'])

    async def handle_refresh_rating(self, callback: Dict[str, Any], bot: Bot):
        """Refresh rating callback"""
        user_id = callback['from']['id']
        try:
            # Cache ni tozalash va yangilash
            await self.rating_service.update_cache(user_id)
            rating_text = await self.rating_service.get_rating_text(user_id)

            await bot.edit_message_text(
                chat_id=callback['message']['chat']['id'],
                message_id=callback['message']['message_id'],
                text=rating_text,
                parse_mode="Markdown"
            )
            await bot.answer_callback_query(callback['id'], "✅ Yangilandi!")
        except Exception as e:
            logger.error(f"Refresh rating error: {e}")
            await bot.answer_callback_query(callback['id'], "Xatolik yuz berdi")

    async def handle_shartlar(self, message: Dict[str, Any], bot: Bot):
        """Handle 'Shartlar' button"""
        user_id = message['from']['id']
        try:
            # Rate limit
            if await self._check_rate_limit(user_id, 'menu_shartlar'):
                await bot.send_message(user_id, MESSAGES['rate_limited'])
                return

            # Settings olish
            settings = await self.competition_service.get_competition_settings(self.bot_id)
            if not settings:
                await bot.send_message(user_id, MESSAGES['settings_not_found'])
                return

            # Rules text
            rules_text = settings.get('rules_text', '')
            if not rules_text:
                rules_text = MESSAGES['rules_default']

            text = MESSAGES['rules_header'] + rules_text

            await bot.send_message(user_id, text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Handle shartlar error: {e}", exc_info=True)
            await bot.send_message(user_id, MESSAGES['error_occurred'])

    async def handle_share_post(self, callback: Dict[str, Any], bot: Bot):
        """Share post callback"""
        user_id = callback['from']['id']
        try:
            participant = await self.user_service.get_participant_by_user_id(user_id, self.bot_id)
            if not participant:
                await bot.answer_callback_query(callback['id'], MESSAGES['not_registered'], show_alert=True)
                return

            settings = await self.competition_service.get_competition_settings(self.bot_id)
            bot_username = clean_channel_username(settings.get('bot_username', ''))
            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

            await bot.answer_callback_query(
                callback['id'],
                f"Havolani nusxalang va do'stlaringizga yuboring:\n{referral_link}",
                show_alert=True
            )
        except Exception as e:
            logger.error(f"Share post error: {e}")
            await bot.answer_callback_query(callback['id'], MESSAGES['error_occurred'], show_alert=True)

    async def _check_rate_limit(self, user_id: int, action: str) -> bool:
        """Rate limit tekshirish"""
        try:
            if not redis_client.is_connected():
                return False
            key = CACHE_KEYS['rate_limit'].format(bot_id=self.bot_id, user_id=user_id, action=action)
            limit_config = RATE_LIMITS.get('menu_action', {'limit': 10, 'window': 30})
            return await redis_client.check_rate_limit(key, limit_config['limit'], limit_config['window'])
        except Exception as e:
            logger.error(f"Menu rate limit check error: {e}")
            return False