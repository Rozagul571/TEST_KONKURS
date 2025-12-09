# bots/user_bots/base_template/services/channel_service.py
class ChannelService:
    """Kanal servisi. Vazifasi: Obuna statusini tekshirish. Misol: check_user_channels_status - obuna bo'lmaganlarni qaytaradi."""
    def __init__(self, competition: dict):
        self.channels = competition.get('channels', [])

    async def check_user_channels_status(self, user_id: int, bot):
        not_joined = []
        for channel in self.channels:
            is_member = await self.check_channel_membership(user_id, channel['channel_username'], bot)
            if not is_member:
                not_joined.append(channel)
        return {'all_joined': not bool(not_joined), 'not_joined_channels': not_joined}

    async def check_channel_membership(self, user_id: int, channel_username: str, bot):
        channel_username = channel_username.replace('@', '')
        try:
            chat_member = await bot.get_chat_member(f"@{channel_username}", user_id)
            return chat_member.status in ['member', 'administrator', 'creator']
        except:
            return False