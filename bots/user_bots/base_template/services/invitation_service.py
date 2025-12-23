#bots/user_bots/base_template/services/invitation_service.py
"""
Invitation service for generating invitation posts
"""
import logging
from typing import Dict, Any
from shared.utils import truncate_text, get_prize_emoji, format_points

logger = logging.getLogger(__name__)


class InvitationService:
    """Service for generating invitation posts"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def generate_invitation_post(self, settings: Dict[str, Any], participant) -> str:
        """Generate invitation post text"""
        try:
            from .prize_service import PrizeService

            prize_service = PrizeService(self.bot_id)
            prizes = await prize_service.get_prizes()

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

        except Exception as e:
            logger.error(f"Generate invitation post error: {e}")
            return "🎉 Do'stlaringizni taklif qiling va ballar yig'ing!"