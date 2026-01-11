# fastapi_app/workers/bot_worker.py
"""
High-performance bot worker with async processing - TO'G'RILANGAN
Vazifasi: B botlar uchun update larni qayta ishlash
"""
import asyncio
import logging
import os
from typing import Dict, Any, Optional

from aiogram import Bot
from cryptography.fernet import Fernet

from bots.user_bots.base_template.handlers.menu_handler import MenuHandlers
from bots.user_bots.base_template.handlers.start_handler import StartHandler
from bots.user_bots.base_template.handlers.channel_handler import ChannelHandler
from bots.user_bots.base_template.services.competition_service import CompetitionService
from shared.redis_client import redis_client
from shared.constants import BUTTON_TEXTS
from asgiref.sync import sync_to_async
from django_app.core.models import BotSetUp

logger = logging.getLogger(__name__)


class BotWorker:
    """High-performance bot worker with async processing"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.running = False
        self.bot: Optional[Bot] = None
        self.token: Optional[str] = None
        self.handlers: Dict[str, Any] = {}

    async def start(self):
        """Worker ni ishga tushirish"""
        try:
            self.running = True

            # Bot token olish
            self.token = await self._get_bot_token()
            if not self.token:
                logger.error(f"❌ Failed to get token for bot {self.bot_id}")
                self.running = False
                return

            # Bot init
            self.bot = Bot(token=self.token)

            # Test connection
            me = await self.bot.get_me()
            logger.info(f"✅ Bot worker started: @{me.username} (ID: {self.bot_id})")

            # Handlers init
            await self._initialize_handlers()

            # Processing loop
            asyncio.create_task(self._processing_loop())

        except Exception as e:
            logger.error(f"❌ Start worker error: {e}", exc_info=True)
            self.running = False

    async def _get_bot_token(self) -> Optional[str]:
        """Bot token ni database dan olish"""
        try:
            @sync_to_async
            def _get_token():
                try:
                    bot = BotSetUp.objects.get(id=self.bot_id, is_active=True)
                    fernet = Fernet(os.getenv("FERNET_KEY").encode())
                    return fernet.decrypt(bot.encrypted_token.encode()).decode()
                except BotSetUp.DoesNotExist:
                    logger.error(f"Bot {self.bot_id} not found or not active")
                    return None
                except Exception as e:
                    logger.error(f"Token decrypt error: {e}")
                    return None

            return await _get_token()
        except Exception as e:
            logger.error(f"Get bot token error: {e}")
            return None

    async def _initialize_handlers(self):
        """Barcha handler larni init qilish"""
        try:
            self.handlers['start'] = StartHandler(self.bot_id)
            self.handlers['menu'] = MenuHandlers(self.bot_id)
            self.handlers['channel'] = ChannelHandler(self.bot_id)
            logger.info(f"✅ Handlers initialized for bot {self.bot_id}")
        except Exception as e:
            logger.error(f"Initialize handlers error: {e}")

    async def _processing_loop(self):
        """Asosiy processing loop"""
        while self.running:
            try:
                # Update ni olish
                update = await redis_client.pop_update(self.bot_id)
                if update:
                    logger.info(f"Processing update for bot {self.bot_id}: {update.get('update_id')}")
                    await self._process_update(update)
                else:
                    await asyncio.sleep(0.1)  # CPU ni bo'shatish
            except Exception as e:
                logger.error(f"Processing loop error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_update(self, update: Dict[str, Any]):
        """Bitta update ni qayta ishlash"""
        try:
            # Message
            if "message" in update:
                await self._process_message(update["message"])
            # Callback query
            elif "callback_query" in update:
                await self._process_callback(update["callback_query"])
        except Exception as e:
            logger.error(f"Process update error: {e}", exc_info=True)

    async def _process_message(self, message: Dict[str, Any]):
        """Message update ni qayta ishlash"""
        try:
            text = message.get("text", "").strip()

            # /start command
            if text.startswith("/start"):
                if 'start' in self.handlers:
                    await self.handlers['start'].handle_start(message, self.bot)
                return

            # Menu commands - har xil formatlar
            menu_mappings = {
                # Konkursda qatnashish
                BUTTON_TEXTS['konkurs_qatnashish']: 'handle_konkurs_qatnashish',
                'Konkursda qatnashish': 'handle_konkurs_qatnashish',
                '🚀 Konkursda qatnashish': 'handle_konkurs_qatnashish',
                # Sovg'alar
                BUTTON_TEXTS['sovgalar']: 'handle_sovgalar',
                'Sovg\'alar': 'handle_sovgalar',
                '🎁 Sovg\'alar': 'handle_sovgalar',
                # Ballarim
                BUTTON_TEXTS['ballarim']: 'handle_ballarim',
                'Ballarim': 'handle_ballarim',
                '📊 Ballarim': 'handle_ballarim',
                # Reyting
                BUTTON_TEXTS['reyting']: 'handle_reyting',
                'Reyting': 'handle_reyting',
                '🏆 Reyting': 'handle_reyting',
                # Shartlar
                BUTTON_TEXTS['shartlar']: 'handle_shartlar',
                'Shartlar': 'handle_shartlar',
                '📜 Shartlar': 'handle_shartlar',
                '📜Shartlar': 'handle_shartlar',
            }

            handler_method = menu_mappings.get(text)
            if handler_method and 'menu' in self.handlers:
                method = getattr(self.handlers['menu'], handler_method, None)
                if method:
                    await method(message, self.bot)

        except Exception as e:
            logger.error(f"Process message error: {e}", exc_info=True)

    async def _process_callback(self, callback: Dict[str, Any]):
        """Callback query ni qayta ishlash"""
        try:
            data = callback.get("data", "")

            # Channel subscription check - FAQAT 2 ARGUMENT (callback, bot)
            if data == "check_subscription":
                if 'channel' in self.handlers:
                    await self.handlers['channel'].handle_check_subscription(callback, self.bot)

            # Generate invitation post
            elif data == "generate_invitation_post" or data == "taklif_posti":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_konkurs_qatnashish_callback(callback, self.bot)

            # Share post
            elif data == "share_post":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_share_post(callback, self.bot)

            # Refresh rating
            elif data == "refresh_rating":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_refresh_rating(callback, self.bot)

            # Copy link
            elif data == "copy_link":
                await self.bot.answer_callback_query(callback["id"], "Havolani nusxalash uchun unga uzoq bosing", show_alert=True)

            # Back to menu
            elif data == "back_to_menu":
                from bots.user_bots.base_template.keyboards.reply import get_main_menu_keyboard
                await self.bot.send_message(callback['from']['id'], "👇 Asosiy menyu:", reply_markup=get_main_menu_keyboard())

            # Answer callback query (agar javob berilmagan bo'lsa)
            try:
                await self.bot.answer_callback_query(callback["id"])
            except:
                pass

        except Exception as e:
            logger.error(f"Process callback error: {e}", exc_info=True)

    async def stop(self):
        """Worker ni to'xtatish"""
        self.running = False
        if self.bot:
            await self.bot.session.close()
        logger.info(f"✅ Bot worker stopped: {self.bot_id}")


class BotWorkerPool:
    """Worker pool manager"""

    def __init__(self):
        self.workers: Dict[int, list] = {}
        self.worker_configs: Dict[int, Dict] = {}

    async def start_worker(self, bot_id: int, worker_count: int = 1):
        """Bot uchun worker ishga tushirish"""
        if bot_id in self.workers:
            logger.info(f"Worker already running for bot {bot_id}")
            return

        workers = []
        for i in range(worker_count):
            worker = BotWorker(bot_id)
            workers.append(worker)
            await worker.start()

        self.workers[bot_id] = workers
        self.worker_configs[bot_id] = {'count': worker_count}
        logger.info(f"✅ Started {worker_count} workers for bot {bot_id}")

    async def stop_worker(self, bot_id: int):
        """Bot uchun worker to'xtatish"""
        if bot_id not in self.workers:
            logger.info(f"No workers running for bot {bot_id}")
            return

        for worker in self.workers[bot_id]:
            await worker.stop()

        del self.workers[bot_id]
        del self.worker_configs[bot_id]
        logger.info(f"✅ Stopped workers for bot {bot_id}")

    async def get_worker_status(self, bot_id: int) -> Dict[str, Any]:
        """Worker statusini olish"""
        if bot_id not in self.workers:
            return {'status': 'stopped', 'workers': 0}

        workers = self.workers[bot_id]
        running_count = sum(1 for w in workers if w.running)

        return {
            'status': 'running' if running_count > 0 else 'stopped',
            'workers': len(workers),
            'running': running_count,
            'bot_id': bot_id
        }

    async def get_all_status(self) -> Dict[int, Dict[str, Any]]:
        """Barcha worker statuslarini olish"""
        status = {}
        for bot_id in self.workers:
            status[bot_id] = await self.get_worker_status(bot_id)
        return status


# Global worker pool instance
worker_pool = BotWorkerPool()