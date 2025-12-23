#fastapi_app/workers/bot_worker.py
"""
High-performance bot worker with async processing - TO'G'RILANGAN
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from aiogram import Bot
from cryptography.fernet import Fernet
import os

from bots.user_bots.base_template.handlers.menu_handler import MenuHandlers
from shared.redis_client import redis_client
from asgiref.sync import sync_to_async
from django_app.core.models import BotSetUp

logger = logging.getLogger(__name__)


class BotWorker:
    """High-performance bot worker with async processing"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.running = False
        self.bot = None
        self.token = None
        self.handlers = {}

    async def start(self):
        """Start worker"""
        try:
            self.running = True

            # Get bot token
            self.token = await self._get_bot_token()
            if not self.token:
                logger.error(f"❌ Failed to get token for bot {self.bot_id}")
                self.running = False
                return

            # Initialize bot
            self.bot = Bot(token=self.token)

            # Test connection
            me = await self.bot.get_me()
            logger.info(f"✅ Bot worker started: @{me.username} (ID: {self.bot_id})")

            # Initialize handlers
            await self._initialize_handlers()

            # Start processing loop
            asyncio.create_task(self._processing_loop())

        except Exception as e:
            logger.error(f"❌ Start worker error: {e}", exc_info=True)
            self.running = False

    async def _get_bot_token(self) -> Optional[str]:
        """Get bot token from database"""
        try:
            @sync_to_async
            def _get_token():
                try:
                    bot = BotSetUp.objects.get(id=self.bot_id, is_active=True)

                    # Decrypt token
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
        """Initialize all handlers"""
        try:
            from bots.user_bots.base_template.handlers.start_handler import StartHandler
            from bots.user_bots.base_template.handlers.channel_handler import ChannelHandler

            self.handlers['start'] = StartHandler(self.bot_id)
            self.handlers['menu'] = MenuHandlers(self.bot_id)
            self.handlers['channel'] = ChannelHandler(self.bot_id)

            logger.info(f"✅ Handlers initialized for bot {self.bot_id}")
        except Exception as e:
            logger.error(f"Initialize handlers error: {e}")

    async def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Get update from queue
                update = await redis_client.pop_update(self.bot_id)

                if update:
                    await self._process_update(update)
                else:
                    # No updates, sleep a bit
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(1)

    async def _process_update(self, update: Dict[str, Any]):
        """Process single update"""
        try:
            # Get bot settings from cache
            from bots.user_bots.base_template.services.competition_service import CompetitionService
            comp_service = CompetitionService()
            settings = await comp_service.get_competition_settings(self.bot_id)

            if not settings:
                logger.warning(f"No settings for bot {self.bot_id}")
                return

            # Process based on update type
            if "message" in update:
                await self._process_message(update["message"], settings)
            elif "callback_query" in update:
                await self._process_callback(update["callback_query"], settings)

        except Exception as e:
            logger.error(f"Process update error: {e}", exc_info=True)

    async def _process_message(self, message: Dict[str, Any], settings: Dict[str, Any]):
        """Process message update"""
        try:
            text = message.get("text", "").strip()
            user_id = message["from"]["id"]

            # /start command
            if text.startswith("/start"):
                if 'start' in self.handlers:
                    await self.handlers['start'].handle_start(message, self.bot)
                return

            # Menu commands
            if text == "🚀 Konkursda qatnashish":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_konkurs_qatnashish(message, self.bot)
            elif text == "🎁 Sovg'alar":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_sovgalar(message, self.bot)
            elif text == "📊 Ballarim":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_ballarim(message, self.bot)
            elif text == "🏆 Reyting":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_reyting(message, self.bot)
            elif text == "📜 Shartlar":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_shartlar(message, self.bot)

        except Exception as e:
            logger.error(f"Process message error: {e}")

    async def _process_callback(self, callback: Dict[str, Any], settings: Dict[str, Any]):
        """Process callback query"""
        try:
            data = callback.get("data", "")
            user_id = callback["from"]["id"]

            # Channel subscription check
            if data == "check_subscription":
                if 'channel' in self.handlers:
                    await self.handlers['channel'].handle_check_subscription(callback, settings, self.bot)

            # Generate invitation post
            elif data == "generate_invitation_post":
                if 'menu' in self.handlers:
                    await self.handlers['menu'].handle_generate_invitation_post(callback, self.bot)

            # Answer callback query
            await self.bot.answer_callback_query(callback["id"])

        except Exception as e:
            logger.error(f"Process callback error: {e}")

    async def stop(self):
        """Stop worker"""
        self.running = False

        # Close bot session
        if self.bot:
            await self.bot.session.close()

        logger.info(f"✅ Bot worker stopped: {self.bot_id}")


class BotWorkerPool:
    """Worker pool manager"""

    def __init__(self):
        self.workers = {}
        self.worker_configs = {}

    async def start_worker(self, bot_id: int, worker_count: int = 1):
        """Start worker for bot"""
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
        """Stop worker for bot"""
        if bot_id not in self.workers:
            logger.info(f"No workers running for bot {bot_id}")
            return

        for worker in self.workers[bot_id]:
            await worker.stop()

        del self.workers[bot_id]
        del self.worker_configs[bot_id]

        logger.info(f"✅ Stopped workers for bot {bot_id}")

    async def get_worker_status(self, bot_id: int) -> Dict[str, Any]:
        """Get worker status"""
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
        """Get status of all workers"""
        status = {}
        for bot_id in self.workers:
            status[bot_id] = await self.get_worker_status(bot_id)

        return status


# Global worker pool instance
worker_pool = BotWorkerPool()