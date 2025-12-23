# bots/main_bot/api/webhook.py
from fastapi import APIRouter, Request
from asgiref.sync import sync_to_async
from django_app.core.models.bot import BotSetUp
from bots.main_bot.services.notification_service import NotificationService
import logging
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/handle-user-completed")
async def handle_user_completed(request: Request):
    try:
        data = await request.json()
        user_tg_id = data["user_tg_id"]
        competition_name = data["competition_name"]
        description = data["description"]

        bot_username = await get_bot_username_async(user_tg_id)

        service = NotificationService()
        await service.send_user_competition_completed(user_tg_id, bot_username, competition_name, description)

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Notification xatosi: {e}")
        return {"status": "error", "detail": str(e)}, 500

@sync_to_async
def get_bot_username_async(user_tg_id):
    bot = BotSetUp.objects.filter(owner__telegram_id=user_tg_id, is_active=True).order_by('-created_at').first()
    return bot.bot_username if bot else "topilmadi"