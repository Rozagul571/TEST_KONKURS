from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import logging
import json
from typing import Dict, Any

from shared.redis_client import redis_client
from asgiref.sync import sync_to_async
from django_app.core.models import BotSetUp, BotStatus
import django

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/dispatch/{bot_id}")
async def dispatch_webhook(bot_id: int, request: Request, background_tasks: BackgroundTasks):
    """
    B Botlar uchun webhook dispatcher
    URL: https://your-ngrok.ngrok-free.dev/api/webhooks/dispatch/{bot_id}
    """
    try:
        # Update ni olish
        update = await request.json()
        logger.debug(f"📥 Update for bot {bot_id}: {update.get('update_id', 'unknown')}")

        # Bot faolligini tekshirish
        if not await is_bot_running(bot_id):
            logger.warning(f"Bot {bot_id} is not running")
            return {"ok": True}  # Telegramga har doim OK qaytarish

        # Update ni boyitish
        update["_bot_id"] = bot_id
        update["_received_at"] = django.utils.timezone.now().isoformat()

        # Background task sifatida queue ga qo'shish
        background_tasks.add_task(queue_update, bot_id, update)

        # Tez javob qaytarish
        return {"ok": True}

    except json.JSONDecodeError:
        logger.error("Invalid JSON received")
        return {"ok": True}  # Telegramga har doim OK
    except Exception as e:
        logger.error(f"Dispatch error: {e}")
        return {"ok": True}  # Telegramga har doim OK


async def is_bot_running(bot_id: int) -> bool:
    """Bot running holatda ekanligini tekshirish"""
    try:
        bot = await sync_to_async(BotSetUp.objects.get)(id=bot_id)
        return bot.status == BotStatus.RUNNING and bot.is_active
    except BotSetUp.DoesNotExist:
        return False
    except Exception as e:
        logger.error(f"Check bot running error: {e}")
        return False


async def queue_update(bot_id: int, update: Dict[str, Any]):
    """Update ni queue ga qo'shish"""
    try:
        if redis_client.is_connected():
            # Queue ga qo'shish
            success = redis_client.push_update(bot_id, update)

            if success:
                logger.debug(f"✅ Update queued for bot {bot_id}")

                # Queue uzunligini log qilish
                queue_key = f"bot_queue:{bot_id}"
                length = redis_client.client.llen(queue_key)
                if length > 100:
                    logger.warning(f"Queue length for bot {bot_id}: {length}")
            else:
                logger.error(f"❌ Failed to queue update for bot {bot_id}")
        else:
            logger.error("Redis not connected")

    except Exception as e:
        logger.error(f"Queue update error: {e}")