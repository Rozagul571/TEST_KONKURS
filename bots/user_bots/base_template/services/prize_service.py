# bots/user_bots/base_template/services/prize_service.py
import logging
from typing import List, Dict, Any
from asgiref.sync import sync_to_async
from django_app.core.models import Competition, Prize
from shared.utils import get_prize_emoji
logger = logging.getLogger(__name__)
class PrizeService:
    def __init__(self, competition_id: int):
        self.competition_id = competition_id
    async def get_prizes(self) -> List[Dict[str, Any]]:
        try:
            prizes = await sync_to_async(list)(
                Prize.objects.filter(
                    competition_id=self.competition_id
                ).order_by('place')
            )
            formatted_prizes = []
            for prize in prizes:
                formatted_prize = {
                    'place': prize.place,
                    'type': prize.type,
                    'description': prize.description or '',
                    'prize_name': prize.prize_name or '',
                    'prize_amount': prize.prize_amount
                }
                # Format display text
                if prize.type == 'text':
                    display_text = f"{prize.place} - {prize.prize_name}"
                    if prize.description:
                        display_text += f" {prize.description}"
                elif prize.type == 'number':
                    amount = f"{prize.prize_amount:,.0f} soʻm" if prize.prize_amount else ''
                    display_text = f"{prize.place} - {prize.prize_name} ({amount})" if prize.prize_name else f"{prize.place} - {amount}"
                formatted_prize['display_text'] = display_text
                formatted_prizes.append(formatted_prize)
            return formatted_prizes
        except Exception as e:
            logger.error(f"Get prizes error: {e}")
            return []
    async def get_formatted_prizes_text(self) -> str:
        prizes = await self.get_prizes()
        if not prizes:
            return "🎁 *Sovg'alar hozircha belgilanmagan.*"
        text = "🎁 *KONKURS SOVG'ALARI* 🎁\n\n"
        for prize in prizes:
            emoji = get_prize_emoji(prize['place'])
            text += f"{emoji} *{prize['display_text']}*\n\n"
        return text