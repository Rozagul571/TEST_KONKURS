# bots/user_bots/base_template/handlers/main_menu.py
from aiogram import Router, F
from aiogram.types import Message
from ..services.user_service import UserService
from ..services.point_service import PointService
from ..services.prize_service import PrizeService
from ..services.rating_service import RatingService

router = Router()

@router.message(F.text == "🎁 Sovg'alar")
async def prizes_handler(message: Message, competition: dict):
    """Sovg'alar handler. Vazifasi: Sovrinlar va referral link chiqarish. Misol: Sovrinlar ro'yxati va link chiqadi."""
    user_service = UserService()
    prize_service = PrizeService(competition)
    user = await user_service.get_or_create_user_from_message(message, competition)
    participant = await user_service.get_or_create_participant(user, competition)
    if not participant:
        await message.answer("❌ Xatolik yuz berdi.")
        return
    prizes = await prize_service.get_prizes()
    bot_username = (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={participant.referral_code}"
    prizes_text = "🎁 <b>Sovrinlar:</b>\n\n"
    for prize in prizes:
        if prize.type == 'text':
            prizes_text += f"{prize.place}-o‘rin — {prize.prize_name}\n"
        else:
            prizes_text += f"{prize.place}-o‘rin — {prize.prize_amount:,} so‘m\n"
    prizes_text += f"\n🔗 <b>Sizning referal linkingiz:</b>\n{referral_link}"
    await message.answer(prizes_text, parse_mode="HTML")

@router.message(F.text == "📊 Ballarim")
async def points_handler(message: Message, competition: dict):
    """Ballar handler. Vazifasi: User ballarini chiqarish. Misol: Jami 35 ball, referallardan 25."""
    user_service = UserService()
    point_service = PointService(competition)
    user = await user_service.get_or_create_user_from_message(message, competition)
    participant = await user_service.get_or_create_participant(user, competition)
    if not participant:
        await message.answer("❌ Xatolik yuz berdi.")
        return
    stats = await point_service.get_user_stats(participant)
    user_status = "⭐ Premium Foydalanuvchi" if user.is_premium else "👤 Oddiy Foydalanuvchi"
    points_text = (
        f"📊 <b>Ballaringiz:</b>\n\n"
        f"💰 <b>Jami:</b> {stats['total_points']} ball ✅\n\n"
        f"📈 <b>Tafsilotlar:</b>\n"
        f"• Referallardan: {stats['referral_points']} ball\n"
        f"• Kanallardan: {stats['channel_points']} ball\n"
        f"• Boshqalar: {stats['other_points']} ball\n\n"
        f"👤 <b>Holatingiz:</b> {user_status}"
    )
    await message.answer(points_text, parse_mode="HTML")


@router.message(F.text == "🏆 Reyting")
async def rating_handler(message: Message, competition: dict):
    """Reyting handler. Vazifasi: Top 10 va user o'rni chiqarish. Misol: 1) @Lola — 152 ball, full_name va username birga."""
    rating_service = RatingService(competition)
    user_service = UserService()
    user = await user_service.get_or_create_user_from_message(message, competition)
    participant = await user_service.get_or_create_participant(user, competition)
    if not participant:
        await message.answer("❌ Xatolik yuz berdi.")
        return
    rating_text = await rating_service.get_rating_text(participant)
    await message.answer(rating_text, parse_mode="HTML")

@router.message(F.text == "📜 Shartlar")
async def rules_handler(message: Message, competition: dict):
    """Shartlar handler. Vazifasi: Shartlar va ball tizimini chiqarish. Misol: Shartlar text va ball qoidalari."""
    point_service = PointService(competition)
    point_rules = await point_service.get_point_rules()
    rules_text = f"📜 <b>Konkurs shartlari:</b>\n\n{competition['rules_text'] or 'Shartlar admin tomonidan belgilangan.'}\n\n⚡ <b>Ball to'plash usullari:</b>\n"
    for action_type, points in point_rules.items():
        action_name = {
            'referral': "Har bir taklif qilgan do'stingiz uchun",
            'premium_ref': "Har bir taklif qilgan PREMIUM do'stingiz uchun",
            'channel_join': "Har bir kanalga obuna bo'lish uchun",
            'premium_user': "PREMIUM foydalanuvchi bonus"
        }.get(action_type, action_type)
        rules_text += f"• {action_name}: +{points} ball\n"
    if competition['end_at']:
        rules_text += f"\n\n⏱ <b>Yakunlanish:</b> {competition['end_at'].strftime('%d-%m-%Y, %H:%M')}"
    await message.answer(rules_text, parse_mode="HTML")