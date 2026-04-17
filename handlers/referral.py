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


def get_user_lang(tg_id):
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


REFERRAL_TEXTS = {
    "uz": {
        "title": "👥 <b>Referral tizimi</b>",
        "link_label": "🔗 Sizning havolangiz:",
        "stats": "📊 <b>Statistika:</b>",
        "invited": "👤 Taklif qilganlar:",
        "bonus_label": "💰 Referral bonus:",
        "rules": "🎁 <b>Qoidalar:</b>",
        "rule1": "• Har bir do'stingiz ro'yxatdan o'tsa — <b>{bonus} USDT</b> bonus",
        "rule2": "• Bonus avtomatik balansingizga tushadi",
        "rule3": "• Havolani do'stlaringizga yuboring!",
        "count_suffix": "ta",
    },
    "ru": {
        "title": "👥 <b>Реферальная система</b>",
        "link_label": "🔗 Ваша ссылка:",
        "stats": "📊 <b>Статистика:</b>",
        "invited": "👤 Приглашено:",
        "bonus_label": "💰 Реферальный бонус:",
        "rules": "🎁 <b>Правила:</b>",
        "rule1": "• За каждого друга — <b>{bonus} USDT</b> бонус",
        "rule2": "• Бонус автоматически зачисляется на баланс",
        "rule3": "• Отправьте ссылку друзьям!",
        "count_suffix": "чел.",
    },
    "en": {
        "title": "👥 <b>Referral System</b>",
        "link_label": "🔗 Your referral link:",
        "stats": "📊 <b>Statistics:</b>",
        "invited": "👤 Invited:",
        "bonus_label": "💰 Referral bonus:",
        "rules": "🎁 <b>Rules:</b>",
        "rule1": "• For each friend who joins — <b>{bonus} USDT</b> bonus",
        "rule2": "• Bonus is credited to your balance automatically",
        "rule3": "• Share the link with your friends!",
        "count_suffix": "users",
    },
}


@router.message(F.text.in_(["👥 Referral", "👥 Реферал", "👥 Referral"]))
async def show_referral(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval /start bosing.")
        return

    lang = get_user_lang(message.from_user.id)
    tx = REFERRAL_TEXTS.get(lang, REFERRAL_TEXTS["uz"])

    ref_code = user.get("referral_code", "—")
    stats = get_referral_stats(message.from_user.id)
    bonus_val = get_referral_bonus_val()

    bot_username = (await message.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{ref_code}"

    text = (
        f"{tx['title']}\n\n"
        f"{tx['link_label']}\n"
        f"<code>{ref_link}</code>\n\n"
        f"{tx['stats']}\n"
        f"{tx['invited']} <b>{stats['count']} {tx['count_suffix']}</b>\n"
        f"{tx['bonus_label']} <b>{stats['bonus']:.4f} USDT</b>\n\n"
        f"{tx['rules']}\n"
        f"{tx['rule1'].format(bonus=bonus_val)}\n"
        f"{tx['rule2']}\n"
        f"{tx['rule3']}"
    )
    await message.answer(text)