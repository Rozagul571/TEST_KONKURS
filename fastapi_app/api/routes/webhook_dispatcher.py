#fastapi_app/api/routes/webhook_dispatcher.py
"""
High-performance webhook dispatcher with anti-cheat
"""
import logging
import json
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from shared.redis_client import redis_client
from shared.anti_cheat import get_anti_cheat_engine
from asgiref.sync import sync_to_async
from django_app.core.models import BotSetUp
from shared.constants import BOT_STATUSES, RATE_LIMITS

logger = logging.getLogger(__name__)
router = APIRouter()


class WebhookResponse(BaseModel):
    """Webhook response model"""
    ok: bool = True
    processed: bool = False
    bot_id: Optional[int] = None
    error: Optional[str] = None


@router.post("/dispatch/{bot_id}", response_model=WebhookResponse)
async def dispatch_webhook(
        bot_id: int,
        request: Request,
        background_tasks: BackgroundTasks
) -> WebhookResponse:
    """
    High-performance webhook dispatcher for B bots
    Features:
    1. Rate limiting
    2. Anti-cheat
    3. Async processing
    4. Background queueing
    """
    start_time = time.time()

    try:
        # 1. Parse update
        try:
            update = await request.json()
        except json.JSONDecodeError:
            return WebhookResponse(ok=True, processed=False, error="Invalid JSON")

        logger.debug(f"📥 Webhook for bot {bot_id}, update_id: {update.get('update_id')}")

        # 2. Validate bot is active
        if not await _is_bot_active(bot_id):
            logger.warning(f"Bot {bot_id} is not active")
            return WebhookResponse(ok=True, processed=False, bot_id=bot_id, error="Bot not active")

        # 3. Extract user info
        user_id = _extract_user_id(update)
        if not user_id:
            return WebhookResponse(ok=True, processed=False, bot_id=bot_id)

        # 4. Anti-cheat checks
        anti_cheat = get_anti_cheat_engine(bot_id)

        # Rate limiting
        action_type = _determine_action_type(update)
        if action_type:
            is_blocked = await anti_cheat.check_rate_limit(
                user_id, action_type, RATE_LIMITS
            )
            if is_blocked:
                logger.warning(f"Rate limit blocked: bot={bot_id}, user={user_id}")
                return WebhookResponse(ok=True, processed=False, bot_id=bot_id, error="Rate limit")

        # Bot pattern detection
        if action_type in ['start', 'callback']:
            suspicious = await anti_cheat.detect_bot_patterns(user_id, update)
            if suspicious['is_suspicious']:
                logger.warning(f"Suspicious activity blocked: {suspicious}")
                return WebhookResponse(ok=True, processed=False, bot_id=bot_id, error="Suspicious activity")

        # 5. Prepare update for processing
        update['_bot_id'] = bot_id
        update['_received_at'] = time.time()
        update['_webhook_received_at'] = start_time

        # 6. Queue update for background processing (non-blocking)
        background_tasks.add_task(_queue_update_async, bot_id, update)

        # 7. Return immediate response
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.debug(f"✅ Webhook processed in {processing_time:.1f}ms")

        return WebhookResponse(
            ok=True,
            processed=True,
            bot_id=bot_id
        )

    except Exception as e:
        logger.error(f"❌ Webhook dispatch error: {e}", exc_info=True)
        return WebhookResponse(
            ok=True,
            processed=False,
            bot_id=bot_id,
            error=str(e)[:100]
        )


def _extract_user_id(update: Dict[str, Any]) -> Optional[int]:
    """Extract user ID from Telegram update"""
    if "message" in update:
        return update["message"]["from"]["id"]
    elif "callback_query" in update:
        return update["callback_query"]["from"]["id"]
    elif "my_chat_member" in update:
        return update["my_chat_member"]["from"]["id"]
    elif "inline_query" in update:
        return update["inline_query"]["from"]["id"]
    elif "chosen_inline_result" in update:
        return update["chosen_inline_result"]["from"]["id"]

    return None


def _determine_action_type(update: Dict[str, Any]) -> Optional[str]:
    """Determine action type for rate limiting"""
    if "message" in update:
        text = update["message"].get("text", "")
        if text.startswith("/start"):
            return "start"
        return "message"
    elif "callback_query" in update:
        return "callback"
    elif "inline_query" in update:
        return "inline_query"

    return None


async def _is_bot_active(bot_id: int) -> bool:
    """Check if bot is active and running"""
    try:
        @sync_to_async
        def _check_bot():
            try:
                bot = BotSetUp.objects.get(id=bot_id)
                return bot.is_active and bot.status == BOT_STATUSES['RUNNING']
            except BotSetUp.DoesNotExist:
                return False

        return await _check_bot()

    except Exception as e:
        logger.error(f"Check bot active error: {e}")
        return False


async def _queue_update_async(bot_id: int, update: Dict[str, Any]):
    """Queue update for async processing"""
    try:
        # Push to Redis queue
        success = await redis_client.push_update(bot_id, update)

        if success:
            # Log queue metrics
            queue_length = await redis_client.get_queue_length(bot_id)
            if queue_length > 100:
                logger.warning(f"Queue length for bot {bot_id}: {queue_length}")

            logger.debug(f"✅ Update queued for bot {bot_id}")
        else:
            logger.error(f"❌ Failed to queue update for bot {bot_id}")

    except Exception as e:
        logger.error(f"Queue update error: {e}")


@router.get("/status/{bot_id}")
async def get_webhook_status(bot_id: int):
    """Get webhook status for bot"""
    try:
        queue_length = await redis_client.get_queue_length(bot_id)
        is_active = await _is_bot_active(bot_id)

        return {
            "bot_id": bot_id,
            "is_active": is_active,
            "queue_length": queue_length,
            "redis_connected": redis_client.is_connected()
        }

    except Exception as e:
        logger.error(f"Get webhook status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/{bot_id}")
async def test_webhook(bot_id: int, test_data: Dict[str, Any]):
    """Test webhook endpoint"""
    try:
        # Validate bot
        if not await _is_bot_active(bot_id):
            raise HTTPException(status_code=404, detail="Bot not found or not active")

        # Prepare test update
        update = {
            "update_id": 999999999,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "test_user",
                    "language_code": "uz"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "test_user",
                    "type": "private"
                },
                "date": int(time.time()),
                "text": "/start"
            }
        }

        # Merge test data
        update.update(test_data)

        # Queue the update
        success = await redis_client.push_update(bot_id, update)

        return {
            "success": success,
            "bot_id": bot_id,
            "message": "Test update queued"
        }

    except Exception as e:
        logger.error(f"Test webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))