from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user, set_bot_active
from utils.arbitrage import find_triangular_opportunities, monitor_arbitrage_loop
from keyboards.kb import main_menu, cancel_keyboard

router = Router()
arbitrage_tasks = {}

ARB_TX = {
    "uz": {
        "title": "🔺 <b>Uchburchak Arbitraj</b>",
        "desc": "Bot MEXC birjasida avtomatik ravishda arbitraj imkoniyatlarini qidiradi.",
        "example": "📍 Misol: USDT → BTC → ETH → USDT",
        "profit": "💰 Foyda: 0.3% — 2% har trade",
        "status": "⚙️ Holat",
        "running": "✅ Monitor ishlayapti",
        "stopped": "⏹ Monitor to'xtatilgan",
        "btn_find": "🔍 Arbitraj izlash",
        "btn_stop": "⏹ Monitorni to'xtatish",
        "btn_start": "▶️ Avtomatik monitor",
        "btn_info": "ℹ️ Nima bu?",
        "info_title": "ℹ️ <b>Uchburchak Arbitraj nima?</b>",
        "info_desc": "Bu bir birja ichida 3 ta juftlik orqali foyda qilish:",
        "info_ex": "<b>Misol:</b>\n1️⃣ 100 USDT → BTC sotib olish\n2️⃣ BTC → ETH almashtirish\n3️⃣ ETH → USDT sotish\n💰 Natija: 100.5 USDT (+0.5%)",
        "pros": "<b>Afzalliklari:</b>\n✅ Bozor yo'nalishiga bog'liq emas\n✅ Juda tez (sekundlar ichida)\n✅ Kichik risk",
        "cons": "<b>Kamchiliklari:</b>\n⚠️ Komissiya xarajati bor (0.1% × 3)\n⚠️ Narx o'zgarib ketishi mumkin\n⚠️ Katta miqdor kerak (min 10 USDT)",
        "searching": "🔍 <b>MEXC da arbitraj imkoniyatlari izlanmoqda...</b>\n\n⏳ 10-30 soniya kuting...",
        "wait": "⏳ Arbitraj izlanmoqda, kuting...",
        "not_found": "😔 <b>Hozircha foydali arbitraj topilmadi</b>\n\nBu normal holat — bozor muvozanatda.\nBiroz kutib qayta izlang.",
        "found": "✅ <b>{n} ta arbitraj topildi!</b>",
        "path": "📍",
        "profit_label": "💰 Foyda",
        "btn_retry": "🔄 Qayta izlash",
        "btn_auto": "▶️ Avtomatik bajarish",
        "btn_back": "🔙 Orqaga",
        "need_api": "❌ Avval MEXC API kalitini ulang!",
        "need_tariff": "❌ Tarif kerak!",
        "amount_title": "💰 <b>Arbitraj uchun miqdor</b>",
        "amount_desc": "Har bir arbitraj uchun necha USDT ishlatsin?\n\nMinimal: 10 USDT\nTavsiya: 50-100 USDT\n\nMiqdorni kiriting:",
        "min_err": "❌ Minimal 10 USDT kiriting.",
        "amount_ok": "✅ Miqdor: <b>{amount} USDT</b>",
        "profit_ask": "📊 Minimal foyda foizini kiriting:\n\nTavsiya: <b>0.3</b>\n(0.3 = 0.3% foydadan past bo'lsa bajarmaydi)",
        "profit_err": "❌ 0.1 dan 10 gacha kiriting.",
        "monitor_started": "✅ <b>Arbitraj monitor ishga tushdi!</b>\n\n💰 Miqdor: {amount} USDT\n📊 Min foyda: {profit}%\n🔄 Har 30 soniyada tekshiradi\n\nArbitraj topilganda xabar olasiz!",
        "monitor_stopped": "⏹ <b>Arbitraj monitor to'xtatildi!</b>",
        "already_stopped": "Monitor allaqachon to'xtatilgan.",
        "num_err": "❌ Raqam kiriting.",
        "cancelled": "❌ Bekor qilindi.",
    },
    "ru": {
        "title": "🔺 <b>Треугольный Арбитраж</b>",
        "desc": "Бот автоматически ищет арбитражные возможности на бирже MEXC.",
        "example": "📍 Пример: USDT → BTC → ETH → USDT",
        "profit": "💰 Прибыль: 0.3% — 2% за сделку",
        "status": "⚙️ Статус",
        "running": "✅ Монитор работает",
        "stopped": "⏹ Монитор остановлен",
        "btn_find": "🔍 Найти арбитраж",
        "btn_stop": "⏹ Остановить монитор",
        "btn_start": "▶️ Автоматический мониторинг",
        "btn_info": "ℹ️ Что это?",
        "info_title": "ℹ️ <b>Что такое треугольный арбитраж?</b>",
        "info_desc": "Получение прибыли через 3 пары на одной бирже:",
        "info_ex": "<b>Пример:</b>\n1️⃣ 100 USDT → купить BTC\n2️⃣ BTC → обменять на ETH\n3️⃣ ETH → продать за USDT\n💰 Итог: 100.5 USDT (+0.5%)",
        "pros": "<b>Преимущества:</b>\n✅ Не зависит от направления рынка\n✅ Очень быстро (секунды)\n✅ Низкий риск",
        "cons": "<b>Недостатки:</b>\n⚠️ Есть комиссия (0.1% × 3)\n⚠️ Цена может измениться\n⚠️ Нужна большая сумма (мин 10 USDT)",
        "searching": "🔍 <b>Поиск арбитражных возможностей на MEXC...</b>\n\n⏳ Подождите 10-30 секунд...",
        "wait": "⏳ Ищем арбитраж, подождите...",
        "not_found": "😔 <b>Выгодный арбитраж не найден</b>\n\nЭто нормально — рынок сбалансирован.\nПодождите и попробуйте снова.",
        "found": "✅ <b>Найдено {n} арбитражных возможностей!</b>",
        "path": "📍",
        "profit_label": "💰 Прибыль",
        "btn_retry": "🔄 Искать снова",
        "btn_auto": "▶️ Запустить автоматически",
        "btn_back": "🔙 Назад",
        "need_api": "❌ Сначала подключите API ключ MEXC!",
        "need_tariff": "❌ Требуется тариф!",
        "amount_title": "💰 <b>Сумма для арбитража</b>",
        "amount_desc": "Сколько USDT использовать для каждого арбитража?\n\nМинимум: 10 USDT\nРекомендуется: 50-100 USDT\n\nВведите сумму:",
        "min_err": "❌ Введите минимум 10 USDT.",
        "amount_ok": "✅ Сумма: <b>{amount} USDT</b>",
        "profit_ask": "📊 Введите минимальный % прибыли:\n\nРекомендуется: <b>0.3</b>",
        "profit_err": "❌ Введите от 0.1 до 10.",
        "monitor_started": "✅ <b>Арбитражный монитор запущен!</b>\n\n💰 Сумма: {amount} USDT\n📊 Мин. прибыль: {profit}%\n🔄 Проверяет каждые 30 секунд\n\nПолучите уведомление при нахождении арбитража!",
        "monitor_stopped": "⏹ <b>Арбитражный монитор остановлен!</b>",
        "already_stopped": "Монитор уже остановлен.",
        "num_err": "❌ Введите число.",
        "cancelled": "❌ Отменено.",
    },
    "en": {
        "title": "🔺 <b>Triangular Arbitrage</b>",
        "desc": "Bot automatically searches for arbitrage opportunities on MEXC.",
        "example": "📍 Example: USDT → BTC → ETH → USDT",
        "profit": "💰 Profit: 0.3% — 2% per trade",
        "status": "⚙️ Status",
        "running": "✅ Monitor running",
        "stopped": "⏹ Monitor stopped",
        "btn_find": "🔍 Find arbitrage",
        "btn_stop": "⏹ Stop monitor",
        "btn_start": "▶️ Auto monitor",
        "btn_info": "ℹ️ What is this?",
        "info_title": "ℹ️ <b>What is triangular arbitrage?</b>",
        "info_desc": "Profiting through 3 pairs on one exchange:",
        "info_ex": "<b>Example:</b>\n1️⃣ 100 USDT → Buy BTC\n2️⃣ BTC → Swap to ETH\n3️⃣ ETH → Sell for USDT\n💰 Result: 100.5 USDT (+0.5%)",
        "pros": "<b>Advantages:</b>\n✅ Not dependent on market direction\n✅ Very fast (seconds)\n✅ Low risk",
        "cons": "<b>Disadvantages:</b>\n⚠️ Commission fee (0.1% × 3)\n⚠️ Price may change quickly\n⚠️ Larger amount needed (min 10 USDT)",
        "searching": "🔍 <b>Searching for arbitrage opportunities on MEXC...</b>\n\n⏳ Please wait 10-30 seconds...",
        "wait": "⏳ Searching for arbitrage, please wait...",
        "not_found": "😔 <b>No profitable arbitrage found</b>\n\nThis is normal — market is balanced.\nWait a bit and try again.",
        "found": "✅ <b>Found {n} arbitrage opportunities!</b>",
        "path": "📍",
        "profit_label": "💰 Profit",
        "btn_retry": "🔄 Search again",
        "btn_auto": "▶️ Run automatically",
        "btn_back": "🔙 Back",
        "need_api": "❌ Please connect your MEXC API key first!",
        "need_tariff": "❌ Tariff required!",
        "amount_title": "💰 <b>Arbitrage amount</b>",
        "amount_desc": "How much USDT to use per arbitrage?\n\nMinimum: 10 USDT\nRecommended: 50-100 USDT\n\nEnter amount:",
        "min_err": "❌ Minimum 10 USDT required.",
        "amount_ok": "✅ Amount: <b>{amount} USDT</b>",
        "profit_ask": "📊 Enter minimum profit %:\n\nRecommended: <b>0.3</b>",
        "profit_err": "❌ Enter between 0.1 and 10.",
        "monitor_started": "✅ <b>Arbitrage monitor started!</b>\n\n💰 Amount: {amount} USDT\n📊 Min profit: {profit}%\n🔄 Checks every 30 seconds\n\nYou'll be notified when arbitrage is found!",
        "monitor_stopped": "⏹ <b>Arbitrage monitor stopped!</b>",
        "already_stopped": "Monitor is already stopped.",
        "num_err": "❌ Please enter a number.",
        "cancelled": "❌ Cancelled.",
    },
}


def get_user_lang(tg_id):
    from database.db import get_user
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


def arbitrage_main_kb(lang="uz", is_running=False):
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=tx["btn_find"], callback_data="arb_find"))
    if is_running:
        kb.add(InlineKeyboardButton(text=tx["btn_stop"], callback_data="arb_stop"))
    else:
        kb.add(InlineKeyboardButton(text=tx["btn_start"], callback_data="arb_start"))
    kb.add(InlineKeyboardButton(text=tx["btn_info"], callback_data="arb_info"))
    kb.adjust(1)
    return kb.as_markup()


class ArbState(StatesGroup):
    waiting_amount = State()
    waiting_min_profit = State()


@router.message(F.text.in_(["🔺 Arbitraj", "🔺 Арбитраж", "🔺 Arbitrage"]))
async def show_arbitrage(message: Message):
    lang = get_user_lang(message.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    user_id = message.from_user.id
    is_running = user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done()
    status = tx["running"] if is_running else tx["stopped"]
    await message.answer(
        f"{tx['title']}\n\n{tx['desc']}\n\n{tx['example']}\n{tx['profit']}\n\n{tx['status']}: {status}",
        reply_markup=arbitrage_main_kb(lang, is_running)
    )


@router.callback_query(F.data == "arb_info")
async def cb_arb_info(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    await call.message.edit_text(
        f"{tx['info_title']}\n\n{tx['info_desc']}\n\n{tx['info_ex']}\n\n{tx['pros']}\n\n{tx['cons']}",
        reply_markup=arbitrage_main_kb(lang)
    )


@router.callback_query(F.data == "arb_find")
async def cb_arb_find(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    await call.answer(tx["wait"])
    await call.message.edit_text(tx["searching"])
    opportunities = await find_triangular_opportunities(min_profit=0.1)
    if not opportunities:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text=tx["btn_retry"], callback_data="arb_find"))
        kb.add(InlineKeyboardButton(text=tx["btn_back"], callback_data="arb_back"))
        kb.adjust(2)
        await call.message.edit_text(tx["not_found"], reply_markup=kb.as_markup())
        return
    text = f"{tx['found'].format(n=len(opportunities))}\n\n"
    for i, opp in enumerate(opportunities[:5], 1):
        text += f"{i}. {tx['path']} {opp['path']}\n   {tx['profit_label']}: <b>+{opp['profit_pct']}%</b>\n\n"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=tx["btn_retry"], callback_data="arb_find"))
    kb.add(InlineKeyboardButton(text=tx["btn_auto"], callback_data="arb_start"))
    kb.add(InlineKeyboardButton(text=tx["btn_back"], callback_data="arb_back"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "arb_start")
async def cb_arb_start(call: CallbackQuery, state: FSMContext):
    lang = get_user_lang(call.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    user = get_user(call.from_user.id)
    if not user or not user.get('mexc_api_key'):
        await call.answer(tx["need_api"], show_alert=True)
        return
    if not user.get('tariff'):
        await call.answer(tx["need_tariff"], show_alert=True)
        return
    await call.message.edit_text(f"{tx['amount_title']}\n\n{tx['amount_desc']}")
    await state.set_state(ArbState.waiting_amount)


@router.message(ArbState.waiting_amount)
async def process_arb_amount(message: Message, state: FSMContext):
    from keyboards.kb import CANCEL_TEXTS
    lang = get_user_lang(message.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    if message.text in CANCEL_TEXTS:
        await state.clear()
        await message.answer(tx["cancelled"], reply_markup=main_menu(lang))
        return
    try:
        amount = float(message.text.replace(",", "."))
        if amount < 10:
            await message.answer(tx["min_err"])
            return
        await state.update_data(arb_amount=amount)
        await message.answer(f"{tx['amount_ok'].format(amount=amount)}\n\n{tx['profit_ask']}")
        await state.set_state(ArbState.waiting_min_profit)
    except ValueError:
        await message.answer(tx["num_err"])


@router.message(ArbState.waiting_min_profit)
async def process_arb_min_profit(message: Message, state: FSMContext):
    from keyboards.kb import CANCEL_TEXTS
    lang = get_user_lang(message.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    if message.text in CANCEL_TEXTS:
        await state.clear()
        await message.answer(tx["cancelled"], reply_markup=main_menu(lang))
        return
    try:
        min_profit = float(message.text.replace(",", "."))
        if min_profit < 0.1 or min_profit > 10:
            await message.answer(tx["profit_err"])
            return
        data = await state.get_data()
        amount = data['arb_amount']
        user = get_user(message.from_user.id)
        await state.clear()
        user_id = message.from_user.id
        if user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done():
            arbitrage_tasks[user_id].cancel()
        task = asyncio.create_task(
            monitor_arbitrage_loop(message.bot, user_id, user['mexc_api_key'], user['mexc_secret_key'], amount, min_profit)
        )
        arbitrage_tasks[user_id] = task
        await message.answer(
            tx["monitor_started"].format(amount=amount, profit=min_profit),
            reply_markup=main_menu(lang)
        )
    except ValueError:
        await message.answer(tx["num_err"])


@router.callback_query(F.data == "arb_stop")
async def cb_arb_stop(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    user_id = call.from_user.id
    if user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done():
        arbitrage_tasks[user_id].cancel()
        del arbitrage_tasks[user_id]
        await call.message.edit_text(tx["monitor_stopped"], reply_markup=arbitrage_main_kb(lang, False))
    else:
        await call.answer(tx["already_stopped"], show_alert=True)


@router.callback_query(F.data == "arb_back")
async def cb_arb_back(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = ARB_TX.get(lang, ARB_TX["uz"])
    user_id = call.from_user.id
    is_running = user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done()
    status = tx["running"] if is_running else tx["stopped"]
    await call.message.edit_text(
        f"{tx['title']}\n\n{tx['status']}: {status}",
        reply_markup=arbitrage_main_kb(lang, is_running)
    )