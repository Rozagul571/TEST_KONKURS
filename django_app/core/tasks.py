from celery import shared_task
from django.utils import timezone
from .models.competition import Competition, CompetitionStatus
from .models.bot import BotSetUp, BotStatus
from bots.user_bots.process_manager.process_manager import ProcessManager
import os
from aiogram import Bot

@shared_task
def schedule_competition_end(competition_id):
    """Avto-finish task. Vazifasi: end_at da competition ni FINISHED qilish."""
    competition = Competition.objects.get(id=competition_id)
    if competition.status == CompetitionStatus.ACTIVE:
        competition.status = CompetitionStatus.FINISHED
        competition.save()
        bot = competition.bot
        if bot:
            bot.status = BotStatus.STOPPED
            if bot.process_id:
                ProcessManager().stop_bot(bot.id)
            bot.process_id = None
            bot.save()
    # Owner ga xabar (main bot orqali)
    main_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    main_bot = Bot(token=main_bot_token)
    main_bot.send_message(
        competition.creator.telegram_id,
        f"🏁 Konkurs '{competition.name}' tugadi! G'oliblar: [admin panelda ko'ring]."
    )
    main_bot.session.close()