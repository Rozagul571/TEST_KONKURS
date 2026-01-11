# bots/user_bots/base_template/services/competition_service.py
"""
Competition Service - Bot sozlamalarini olish
MUHIM: Faqat shu bot_id ga tegishli ma'lumotlar
"""
import logging
from typing import Dict, Any, Optional
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class CompetitionService:
    """Competition settings service"""

    async def get_competition_settings(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Competition sozlamalarini olish"""
        try:
            # Redis cache (agar mavjud bo'lsa)
            try:
                from shared.redis_client import redis_client
                if redis_client.is_connected():
                    cached = await redis_client.get_bot_settings(bot_id)
                    if cached:
                        return cached
            except:
                pass

            # Database dan
            settings = await self._fetch_from_db(bot_id)

            # Cache (agar Redis bor bo'lsa)
            if settings:
                try:
                    from shared.redis_client import redis_client
                    if redis_client.is_connected():
                        await redis_client.set_bot_settings(bot_id, settings, 300)
                except:
                    pass

            return settings

        except Exception as e:
            logger.error(f"Get settings error: {e}", exc_info=True)
            return None

    @sync_to_async
    def _fetch_from_db(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Database dan olish"""
        try:
            from django_app.core.models import Competition

            competition = Competition.objects.select_related(
                'bot', 'bot__owner'
            ).prefetch_related(
                'channels', 'point_rules', 'prize_set'
            ).filter(
                bot_id=bot_id,
                bot__is_active=True
            ).first()

            if not competition:
                logger.warning(f"Competition not found for bot {bot_id}")
                return None

            # Channels
            channels_data = []
            for ch in competition.channels.all():
                channels_data.append({
                    'id': ch.id,
                    'channel_username': ch.channel_username or '',
                    'channel_name': ch.title or ch.channel_username or '',
                    'type': ch.type
                })

            # Point rules
            point_rules = {}
            for rule in competition.point_rules.all():
                point_rules[rule.action_type] = rule.points

            # Prizes
            prizes_data = []
            for prize in competition.prize_set.all().order_by('place'):
                prizes_data.append({
                    'place': prize.place,
                    'prize_name': prize.prize_name or '',
                    'prize_amount': float(prize.prize_amount) if prize.prize_amount else None,
                    'type': prize.type,
                    'description': prize.description or ''
                })

            return {
                'id': competition.id,
                'bot_id': bot_id,
                'name': competition.name or '',
                'description': competition.description or '',
                'rules_text': competition.rules_text or '',
                'status': competition.status,
                'bot_username': competition.bot.bot_username if competition.bot else '',
                'channels': channels_data,
                'point_rules': point_rules,
                'prizes': prizes_data
            }

        except Exception as e:
            logger.error(f"Fetch from DB error: {e}", exc_info=True)
            return None