# shared/constants.py
"""
Shared constants - Barcha konstantalar va messagelar bir joyda
Vazifasi: DRY prinsipi - barcha text va sozlamalar markazlashtirilgan
"""

# =====================================
# BOT STATUSLARI
# =====================================
BOT_STATUSES = {
    'DRAFT': 'draft',
    'PENDING': 'pending',
    'RUNNING': 'running',
    'STOPPED': 'stopped',
    'REJECTED': 'rejected'
}

# =====================================
# COMPETITION STATUSLARI
# =====================================
COMPETITION_STATUSES = {
    'DRAFT': 'draft',
    'PENDING': 'pending',
    'ACTIVE': 'active',
    'FINISHED': 'finished',
    'CANCELED': 'canceled'
}

# =====================================
# CACHE KEYS - Redis uchun
# =====================================
CACHE_KEYS = {
    'bot_settings': 'bot_settings:{bot_id}',
    'user_state': 'user_state:{bot_id}:{user_id}',
    'rate_limit': 'rate_limit:{bot_id}:{user_id}:{action}',
    'referral_pending': 'referral_pending:{bot_id}:{user_id}',
    'rating_cache': 'rating_cache:{bot_id}:{user_id}',
    'bot_queue': 'bot_queue:{bot_id}',
    'channel_check': 'channel_check:{bot_id}:{user_id}'
}

# =====================================
# RATE LIMITS - Anti-spam uchun
# Limit: necha marta, Window: necha sekundda
# =====================================
RATE_LIMITS = {
    'start': {'limit': 5, 'window': 60},  # 5 /start per minute
    'message': {'limit': 30, 'window': 60},  # 30 messages per minute
    'callback': {'limit': 20, 'window': 60},  # 20 callbacks per minute
    'join_check': {'limit': 5, 'window': 15},  # 5 checks per 15 seconds
    'menu_action': {'limit': 10, 'window': 30},  # 10 menu actions per 30 seconds
    'rating': {'limit': 5, 'window': 30},  # 5 rating requests per 30 seconds
    'inline_query': {'limit': 10, 'window': 60}  # 10 inline queries per minute
}

# =====================================
# DEFAULT POINT VALUES - Ball qiymatlari
# =====================================
DEFAULT_POINTS = {
    'channel_join': 1,  # Har bir kanal uchun
    'referral': 5,  # Oddiy referral
    'premium_referral': 10,  # Premium referral
    'premium_multiplier': 2  # Premium user multiplier
}

# =====================================
# MESSAGES - Barcha xabarlar
# =====================================
MESSAGES = {
    # Errors
    'error_occurred': '❌ Xatolik yuz berdi. Keyinroq urinib ko\'ring.',
    'settings_not_found': '❌ Bot sozlamalari topilmadi.',
    'rate_limited': '🚫 Juda tez so\'rov yuborilmoqda. Biroz kuting.',
    'not_registered': '❌ Avval /start ni bosing va konkursda ro\'yxatdan o\'ting!',

    # Success
    'registration_success': '🎉 Tabriklaymiz! Siz konkursda muvaffaqiyatli ro\'yxatdan o\'tdingiz!',
    'subscription_success': '✅ Barcha kanallarga obuna bo\'ldingiz!',
    'all_channels_joined': '✅ Muvaffaqiyatli ro\'yxatdan o\'tdingiz!',

    # Channel subscription
    'channels_intro': '😎 Konkursda qatnashish uchun quyidagi kanallarga obuna bo\'ling:\n\n',
    'channels_remaining': '⚠️ Hali {count} ta kanalga obuna bo\'lmagansiz!\n\n',
    'channels_instruction': '\n📋 *Qadamlar:*\n1. Har bir kanal tugmasini bosing\n2. Kanallarga o\'ting va "Join" tugmasini bosing\n3. Barchasiga obuna bo\'lgach, ✅ tugmasini qayta bosing',
    'channels_warning': '\n\n⚠️ *Eslatma:* Faqat barcha kanallarga obuna bo\'lganingizdan so\'ng konkursda qatnashishingiz mumkin!',

    # Menu
    'main_menu_intro': '👇 Quyidagi tugmalar orqali konkursda ishtirok eting:',

    # Prizes
    'no_prizes': '🎁 *Sovg\'alar hozircha belgilanmagan.*\n\nAdmin tez orada konkurs sovrinlarini belgilaydi.',
    'prizes_header': '🎁 *KONKURS SOVG\'ALARI* 🎁\n\n',
    'prizes_footer': '\n🏆 *G\'olib bo\'lish uchun ko\'proq ball yig\'ing!*\n🚀 Do\'stlaringizni taklif qiling va ballaringizni oshiring!',

    # Points
    'points_header': '📊 *BALLARIM: {points} ball*\n\n',
    'points_breakdown': '💰 *Ballar tafsiloti:*\n• 📢 Kanallar: {channel} ball\n• 👥 Referrallar: {referral} ball\n• ⭐️ Premium bonus: {premium} ball\n• 📝 Boshqa: {other} ball\n\n',
    'points_premium_status': '⭐️ *Siz Premium foydalanuvchisiz!* Ikki baravar ko\'p ball olasiz.\n\n',
    'points_motivation': '🚀 *Ko\'proq ball yig\'ish uchun:*\n1. Do\'stlaringizni taklif qiling\n2. Kunlik topshiriqlarni bajaring\n3. Postlarni ulashing\n4. Aktiv bo\'ling!',

    # Rating
    'rating_header': '🏆 *TOP 10 Reyting* 🏆\n\n',
    'rating_empty': '🏆 *TOP 10 Reyting*\n\nHozircha hech kim ball to\'plamagan.\n🚀 Birinchi bo\'ling!',
    'rating_user_in_top': '\n✅ *Siz {rank}-o\'rindasiz!* - {points} ball',
    'rating_user_not_in_top': '\n🎯 *Siz:* {rank}-o\'rinda - {points} ball',
    'rating_points_needed': '\n🔝 *TOP 10 uchun {points} ball kerak!*',
    'rating_not_registered': '\n❌ *Siz hali reytingda emassiz.* /start ni bosib ro\'yxatdan o\'ting!',
    'rating_total_participants': '\n📊 *Jami ishtirokchilar:* {total} ta (Siz {percentage:.1f}% ichidasiz)',
    'rating_motivation': '\n\n🚀 *Ko\'proq ball yig\'ish uchun do\'stlaringizni taklif qiling!*',

    # Rules
    'rules_header': '📜 *KONKURS QOIDALARI*\n\n',
    'rules_default': '1. Barcha majburiy kanallarga obuna bo\'ling\n2. Do\'stlaringizni taklif qiling va ballar yig\'ing\n3. Har bir taklif qilgan do\'stingiz uchun ballar olasiz\n4. Premium foydalanuvchilar 2x ko\'p ball oladi\n5. Eng ko\'p ball to\'plagan TOP 10 sovrinlarni oladi\n6. Har bir qoidani buzish diskvalifikatsiyaga olib kelishi mumkin\n\n🚀 Ko\'proq odam taklif qiling va g\'olib bo\'ling!',

    # Invitation
    'invitation_header': '🎉 *DO\'STLARINGIZNI TAKLIF QILING VA BALLAR YIG\'ING!*\n\n',
    'invitation_competition': '🏆 *Konkurs:* {name}\n\n',
    'invitation_description': '📝 *Tavsif:* {description}\n\n',
    'invitation_prizes': '🎁 *Asosiy sovrinlar:*\n',
    'invitation_rules': '📜 *Qoidalar:* {rules}\n\n',
    'invitation_link': '🔗 *Mening taklif havolam:*\n`{link}`\n\n',
    'invitation_cta': '👇 *Ishtirok etish uchun havolani bosing!*',
    'invitation_share_instruction': '👆 Ushbu postni do\'stlaringizga ulashing va ballar yig\'ing!',

    # Welcome
    'welcome_registered': '🎉 Tabriklaymiz, {name}! Siz konkursda muvaffaqiyatli ro\'yxatdan o\'tdingiz!\n\n🚀 Do\'stlaringizni taklif qiling va eng ko\'p ball to\'plang!\n\n',

    # Notifications
    'bot_created': '🎉 <b>Bot Muvaffaqiyatli Yaratildi!</b>\n\n🤖 <b>Bot:</b> {bot_username}\n👤 <b>Admin login:</b> <code>{admin_username}</code>\n🔐 <b>Parol:</b> <code>{password}</code>\n\n<b>📋 Keyingi qadamlar:</b>\n1. Quyidagi tugma orqali panelga kiring\n2. Konkurs ma\'lumotlarini to\'ldirish (kanallar, sovrinlar, vaqt)\n3. "Save" tugmasini bosish\n4. SuperAdmin tasdiqlashini kuting\n\n⏳ <b>Status:</b> "draft" - Panel to\'ldirilgach "pending" bo\'ladi, keyin SuperAdmin tasdiqlaydi',
    'competition_completed': '🎉 <b>Konkurs muvaffaqiyatli yaratildi!</b>\n\n🤖 <b>Sizning botingiz:</b> @{bot_username}\n🏆 <b>Konkurs nomi:</b> {name}\n📝 <b>Tavsif:</b> {description}\n\n✅ <b>Barcha kerakli ma\'lumotlar to\'ldirildi!</b>\n⏳ <b>Status:</b> Pending - SuperAdmin tasdiqlashini kuting\n🚀 <b>Run qilish uchun SuperAdmin bilan bog\'lanish</b> 👇',
    'bot_running': '🎉 <b>Bot ishga tushdi!</b>\n\n🤖 <b>Bot:</b> @{bot_username}\n🆔 <b>ID:</b> {bot_id}\n🔗 <b>Link:</b> https://t.me/{bot_username}\n\n✅ <b>Status:</b> Ishga tushdi\n📊 Endi ishtirokchilar qatnasha boshlashi mumkin!',
    'superadmin_new_bot': '🔔 <b>Yangi Bot Tayyor!</b>\n\n👤 <b>Admin:</b> {full_name}\n🆔 <b>Telegram ID:</b> {telegram_id}\n🤖 <b>Bot:</b> @{bot_username}\n🔑 <b>Admin login:</b> <code>{admin_username}</code>\n\n⏳ <b>Status:</b> Pending - Tasdiqlang yoki rad eting'
}

# =====================================
# BUTTON TEXTS - Tugma textlari
# =====================================
BUTTON_TEXTS = {
    # Main menu buttons
    'konkurs_qatnashish': '🚀 Konkursda qatnashish',
    'sovgalar': '🎁 Sovg\'alar',
    'ballarim': '📊 Ballarim',
    'reyting': '🏆 Reyting',
    'shartlar': '📜 Shartlar',

    # Inline buttons
    'azo_boldim': '✅ A\'zo bo\'ldim',
    'taklif_qilish': '👥 Do\'stlarni taklif qilish',
    'postni_ulashish': '📢 Postni ulashish',
    'admin_panel': '🚀 Konkurs Paneliga Kirish',
    'admin_contact': '👩‍💻 Admin bilan bog\'lanish',

    # Management buttons
    'run_bot': '✅ Run Bot',
    'stop_bot': '⏹️ Stop Bot',
    'reject_bot': '❌ Reject Bot'
}

# =====================================
# PRIZE EMOJIS - O'rin emojilar
# =====================================
PRIZE_EMOJIS = {
    1: "🥇",
    2: "🥈",
    3: "🥉",
    4: "4️⃣",
    5: "5️⃣",
    6: "6️⃣",
    7: "7️⃣",
    8: "8️⃣",
    9: "9️⃣",
    10: "🔟"
}

# =====================================
# CACHE TTL VALUES (sekundlarda)
# =====================================
CACHE_TTL = {
    'bot_settings': 300,  # 5 minutes
    'user_state': 600,  # 10 minutes
    'rating': 30,  # 30 seconds
    'channel_check': 15,  # 15 seconds
    'referral_pending': 3600  # 1 hour
}