# bots/user_bots/base_template/bot_processor.py
"""
Bot Processor - TO'LIQ TO'G'IRLANGAN
- Chat not found xatosi hal qilindi
- Konkursda qatnashish tugmasi ishlaydi
- Reyting username bilan ko'rsatiladi
"""
import os
import logging
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from cryptography.fernet import Fernet
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class BotProcessor:
    """B Bot update processor"""

    # Referral code cache (Redis yo'q bo'lganda)
    _referral_cache: Dict[str, str] = {}

    def __init__(self, bot_id: int):
        self.bot_id = bot_id
        self.bot: Optional[Bot] = None
        self.settings: Optional[Dict] = None

    async def process_update(self, update: Dict[str, Any]):
        """Asosiy update processor"""
        try:
            # Bot init
            await self._init_bot()
            if not self.bot:
                logger.error(f"Bot {self.bot_id} init failed")
                return

            # Settings olish
            await self._load_settings()

            # Update turini aniqlash
            if "message" in update:
                await self._process_message(update["message"])
            elif "callback_query" in update:
                await self._process_callback(update["callback_query"])

        except Exception as e:
            logger.error(f"Process update error: {e}", exc_info=True)
        finally:
            if self.bot:
                await self.bot.session.close()

    async def _init_bot(self):
        """Bot ni init qilish"""
        try:
            token = await self._get_token()
            if token:
                self.bot = Bot(token=token)
        except Exception as e:
            logger.error(f"Bot init error: {e}")

    async def _get_token(self) -> Optional[str]:
        """Token olish"""

        @sync_to_async
        def _get():
            try:
                from django_app.core.models import BotSetUp
                bot = BotSetUp.objects.get(id=self.bot_id, is_active=True)
                fernet = Fernet(os.getenv("FERNET_KEY").encode())
                return fernet.decrypt(bot.encrypted_token.encode()).decode()
            except Exception as e:
                logger.error(f"Get token error: {e}")
                return None

        return await _get()

    async def _load_settings(self):
        """Settings yuklash"""
        try:
            from bots.user_bots.base_template.services.competition_service import CompetitionService
            service = CompetitionService()
            self.settings = await service.get_competition_settings(self.bot_id)
            if not self.settings:
                logger.warning(f"Settings not found for bot {self.bot_id}")
        except Exception as e:
            logger.error(f"Load settings error: {e}")

    async def _process_message(self, message: Dict[str, Any]):
        """Message process"""
        text = message.get("text", "").strip()
        user_id = message["from"]["id"]

        logger.info(f"Processing message from {user_id}: {text[:50]}")

        # /start command
        if text.startswith("/start"):
            await self._handle_start(message)
            return

        # Menu tugmalari - barcha variantlar
        text_lower = text.lower()

        if "konkurs" in text_lower or "qatnash" in text_lower:
            await self._handle_konkurs(message)
        elif "sovg'a" in text_lower or "sovrin" in text_lower:
            await self._handle_prizes(message)
        elif "ball" in text_lower:
            await self._handle_points(message)
        elif "reyting" in text_lower or "top" in text_lower:
            await self._handle_rating(message)
        elif "shart" in text_lower or "qoida" in text_lower:
            await self._handle_rules(message)

    async def _process_callback(self, callback: Dict[str, Any]):
        """Callback process"""
        data = callback.get("data", "")

        if data == "check_subscription":
            await self._handle_check_subscription(callback)

        # Answer callback
        try:
            await self.bot.answer_callback_query(callback["id"])
        except:
            pass

    async def _handle_start(self, message: Dict[str, Any]):
        """/start handler"""
        user_id = message["from"]["id"]
        text = message.get("text", "")

        try:
            if not self.settings:
                await self.bot.send_message(user_id, "❌ Bot sozlamalari topilmadi.")
                return

            # Referral kodni olish
            referral_code = None
            if "ref_" in text:
                parts = text.split()
                for p in parts:
                    if p.startswith("ref_"):
                        referral_code = p.replace("ref_", "")
                        break

            # Referral kodni saqlash
            if referral_code:
                await self._save_referral_code(user_id, referral_code)

            # Allaqachon ro'yxatdan o'tganmi tekshirish
            participant = await self._get_participant(user_id)
            if participant:
                await self._send_menu(user_id, "👋 Xush kelibsiz! Siz allaqachon konkursda qatnashyapsiz.")
                return

            # Kanallar ro'yxati
            channels = self.settings.get("channels", [])

            if not channels:
                await self._register_user(message)
                return

            # Kanallarni tekshirish
            from bots.user_bots.base_template.services.channel_service import ChannelService
            channel_service = ChannelService(self.settings)
            result = await channel_service.check_user_channels(user_id, self.bot)

            if result["all_joined"]:
                await self._register_user(message)
            else:
                await self._show_channels(user_id, channels)

        except Exception as e:
            logger.error(f"Start handler error: {e}", exc_info=True)
            try:
                await self.bot.send_message(user_id, "❌ Xatolik yuz berdi. Qaytadan /start bosing.")
            except:
                pass

    async def _show_channels(self, user_id: int, channels: list):
        """Kanallarni ko'rsatish"""
        competition_name = self.settings.get("name", "Konkurs")
        description = self.settings.get("description", "")

        msg_text = f"⚡ <b>{competition_name}</b>"
        if description:
            msg_text += f"\n\n{description}"
        msg_text += "\n\nKeyin \"✅ A'zo bo'ldim\" tugmasini bosing:"

        buttons = []

        for ch in channels:
            raw_username = ch.get("channel_username", "")
            name = ch.get("channel_name", "") or raw_username

            if not raw_username:
                continue

            # Username ni to'g'ri tozalash
            clean_name = str(raw_username).replace("@", "").replace("https://t.me/", "").replace("http://t.me/",
                                                                                                 "").strip()

            if not clean_name:
                continue

            url = f"https://t.me/{clean_name}"
            buttons.append([InlineKeyboardButton(text=name, url=url)])

        buttons.append([InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_subscription")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        try:
            await self.bot.send_message(user_id, msg_text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Show channels error: {e}")
            await self.bot.send_message(user_id, "Iltimos, kanallarga qo'shiling va qaytadan /start bosing.")

    async def _handle_check_subscription(self, callback: Dict[str, Any]):
        """A'zo bo'ldim tugmasi bosilganda"""
        user_id = callback["from"]["id"]
        message_id = callback["message"]["message_id"]

        try:
            if not self.settings:
                await self.bot.answer_callback_query(callback["id"], "❌ Bot sozlamalari topilmadi!", show_alert=True)
                return

            from bots.user_bots.base_template.services.channel_service import ChannelService
            channel_service = ChannelService(self.settings)
            result = await channel_service.check_user_channels(user_id, self.bot)

            if result["all_joined"]:
                message = {"from": callback["from"], "chat": callback["message"]["chat"]}
                await self._register_user(message)

                try:
                    await self.bot.delete_message(user_id, message_id)
                except:
                    pass
            else:
                not_joined_count = len(result["not_joined"])
                await self.bot.answer_callback_query(callback["id"],
                                                     f"⚠️ Hali {not_joined_count} ta kanalga obuna bo'lmagansiz!",
                                                     show_alert=True)

        except Exception as e:
            logger.error(f"Check subscription error: {e}", exc_info=True)
            await self.bot.answer_callback_query(callback["id"], "❌ Xatolik!", show_alert=True)

    async def _register_user(self, message: Dict[str, Any]):
        """Foydalanuvchini RO'YXATDAN O'TKAZISH"""
        user_id = message["from"]["id"]

        try:
            from bots.user_bots.base_template.services.registration_service import RegistrationService

            reg_service = RegistrationService(self.bot_id)

            user_data = {
                "telegram_id": user_id,
                "username": message["from"].get("username", ""),
                "first_name": message["from"].get("first_name", ""),
                "last_name": message["from"].get("last_name", ""),
                "is_premium": message["from"].get("is_premium", False)
            }

            referral_code = await self._get_referral_code(user_id)

            result = await reg_service.register_user(
                user_data=user_data,
                referral_code=referral_code,
                settings=self.settings
            )

            if result["success"]:
                participant = result["participant"]

                if result.get("already_registered"):
                    await self._send_menu(user_id, "👋 Siz allaqachon konkursda qatnashyapsiz!")
                else:
                    await self._send_welcome(user_id, participant, result)
            else:
                await self.bot.send_message(user_id, "❌ Ro'yxatdan o'tishda xatolik.")

        except Exception as e:
            logger.error(f"Register user error: {e}", exc_info=True)
            await self.bot.send_message(user_id, "❌ Xatolik yuz berdi.")

    async def _send_welcome(self, user_id: int, participant, result: Dict):
        """Welcome xabar va menu"""
        channel_points = result.get("channel_points", 0)
        referral_bonus = result.get("referral_bonus", 0)
        total_points = participant.current_points

        text = "🎉 *Tabriklaymiz!* Siz konkursda muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
        text += f"📊 *Sizning ballaringiz:*\n"
        text += f"• Kanallar uchun: +{channel_points} ball\n"
        if referral_bonus > 0:
            text += f"• Taklif bonusi: +{referral_bonus} ball\n"
        text += f"\n💰 *Jami:* {total_points} ball\n\n"
        text += "👇 Quyidagi tugmalar orqali konkursda ishtirok eting:"

        keyboard = self._get_main_menu_keyboard()
        await self.bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="Markdown")

    async def _send_menu(self, user_id: int, text: str = "👇 Asosiy menyu:"):
        """Menu ko'rsatish"""
        keyboard = self._get_main_menu_keyboard()
        await self.bot.send_message(user_id, text, reply_markup=keyboard)

    def _get_main_menu_keyboard(self) -> ReplyKeyboardMarkup:
        """Asosiy menu keyboard"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🚀 Konkursda qatnashish")],
                [KeyboardButton(text="🎁 Sovg'alar"), KeyboardButton(text="📊 Ballarim")],
                [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="📜 Shartlar")]
            ],
            resize_keyboard=True
        )

    async def _save_referral_code(self, user_id: int, code: str):
        """Referral kodni saqlash"""
        try:
            from shared.redis_client import redis_client
            if redis_client.is_connected():
                await redis_client.set_user_state(self.bot_id, user_id, {"referral_code": code}, 3600)
            else:
                BotProcessor._referral_cache[f"{self.bot_id}:{user_id}"] = code
        except Exception as e:
            logger.error(f"Save referral code error: {e}")
            BotProcessor._referral_cache[f"{self.bot_id}:{user_id}"] = code

    async def _get_referral_code(self, user_id: int) -> Optional[str]:
        """Referral kodni olish"""
        try:
            from shared.redis_client import redis_client
            if redis_client.is_connected():
                state = await redis_client.get_user_state(self.bot_id, user_id)
                if state:
                    return state.get("referral_code")
            return BotProcessor._referral_cache.get(f"{self.bot_id}:{user_id}")
        except:
            return BotProcessor._referral_cache.get(f"{self.bot_id}:{user_id}")

    async def _get_participant(self, user_id: int):
        """Participant olish"""

        @sync_to_async
        def _get():
            try:
                from django_app.core.models import Participant
                return Participant.objects.select_related('user').get(
                    user__telegram_id=user_id,
                    competition__bot_id=self.bot_id,
                    is_participant=True
                )
            except:
                return None

        return await _get()

    # ============ MENU HANDLERS ============

    async def _handle_konkurs(self, message: Dict[str, Any]):
        """
        🚀 Konkursda qatnashish - Referral post

        POST FORMATI:
        - Admin paneldan description
        - Referral link
        - Share button (to'liq post bilan)
        """
        user_id = message["from"]["id"]

        try:
            participant = await self._get_participant(user_id)
            if not participant:
                await self.bot.send_message(user_id, "❌ Avval /start ni bosing va kanallarga qo'shiling!")
                return

            # Bot username ni olish
            bot_username = self.settings.get("bot_username", "")
            if not bot_username:
                me = await self.bot.get_me()
                bot_username = me.username

            referral_link = f"https://t.me/{bot_username}?start=ref_{participant.referral_code}"

            # Admin paneldan description olish
            description = self.settings.get("description", "")

            # POST YARATISH - Description + Link (HTML format)
            if description:
                text = f"{description}\n\n"
            else:
                text = "🎁 Konkursda ishtirok eting va sovg'alar yutib oling!\n\n"

            text += f"📎 Havola:\n{referral_link}\n\n"
            text += "👆 Havolani bosib nusxa oling va do'stlaringizga yuboring!"

            # Share uchun TO'LIQ POST (URL encode)
            import urllib.parse

            share_text = ""
            if description:
                share_text = f"{description}\n\n"
            else:
                share_text = "🎁 Konkursda ishtirok eting va sovg'alar yutib oling!\n\n"
            share_text += f"📎 Havola:\n{referral_link}"

            # URL encode - maxsus belgilarni to'g'ri encode qilish
            encoded_text = urllib.parse.quote(share_text, safe='')
            share_url = f"https://t.me/share/url?url={urllib.parse.quote(referral_link, safe='')}&text={encoded_text}"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📤 Do'stlarga ulashish", url=share_url)]
            ])

            # HTML parse_mode ishlatamiz (Markdown muammolardan qochish uchun)
            await self.bot.send_message(user_id, text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Handle konkurs error: {e}", exc_info=True)
            await self.bot.send_message(user_id, "❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.")

    async def _handle_prizes(self, message: Dict[str, Any]):
        """
        🎁 Sovg'alar

        Type bo'yicha:
        - text → description dan oladi
        - number → prize_amount dan oladi
        """
        user_id = message["from"]["id"]

        try:
            prizes = self.settings.get("prizes", [])

            if not prizes:
                await self.bot.send_message(user_id, "🎁 Sovg'alar hozircha belgilanmagan.")
                return

            text = "🎁 *KONKURS SOVG'ALARI* 🎁\n\n"

            emojis = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"}

            for prize in prizes:
                place = prize.get("place", 0)
                emoji = emojis.get(place, f"{place}.")
                prize_name = prize.get("prize_name", "")
                prize_type = prize.get("type", "number")  # text yoki number
                description = prize.get("description", "")
                amount = prize.get("prize_amount")

                # TYPE BO'YICHA FORMATLASH
                if prize_type == "text":
                    # Text type - description dan oladi
                    if description:
                        text += f"{emoji} *{place}-o'rin:* {description}\n\n"
                    elif prize_name:
                        text += f"{emoji} *{place}-o'rin:* {prize_name}\n\n"
                    else:
                        text += f"{emoji} *{place}-o'rin:* Sovg'a\n\n"
                else:
                    # Number type - amount dan oladi
                    if amount:
                        if prize_name:
                            text += f"{emoji} *{place}-o'rin:* {prize_name} - {int(amount):,} so'm\n\n"
                        else:
                            text += f"{emoji} *{place}-o'rin:* {int(amount):,} so'm\n\n"
                    elif prize_name:
                        text += f"{emoji} *{place}-o'rin:* {prize_name}\n\n"
                    else:
                        text += f"{emoji} *{place}-o'rin:* Sovg'a\n\n"

            text += "🚀 G'olib bo'lish uchun do'stlaringizni taklif qiling!"

            await self.bot.send_message(user_id, text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Handle prizes error: {e}")
            await self.bot.send_message(user_id, "❌ Xatolik yuz berdi.")

    async def _handle_points(self, message: Dict[str, Any]):
        """📊 Ballarim"""
        user_id = message["from"]["id"]

        try:
            participant = await self._get_participant(user_id)
            if not participant:
                await self.bot.send_message(user_id, "❌ Avval /start ni bosing!")
                return

            stats = await self._get_user_stats(participant)

            text = f"📊 *Sizning ballaringiz*\n\n"
            text += f"💰 *Jami:* {participant.current_points:,} ball\n\n"

            if stats:
                text += "📈 *Tafsilot:*\n"
                if stats.get('channel_points', 0) > 0:
                    text += f"• Kanallar: {stats['channel_points']} ball\n"
                if stats.get('referral_points', 0) > 0:
                    text += f"• Taklif qilganlar: {stats['referral_points']} ball\n"
                if stats.get('referral_count', 0) > 0:
                    text += f"\n👥 *Taklif qilganlar soni:* {stats['referral_count']} ta\n"

            text += "\n🚀 Ko'proq ball yig'ish uchun do'stlaringizni taklif qiling!"

            await self.bot.send_message(user_id, text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Handle points error: {e}")
            await self.bot.send_message(user_id, "❌ Xatolik yuz berdi.")

    async def _handle_rating(self, message: Dict[str, Any]):
        """🏆 Reyting - USERNAME VA PROFIL LINK BILAN"""
        user_id = message["from"]["id"]

        try:
            from bots.user_bots.base_template.services.rating_service import RatingService
            rating_service = RatingService(self.bot_id)
            text = await rating_service.get_rating_text(user_id)

            await self.bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Handle rating error: {e}", exc_info=True)
            await self.bot.send_message(user_id, "❌ Xatolik yuz berdi.")

    async def _handle_rules(self, message: Dict[str, Any]):
        """📜 Shartlar"""
        user_id = message["from"]["id"]

        try:
            rules = self.settings.get("rules_text", "")
            if not rules:
                rules = "Konkurs qoidalari hali belgilanmagan."

            text = f"📜 *KONKURS QOIDALARI*\n\n{rules}"
            await self.bot.send_message(user_id, text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Handle rules error: {e}")
            await self.bot.send_message(user_id, "❌ Xatolik yuz berdi.")

    async def _get_user_stats(self, participant) -> Dict:
        """User statistikasini olish"""

        @sync_to_async
        def _get():
            try:
                from django_app.core.models import Point, Referral
                from django_app.core.models.pointrule import PointAction
                from django.db.models import Sum

                points = Point.objects.filter(participant=participant)

                channel_points = points.filter(reason=PointAction.CHANNEL_JOIN).aggregate(total=Sum('earned_points'))[
                                     'total'] or 0
                referral_points = points.filter(reason=PointAction.REFERRAL).aggregate(total=Sum('earned_points'))[
                                      'total'] or 0

                referral_count = Referral.objects.filter(referrer=participant.user,
                                                         competition=participant.competition).count()

                return {
                    'channel_points': channel_points,
                    'referral_points': referral_points,
                    'referral_count': referral_count
                }
            except Exception as e:
                logger.error(f"Get user stats error: {e}")
                return {}

        return await _get()