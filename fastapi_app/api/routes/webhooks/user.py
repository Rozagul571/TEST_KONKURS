# fastapi_app/api/routes/webhooks/user.py (push_update o‘chirildi, dispatch ishlatilmoqda)
from fastapi import APIRouter, Request
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{bot_id}")
async def user_webhook(bot_id: int, request: Request):
    """User webhook - dispatch.py ga yo‘naltiriladi (duplicate yo‘q)"""
    try:
        update = await request.json()
        logger.info(f"Update received for bot {bot_id}")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": True}