import django
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
import logging
import json
from typing import Dict, Any, Optional
from shared.redis_client import redis_client
from shared.anti_cheat import get_anti_cheat_engine
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)
router = APIRouter()

# Rate limits configuration
RATE_LIMITS = {
    "start": {"limit": 3, "window": 60},  # 3 starts per minute
    "message": {"limit": 30, "window": 60},  # 30 messages per minute
    "callback": {"limit": 20, "window": 60},  # 20 callbacks per minute
    "join_check": {"limit": 4, "window": 15},  # 4 checks per 15 seconds
}


@router.post("/dispatch/{bot_id}")
async def dispatch_webhook(bot_id: int, request: Request, background_tasks: BackgroundTasks):
    """
    Universal webhook dispatcher for all B bots
    Handles Telegram updates and routes to appropriate queues
    """
    try:
        # Parse update
        update = await request.json()

        # Validate bot exists and is running
        bot_active = await _check_bot_active(bot_id)
        if not bot_active:
            raise HTTPException(status_code=404, detail="Bot not found or not running")

        # Extract user info
        user_id = _extract_user_id(update)
        if not user_id:
            return {"ok": True}  # Ignore updates without user

        # Anti-cheat check
        anti_cheat = get_anti_cheat_engine(bot_id)

        # Check rate limits
        action_type = _determine_action_type(update)
        if action_type:
            is_blocked = await anti_cheat.check_rate_limit(
                user_id, action_type, RATE_LIMITS
            )
            if is_blocked:
                logger.warning(f"Rate limit blocked: bot={bot_id}, user={user_id}")
                return {"ok": True}  # Silently ignore

        # Detect suspicious patterns
        if action_type in ["start", "callback"]:
            suspicious = await anti_cheat.detect_bot_patterns(user_id, update)
            if suspicious['is_suspicious']:
                logger.warning(f"Suspicious activity blocked: {suspicious}")
                return {"ok": True}

        # Enrich update with bot_id for worker
        update["_bot_id"] = bot_id
        update["_received_at"] = (django
                                  .utils.timezone.now().isoformat())

        # Push to bot-specific queue (non-blocking)
        background_tasks.add_task(_queue_update, bot_id, update)

        # Immediate response to Telegram
        return {"ok": True}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Webhook dispatch error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


def _extract_user_id(update: Dict[str, Any]) -> Optional[int]:
    """Extract user ID from Telegram update"""
    if "message" in update:
        return update["message"]["from"]["id"]
    elif "callback_query" in update:
        return update["callback_query"]["from"]["id"]
    elif "my_chat_member" in update:
        return update["my_chat_member"]["from"]["id"]
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
    return None


async def _check_bot_active(bot_id: int) -> bool:
    """Check if bot is active and running"""
    from django_app.core.models import BotSetUp, BotStatus

    try:
        bot = await sync_to_async(BotSetUp.objects.get)(id=bot_id)
        return bot.status == BotStatus.RUNNING and bot.is_active
    except BotSetUp.DoesNotExist:
        return False


async def _queue_update(bot_id: int, update: Dict[str, Any]):
    """Queue update for background processing"""
    try:
        success = redis_client.push_update(bot_id, update)
        if success:
            logger.debug(f"Update queued for bot {bot_id}")
        else:
            logger.error(f"Failed to queue update for bot {bot_id}")
    except Exception as e:
        logger.error(f"Queue update error: {e}")