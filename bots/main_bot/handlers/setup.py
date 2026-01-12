from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from ..utils.db_utils import get_or_create_user
from ..buttons.inline import get_admin_panel_keyboard
from django_app.core.models.bot import BotSetUp, BotStatus
from django_app.core.models.competition import Competition, CompetitionStatus
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
import os
import logging
logger = logging.getLogger(__name__)
router = Router()


class SetupStates(StatesGroup):
    waiting_token_username = State()
    waiting_username = State()
    waiting_password = State()


@router.message(F.text == "/setup_bot")
async def setup_start(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "⚠️ Siz allaqachon sozlash jarayonidasiz. Davom eting yoki /cancel buyrug'i bilan bekor qiling.")
        return
    video_url = os.getenv("VIDEO_GUIDE_URL")
    video_text = f"\n🎥 Video yo'riqnoma: {video_url}" if video_url else ""
    await message.answer(
        f"🤖 **Yangi Bot Yaratish**\n\n"
        f"Quyidagi qadamlarni bajaring:\n"
        f"1. @BotFather ga boring va yangi bot yarating\n"
        f"2. Bot tokenini oling\n"
        f"3. Token va bot username'ni (@ bilan) yuboring\n\n"
        f"📝 **Format:** `@MyBot 123456:ABC-DEF1234...`\n"
        f"{video_text}",
        parse_mode="Markdown"
    )
    await state.set_state(SetupStates.waiting_token_username)


@router.message(SetupStates.waiting_token_username)
async def get_token_username(message: Message, state: FSMContext):
    parts = message.text.strip().split()
    if len(parts) < 2 or not parts[0].startswith("@"):
        await message.answer("❌ Noto'g'ri format! @bot_username token deb yuboring.")
        return
    bot_username = parts[0]
    token = " ".join(parts[1:])
    try:
        from aiogram import Bot
        test_bot = Bot(token=token)
        me = await test_bot.get_me()
        if me.username.lower() != bot_username[1:].lower():
            await message.answer("❌ Token va username mos emas! BotFather dan to'g'ri oling.")
            await test_bot.session.close()
            return
        await test_bot.session.close()
    except:
        await message.answer("❌ Token noto'g'ri! Qayta urinib ko'ring.")
        return
    await state.update_data(bot_username=bot_username, token=token)
    await message.answer("✅ Token qabul qilindi.\nAdmin panel uchun username kiriting (3+ belgi):")
    await state.set_state(SetupStates.waiting_username)


@router.message(SetupStates.waiting_username)
async def get_username(message: Message, state: FSMContext):
    username = message.text.strip()
    if len(username) < 3:
        await message.answer("❌ Username juda qisqa! 3+ belgi kiriting.")
        return
    await state.update_data(admin_username=username)
    await message.answer("✅ Username qabul qilindi.\nParol kiriting (6+ belgi):")
    await state.set_state(SetupStates.waiting_password)


@router.message(SetupStates.waiting_password)
async def get_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 6:
        await message.answer("❌ Parol juda qisqa! 6+ belgi kiriting.")
        return
    data = await state.get_data()
    bot_username = data["bot_username"]
    token = data["token"]
    admin_username_base = data["admin_username"]
    user = await get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await sync_to_async(lambda: BotSetUp.objects.filter(owner=user).update(is_active=False))()
    bot_setup, created = await sync_to_async(BotSetUp.objects.get_or_create)(
        owner=user,
        bot_username=bot_username[1:],
        defaults={"encrypted_token": token, "status": BotStatus.DRAFT, "is_active": True}
    )
    if not created:
        bot_setup.encrypted_token = token
        bot_setup.status = BotStatus.DRAFT
        bot_setup.is_active = True
        await sync_to_async(bot_setup.save)()
    competition, comp_created = await sync_to_async(Competition.objects.get_or_create)(
        bot=bot_setup,
        defaults={
            "creator": user,
            "name": f"Konkurs - @{bot_username[1:]}",
            "status": CompetitionStatus.DRAFT
        }
    )
    unique_username = await create_django_user(admin_username_base, password, user.telegram_id)
    admin_url = f"{os.getenv('ADMIN_PANEL_URL')}?bot_id={bot_setup.id}"
    text = (
        "🎉 <b>Bot Muvaffaqiyatli Yaratildi!</b>\n\n"
        f"🤖 <b>Bot:</b> {bot_username}\n"
        f"👤 <b>Admin login:</b> <code>{unique_username}</code>\n"
        f"🔐 <b>Parol:</b> <code>{password}</code>\n\n"
        "<b>📋 Keyingi qadamlar:</b>\n"
        "1. Quyidagi tugma orqali panelga kiring\n"
        "2. Konkurs ma'lumotlarini to'ldirish (kanallar, sovrinlar, vaqt)\n"
        "3. 'Save' tugmasini bosish\n"
        "4. SuperAdmin tasdiqlashini kuting\n\n"
        "⏳ <b>Status:</b> 'draft' - Panel to'ldirilgach 'pending' bo'ladi, keyin SuperAdmin tasdiqlaydi"
    )
    keyboard = get_admin_panel_keyboard(admin_url)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()


@sync_to_async
def create_django_user(admin_username_base, password, telegram_id):
    admin_username = f"{admin_username_base}_{telegram_id}"
    django_user, created = DjangoUser.objects.get_or_create(
        username=admin_username,
        defaults={
            "email": f"{telegram_id}@konkurs.uz",
            "is_staff": True,
            "is_active": True
        }
    )
    django_user.set_password(password)
    django_user.save()
    bot_admin_group, _ = Group.objects.get_or_create(name='BotAdmin')
    models_to_add = ["competition", "channel", "pointrule", "prize", "participant"]
    all_perms = Permission.objects.filter(content_type__app_label="core", content_type__model__in=models_to_add)
    bot_admin_group.permissions.add(*all_perms)
    django_user.groups.add(bot_admin_group)
    return admin_username