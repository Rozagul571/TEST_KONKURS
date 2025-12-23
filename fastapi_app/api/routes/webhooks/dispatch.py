# fastapi_app/api/routes/webhooks/dispatch.py - YANGI VERSIYA
from fastapi import APIRouter, Request, BackgroundTasks
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{bot_id}")
async def dispatch_webhook(bot_id: int, request: Request, background_tasks: BackgroundTasks):
    """B Botlar uchun webhook dispatcher"""
    try:
        # Update ni olish
        update = await request.json()

        # Bot ID ni qo'shish
        update['_bot_id'] = bot_id

        # Background task ga qo'shish
        background_tasks.add_task(process_update_async, bot_id, update)

        # Darhol javob qaytarish
        return {"ok": True}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": True}  # Telegramga har doim True qaytarish kerak


async def process_update_async(bot_id: int, update: dict):
    """Async update processing"""
    try:
        from shared.redis_client import redis_client

        # Redis ga saqlash
        if redis_client.is_connected():
            await redis_client.push_update(bot_id, update)
            logger.info(f"Update queued for bot {bot_id}")

    except Exception as e:
        logger.error(f"Process update error: {e}")