# bots/main_bot/utils/message_texts.py

def get_bot_created_message(bot_username: str, admin_username: str, password: str, admin_url: str) -> str:
    """Bot yaratilganda xabar. Vazifasi: User ga ma'lumot yuborish. Misol: Bot yaratilganda chiqadi. O'ZGARTIRILGAN: DRAFT status, panel link."""
    return (
        "🎉 <b>Bot Muvaffaqiyatli Yaratildi!</b>\n\n"
        f"🤖 <b>Bot:</b> {bot_username}\n"
        f"👤 <b>Admin login:</b> <code>{admin_username}</code>\n"
        f"🔐 <b>Parol:</b> <code>{password}</code>\n\n"
        "<b>📋 Keyingi qadamlar:</b>\n"
        "1. Quyidagi tugma orqali panelga kiring\n"
        "2. Konkurs ma'lumotlarini to'ldirish (kanallar, sovrinlar, vaqt)\n"
        "3. 'Save' tugmasini bosish\n"
        "4. SuperAdmin tasdiqlashini kuting\n\n"
        "⏳ <b>Status:</b> 'draft' - Panel to'ldirilgach 'pending' bo'ladi, keyin SuperAdmin tasdiqlaydi"
    )

def get_superadmin_notification_message(user, bot_username: str, admin_username: str) -> str:
    """Superadmin notification. Vazifasi: Yangi bot haqida xabar. Misol: Full_name va username chiqaradi, agar username yo'q bo'lsa faqat full_name. O'ZGARTIRILGAN: Pending da, bot_id ko'rsatiladi."""
    username_display = f"@{user.username}" if user.username else ""
    full_display = f"{user.full_name or 'Nomalum'} {username_display}".strip()
    return (
        f"🔔 <b>Yangi Bot Tayyor!</b>\n\n"
        f"👤 <b>Admin:</b> {full_display}\n"
        f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
        f"🤖 <b>Bot:</b> @{bot_username}\n"
        f"🔑 <b>Admin login:</b> <code>{admin_username}</code>\n\n"
        "⏳ <b>Status:</b> Pending - Tasdiqlang yoki rad eting"
    )

def get_competition_complete_message(user_bot_username: str, competition_name: str, competition_description: str) -> str:
    """Competition to'ldirilganda xabar. Vazifasi: User ga tasdiqlash xabari. Misol: Konkurs nomi va tavsif chiqadi. O'ZGARTIRILGAN: Pending tasdiq kutilishi."""
    return (
        f"🎉 <b>Konkurs muvaffaqiyatli yaratildi!</b>\n\n"
        f"🤖 <b>Sizning botingiz:</b> @{user_bot_username}\n"
        f"🏆 <b>Konkurs nomi:</b> {competition_name}\n"
        f"📝 <b>Tavsif:</b> {competition_description}\n\n"
        "✅ <b>Barcha kerakli ma'lumotlar to'ldirildi!</b>\n"
        "⏳ <b>Status:</b> Pending - SuperAdmin tasdiqlashini kuting\n"
        "🚀 <b>Run qilish uchun SuperAdmin bilan bog'lanish</b> 👇"
    )