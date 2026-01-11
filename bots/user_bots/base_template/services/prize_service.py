# bots/user_bots/base_template/services/prize_service.py
"""
Prize service - Sovrinlarni olish va formatlash
Vazifasi: Konkurs sovrinlarini olish
"""
import logging
from typing import List, Dict, Any
from asgiref.sync import sync_to_async

from django_app.core.models import Prize
from shared.utils import get_prize_emoji

logger = logging.getLogger(__name__)


class PrizeService:
    """Prize service"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id

    async def get_prizes(self) -> List[Dict[str, Any]]:
        """
        Konkurs sovrinlarini olish

        Returns:
            Sovrinlar ro'yxati
        """
        try:
            @sync_to_async
            def _get_prizes():
                prizes = Prize.objects.filter(
                    competition__bot_id=self.bot_id
                ).order_by('place')

                formatted_prizes = []
                for prize in prizes:
                    formatted_prize = {
                        'place': prize.place,
                        'type': prize.type,
                        'description': prize.description or '',
                        'prize_name': prize.prize_name or '',
                        'prize_amount': float(prize.prize_amount) if prize.prize_amount else None
                    }

                    # Display text format
                    if prize.type == 'text':
                        display_text = f"{prize.place}-o'rin - {prize.prize_name}"
                        if prize.description:
                            display_text += f" ({prize.description})"
                    elif prize.type == 'number':
                        amount = f"{prize.prize_amount:,.0f} soʻm" if prize.prize_amount else ''
                        if prize.prize_name:
                            display_text = f"{prize.place}-o'rin - {prize.prize_name} ({amount})"
                        else:
                            display_text = f"{prize.place}-o'rin - {amount}"
                    else:
                        display_text = f"{prize.place}-o'rin"

                    formatted_prize['display_text'] = display_text
                    formatted_prizes.append(formatted_prize)

                return formatted_prizes

            return await _get_prizes()

        except Exception as e:
            logger.error(f"Get prizes error: {e}")
            return []

    async def get_formatted_prizes_text(self) -> str:
        """
        Formatlangan sovrinlar texti

        Returns:
            Markdown formatlangan text
        """
        prizes = await self.get_prizes()

        if not prizes:
            return "🎁 *Sovg'alar hozircha belgilanmagan.*"

        text = "🎁 *KONKURS SOVG'ALARI* 🎁\n\n"

        for prize in prizes:
            emoji = get_prize_emoji(prize['place'])
            text += f"{emoji} *{prize['display_text']}*\n\n"

        return text