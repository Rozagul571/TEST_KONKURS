import os

import redis
r = redis.Redis.from_url(os.getenv('REDIS_URL'))

def preload_bot_settings(bot_id, settings):
    r.set(f"bot:{bot_id}:settings", settings)

def get_bot_settings(bot_id):
    return r.get(f"bot:{bot_id}:settings")