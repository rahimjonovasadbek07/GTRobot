from aiogram import Router, F
from aiogram.types import Message
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user, get_referral_stats

router = Router()


def get_referral_bonus_val():
    from database.db import get_bot_settings
    s = get_bot_settings()
    return float(s.get("referral_bonus", "0.5"))


@router.message(F.text.in_(["👥 Referral", "👥 Реферал", "👥 Referral"]))
async def show_referral(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval /start bosing.")
        return

    ref_code = user.get("referral_code", "—")
    stats = get_referral_stats(message.from_user.id)
    bonus_val = get_referral_bonus_val()

    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{ref_code}"

    text = (
        f"👥 <b>Referral tizimi</b>\n\n"
        f"🔗 Sizning havolangiz:\n"
        f"<code>{ref_link}</code>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"👤 Taklif qilganlar: <b>{stats['count']} ta</b>\n"
        f"💰 Referral bonus: <b>{stats['bonus']:.4f} USDT</b>\n\n"
        f"🎁 <b>Qoidalar:</b>\n"
        f"• Har bir do'stingiz ro'yxatdan o'tsa — <b>{bonus_val} USDT</b> bonus\n"
        f"• Bonus avtomatik balansingizga tushadi\n"
        f"• Havolani do'stlaringizga yuboring!"
    )
    await message.answer(text)
