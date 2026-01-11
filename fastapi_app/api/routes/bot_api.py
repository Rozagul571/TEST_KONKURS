# fastapi_app/api/routes/bot_api.py
"""
Bot API - Bot management endpoints
Vazifasi: Botlarni run/stop qilish
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from aiogram import Bot
from asgiref.sync import sync_to_async
import os
import logging
import asyncio
from cryptography.fernet import Fernet

from bots.main_bot.services.notification_service import NotificationService
from django_app.core.models import BotSetUp, BotStatus, Competition, CompetitionStatus
from shared.redis_client import redis_client
from fastapi_app.workers.bot_worker import worker_pool
from bots.user_bots.base_template.services.competition_service import CompetitionService

logger = logging.getLogger(__name__)

router = APIRouter()


async def decrypt_token_async(encrypted_token: str) -> str:
    """Token ni decrypt qilish"""
    fernet = Fernet(os.getenv("FERNET_KEY").encode())

    def _decrypt():
        return fernet.decrypt(encrypted_token.encode()).decode()

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _decrypt)


@router.post("/run/{bot_id}")
async def run_bot(bot_id: int, background_tasks: BackgroundTasks):
    """
    Bot ni ishga tushirish

    Args:
        bot_id: Bot ID
    """
    try:
        logger.info(f"🚀 Running bot {bot_id}...")

        # Bot olish
        bot_setup = await sync_to_async(
            BotSetUp.objects.select_related('owner').get
        )(id=bot_id, is_active=True, status=BotStatus.PENDING)

        logger.info(f"✅ Bot found: @{bot_setup.bot_username}")

        # Token decrypt
        token = await decrypt_token_async(bot_setup.encrypted_token)

        # Bot tekshirish
        bot = Bot(token=token)
        me = await bot.get_me()
        logger.info(f"✅ Bot verified: @{me.username}")

        # Username yangilash (agar o'zgargan bo'lsa)
        if bot_setup.bot_username != me.username:
            bot_setup.bot_username = me.username
            await sync_to_async(bot_setup.save)(update_fields=['bot_username'])

        # Webhook o'rnatish
        base_url = os.getenv("WEBHOOK_URL", "http://localhost:8001")
        webhook_url = f"{base_url}/api/webhooks/dispatch/{bot_id}"

        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info(f"✅ Webhook set: {webhook_url}")

        # Status yangilash
        bot_setup.status = BotStatus.RUNNING
        await sync_to_async(bot_setup.save)(update_fields=['status'])

        # Competition status yangilash
        try:
            competition = await sync_to_async(Competition.objects.get)(bot=bot_setup)
            competition.status = CompetitionStatus.ACTIVE
            await sync_to_async(competition.save)(update_fields=['status'])
            logger.info("✅ Competition status updated to ACTIVE")
        except Competition.DoesNotExist:
            logger.warning(f"Competition not found for bot {bot_id}")

        # Redis ga settings yuklash
        await preload_bot_settings_to_redis(bot_id)

        # Worker ishga tushirish
        await worker_pool.start_worker(bot_id, worker_count=1)
        logger.info(f"✅ Worker started for bot {bot_id}")

        # Notifications yuborish
        await send_run_notifications(bot_setup, bot_id, me.username)

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
    """Bot settings ni Redis ga yuklash"""
    try:
        service = CompetitionService()
        settings = await service.get_competition_settings(bot_id)

        if settings and redis_client.is_connected():
            await redis_client.set_bot_settings(bot_id, settings, 3600)
            logger.info(f"✅ Bot {bot_id} settings cached in Redis")
        else:
            logger.warning(f"No settings found for bot {bot_id} or Redis not connected")

    except Exception as e:
        logger.error(f"Preload settings error: {e}")


async def send_run_notifications(bot_setup: BotSetUp, bot_id: int, bot_username: str):
    """Run notifications yuborish"""
    service = NotificationService()
    await service.send_bot_run_to_owner(bot_setup.owner.telegram_id, bot_username, bot_id)
    await service.send_bot_run_to_superadmin(bot_username, bot_id)


@router.get("/status/{bot_id}")
async def get_bot_status(bot_id: int):
    """Bot statusini olish"""
    try:
        bot = await sync_to_async(BotSetUp.objects.get)(id=bot_id)

        queue_length = 0
        if redis_client.is_connected():
            queue_length = await redis_client.get_queue_length(bot_id)

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
        raise HTTPException(status_code=404, detail="Bot topilmadi")


@router.post("/stop/{bot_id}")
async def stop_bot(bot_id: int):
    """Bot ni to'xtatish"""
    try:
        bot_setup = await sync_to_async(BotSetUp.objects.get)(id=bot_id)

        # Status yangilash
        bot_setup.status = BotStatus.STOPPED
        await sync_to_async(bot_setup.save)(update_fields=['status'])

        # Competition status yangilash
        try:
            competition = await sync_to_async(Competition.objects.get)(bot=bot_setup)
            competition.status = CompetitionStatus.FINISHED
            await sync_to_async(competition.save)(update_fields=['status'])
        except:
            pass

        # Worker to'xtatish
        await worker_pool.stop_worker(bot_id)

        # Webhook o'chirish
        try:
            token = await decrypt_token_async(bot_setup.encrypted_token)
            bot = Bot(token=token)
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.session.close()
        except:
            pass

        # Cache tozalash
        if redis_client.is_connected():
            await redis_client.clear_bot_cache(bot_id)

        logger.info(f"✅ Bot {bot_id} stopped")

        return {
            "status": "stopped",
            "bot_id": bot_id,
            "bot_username": bot_setup.bot_username,
            "message": "Bot to'xtatildi"
        }

    except BotSetUp.DoesNotExist:
        raise HTTPException(status_code=404, detail="Bot topilmadi")

    except Exception as e:
        logger.error(f"Stop bot error: {e}")
        raise HTTPException(status_code=500, detail=f"Xatolik: {str(e)}")