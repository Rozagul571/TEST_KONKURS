from aiogram import Router, F
from aiogram.types import CallbackQuery
from asgiref.sync import sync_to_async
from django_app.core.models.bot import BotSetUp, BotStatus
from django_app.core.models.competition import Competition, CompetitionStatus
import httpx
import os
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)
router = Router()
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8001")


@router.callback_query(F.data.startswith("run_bot:"))
async def run_bot_handler(callback: CallbackQuery):
    bot_id = int(callback.data.split(":")[1])
    bot = await sync_to_async(BotSetUp.objects.select_related('owner').get)(id=bot_id, is_active=True,
                                                                            status=BotStatus.PENDING)
    if not bot:
        await callback.bot.answer_callback_query(callback.id, text="❌ Bot topilmadi!", show_alert=True)
        return
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_URL}/api/bots/run/{bot_id}")
        if response.status_code == 200:
            bot.status = BotStatus.RUNNING
            await sync_to_async(bot.save)()
            competition = await sync_to_async(Competition.objects.get)(bot=bot)
            competition.status = CompetitionStatus.ACTIVE
            await sync_to_async(competition.save)()
            await callback.message.edit_text(
                f"✅ <b>Bot ishga tushirildi!</b>\n\n"
                f"🤖 <b>Bot:</b> @{bot.bot_username}\n"
                f"👤 <b>Admin:</b> {bot.owner.full_name}\n"
                f"🔄 <b>Status:</b> Running",
                parse_mode="HTML"
            )
            await callback.bot.answer_callback_query(callback.id, text="✅ Bot ishga tushirildi!", show_alert=True)
            # User ga xabar
            main_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            main_bot = Bot(token=main_bot_token)
            await main_bot.send_message(
                bot.owner.telegram_id,
                f"🏁 Bot @{bot.bot_username} ishga tushdi! Endi participantlar kirishi mumkin."
            )
            await main_bot.session.close()
        else:
            await callback.bot.answer_callback_query(callback.id, text="❌ FastAPI dan xato!", show_alert=True)
    except Exception as e:
        logger.error(f"Run handler xato: {str(e)}")
        await callback.bot.answer_callback_query(callback.id, text="❌ Xatolik!", show_alert=True)
