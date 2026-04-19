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

MINING_PLANS = [
    {"id": 1, "name": "⛏️ Miner v1", "hourly_usdt": 0.0005, "daily_price": 1.0,
     "weekly_price": 6.0, "monthly_price": 20.0, "daily_earn": 0.012, "weekly_earn": 0.084, "monthly_earn": 0.36},
    {"id": 2, "name": "⛏️ Miner v2", "hourly_usdt": 0.002, "daily_price": 3.0,
     "weekly_price": 18.0, "monthly_price": 60.0, "daily_earn": 0.048, "weekly_earn": 0.336, "monthly_earn": 1.44},
    {"id": 3, "name": "⛏️ Miner v3", "hourly_usdt": 0.008, "daily_price": 10.0,
     "weekly_price": 60.0, "monthly_price": 200.0, "daily_earn": 0.192, "weekly_earn": 1.344, "monthly_earn": 5.76},
]

# Til matnlari
MINING_TX = {
    "uz": {
        "title": "⛏️ <b>Cloud Mining</b>",
        "active": "✅ <b>Mining faol!</b>",
        "inactive_desc": "Tarif tanlang va mining boshlang!",
        "how": "<b>Qanday ishlaydi:</b>",
        "step1": "1️⃣ Tarif va muddat tanlang",
        "step2": "2️⃣ Balansdan USDT to'lanadi",
        "step3": "3️⃣ Bot har soatda daromad hisoblaydi",
        "step4": "4️⃣ Daromad balansingizga tushadi",
        "balance": "💰 Balans",
        "plan_label": "📋 Tarif",
        "hourly": "💰 Soatlik",
        "remaining": "⏰ Qolgan",
        "total_earned": "💵 Jami daromad",
        "hour": "soat",
        "min": "daqiqa",
        "btn_plans": "⛏️ Tarif tanlash",
        "btn_stats": "📊 Mining statistika",
        "btn_stop": "⏹ Miningni to'xtatish",
        "plans_title": "⛏️ <b>Cloud Mining Tariflar</b>",
        "hourly_label": "💰 Soatlik",
        "daily_earn": "📈 Kunlik daromad",
        "daily_price": "💳 Kunlik narx",
        "net_profit": "📊 Sof foyda/kun",
        "select_duration": "Muddatni tanlang:",
        "daily_btn": "📅 Kunlik",
        "weekly_btn": "📆 Haftalik",
        "monthly_btn": "🗓 Oylik",
        "back": "🔙 Orqaga",
        "started": "✅ <b>Mining boshlandi!</b>",
        "plan_name": "⛏️ Tarif",
        "duration": "⏱ Muddat",
        "paid": "💳 To'langan",
        "income": "📈 Daromad",
        "hourly_income": "• Soatlik",
        "approx_total": "• Jami taxminiy",
        "net": "• Sof foyda",
        "auto_msg": "💵 Daromad har soatda balansingizga tushadi! ✅",
        "mining_active": "✅ Mining faol!",
        "stats_title": "📊 <b>Mining Statistika</b>",
        "started_at": "📅 Boshlangan",
        "expires_at": "⏰ Tugaydi",
        "time_left": "⌛ Qolgan",
        "no_mining": "❌ Faol mining yo'q!",
        "stopped": "⏹ <b>Mining to'xtatildi!</b>",
        "main_menu": "Asosiy menyu:",
        "expired_msg": "⏰ <b>Mining muddati tugadi!</b>\n\nYangi tarif tanlash uchun ⛏️ Cloud Mining ga kiring.",
        "payout_msg": "⛏️ <b>Mining daromad!</b>\n\n💰 +{amount} USDT\n⏰ {hours} soatlik daromad\n\n✅ Balansga qo'shildi!",
        "not_enough": "❌ Balans yetarli emas!\nKerak: {price} USDT\nBalans: {balance:.4f} USDT",
        "day": "1 kun", "week": "7 kun", "month": "30 kun",
    },
    "ru": {
        "title": "⛏️ <b>Cloud Mining</b>",
        "active": "✅ <b>Майнинг активен!</b>",
        "inactive_desc": "Выберите тариф и начните майнинг!",
        "how": "<b>Как это работает:</b>",
        "step1": "1️⃣ Выберите тариф и срок",
        "step2": "2️⃣ Оплата списывается с баланса",
        "step3": "3️⃣ Бот начисляет доход каждый час",
        "step4": "4️⃣ Доход поступает на ваш баланс",
        "balance": "💰 Баланс",
        "plan_label": "📋 Тариф",
        "hourly": "💰 В час",
        "remaining": "⏰ Осталось",
        "total_earned": "💵 Всего заработано",
        "hour": "ч", "min": "мин",
        "btn_plans": "⛏️ Выбрать тариф",
        "btn_stats": "📊 Статистика майнинга",
        "btn_stop": "⏹ Остановить майнинг",
        "plans_title": "⛏️ <b>Тарифы Cloud Mining</b>",
        "hourly_label": "💰 В час",
        "daily_earn": "📈 Дневной доход",
        "daily_price": "💳 Цена в день",
        "net_profit": "📊 Чистая прибыль/день",
        "select_duration": "Выберите срок:",
        "daily_btn": "📅 Дневной",
        "weekly_btn": "📆 Недельный",
        "monthly_btn": "🗓 Месячный",
        "back": "🔙 Назад",
        "started": "✅ <b>Майнинг запущен!</b>",
        "plan_name": "⛏️ Тариф",
        "duration": "⏱ Срок",
        "paid": "💳 Оплачено",
        "income": "📈 Доход",
        "hourly_income": "• В час",
        "approx_total": "• Примерно всего",
        "net": "• Чистая прибыль",
        "auto_msg": "💵 Доход начисляется каждый час! ✅",
        "mining_active": "✅ Майнинг активен!",
        "stats_title": "📊 <b>Статистика майнинга</b>",
        "started_at": "📅 Начат",
        "expires_at": "⏰ Истекает",
        "time_left": "⌛ Осталось",
        "no_mining": "❌ Нет активного майнинга!",
        "stopped": "⏹ <b>Майнинг остановлен!</b>",
        "main_menu": "Главное меню:",
        "expired_msg": "⏰ <b>Срок майнинга истёк!</b>\n\nЗайдите в ⛏️ Cloud Mining для выбора нового тарифа.",
        "payout_msg": "⛏️ <b>Доход от майнинга!</b>\n\n💰 +{amount} USDT\n⏰ За {hours} ч.\n\n✅ Зачислено на баланс!",
        "not_enough": "❌ Недостаточно средств!\nНужно: {price} USDT\nБаланс: {balance:.4f} USDT",
        "day": "1 день", "week": "7 дней", "month": "30 дней",
    },
    "en": {
        "title": "⛏️ <b>Cloud Mining</b>",
        "active": "✅ <b>Mining is active!</b>",
        "inactive_desc": "Choose a plan and start mining!",
        "how": "<b>How it works:</b>",
        "step1": "1️⃣ Choose plan and duration",
        "step2": "2️⃣ Payment deducted from balance",
        "step3": "3️⃣ Bot calculates earnings every hour",
        "step4": "4️⃣ Earnings added to your balance",
        "balance": "💰 Balance",
        "plan_label": "📋 Plan",
        "hourly": "💰 Hourly",
        "remaining": "⏰ Remaining",
        "total_earned": "💵 Total earned",
        "hour": "hr", "min": "min",
        "btn_plans": "⛏️ Choose plan",
        "btn_stats": "📊 Mining statistics",
        "btn_stop": "⏹ Stop mining",
        "plans_title": "⛏️ <b>Cloud Mining Plans</b>",
        "hourly_label": "💰 Hourly",
        "daily_earn": "📈 Daily earnings",
        "daily_price": "💳 Daily price",
        "net_profit": "📊 Net profit/day",
        "select_duration": "Select duration:",
        "daily_btn": "📅 Daily",
        "weekly_btn": "📆 Weekly",
        "monthly_btn": "🗓 Monthly",
        "back": "🔙 Back",
        "started": "✅ <b>Mining started!</b>",
        "plan_name": "⛏️ Plan",
        "duration": "⏱ Duration",
        "paid": "💳 Paid",
        "income": "📈 Earnings",
        "hourly_income": "• Hourly",
        "approx_total": "• Approx total",
        "net": "• Net profit",
        "auto_msg": "💵 Earnings credited every hour! ✅",
        "mining_active": "✅ Mining active!",
        "stats_title": "📊 <b>Mining Statistics</b>",
        "started_at": "📅 Started",
        "expires_at": "⏰ Expires",
        "time_left": "⌛ Remaining",
        "no_mining": "❌ No active mining!",
        "stopped": "⏹ <b>Mining stopped!</b>",
        "main_menu": "Main menu:",
        "expired_msg": "⏰ <b>Mining period expired!</b>\n\nGo to ⛏️ Cloud Mining to choose a new plan.",
        "payout_msg": "⛏️ <b>Mining earnings!</b>\n\n💰 +{amount} USDT\n⏰ For {hours} hr\n\n✅ Added to balance!",
        "not_enough": "❌ Insufficient balance!\nNeeded: {price} USDT\nBalance: {balance:.4f} USDT",
        "day": "1 day", "week": "7 days", "month": "30 days",
    },
}


def get_user_lang(tg_id):
    from database.db import get_user
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


def mining_main_kb(lang="uz"):
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=tx["btn_plans"], callback_data="mining_plans"))
    kb.add(InlineKeyboardButton(text=tx["btn_stats"], callback_data="mining_stats"))
    kb.add(InlineKeyboardButton(text=tx["btn_stop"], callback_data="mining_stop"))
    kb.adjust(1)
    return kb.as_markup()


def plans_kb(lang="uz"):
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    kb = InlineKeyboardBuilder()
    for p in MINING_PLANS:
        kb.add(InlineKeyboardButton(
            text=f"{p['name']} — {p['hourly_usdt']} USDT/h",
            callback_data=f"plan_{p['id']}"
        ))
    kb.add(InlineKeyboardButton(text=tx["back"], callback_data="mining_back"))
    kb.adjust(1)
    return kb.as_markup()


def duration_kb(plan_id: int, lang="uz"):
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    plan = next((p for p in MINING_PLANS if p["id"] == plan_id), None)
    if not plan:
        return InlineKeyboardBuilder().as_markup()
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=f"{tx['daily_btn']} — {plan['daily_price']} USDT", callback_data=f"buy_mining_{plan_id}_daily"))
    kb.add(InlineKeyboardButton(text=f"{tx['weekly_btn']} — {plan['weekly_price']} USDT", callback_data=f"buy_mining_{plan_id}_weekly"))
    kb.add(InlineKeyboardButton(text=f"{tx['monthly_btn']} — {plan['monthly_price']} USDT", callback_data=f"buy_mining_{plan_id}_monthly"))
    kb.add(InlineKeyboardButton(text=tx["back"], callback_data="mining_plans"))
    kb.adjust(1)
    return kb.as_markup()


@router.message(F.text.in_(["⛏️ Cloud Mining", "⛏️ Облачный майнинг", "⛏️ Cloud Mining"]))
async def show_mining(message: Message):
    lang = get_user_lang(message.from_user.id)
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    user = get_user(message.from_user.id)
    mining = get_user_mining(message.from_user.id)

    if mining:
        stats = get_mining_stats(message.from_user.id)
        expires = datetime.fromisoformat(stats["expires_at"])
        time_left = expires - datetime.now()
        hours_left = max(0, int(time_left.total_seconds() / 3600))
        minutes_left = max(0, int((time_left.total_seconds() % 3600) / 60))
        plan = next((p for p in MINING_PLANS if p["name"] == stats["plan_name"]), None)
        hourly = plan["hourly_usdt"] if plan else stats["hourly_income"]
        await message.answer(
            f"{tx['title']}\n\n{tx['active']}\n\n"
            f"{tx['plan_label']}: <b>{stats['plan_name']}</b>\n"
            f"{tx['hourly']}: <b>{hourly} USDT</b>\n"
            f"{tx['remaining']}: <b>{hours_left} {tx['hour']} {minutes_left} {tx['min']}</b>\n"
            f"{tx['total_earned']}: <b>{stats['total_earned']:.6f} USDT</b>\n\n"
            f"{tx['balance']}: <b>{user['balance']:.4f} USDT</b>",
            reply_markup=mining_main_kb(lang)
        )
    else:
        await message.answer(
            f"{tx['title']}\n\n{tx['inactive_desc']}\n\n"
            f"{tx['how']}\n"
            f"{tx['step1']}\n{tx['step2']}\n{tx['step3']}\n{tx['step4']}\n\n"
            f"{tx['balance']}: <b>{user['balance']:.4f} USDT</b>",
            reply_markup=mining_main_kb(lang)
        )


@router.callback_query(F.data == "mining_plans")
async def cb_mining_plans(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    text = f"{tx['plans_title']}\n\n"
    for p in MINING_PLANS:
        profit_d = round(p["daily_earn"] - p["daily_price"], 4)
        text += (
            f"<b>{p['name']}</b>\n"
            f"{tx['hourly_label']}: <b>{p['hourly_usdt']} USDT</b>\n"
            f"{tx['daily_earn']}: <b>{p['daily_earn']} USDT</b>\n"
            f"{tx['daily_price']}: {p['daily_price']} USDT\n"
            f"{tx['net_profit']}: +{profit_d} USDT\n\n"
        )
    await call.message.edit_text(text, reply_markup=plans_kb(lang))


@router.callback_query(F.data.startswith("plan_"))
async def cb_plan_select(call: CallbackQuery):
    plan_id = int(call.data.split("_")[1])
    plan = next((p for p in MINING_PLANS if p["id"] == plan_id), None)
    if not plan:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    lang = get_user_lang(call.from_user.id)
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    user = get_user(call.from_user.id)
    balance = user["balance"] if user else 0
    await call.message.edit_text(
        f"⛏️ <b>{plan['name']}</b>\n\n"
        f"{tx['hourly_label']}: <b>{plan['hourly_usdt']} USDT</b>\n\n"
        f"{tx['daily_btn']}:\n"
        f"   {tx['daily_price']}: {plan['daily_price']} USDT | {tx['daily_earn']}: {plan['daily_earn']} USDT\n"
        f"   {tx['net_profit']}: +{round(plan['daily_earn'] - plan['daily_price'], 4)} USDT\n\n"
        f"{tx['weekly_btn']}:\n"
        f"   {tx['daily_price']}: {plan['weekly_price']} USDT | {tx['daily_earn']}: {plan['weekly_earn']} USDT\n"
        f"   {tx['net_profit']}: +{round(plan['weekly_earn'] - plan['weekly_price'], 4)} USDT\n\n"
        f"{tx['monthly_btn']}:\n"
        f"   {tx['daily_price']}: {plan['monthly_price']} USDT | {tx['daily_earn']}: {plan['monthly_earn']} USDT\n"
        f"   {tx['net_profit']}: +{round(plan['monthly_earn'] - plan['monthly_price'], 4)} USDT\n\n"
        f"{tx['balance']}: <b>{balance:.4f} USDT</b>\n\n"
        f"{tx['select_duration']}",
        reply_markup=duration_kb(plan_id, lang)
    )


@router.callback_query(F.data.startswith("buy_mining_"))
async def cb_buy_mining(call: CallbackQuery):
    parts = call.data.split("_")
    plan_id = int(parts[2])
    duration = parts[3]
    plan = next((p for p in MINING_PLANS if p["id"] == plan_id), None)
    if not plan:
        await call.answer("❌ Topilmadi!", show_alert=True)
        return
    lang = get_user_lang(call.from_user.id)
    tx = MINING_TX.get(lang, MINING_TX["uz"])

    if duration == "daily":
        price, earn, dur_label = plan["daily_price"], plan["daily_earn"], tx["day"]
        expires = (datetime.now() + timedelta(days=1)).isoformat()
    elif duration == "weekly":
        price, earn, dur_label = plan["weekly_price"], plan["weekly_earn"], tx["week"]
        expires = (datetime.now() + timedelta(weeks=1)).isoformat()
    else:
        price, earn, dur_label = plan["monthly_price"], plan["monthly_earn"], tx["month"]
        expires = (datetime.now() + timedelta(days=30)).isoformat()

    user = get_user(call.from_user.id)
    balance = user["balance"] if user else 0

    if balance < price:
        await call.answer(tx["not_enough"].format(price=price, balance=balance), show_alert=True)
        return

    update_balance(call.from_user.id, -price)
    start_mining(call.from_user.id, plan_id, plan["name"], plan["hourly_usdt"], expires)

    await call.message.edit_text(
        f"{tx['started']}\n\n"
        f"{tx['plan_name']}: <b>{plan['name']}</b>\n"
        f"{tx['duration']}: <b>{dur_label}</b>\n"
        f"{tx['paid']}: <b>{price} USDT</b>\n\n"
        f"{tx['income']}:\n"
        f"{tx['hourly_income']}: {plan['hourly_usdt']} USDT\n"
        f"{tx['approx_total']}: {earn} USDT\n"
        f"{tx['net']}: +{round(earn - price, 4)} USDT\n\n"
        f"{tx['auto_msg']}"
    )
    await call.message.answer(tx["mining_active"], reply_markup=main_menu(lang))


@router.callback_query(F.data == "mining_stats")
async def cb_mining_stats(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    stats = get_mining_stats(call.from_user.id)
    user = get_user(call.from_user.id)

    if not stats:
        await call.answer(tx["no_mining"], show_alert=True)
        return

    expires = datetime.fromisoformat(stats["expires_at"])
    time_left = expires - datetime.now()
    hours_left = max(0, int(time_left.total_seconds() / 3600))
    minutes_left = max(0, int((time_left.total_seconds() % 3600) / 60))
    plan = next((p for p in MINING_PLANS if p["name"] == stats["plan_name"]), None)
    hourly = plan["hourly_usdt"] if plan else stats["hourly_income"]

    await call.message.edit_text(
        f"{tx['stats_title']}\n\n"
        f"⛏️ {tx['plan_label']}: <b>{stats['plan_name']}</b>\n"
        f"{tx['started_at']}: {stats['started_at'][:16]}\n"
        f"{tx['expires_at']}: {stats['expires_at'][:16]}\n"
        f"{tx['time_left']}: <b>{hours_left} {tx['hour']} {minutes_left} {tx['min']}</b>\n\n"
        f"{tx['hourly']}: <b>{hourly} USDT</b>\n"
        f"{tx['total_earned']}: <b>{stats['total_earned']:.6f} USDT</b>\n\n"
        f"{tx['balance']}: <b>{user['balance']:.4f} USDT</b>",
        reply_markup=mining_main_kb(lang)
    )


@router.callback_query(F.data == "mining_stop")
async def cb_mining_stop(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    mining = get_user_mining(call.from_user.id)
    if not mining:
        await call.answer(tx["no_mining"], show_alert=True)
        return
    stop_mining(call.from_user.id)
    await call.message.edit_text(tx["stopped"])
    await call.message.answer(tx["main_menu"], reply_markup=main_menu(lang))


@router.callback_query(F.data == "mining_back")
async def cb_mining_back(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = MINING_TX.get(lang, MINING_TX["uz"])
    user = get_user(call.from_user.id)
    await call.message.edit_text(
        f"{tx['title']}\n\n{tx['balance']}: <b>{user['balance']:.4f} USDT</b>",
        reply_markup=mining_main_kb(lang)
    )


async def mining_payout_loop(bot):
    while True:
        try:
            miners = get_all_active_miners()
            now = datetime.now()
            for miner in miners:
                tg_id, hourly_income, last_payout, expires_at = miner
                expires = datetime.fromisoformat(expires_at)
                if now > expires:
                    stop_mining(tg_id)
                    lang = get_user_lang(tg_id)
                    tx = MINING_TX.get(lang, MINING_TX["uz"])
                    try:
                        await bot.send_message(tg_id, tx["expired_msg"])
                    except Exception:
                        pass
                    continue
                last = datetime.fromisoformat(last_payout)
                hours_passed = (now - last).total_seconds() / 3600
                if hours_passed >= 1:
                    payout_hours = int(hours_passed)
                    amount_usdt = hourly_income * payout_hours
                    add_mining_earnings(tg_id, amount_usdt)
                    lang = get_user_lang(tg_id)
                    tx = MINING_TX.get(lang, MINING_TX["uz"])
                    try:
                        await bot.send_message(tg_id, tx["payout_msg"].format(amount=f"{amount_usdt:.6f}", hours=payout_hours))
                    except Exception:
                        pass
        except Exception:
            pass
        await asyncio.sleep(1800)