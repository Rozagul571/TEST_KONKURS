import os
import json
import logging
from redis import Redis
from asgiref.sync import sync_to_async
from django_app.core.models import Competition, BotSetUp

logger = logging.getLogger(__name__)


# FIX: Redis connection retry bilan
def get_redis_client():
    """Redis client yaratish, agar ulanish bo'lmasa retry"""
    try:
        client = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
            max_connections=10
        )

        # Test connection
        client.ping()
        logger.info("✅ Redis ga muvaffaqiyatli ulandi")
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis ga ulanish xatosi: {e}")
        # In-memory fallback yaratish
        return None


redis_client = get_redis_client()


async def preload_bot_settings(bot_id: int):
    """Bot sozlamalarini Redis cache ga yuklash"""
    try:
        # Agar Redis bo'lmasa, hech narsa qilmaymiz
        if not redis_client:
            logger.warning(f"⚠️ Redis yo'q, cache skip qilindi bot {bot_id}")
            return False

        # Bot ma'lumotlarini olish
        bot_setup = await sync_to_async(
            lambda: BotSetUp.objects.select_related('owner').get(id=bot_id)
        )()

        # Competition ma'lumotlarini olish
        try:
            competition = await sync_to_async(
                lambda: Competition.objects.select_related('bot').prefetch_related(
                    'channels', 'point_rules', 'prize_set'
                ).get(bot=bot_setup)
            )()

            # Kanallar
            channels = competition.channels.all()
            # Point rules
            point_rules = competition.point_rules.all()
            # Sovrinlar
            prizes = competition.prize_set.all()

            # Sync funksiyalar
            channels_list = await sync_to_async(list)(channels)
            point_rules_list = await sync_to_async(list)(point_rules)
            prizes_list = await sync_to_async(list)(prizes)

            settings = {
                "id": competition.id,
                "name": competition.name or f"Konkurs {bot_id}",
                "description": competition.description or "",
                "rules_text": competition.rules_text or "",
                "start_at": str(competition.start_at) if competition.start_at else "",
                "end_at": str(competition.end_at) if competition.end_at else "",
                "bot_username": bot_setup.bot_username,
                "bot_id": bot_id,
                "owner_id": bot_setup.owner.telegram_id,
                "channels": [
                    {"channel_username": ch.channel_username, "id": ch.id}
                    for ch in channels_list
                ],
                "point_rules": {
                    rule.action_type: rule.points
                    for rule in point_rules_list
                },
                "prizes": [
                    {
                        "place": p.place,
                        "prize_name": p.prize_name or "",
                        "prize_amount": str(p.prize_amount) if p.prize_amount else "",
                        "type": p.type
                    }
                    for p in prizes_list
                ]
            }
        except Competition.DoesNotExist:
            # Competition bo'lmasa ham boshlang'ich sozlamalar
            settings = {
                "id": bot_id,
                "name": f"Konkurs {bot_setup.bot_username}",
                "description": "",
                "rules_text": "",
                "bot_username": bot_setup.bot_username,
                "bot_id": bot_id,
                "owner_id": bot_setup.owner.telegram_id,
                "channels": [],
                "point_rules": {},
                "prizes": []
            }

        # Redis ga saqlash
        redis_client.set(f"bot_settings:{bot_id}", json.dumps(settings), ex=86400)

        logger.info(f"✅ Bot {bot_id} sozlamalari cache ga yuklandi")
        return True

    except Exception as e:
        logger.error(f"❌ Preload xatosi bot {bot_id}: {e}")
        return False


def get_bot_settings(bot_id: int) -> dict:
    """Redis dan bot sozlamalarini olish"""
    try:
        if not redis_client:
            return {}

        data = redis_client.get(f"bot_settings:{bot_id}")
        if data:
            return json.loads(data)
        return {}
    except Exception as e:
        logger.error(f"Get settings xatosi bot {bot_id}: {e}")
        return {}


# Test funksiyasi
def test_redis():
    """Redis ulanishini test qilish"""
    try:
        if redis_client and redis_client.ping():
            logger.info("✅ Redis ishlayapti")
            return True
        else:
            logger.warning("⚠️ Redis yo'q yoki ishlamayapti")
            return False
    except:
        logger.warning("⚠️ Redis ga ulanish imkoni yo'q")
        return False