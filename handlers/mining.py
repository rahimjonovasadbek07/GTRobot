from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from datetime import datetime, timedelta
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    get_user, update_balance, get_mining_plans_db,
    get_user_mining, start_mining, add_mining_earnings,
    stop_mining, get_mining_stats, get_all_active_miners
)
from keyboards.kb import main_menu

router = Router()


# Mining planlar USDT da
MINING_PLANS = [
    {
        "id": 1,
        "name": "⛏️ Miner v1",
        "hourly_usdt": 0.0005,
        "daily_price": 1.0,
        "weekly_price": 6.0,
        "monthly_price": 20.0,
        "daily_earn": 0.012,
        "weekly_earn": 0.084,
        "monthly_earn": 0.36,
    },
    {
        "id": 2,
        "name": "⛏️ Miner v2",
        "hourly_usdt": 0.002,
        "daily_price": 3.0,
        "weekly_price": 18.0,
        "monthly_price": 60.0,
        "daily_earn": 0.048,
        "weekly_earn": 0.336,
        "monthly_earn": 1.44,
    },
    {
        "id": 3,
        "name": "⛏️ Miner v3",
        "hourly_usdt": 0.008,
        "daily_price": 10.0,
        "weekly_price": 60.0,
        "monthly_price": 200.0,
        "daily_earn": 0.192,
        "weekly_earn": 1.344,
        "monthly_earn": 5.76,
    },
]


def get_mining_lang(tg_id):
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


def mining_main_kb(lang="uz"):
    kb = InlineKeyboardBuilder()
    if lang == "ru":
        kb.add(InlineKeyboardButton(text="⛏️ Выбрать тариф", callback_data="mining_plans"))
        kb.add(InlineKeyboardButton(text="📊 Статистика майнинга", callback_data="mining_stats"))
        kb.add(InlineKeyboardButton(text="⏹ Остановить майнинг", callback_data="mining_stop"))
    elif lang == "en":
        kb.add(InlineKeyboardButton(text="⛏️ Select plan", callback_data="mining_plans"))
        kb.add(InlineKeyboardButton(text="📊 Mining statistics", callback_data="mining_stats"))
        kb.add(InlineKeyboardButton(text="⏹ Stop mining", callback_data="mining_stop"))
    else:
        kb.add(InlineKeyboardButton(text="⛏️ Tarif tanlash", callback_data="mining_plans"))
        kb.add(InlineKeyboardButton(text="📊 Mining statistika", callback_data="mining_stats"))
        kb.add(InlineKeyboardButton(text="⏹ Miningni to'xtatish", callback_data="mining_stop"))
    kb.adjust(1)
    return kb.as_markup()


def plans_kb(lang="uz"):
    kb = InlineKeyboardBuilder()
    for p in MINING_PLANS:
        kb.add(InlineKeyboardButton(
            text=f"{p['name']} — {p['hourly_usdt']} USDT/h",
            callback_data=f"plan_{p['id']}"
        ))
    back_text = "🔙 Назад" if lang == "ru" else ("🔙 Back" if lang == "en" else "🔙 Orqaga")
    kb.add(InlineKeyboardButton(text=back_text, callback_data="mining_back"))
    kb.adjust(1)
    return kb.as_markup()


def duration_kb(plan_id: int, lang="uz"):
    plan = next((p for p in MINING_PLANS if p["id"] == plan_id), None)
    if not plan:
        return InlineKeyboardBuilder().as_markup()
    kb = InlineKeyboardBuilder()
    if lang == "ru":
        kb.add(InlineKeyboardButton(text=f"📅 Дневной — {plan['daily_price']} USDT", callback_data=f"buy_mining_{plan_id}_daily"))
        kb.add(InlineKeyboardButton(text=f"📆 Недельный — {plan['weekly_price']} USDT", callback_data=f"buy_mining_{plan_id}_weekly"))
        kb.add(InlineKeyboardButton(text=f"🗓 Месячный — {plan['monthly_price']} USDT", callback_data=f"buy_mining_{plan_id}_monthly"))
        kb.add(InlineKeyboardButton(text="🔙 Назад", callback_data="mining_plans"))
    elif lang == "en":
        kb.add(InlineKeyboardButton(text=f"📅 Daily — {plan['daily_price']} USDT", callback_data=f"buy_mining_{plan_id}_daily"))
        kb.add(InlineKeyboardButton(text=f"📆 Weekly — {plan['weekly_price']} USDT", callback_data=f"buy_mining_{plan_id}_weekly"))
        kb.add(InlineKeyboardButton(text=f"🗓 Monthly — {plan['monthly_price']} USDT", callback_data=f"buy_mining_{plan_id}_monthly"))
        kb.add(InlineKeyboardButton(text="🔙 Back", callback_data="mining_plans"))
    else:
        kb.add(InlineKeyboardButton(text=f"📅 Kunlik — {plan['daily_price']} USDT", callback_data=f"buy_mining_{plan_id}_daily"))
        kb.add(InlineKeyboardButton(text=f"📆 Haftalik — {plan['weekly_price']} USDT", callback_data=f"buy_mining_{plan_id}_weekly"))
        kb.add(InlineKeyboardButton(text=f"🗓 Oylik — {plan['monthly_price']} USDT", callback_data=f"buy_mining_{plan_id}_monthly"))
        kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="mining_plans"))
    kb.adjust(1)
    return kb.as_markup()



@router.message(F.text.in_(["⛏️ Cloud Mining", "⛏️ Cloud Mining"]))
async def show_mining(message: Message):
    user = get_user(message.from_user.id)
    lang = get_mining_lang(message.from_user.id)
    mining = get_user_mining(message.from_user.id)

    if mining:
        stats = get_mining_stats(message.from_user.id)
        expires = datetime.fromisoformat(stats["expires_at"])
        time_left = expires - datetime.now()
        hours_left = max(0, int(time_left.total_seconds() / 3600))
        minutes_left = max(0, int((time_left.total_seconds() % 3600) / 60))

        plan = next((p for p in MINING_PLANS if p["name"] == stats["plan_name"]), None)
        hourly = plan["hourly_usdt"] if plan else stats.get("hourly_uzs", stats.get("hourly_income", 0))

        await message.answer(
            f"⛏️ <b>Cloud Mining</b>\n\n"
            f"✅ <b>Mining faol!</b>\n\n"
            f"📋 Tarif: <b>{stats['plan_name']}</b>\n"
            f"💰 Soatlik: <b>{hourly} USDT</b>\n"
            f"⏰ Qolgan: <b>{hours_left} soat {minutes_left} daqiqa</b>\n"
            f"💵 Jami daromad: <b>{stats['total_earned']:.6f} USDT</b>\n\n"
            f"💰 Balans: <b>{user['balance']:.4f} USDT</b>",
            reply_markup=mining_main_kb(lang)
        )
    else:
        await message.answer(
            f"⛏️ <b>Cloud Mining</b>\n\n"
            f"Tarif tanlang va mining boshlang!\n\n"
            f"<b>Qanday ishlaydi:</b>\n"
            f"1️⃣ Tarif va muddat tanlang\n"
            f"2️⃣ Balansdan USDT to'lanadi\n"
            f"3️⃣ Bot har soatda daromad hisoblaydi\n"
            f"4️⃣ Daromad balansingizga tushadi\n\n"
            f"💰 Balans: <b>{user['balance']:.4f} USDT</b>",
            reply_markup=mining_main_kb(lang)
        )


@router.callback_query(F.data == "mining_plans")
async def cb_mining_plans(call: CallbackQuery):
    lang = get_mining_lang(call.from_user.id)
    text = "⛏️ <b>Cloud Mining Tariflar</b>\n\n"
    for p in MINING_PLANS:
        profit_d = round(p["daily_earn"] - p["daily_price"], 4)
        text += (
            f"<b>{p['name']}</b>\n"
            f"💰 Soatlik: <b>{p['hourly_uzs']} USDT</b>\n"
            f"📈 Kunlik daromad: <b>{p['daily_earn']} USDT</b>\n"
            f"💳 Kunlik narx: {p['daily_price']} USDT\n"
            f"📊 Sof foyda/kun: +{profit_d} USDT\n\n"
        )
    await call.message.edit_text(text, reply_markup=plans_kb(lang))


@router.callback_query(F.data.startswith("plan_"))
async def cb_plan_select(call: CallbackQuery):
    lang = get_mining_lang(call.from_user.id)
    plan_id = int(call.data.split("_")[1])
    plan = next((p for p in MINING_PLANS if p["id"] == plan_id), None)
    if not plan:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return

    user = get_user(call.from_user.id)
    balance = user["balance"] if user else 0

    await call.message.edit_text(
        f"⛏️ <b>{plan['name']}</b>\n\n"
        f"💰 Soatlik: <b>{plan['hourly_usdt']} USDT</b>\n\n"
        f"📅 <b>Kunlik:</b>\n"
        f"   Narx: {plan['daily_price']} USDT | Daromad: {plan['daily_earn']} USDT\n"
        f"   Foyda: +{round(plan['daily_earn'] - plan['daily_price'], 4)} USDT\n\n"
        f"📆 <b>Haftalik:</b>\n"
        f"   Narx: {plan['weekly_price']} USDT | Daromad: {plan['weekly_earn']} USDT\n"
        f"   Foyda: +{round(plan['weekly_earn'] - plan['weekly_price'], 4)} USDT\n\n"
        f"🗓 <b>Oylik:</b>\n"
        f"   Narx: {plan['monthly_price']} USDT | Daromad: {plan['monthly_earn']} USDT\n"
        f"   Foyda: +{round(plan['monthly_earn'] - plan['monthly_price'], 4)} USDT\n\n"
        f"💰 Balans: <b>{balance:.4f} USDT</b>\n\n"
        f"Muddatni tanlang:",
        reply_markup=duration_kb(plan_id, lang)
    )


@router.callback_query(F.data.startswith("buy_mining_"))
async def cb_buy_mining(call: CallbackQuery):
    lang = get_mining_lang(call.from_user.id)
    parts = call.data.split("_")
    plan_id = int(parts[2])
    duration = parts[3]

    plan = next((p for p in MINING_PLANS if p["id"] == plan_id), None)
    if not plan:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return

    if duration == "daily":
        price = plan["daily_price"]
        earn = plan["daily_earn"]
        dur_label = "1 kun"
        expires = (datetime.now() + timedelta(days=1)).isoformat()
    elif duration == "weekly":
        price = plan["weekly_price"]
        earn = plan["weekly_earn"]
        dur_label = "7 kun"
        expires = (datetime.now() + timedelta(weeks=1)).isoformat()
    else:
        price = plan["monthly_price"]
        earn = plan["monthly_earn"]
        dur_label = "30 kun"
        expires = (datetime.now() + timedelta(days=30)).isoformat()

    user = get_user(call.from_user.id)
    balance = user["balance"] if user else 0

    if balance < price:
        await call.answer(
            f"❌ Balans yetarli emas!\n"
            f"Kerak: {price} USDT\n"
            f"Balans: {balance:.4f} USDT",
            show_alert=True
        )
        return

    update_balance(call.from_user.id, -price)
    start_mining(call.from_user.id, plan_id, plan["name"], plan["hourly_usdt"], expires)

    await call.message.edit_text(
        f"✅ <b>Mining boshlandi!</b>\n\n"
        f"⛏️ Tarif: <b>{plan['name']}</b>\n"
        f"⏱ Muddat: <b>{dur_label}</b>\n"
        f"💳 To'langan: <b>{price} USDT</b>\n\n"
        f"📈 Daromad:\n"
        f"• Soatlik: {plan['hourly_usdt']} USDT\n"
        f"• Jami taxminiy: {earn} USDT\n"
        f"• Sof foyda: +{round(earn - price, 4)} USDT\n\n"
        f"💵 Daromad har soatda balansingizga tushadi! ✅"
    )
    await call.message.answer("✅ Mining faol!", reply_markup=main_menu(lang))


@router.callback_query(F.data == "mining_stats")
async def cb_mining_stats(call: CallbackQuery):
    lang = get_mining_lang(call.from_user.id)
    stats = get_mining_stats(call.from_user.id)
    user = get_user(call.from_user.id)

    if not stats:
        await call.answer("❌ Faol mining yo'q!", show_alert=True)
        return

    expires = datetime.fromisoformat(stats["expires_at"])
    time_left = expires - datetime.now()
    hours_left = max(0, int(time_left.total_seconds() / 3600))
    minutes_left = max(0, int((time_left.total_seconds() % 3600) / 60))

    plan = next((p for p in MINING_PLANS if p["name"] == stats["plan_name"]), None)
    hourly = plan["hourly_usdt"] if plan else stats.get("hourly_uzs", stats.get("hourly_income", 0))

    await call.message.edit_text(
        f"📊 <b>Mining Statistika</b>\n\n"
        f"⛏️ Tarif: <b>{stats['plan_name']}</b>\n"
        f"📅 Boshlangan: {stats['started_at'][:16]}\n"
        f"⏰ Tugaydi: {stats['expires_at'][:16]}\n"
        f"⌛ Qolgan: <b>{hours_left} soat {minutes_left} daqiqa</b>\n\n"
        f"💰 Soatlik: <b>{hourly} USDT</b>\n"
        f"💵 Jami daromad: <b>{stats['total_earned']:.6f} USDT</b>\n\n"
        f"💳 Balans: <b>{user['balance']:.4f} USDT</b>",
        reply_markup=mining_main_kb(lang)
    )


@router.callback_query(F.data == "mining_stop")
async def cb_mining_stop(call: CallbackQuery):
    lang = get_mining_lang(call.from_user.id)
    mining = get_user_mining(call.from_user.id)
    if not mining:
        await call.answer("❌ Faol mining yo'q!", show_alert=True)
        return
    stop_mining(call.from_user.id)
    await call.message.edit_text("⏹ <b>Mining to'xtatildi!</b>")
    await call.message.answer("Asosiy menyu:", reply_markup=main_menu(lang))


@router.callback_query(F.data == "mining_back")
async def cb_mining_back(call: CallbackQuery):
    lang = get_mining_lang(call.from_user.id)
    user = get_user(call.from_user.id)
    await call.message.edit_text(
        f"⛏️ <b>Cloud Mining</b>\n\n💰 Balans: <b>{user['balance']:.4f} USDT</b>",
        reply_markup=mining_main_kb(lang)
    )


async def mining_payout_loop(bot):
    """Har soatda mining daromadini to'lash - USDT da"""
    while True:
        try:
            miners = get_all_active_miners()
            now = datetime.now()

            for miner in miners:
                tg_id, hourly_income, last_payout, expires_at = miner

                expires = datetime.fromisoformat(expires_at)
                if now > expires:
                    stop_mining(tg_id)
                    try:
                        await bot.send_message(
                            tg_id,
                            "⏰ <b>Mining muddati tugadi!</b>\n\n"
                            "Yangi tarif tanlash uchun ⛏️ Cloud Mining ga kiring."
                        )
                    except Exception:
                        pass
                    continue

                last = datetime.fromisoformat(last_payout)
                hours_passed = (now - last).total_seconds() / 3600

                if hours_passed >= 1:
                    payout_hours = int(hours_passed)
                    # hourly_income USDT da
                    amount_usdt = hourly_income * payout_hours
                    add_mining_earnings(tg_id, amount_usdt)

                    try:
                        await bot.send_message(
                            tg_id,
                            f"⛏️ <b>Mining daromad!</b>\n\n"
                            f"💰 +{amount_usdt:.6f} USDT\n"
                            f"⏰ {payout_hours} soatlik daromad\n\n"
                            f"✅ Balansga qo'shildi!"
                        )
                    except Exception:
                        pass

        except Exception:
            pass

        await asyncio.sleep(1800)