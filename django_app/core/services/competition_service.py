# django_app/core/services/competition_service.py
import logging
from typing import Dict, Any
from asgiref.sync import sync_to_async
from django.core.cache import cache
from django_app.core.models import Competition, BotSetUp

logger = logging.getLogger(__name__)


class CompetitionService:
    """Competition service for handling competition data"""

    async def get_competition_settings(self, bot_id: int) -> Dict[str, Any]:
        """Get competition settings for bot"""
        try:
            # Cache dan olish
            cache_key = f"competition_settings:{bot_id}"
            cached = cache.get(cache_key)

            if cached:
                logger.debug(f"Cache hit for bot {bot_id}")
                return cached

            # Database dan olish
            settings = await self._get_settings_from_db(bot_id)

            # Cache ga saqlash (1 soat)
            cache.set(cache_key, settings, 3600)

            return settings

        except Exception as e:
            logger.error(f"Get competition settings error: {e}")
            return self._get_default_settings(bot_id)

    @sync_to_async
    def _get_settings_from_db(self, bot_id: int) -> Dict[str, Any]:
        """Get settings from database"""
        try:
            # Bot ni topish
            bot = BotSetUp.objects.select_related('owner').get(id=bot_id)

            # Competition ni topish
            competition = Competition.objects.select_related(
                'bot'
            ).prefetch_related(
                'channels', 'point_rules', 'prize_set'
            ).get(bot=bot)

            # Settings tayyorlash
            settings = {
                "id": competition.id,
                "name": competition.name or f"Konkurs {bot_id}",
                "description": competition.description or "",
                "rules_text": competition.rules_text or "",
                "start_at": competition.start_at.isoformat() if competition.start_at else "",
                "end_at": competition.end_at.isoformat() if competition.end_at else "",
                "bot_id": bot_id,
                "bot_username": bot.bot_username,
                "owner_id": bot.owner.telegram_id,
                "channels": [
                    {
                        "id": ch.id,
                        "channel_username": ch.channel_username,
                        "channel_name": ch.channel_name or ""
                    }
                    for ch in competition.channels.all()
                ],
                "point_rules": {
                    rule.action_type: rule.points
                    for rule in competition.point_rules.all()
                },
                "prizes": [
                    {
                        "place": p.place,
                        "prize_name": p.prize_name or "",
                        "prize_amount": str(p.prize_amount) if p.prize_amount else "",
                        "type": p.type,
                        "description": p.description or ""
                    }
                    for p in competition.prize_set.all()
                ]
            }

            logger.info(f"Settings loaded for bot {bot_id}")
            return settings

        except Competition.DoesNotExist:
            logger.warning(f"No competition found for bot {bot_id}")
            return self._get_default_settings(bot_id)
        except Exception as e:
            logger.error(f"Database error for bot {bot_id}: {e}")
            return self._get_default_settings(bot_id)

    def _get_default_settings(self, bot_id: int) -> Dict[str, Any]:
        """Get default settings when competition not found"""
        return {
            "id": bot_id,
            "name": f"Konkurs {bot_id}",
            "description": "",
            "rules_text": "",
            "bot_id": bot_id,
            "bot_username": "",
            "channels": [],
            "point_rules": {},
            "prizes": []
        }