#bots/main_bot/handlers/bot_management.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
import httpx
import os
import logging

logger = logging.getLogger(__name__)
router = Router()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8001")


@router.callback_query(F.data.startswith("run_bot:"))
async def run_bot_handler(callback: CallbackQuery):
    """Run bot handler - to'g'ri endpoint bilan"""
    bot_id = int(callback.data.split(":")[1])

    try:
        await callback.answer("Bot ishga tushirilmoqda...")

        # To'g'ri endpoint: /api/bots/run/{bot_id}
        endpoint = f"{FASTAPI_URL}/api/bots/run/{bot_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint)

        if response.status_code == 200:
            data = response.json()

            # Success message
            success_text = (
                f"✅ *Bot ishga tushdi!*\n\n"
                f"🤖 *Bot:* @{data.get('bot_username', '')}\n"
                f"🆔 *ID:* {bot_id}\n"
                f"🔗 *Link:* https://t.me/{data.get('bot_username', '')}\n\n"
                f"📊 Endi ishtirokchilar qatnasha boshlaydi!"
            )

            await callback.message.edit_text(
                success_text,
                parse_mode="Markdown"
            )

            await callback.answer("✅ Bot ishga tushdi!", show_alert=True)

        else:
            error_text = f"❌ Xato: {response.status_code}\n"
            try:
                error_data = response.json()
                error_text += f"Tafsilot: {error_data.get('detail', 'Noma\'lum xato')}"
            except:
                error_text += f"Response: {response.text[:100]}"

            await callback.message.answer(error_text)
            await callback.answer("❌ Xato yuz berdi!", show_alert=True)

    except httpx.TimeoutException:
        await callback.message.answer("⏳ Server javob bermadi. Iltimos, keyinroq urinib ko'ring.")
        await callback.answer("Timeout xatosi!", show_alert=True)
    except Exception as e:
        logger.error(f"Run bot error: {e}", exc_info=True)
        await callback.message.answer(f"❌ Xatolik: {str(e)[:100]}")
        await callback.answer("Xatolik!", show_alert=True)