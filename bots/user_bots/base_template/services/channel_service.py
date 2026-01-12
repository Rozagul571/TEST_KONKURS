import logging
import asyncio
from typing import Dict, Any, List
from aiogram import Bot

logger = logging.getLogger(__name__)


class ChannelService:

    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.channels = settings.get("channels", [])

    async def check_user_channels(self, user_id: int, bot: Bot) -> Dict[str, Any]:
        """
        Foydalanuvchi BARCHA kanallarga obunami tekshirish

        MUHIM: Faqat HAMMA kanalga qo'shilgan bo'lsa True qaytaradi
        """
        if not self.channels:
            return {"all_joined": True, "not_joined": [], "joined_count": 0, "total": 0}

        tasks = [self._check_single(ch, user_id, bot) for ch in self.channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        not_joined = []
        joined_count = 0
        joined_channels = []

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Check exception: {result}")
                continue

            if result.get("status") == "joined":
                joined_count += 1
                joined_channels.append(result.get("channel", {}))
            elif result.get("status") == "not_joined":
                not_joined.append(result.get("channel", {}))
            elif result.get("status") == "error":
                error_type = result.get("error_type", "")
                if error_type == "inaccessible":
                    joined_count += 1
                    joined_channels.append(result.get("channel", {}))
                else:
                    not_joined.append(result.get("channel", {}))

        total = len(self.channels)

        all_joined = (len(not_joined) == 0) and (joined_count >= total)

        return {
            "all_joined": all_joined,
            "not_joined": not_joined,
            "joined_count": joined_count,
            "joined_channels": joined_channels,
            "total": total
        }

    async def _check_single(self, channel: Dict, user_id: int, bot: Bot) -> Dict:
        """
        Bitta kanalni tekshirish

        Qo'llab-quvvatlanadi:
        - Public kanallar (@username)
        - Private kanallar (invite link yoki ID orqali)
        - Guruhlar
        """
        try:
            # Username yoki ID ni olish
            raw_username = channel.get("channel_username", "")
            channel_id = channel.get("channel_id")  # Private kanallar uchun ID

            # Chat ID ni aniqlash
            if channel_id:
                # Private kanal - ID orqali
                chat_id = channel_id
            elif raw_username:
                # Public kanal - username orqali
                username = str(raw_username).replace("@", "").replace("https://t.me/", "").replace("http://t.me/",
                                                                                                   "").strip()
                if not username:
                    logger.warning(f"Empty channel username: {channel}")
                    return {"channel": channel, "status": "error", "error_type": "empty_username"}
                chat_id = f"@{username}"
            else:
                logger.warning(f"No username or ID for channel: {channel}")
                return {"channel": channel, "status": "error", "error_type": "no_identifier"}

            try:
                member = await bot.get_chat_member(chat_id, user_id)
            except Exception as e:
                error_msg = str(e).lower()

                # Bot member list ga kira olmaydi (admin emas)
                # Bu holda user qo'shilgan deb hisoblaymiz
                if "member list is inaccessible" in error_msg:
                    logger.info(f"Member list inaccessible for {chat_id}, assuming joined")
                    return {"channel": channel, "status": "joined", "error_type": "inaccessible"}

                # User topilmadi - qo'shilmagan
                if "user not found" in error_msg:
                    return {"channel": channel, "status": "not_joined"}

                # Chat topilmadi - noto'g'ri username/ID
                if "chat not found" in error_msg:
                    logger.warning(f"Chat not found: {chat_id}")
                    # Chat topilmasa ham joined deb hisoblaymiz (admin xatosi)
                    return {"channel": channel, "status": "joined", "error_type": "chat_not_found"}

                # Boshqa xatolar
                logger.warning(f"Channel check error {chat_id}: {e}")
                return {"channel": channel, "status": "error", "error_type": "unknown", "error": str(e)}

            # Member status tekshirish
            if member.status in ["member", "administrator", "creator"]:
                return {"channel": channel, "status": "joined"}
            elif member.status == "restricted":
                # Restricted - is_member ni tekshirish
                is_member = getattr(member, "is_member", True)
                return {"channel": channel, "status": "joined" if is_member else "not_joined"}
            else:  # left, kicked
                return {"channel": channel, "status": "not_joined"}

        except Exception as e:
            logger.error(f"Channel check critical error: {e}", exc_info=True)
            return {"channel": channel, "status": "error", "error_type": "critical"}