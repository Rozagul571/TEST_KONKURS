import asyncio
import logging
import json
from typing import Dict, Any
from aiogram import Bot
from cryptography.fernet import Fernet
import os

from shared.redis_client import redis_client
from asgiref.sync import sync_to_async
from django_app.core.models import BotSetUp

logger = logging.getLogger(__name__)


class BotWorker:
    """Soddalashtirilgan bot worker"""

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.running = False
        self.bot_instance = None

    async def start(self):
        """Worker ni ishga tushirish"""
        self.running = True

        # Bot tokenini olish
        try:
            bot_setup = await sync_to_async(BotSetUp.objects.get)(id=self.bot_id)

            # Token decrypt
            fernet = Fernet(os.getenv("FERNET_KEY").encode())
            token = fernet.decrypt(bot_setup.encrypted_token.encode()).decode()

            # Bot yaratish
            self.bot_instance = Bot(token=token)

            # Test
            me = await self.bot_instance.get_me()
            logger.info(f"✅ Bot worker ready: @{me.username}")

            # Ish loop
            asyncio.create_task(self.process_loop())

        except Exception as e:
            logger.error(f"Start worker error: {e}")

    async def process_loop(self):
        """Asosiy processing loop"""
        while self.running:
            try:
                # Queue dan update olish
                if redis_client.is_connected():
                    update = redis_client.pop_update(self.bot_id)

                    if update:
                        await self.process_update(update)
                    else:
                        # Update bo'lmasa, biroz kutish
                        await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Process loop error: {e}")
                await asyncio.sleep(1)

    async def process_update(self, update: Dict[str, Any]):
        """Update ni qayta ishlash"""
        try:
            # Bot settings
            settings = redis_client.get_bot_settings(self.bot_id)
            if not settings:
                logger.warning(f"No settings for bot {self.bot_id}")
                return

            # Message borligini tekshirish
            if "message" in update and "text" in update["message"]:
                text = update["message"]["text"]
                user_id = update["message"]["from"]["id"]

                # /start handler
                if text.startswith("/start"):
                    await self.handle_start(update["message"], settings, user_id)

                # Menu handlerlar
                elif text == "🎁 Sovg'alar":
                    await self.handle_prizes(user_id, settings)
                elif text == "📊 Ballarim":
                    await self.handle_points(user_id, settings)
                elif text == "🏆 Reyting":
                    await self.handle_rating(user_id, settings)
                elif text == "📜 Shartlar":
                    await self.handle_rules(user_id, settings)

            # Callback query
            elif "callback_query" in update:
                callback = update["callback_query"]
                if callback.get("data") == "check_subscription":
                    await self.handle_check_subscription(callback, settings)

        except Exception as e:
            logger.error(f"Process update error: {e}")

    async def handle_start(self, message: Dict, settings: Dict, user_id: int):
        """/start handler"""
        try:
            welcome_text = (
                f"🎉 *Xush kelibsiz!*\n\n"
                f"🏆 *Konkurs:* {settings.get('name', '')}\n"
                f"📝 *Tavsif:* {settings.get('description', '')[:100]}...\n\n"
                f"✅ *Ro'yxatdan o'tdingiz!*\n\n"
                f"👇 Quyidagi menyu orqali ishtirok eting:"
            )

            # Menu keyboard
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🎁 Sovg'alar"), KeyboardButton(text="📊 Ballarim")],
                    [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="📜 Shartlar")]
                ],
                resize_keyboard=True
            )

            await self.bot_instance.send_message(
                chat_id=user_id,
                text=welcome_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

            logger.info(f"Start handled for user {user_id}")

        except Exception as e:
            logger.error(f"Handle start error: {e}")

    async def handle_prizes(self, user_id: int, settings: Dict):
        """Sovg'alar handler"""
        try:
            prizes_text = "🎁 *Sovg'alar:*\n\n"

            for prize in settings.get('prizes', [])[:5]:  # Faqat 5 ta
                prizes_text += f"{prize.get('place', '')}-o'rin: {prize.get('prize_name', '')}\n"

            # Referral link
            referral_link = f"https://t.me/{settings.get('bot_username', '')}?start=ref_{user_id}"
            prizes_text += f"\n🔗 *Referral linkingiz:* {referral_link}"

            await self.bot_instance.send_message(
                chat_id=user_id,
                text=prizes_text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle prizes error: {e}")

    async def handle_points(self, user_id: int, settings: Dict):
        """Ballar handler"""
        try:
            # Redis dan ballarni olish
            points_key = f"user_points:{self.bot_id}:{user_id}"
            points = 0

            if redis_client.is_connected():
                points_data = redis_client.client.get(points_key)
                points = int(points_data) if points_data else 0

            points_text = (
                f"📊 *Ballaringiz:* {points} ball\n\n"
                f"🏆 *Reytingda:* ...\n"
                f"⭐ *Status:* Oddiy foydalanuvchi"
            )

            await self.bot_instance.send_message(
                chat_id=user_id,
                text=points_text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle points error: {e}")

    async def handle_rating(self, user_id: int, settings: Dict):
        """Reyting handler"""
        try:
            rating_text = "🏆 *TOP 10:*\n\n"

            # Bu yerda database dan reyting olish kerak
            # Hozircha demo
            for i in range(1, 6):
                rating_text += f"{i}. User{i} - {100 - i * 10} ball\n"

            rating_text += f"\n🎯 *Siz:* 15-o'rin - 35 ball"

            await self.bot_instance.send_message(
                chat_id=user_id,
                text=rating_text,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle rating error: {e}")

    async def handle_rules(self, user_id: int, settings: Dict):
        """Qoidalar handler"""
        try:
            rules_text = settings.get('rules_text', 'Qoidalar admin tomonidan belgilangan.')

            await self.bot_instance.send_message(
                chat_id=user_id,
                text=f"📜 *Konkurs qoidalari:*\n\n{rules_text}",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Handle rules error: {e}")

    async def handle_check_subscription(self, callback: Dict, settings: Dict):
        """Check subscription handler"""
        try:
            user_id = callback["from"]["id"]

            # Channel check
            all_joined = True
            for channel in settings.get('channels', []):
                # Bu yerda haqiqiy tekshirish bo'lishi kerak
                pass

            if all_joined:
                response = "✅ Barcha kanallarga obuna bo'ldingiz!"
            else:
                response = "❌ Hali barcha kanallarga obuna bo'lmadingiz!"

            await self.bot_instance.send_message(
                chat_id=user_id,
                text=response
            )

        except Exception as e:
            logger.error(f"Handle check subscription error: {e}")


class BotWorkerPool:
    """Worker pool"""

    def __init__(self):
        self.workers = {}

    async def start_worker(self, bot_id: int, worker_count: int = 1):
        """Worker boshlash"""
        if bot_id not in self.workers:
            self.workers[bot_id] = []

        for i in range(worker_count):
            worker = BotWorker(bot_id)
            self.workers[bot_id].append(worker)
            await worker.start()
            logger.info(f"Worker {i + 1} started for bot {bot_id}")

    async def stop_worker(self, bot_id: int):
        """Worker to'xtatish"""
        if bot_id in self.workers:
            for worker in self.workers[bot_id]:
                worker.running = False
            del self.workers[bot_id]
            logger.info(f"Workers stopped for bot {bot_id}")


# Global worker pool
worker_pool = BotWorkerPool()