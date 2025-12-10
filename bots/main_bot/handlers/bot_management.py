from aiogram import Router, F
from aiogram.types import CallbackQuery
import httpx
import os
import logging

logger = logging.getLogger(__name__)
router = Router()
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8001")


@router.callback_query(F.data.startswith("run_bot:"))
async def run_bot_handler(callback: CallbackQuery):
    bot_id = int(callback.data.split(":")[1])

    try:
        await callback.answer("Bot ishga tushirilmoqda...", show_alert=False)

        async with httpx.AsyncClient(timeout=30.0) as client:  # FIX: Timeout qo'shildi
            r = await client.post(f"{FASTAPI_URL}/api/bots/run/{bot_id}")

        if r.status_code == 200:
            result = r.json()
            await callback.message.edit_text(
                f"✅ <b>Bot ishga tushdi!</b>\n\n"
                f"🤖 Bot: @{result.get('bot_username', 'Noma\'lum')}\n"
                f"🆔 ID: {bot_id}\n"
                f"🔗 Link: https://t.me/{result.get('bot_username', '')}\n\n"
                f"📊 Endi ishtirokchilar qatnasha boshlaydi!",
                parse_mode="HTML"
            )
            await callback.answer("Muvaffaqiyatli ishga tushdi!", show_alert=True)
        else:
            error_detail = "Noma'lum xato"
            try:
                error_data = r.json()
                error_detail = error_data.get('detail', error_detail)
            except:
                error_detail = f"HTTP {r.status_code}"

            await callback.message.answer(
                f"❌ Botni ishga tushirishda xato!\n\n"
                f"🆔 Bot ID: {bot_id}\n"
                f"📋 Xato: {error_detail}\n\n"
                f"Iltimos, token va sozlamalarni tekshiring."
            )
            await callback.answer("Xato yuz berdi!", show_alert=True)

    except httpx.TimeoutException:
        await callback.message.answer("⏳ Server javob bermadi. Iltimos, keyinroq urinib ko'ring.")
        await callback.answer("Timeout xatosi!", show_alert=True)
    except Exception as e:
        logger.error(f"Run xatosi: {e}", exc_info=True)
        await callback.message.answer(f"❌ Xatolik: {str(e)[:100]}")
        await callback.answer("Xatolik!", show_alert=True)