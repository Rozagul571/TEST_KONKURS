#shared/constants.py
"""
Constants for the entire system
"""

# Cache keys
CACHE_KEYS = {
    'bot_settings': 'bot_settings:{bot_id}',
    'rate_limit': 'rate_limit:{bot_id}:{user_id}:{action}',
    'user_state': 'user_state:{bot_id}:{user_id}',
    'referral_pending': 'referral_pending:{bot_id}:{user_id}',
    'channels_cache': 'channels:{bot_id}',
    'competition_cache': 'competition:{bot_id}',
    'rating_cache': 'rating:{bot_id}:{user_id}',
    'user_points': 'user_points:{bot_id}:{user_id}',
}

# Rate limits
RATE_LIMITS = {
    'start': {'limit': 3, 'window': 60},
    'message': {'limit': 30, 'window': 60},
    'callback': {'limit': 20, 'window': 60},
    'join_check': {'limit': 4, 'window': 15},
    'referral': {'limit': 10, 'window': 300},
}

# Point rules defaults
POINT_RULES = {
    'channel_join': 1,
    'referral': 5,
    'premium_user': 2.0,
    'premium_referral': 10,
}

# Bot statuses
BOT_STATUSES = {
    'PENDING': 'pending',
    'RUNNING': 'running',
    'STOPPED': 'stopped',
    'ERROR': 'error',
}

# Competition statuses
COMPETITION_STATUSES = {
    'DRAFT': 'draft',
    'PENDING': 'pending',
    'ACTIVE': 'active',
    'ENDED': 'ended',
    'CANCELLED': 'cancelled',
}