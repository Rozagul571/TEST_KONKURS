from fastapi import APIRouter, HTTPException
from aiogram import Bot
from asgiref.sync import sync_to_async
import os
from django_app.core.models import BotSetUp, BotStatus, Competition, CompetitionStatus

router = APIRouter(prefix="/bots", tags=["Bot Management"])


@router.post("/run/{bot_id}")
async def run_bot(bot_id: int):
    """SuperAdmin bosganda — webhook o‘rnatiladi"""
    bot_setup = await sync_to_async(BotSetUp.objects.get)(
        id=bot_id,
        is_active=True,
        status=BotStatus.PENDING
    )

    token = bot_setup.get_token()
    bot = Bot(token=token)

    webhook_url = f"{os.getenv('WEBHOOK_URL')}/api/webhooks/user/{bot_id}"
    await bot.set_webhook(url=webhook_url)

    # Bu yerda muhim!

    await bot.send_message(
        bot_setup.owner.telegram_id,
        f"Bot @{bot_setup.bot_username} muvaffaqiyatli ishga tushdi!\n\n"
        f"Foydalanuvchilar endi qatnashishi mumkin."
    )
    await bot.session.close()

    # Statuslarni yangilash
    bot_setup.status = BotStatus.RUNNING
    await sync_to_async(bot_setup.save)()

    comp = await sync_to_async(Competition.objects.get)(bot=bot_setup)
    comp.status = CompetitionStatus.ACTIVE
    await sync_to_async(comp.save)()

    return {"status": "running", "webhook_set": webhook_url}


@router.post("/stop/{bot_id}")
async def stop_bot(bot_id: int):
    bot_setup = await sync_to_async(BotSetUp.objects.get)(
        id=bot_id,
        status=BotStatus.RUNNING
    )

    token = bot_setup.get_token()
    bot = Bot(token=token)
    await bot.delete_webhook()
    await bot.send_message(bot_setup.owner.telegram_id, f"Bot @{bot_setup.bot_username} to‘xtatildi.")
    await bot.session.close()

    bot_setup.status = BotStatus.STOPPED
    await sync_to_async(bot_setup.save)()

    comp = await sync_to_async(Competition.objects.get)(bot=bot_setup)
    comp.status = CompetitionStatus.FINISHED
    await sync_to_async(comp.save)()

    return {"status": "stopped"}