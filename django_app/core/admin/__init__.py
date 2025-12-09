from .bot_admin import BotSetUpAdmin
from .channel_admin import ChannelAdmin
from .competition_admin import CompetitionAdmin
from .pointrule_admin import PointRuleAdmin
from .prize_admin import PrizeAdmin
from .system_admin import SystemSettingsAdmin
from .user_admin import UserAdmin

__all__ = [
    'BotSetUpAdmin', 'ChannelAdmin', 'CompetitionAdmin', 'PointRuleAdmin',
    'PrizeAdmin', 'SystemSettingsAdmin', 'UserAdmin'
]