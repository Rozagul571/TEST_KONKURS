# bots/user_bots/base_template/services/invitation_service.py
"""
Invitation service for generating invitation posts
Vazifasi: Taklif postini generatsiya qilish
"""
import logging
from typing import Dict, Any

from shared.utils import truncate_text, get_prize_emoji, clean_channel_username
from shared.constants import MESSAGES

logger = logging.getLogger(__name__)


class InvitationService:
    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def generate_invitation_post(self, settings: Dict[str, Any], participant) -> str:
        try:
            from .prize_service import PrizeService
            prize_service = PrizeService(self.bot_id)
            prizes = await prize_service.get_prizes()

            bot_username = clean_channel_username(settings.get('bot_username', ''))
            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

            # Text qurish
            text = MESSAGES['invitation_header']
            text += MESSAGES['invitation_competition'].format(name=settings.get('name', 'Konkurs'))

            # Description
            description = settings.get('description', '')
            if description:
                text += MESSAGES['invitation_description'].format(description=truncate_text(description, 120))

            # Prizes (top 3)
            if prizes:
                text += MESSAGES['invitation_prizes']
                for prize in prizes[:3]:
                    emoji = get_prize_emoji(prize['place'])

                    # Display text
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
                text += MESSAGES['invitation_rules'].format(rules=truncate_text(rules_text, 100))

            # Referral link
            text += MESSAGES['invitation_link'].format(link=referral_link)
            text += MESSAGES['invitation_cta']

            return text

        except Exception as e:
            logger.error(f"Generate invitation post error: {e}")
            return "🎉 Do'stlaringizni taklif qiling va ballar yig'ing!"