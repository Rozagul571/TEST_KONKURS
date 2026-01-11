# bots/main_bot/utils/db_utils.py
from asgiref.sync import sync_to_async
from django_app.core.models.user import User
import os


@sync_to_async
def get_or_create_user(telegram_id, full_name=None, username=None):
    """Telegram user ni DB ga saqlash."""
    first_name, last_name = (full_name.split(" ", 1) + [""])[:2] if full_name else ("", "")

    user, created = User.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "username": username or "",
            "role": "superadmin" if telegram_id == int(os.getenv("SUPER_ADMIN_TELEGRAM_ID", "0")) else "admin"
        }
    )
    return user
