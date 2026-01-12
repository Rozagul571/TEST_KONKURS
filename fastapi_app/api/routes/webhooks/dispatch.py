# fastapi_app/api/routes/webhooks/dispatch.py

from fastapi import APIRouter, Request, BackgroundTasks
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{bot_id}")
async def dispatch_webhook(bot_id: int, request: Request, background_tasks: BackgroundTasks):
    """
    B Bot webhook
    """
    try:
        update = await request.json()
        logger.info(f"📥 Webhook received for bot {bot_id}: update_id={update.get('update_id')}")

        background_tasks.add_task(process_update_directly, bot_id, update)

        return {"ok": True}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": True}


async def process_update_directly(bot_id: int, update: dict):
    """
    Update ni TO'G'RIDAN-TO'G'RI process qilish
    """
    try:
        from bots.user_bots.base_template.bot_processor import BotProcessor

        processor = BotProcessor(bot_id)
        await processor.process_update(update)

    except Exception as e:
        logger.error(f"Process update error for bot {bot_id}: {e}", exc_info=True)