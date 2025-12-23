# fastapi_app/api/routes/webhooks/main_bot.py
"""
Main bot webhook endpoints - TO'G'RILANGAN
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from aiogram import Bot
import os
import logging
from shared.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter()


# ========================
# TELEGRAM WEBHOOK
# ========================
@router.post("/main")
async def telegram_main_webhook(request: Request):
    """
    Main Telegram webhook endpoint for /webhook/main
    """
    try:
        update = await request.json()

        # Log received update
        logger.info(f"📩 Telegram update received: {update.get('update_id', 'unknown')}")

        # Save to Redis queue for async processing
        bot_id = 1  # Main bot ID
        await redis_client.push_update(bot_id, update)

        return {"ok": True, "update_id": update.get('update_id')}

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}


# ========================
# CONTACT ADMIN
# ========================
class AdminContactRequest(BaseModel):
    user_tg_id: int
    message: str


@router.post("/contact-admin")
async def contact_admin(request: AdminContactRequest):
    """Handle user contact admin request"""
    try:
        main_token = os.getenv("TELEGRAM_BOT_TOKEN")
        super_admin_id = os.getenv("SUPER_ADMIN_TELEGRAM_ID")

        if not main_token or not super_admin_id:
            raise HTTPException(status_code=500, detail="Configuration error")

        # Format message
        text = f"""
👤 *Yangi xabar foydalanuvchidan*

🆔 *User ID:* {request.user_tg_id}
📝 *Xabar:* {request.message}

✉️ *Javob berish uchun:* `admin_answer_{request.user_tg_id}`
        """.strip()

        # Send to superadmin
        bot = Bot(token=main_token)
        await bot.send_message(
            chat_id=int(super_admin_id),
            text=text,
            parse_mode="Markdown"
        )
        await bot.session.close()

        # Send confirmation to user
        await send_confirmation_to_user(request.user_tg_id, main_token)

        return {"status": "success", "message": "Message sent to admin"}

    except Exception as e:
        logger.error(f"Contact admin error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_confirmation_to_user(user_id: int, bot_token: str):
    """Send confirmation to user"""
    try:
        bot = Bot(token=bot_token)
        text = """
✅ *Xabaringiz muvaffaqiyatli yuborildi!*

📨 Administator tez orada siz bilan bog'lanadi.

⏳ Iltimos, kutib turing yoki keyinroq qayta urinib ko'ring.
        """.strip()

        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown"
        )
        await bot.session.close()

    except Exception as e:
        logger.error(f"Send confirmation error: {e}")