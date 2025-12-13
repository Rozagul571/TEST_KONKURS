from fastapi import APIRouter, HTTPException, BackgroundTasks
from aiogram import Bot
from asgiref.sync import sync_to_async
import os
import logging
from cryptography.fernet import Fernet
import asyncio
import json

from django_app.core.models import BotSetUp, BotStatus, Competition, CompetitionStatus
from shared.redis_client import redis_client
from fastapi_app.workers.bot_worker import worker_pool

logger = logging.getLogger(__name__)
router = APIRouter()


async def decrypt_token_async(encrypted_token: str) -> str:
    """Async token decrypt"""
    try:
        fernet = Fernet(os.getenv("FERNET_KEY").encode())

        def _decrypt():
            return fernet.decrypt(encrypted_token.encode()).decode()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _decrypt)
    except Exception as e:
        logger.error(f"Token decrypt error: {e}")
        raise


@router.post("/run/{bot_id}")
async def run_bot(bot_id: int, background_tasks: BackgroundTasks):
    """
    Run bot - To'liq ishlaydigan versiya
    """
    try:
        logger.info(f"🚀 Running bot {bot_id}...")

        # 1. Botni topish
        bot_setup = await sync_to_async(
            BotSetUp.objects.select_related('owner').get
        )(id=bot_id, is_active=True, status=BotStatus.PENDING)

        logger.info(f"✅ Bot found: @{bot_setup.bot_username}")

        # 2. Token decrypt qilish
        token = await decrypt_token_async(bot_setup.encrypted_token)

        # 3. Botni test qilish
        bot = Bot(token=token)
        me = await bot.get_me()
        logger.info(f"✅ Bot verified: @{me.username}")

        # 4. Webhook o'rnatish (MUHIM: to'g'ri URL)
        base_url = os.getenv("WEBHOOK_URL", "https://novelettish-madilyn-fungitoxic.ngrok-free.dev")
        webhook_url = f"{base_url}/api/webhooks/dispatch/{bot_id}"  # To'g'ri format

        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        logger.info(f"✅ Webhook set: {webhook_url}")

        # 5. Statuslarni yangilash
        bot_setup.status = BotStatus.RUNNING
        await sync_to_async(bot_setup.save)()

        # 6. Competition statusini yangilash
        try:
            competition = await sync_to_async(Competition.objects.get)(bot=bot_setup)
            competition.status = CompetitionStatus.ACTIVE
            await sync_to_async(competition.save)()
            logger.info("✅ Competition status updated to ACTIVE")
        except Exception as e:
            logger.warning(f"Competition not found: {e}")

        # 7. Bot sozlamalarini Redis ga yuklash
        await preload_bot_settings_to_redis(bot_id)

        # 8. Worker boshlash
        await worker_pool.start_worker(bot_id, worker_count=2)
        logger.info(f"✅ Worker started for bot {bot_id}")

        # 9. Notification yuborish
        await send_run_notifications(bot_setup, bot_id, me.username)

        # 10. Bot sessionni yopish
        await bot.session.close()

        logger.info(f"✅✅✅ BOT {bot_id} (@{me.username}) SUCCESSFULLY STARTED!")

        return {
            "status": "running",
            "bot_id": bot_id,
            "bot_username": me.username,
            "webhook": webhook_url,
            "message": "Bot ishga tushdi!"
        }

    except BotSetUp.DoesNotExist:
        logger.error(f"Bot {bot_id} not found or not pending")
        raise HTTPException(status_code=404, detail="Bot topilmadi yoki pending holatda emas")
    except Exception as e:
        logger.error(f"Run bot error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Xatolik: {str(e)}")


async def preload_bot_settings_to_redis(bot_id: int):
    """Bot sozlamalarini Redis ga yuklash"""
    try:
        from django_app.core.services.competition_service import CompetitionService

        service = CompetitionService()
        settings = await service.get_competition_settings(bot_id)

        if settings:
            # Redis ga saqlash
            if redis_client.is_connected():
                redis_client.set_bot_settings(bot_id, settings)
                logger.info(f"✅ Bot {bot_id} settings cached in Redis")

            # Django cache ga ham saqlash
            from django.core.cache import cache
            cache_key = f"bot_full_settings:{bot_id}"
            cache.set(cache_key, settings, 3600)

        else:
            logger.warning(f"No settings found for bot {bot_id}")

    except Exception as e:
        logger.error(f"Preload settings error: {e}")


async def send_run_notifications(bot_setup: BotSetUp, bot_id: int, bot_username: str):
    """Run notifications yuborish"""
    try:
        main_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not main_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set")
            return

        main_bot = Bot(token=main_token)

        # 1. Owner ga xabar
        owner_message = (
            f"🎉 *Bot ishga tushdi!*\n\n"
            f"🤖 *Bot:* @{bot_username}\n"
            f"🆔 *ID:* {bot_id}\n"
            f"🔗 *Link:* https://t.me/{bot_username}\n\n"
            f"✅ *Status:* Ishga tushdi\n"
            f"📊 Endi ishtirokchilar qatnasha boshlashi mumkin!"
        )

        await main_bot.send_message(
            chat_id=bot_setup.owner.telegram_id,
            text=owner_message,
            parse_mode="Markdown"
        )
        logger.info(f"✅ Notification sent to owner {bot_setup.owner.telegram_id}")

        # 2. SuperAdmin ga xabar
        super_admin_id = os.getenv("SUPER_ADMIN_TELEGRAM_ID")
        if super_admin_id:
            super_message = (
                f"✅ *Bot ishga tushdi!*\n\n"
                f"🤖 *Bot:* @{bot_username}\n"
                f"🆔 *ID:* {bot_id}\n"
                f"🔗 *Link:* https://t.me/{bot_username}\n\n"
                f"📊 Endi ishtirokchilar qatnashishni boshlaydi!"
            )

            await main_bot.send_message(
                chat_id=int(super_admin_id),
                text=super_message,
                parse_mode="Markdown"
            )
            logger.info(f"✅ Notification sent to superadmin {super_admin_id}")

        await main_bot.session.close()

    except Exception as e:
        logger.error(f"Send notification error: {e}")


@router.get("/status/{bot_id}")
async def get_bot_status(bot_id: int):
    """Bot statusini olish"""
    try:
        bot = await sync_to_async(BotSetUp.objects.get)(id=bot_id)

        # Queue uzunligi
        queue_length = 0
        if redis_client.is_connected():
            queue_key = f"bot_queue:{bot_id}"
            queue_length = redis_client.client.llen(queue_key)

        # Webhook check
        webhook_info = ""
        try:
            token = await decrypt_token_async(bot.encrypted_token)
            test_bot = Bot(token=token)
            webhook = await test_bot.get_webhook_info()
            webhook_info = webhook.url if webhook.url else "No webhook"
            await test_bot.session.close()
        except:
            webhook_info = "Error checking"

        return {
            "bot_id": bot_id,
            "username": bot.bot_username,
            "status": bot.status,
            "is_active": bot.is_active,
            "queue_length": queue_length,
            "webhook": webhook_info,
            "owner_id": bot.owner.telegram_id
        }

    except BotSetUp.DoesNotExist:
        raise HTTPException(404, detail="Bot topilmadi")