# django_app/core/services/bot_service.py
from asgiref.sync import sync_to_async
from ..models.bot import BotSetUp

class BotService:
    @sync_to_async
    def get_bot_by_owner(self, owner):
        return BotSetUp.objects.filter(owner=owner).first()

    @sync_to_async
    def update_status(self, bot, status):
        bot.status = status
        bot.save()