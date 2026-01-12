# fastapi_app/scheduler/competition_scheduler.py
"""
Competition Scheduler - Konkurs tugash vaqtini tekshirish
Konkurs tugashi bilan bot avtomatik to'xtatiladi
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Set
import os

logger = logging.getLogger(__name__)


class CompetitionScheduler:
    """Konkurs tugash vaqtini kuzatuvchi scheduler"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.running = False
        self.check_interval = 60  # Har 60 sekundda tekshirish
        self._task = None
        self._stopped_bots: Set[int] = set()  # Allaqachon to'xtatilgan botlar

    async def start(self):
        """Scheduler ni ishga tushirish"""
        if self.running:
            return

        self.running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("✅ Competition scheduler started")

    async def stop(self):
        """Scheduler ni to'xtatish"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Competition scheduler stopped")

    async def _check_loop(self):
        """Asosiy tekshirish sikli"""
        while self.running:
            try:
                await self._check_competitions()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler check error: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

    async def _check_competitions(self):
        """Barcha aktiv konkurslarni tekshirish"""
        try:
            from asgiref.sync import sync_to_async

            @sync_to_async
            def get_expired_competitions():
                from django_app.core.models import Competition
                from django.utils import timezone as dj_timezone

                now = dj_timezone.now()

                # Tugagan lekin hali aktiv bo'lgan konkurslar
                expired = Competition.objects.filter(
                    status='active',
                    end_date__lte=now
                ).select_related('bot')

                return list(expired)

            expired_competitions = await get_expired_competitions()

            for competition in expired_competitions:
                bot_id = competition.bot_id

                # Allaqachon to'xtatilganmi tekshirish
                if bot_id in self._stopped_bots:
                    continue

                logger.info(f"🏁 Competition {competition.id} ended, stopping bot {bot_id}")

                # Botni to'xtatish
                await self._stop_bot(bot_id, competition)

                # Competition statusini yangilash
                await self._update_competition_status(competition.id)

                self._stopped_bots.add(bot_id)

        except Exception as e:
            logger.error(f"Check competitions error: {e}", exc_info=True)

    async def _stop_bot(self, bot_id: int, competition):
        """Botni to'xtatish"""
        try:
            import httpx

            fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8001")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{fastapi_url}/api/bots/stop/{bot_id}",
                    timeout=30
                )

                if response.status_code == 200:
                    logger.info(f"✅ Bot {bot_id} stopped successfully")
                else:
                    logger.warning(f"Bot stop response: {response.status_code}")

        except Exception as e:
            logger.error(f"Stop bot error: {e}")

    async def _update_competition_status(self, competition_id: int):
        """Competition statusini 'finished' ga o'zgartirish"""
        try:
            from asgiref.sync import sync_to_async

            @sync_to_async
            def update_status():
                from django_app.core.models import Competition

                Competition.objects.filter(id=competition_id).update(status='finished')

            await update_status()
            logger.info(f"Competition {competition_id} status updated to 'finished'")

        except Exception as e:
            logger.error(f"Update competition status error: {e}")

    async def _notify_owner(self, bot_id: int, competition):
        """Bot egasiga xabar yuborish"""
        try:
            from aiogram import Bot
            from cryptography.fernet import Fernet
            from asgiref.sync import sync_to_async

            @sync_to_async
            def get_owner_id():
                from django_app.core.models import BotSetUp
                bot = BotSetUp.objects.select_related('owner').get(id=bot_id)
                return bot.owner.telegram_id if bot.owner else None

            owner_id = await get_owner_id()
            if not owner_id:
                return

            # Main bot orqali xabar yuborish
            main_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not main_bot_token:
                return

            bot = Bot(token=main_bot_token)

            text = f"🏁 *Konkurs tugadi!*\n\n"
            text += f"📌 Konkurs: {competition.name}\n"
            text += f"⏰ Tugash vaqti: {competition.end_date.strftime('%Y-%m-%d %H:%M')}\n\n"
            text += "Bot avtomatik to'xtatildi.\n"
            text += "G'oliblarni e'lon qilishni unutmang!"

            await bot.send_message(owner_id, text, parse_mode="Markdown")
            await bot.session.close()

            logger.info(f"Owner {owner_id} notified about competition end")

        except Exception as e:
            logger.error(f"Notify owner error: {e}")


# Global instance
competition_scheduler = CompetitionScheduler()