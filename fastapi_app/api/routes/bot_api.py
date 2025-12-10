from fastapi import APIRouter, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from asgiref.sync import sync_to_async
import os
import logging
from django_app.core.models import BotSetUp, BotStatus, Competition, CompetitionStatus
from cryptography.fernet import Fernet
import asyncio

logger = logging.getLogger(__name__)
router = APIRouter()


# FIX: Token decrypt qilish funksiyasi (async-friendly)
async def decrypt_token_async(encrypted_token: str) -> str:
    """Async kontekstda token decrypt qilish"""
    try:
        FERNET_KEY = os.getenv("FERNET_KEY")
        if not FERNET_KEY:
            raise ValueError("FERNET_KEY not configured")

        # Sync funksiyani async ga o'giramiz
        def _decrypt():
            cipher = Fernet(FERNET_KEY.encode())
            return cipher.decrypt(encrypted_token.encode()).decode()

        # I/O bound operation uchun thread pool dan foydalanish
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _decrypt)

    except Exception as e:
        logger.error(f"Token decrypt xatosi: {e}")
        raise


@router.post("/run/{bot_id}")
async def run_bot(bot_id: int):
    try:
        logger.info(f"🚀 Bot {bot_id} ni ishga tushirish boshlandi...")

        # FIX: Bot ma'lumotlarini olish (async)
        bot_setup = await sync_to_async(
            lambda: BotSetUp.objects.select_related('owner').get(
                id=bot_id,
                is_active=True,
                status=BotStatus.PENDING
            )
        )()

        logger.info(f"✅ Bot topildi: @{bot_setup.bot_username}")

        # FIX: Token decrypt qilish (async)
        token = await decrypt_token_async(bot_setup.encrypted_token)

        # FIX: Bot yaratish va token tekshirish
        bot = Bot(token=token)
        try:
            me = await bot.get_me()
            logger.info(f"✅ Token tekshirildi: @{me.username}")
        except Exception as e:
            logger.error(f"❌ Token noto'g'ri: {e}")
            raise HTTPException(status_code=400, detail=f"Token noto'g'ri: {str(e)}")

        # FIX: Webhook URL
        base_url = os.getenv('WEBHOOK_URL', 'http://localhost:8001/api/webhooks/user')
        webhook_url = f"{base_url}/{bot_id}"
        webhook_secret = os.getenv('WEBHOOK_SECRET', f'secret_{bot_id}')

        # FIX: Avval webhook ni o'chirish
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info(f"✅ Old webhook o'chirildi")
        except:
            pass  # Avval webhook bo'lmasa ham hech narsa qilmaymiz

        # FIX: Yangi webhook o'rnatish
        try:
            await bot.set_webhook(
                url=webhook_url,
                secret_token=webhook_secret,
                drop_pending_updates=True
            )
            logger.info(f"✅ Webhook o'rnatildi: {webhook_url}")
        except Exception as e:
            logger.error(f"❌ Webhook o'rnatish xatosi: {e}")
            raise HTTPException(status_code=500, detail=f"Webhook o'rnatish xatosi: {str(e)}")

        # FIX: Statuslarni yangilash (async)
        await sync_to_async(lambda: setattr(bot_setup, 'status', BotStatus.RUNNING))()
        await sync_to_async(bot_setup.save)()

        logger.info(f"✅ Bot status RUNNING ga o'zgartirildi")

        # FIX: Competition statusini yangilash
        try:
            competition = await sync_to_async(
                lambda: Competition.objects.get(bot=bot_setup)
            )()
            await sync_to_async(lambda: setattr(competition, 'status', CompetitionStatus.ACTIVE))()
            await sync_to_async(competition.save)()
            logger.info(f"✅ Competition status ACTIVE ga o'zgartirildi")
        except Exception as e:
            logger.warning(f"⚠️ Competition topilmadi: {e}")

        # FIX: Cache preload
        try:
            from fastapi_app.cache import preload_bot_settings
            await preload_bot_settings(bot_id)
            logger.info(f"✅ Cache preload qilindi")
        except Exception as e:
            logger.warning(f"⚠️ Cache preload xatosi: {e}")

        # FIX: User ga xabar yuborish
        main_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if main_token and bot_setup.owner.telegram_id:
            try:
                main_bot = Bot(token=main_token)
                message_text = (
                    f"🎉 *Bot ishga tushdi!*\n\n"
                    f"🤖 *Bot:* @{bot_setup.bot_username}\n"
                    f"🆔 *ID:* {bot_id}\n"
                    f"🔗 *Link:* https://t.me/{bot_setup.bot_username}\n\n"
                    f"✅ *Status:* Ishga tushdi\n"
                    f"📊 Endi ishtirokchilar qatnasha boshlashi mumkin!"
                )
                await main_bot.send_message(
                    chat_id=bot_setup.owner.telegram_id,
                    text=message_text,
                    parse_mode="Markdown"
                )
                await main_bot.session.close()
                logger.info(f"✅ Owner ga xabar yuborildi")
            except Exception as e:
                logger.error(f"⚠️ Owner ga xabar yuborish xatosi: {e}")

        # FIX: Bot session ni yopish
        await bot.session.close()

        logger.info(f"✅✅✅ BOT {bot_id} (@{me.username}) MUVAFFAQIYATLI ISHGA TUSHIRILDI!")

        return {
            "status": "running",
            "bot_id": bot_id,
            "bot_username": me.username,
            "webhook": webhook_url,
            "message": "Bot ishga tushirildi!"
        }

    except BotSetUp.DoesNotExist:
        logger.error(f"❌ Bot {bot_id} topilmadi yoki pending emas")
        raise HTTPException(status_code=404, detail="Bot topilmadi yoki pending emas")
    except Exception as e:
        logger.error(f"❌ RUN XATOSI bot {bot_id}: {str(e)}", exc_info=True)
        error_detail = str(e)

        # FIX: Xato turlarini aniqlash
        if "Unauthorized" in error_detail or "invalid token" in error_detail.lower():
            error_detail = "Bot tokeni noto'g'ri yoki yaroqsiz. Iltimos, yangi token oling."
        elif "Connection" in error_detail:
            error_detail = "Telegram API ga ulanish xatosi. Internet aloqasini tekshiring."
        elif "decrypt" in error_detail.lower():
            error_detail = "Token decrypt qilish xatosi. FERNET_KEY ni tekshiring."

        raise HTTPException(status_code=500, detail=error_detail)