# bots/user_bots/base_template/services/channel_service.py
"""
Channel Service - Foydalanuvchi kanallarni tekshirish
NoneType xatosi to'g'irlangan
"""
import logging
import asyncio
from typing import Dict, Any, List
from aiogram import Bot

logger = logging.getLogger(__name__)


class ChannelService:
    """Kanal tekshirish service"""

    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.channels = settings.get("channels", [])

    async def check_user_channels(self, user_id: int, bot: Bot) -> Dict[str, Any]:
        """Foydalanuvchi barcha kanallarga obunami tekshirish"""
        if not self.channels:
            return {"all_joined": True, "not_joined": [], "joined_count": 0, "total": 0}

        tasks = [self._check_single(ch, user_id, bot) for ch in self.channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        not_joined = []
        joined_count = 0

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Check exception: {result}")
                continue

            if result.get("status") == "joined":
                joined_count += 1
            else:
                not_joined.append(result.get("channel", {}))

        total = len(self.channels)
        all_joined = (joined_count == total) and (len(not_joined) == 0)

        return {
            "all_joined": all_joined,
            "not_joined": not_joined,
            "joined_count": joined_count,
            "total": total
        }

    async def _check_single(self, channel: Dict, user_id: int, bot: Bot) -> Dict:
        """Bitta kanalni tekshirish"""
        try:
            # Username ni xavfsiz olish
            raw_username = channel.get("channel_username")
            if not raw_username:
                logger.warning(f"Empty channel username: {channel}")
                return {"channel": channel, "status": "error"}

            # Tozalash
            username = str(raw_username).replace("@", "").replace("https://t.me/", "").strip()
            if not username:
                return {"channel": channel, "status": "error"}

            chat_id = f"@{username}"

            try:
                member = await bot.get_chat_member(chat_id, user_id)
            except Exception as e:
                error_msg = str(e).lower()

                # Bot admin emas - user obuna deb hisoblaymiz
                if "member list is inaccessible" in error_msg:
                    logger.info(f"Member list inaccessible for {chat_id}, assuming joined")
                    return {"channel": channel, "status": "joined", "username": username}

                # User topilmadi
                if "user not found" in error_msg:
                    return {"channel": channel, "status": "not_joined", "username": username}

                # Chat topilmadi
                if "chat not found" in error_msg:
                    logger.warning(f"Chat not found: {chat_id}")
                    return {"channel": channel, "status": "joined", "username": username}  # Skip

                logger.warning(f"Channel check error {chat_id}: {e}")
                return {"channel": channel, "status": "error", "error": str(e)}

            # Status
            if member.status in ["member", "administrator", "creator"]:
                return {"channel": channel, "status": "joined", "username": username}
            elif member.status == "restricted":
                is_member = getattr(member, "is_member", True)
                return {"channel": channel, "status": "joined" if is_member else "not_joined"}
            else:  # left, kicked, etc.
                return {"channel": channel, "status": "not_joined", "username": username}

        except Exception as e:
            logger.error(f"Channel check critical error: {e}", exc_info=True)
            return {"channel": channel, "status": "error"}