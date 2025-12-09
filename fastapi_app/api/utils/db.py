from asgiref.sync import sync_to_async
from django_app.core.models import BotSetUp, SystemSettings

@sync_to_async
def get_pending_bot_username(tg_id: int) -> str:
    try:
        bot = BotSetUp.objects.filter(owner__telegram_id=tg_id, status='pending').first()
        return bot.bot_username if bot else "topilmadi"
    except:
        return "topilmadi"

@sync_to_async
def get_admin_telegram_url() -> str:
    settings = SystemSettings.get()
    return settings.get_telegram_url()