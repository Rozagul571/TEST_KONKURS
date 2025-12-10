# fastapi_app/api/routes/webhooks/user.py
from fastapi import APIRouter, Request
from fastapi_app.queue import push_update
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{bot_id}")
async def user_webhook(bot_id: int, request: Request):
    try:
        update = await request.json()
        push_update(bot_id, update)
        logger.info(f"Update bot {bot_id} dan keldi")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook xatosi: {e}")
        return {"ok": False}, 500