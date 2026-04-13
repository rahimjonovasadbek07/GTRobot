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

# Arbitraj monitorlari
arbitrage_tasks = {}


def arbitrage_main_kb(is_running: bool = False):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔍 Arbitraj izlash", callback_data="arb_find"))
    if is_running:
        kb.add(InlineKeyboardButton(text="⏹ Monitorni to'xtatish", callback_data="arb_stop"))
    else:
        kb.add(InlineKeyboardButton(text="▶️ Avtomatik monitor", callback_data="arb_start"))
    kb.add(InlineKeyboardButton(text="ℹ️ Nima bu?", callback_data="arb_info"))
    kb.adjust(1)
    return kb.as_markup()


class ArbState(StatesGroup):
    waiting_amount = State()
    waiting_min_profit = State()


@router.message(F.text == "🔺 Arbitraj")
async def show_arbitrage(message: Message):
    user_id = message.from_user.id
    is_running = user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done()
    
    status = "✅ Monitor ishlayapti" if is_running else "⏹ Monitor to'xtatilgan"
    
    await message.answer(
        f"🔺 <b>Uchburchak Arbitraj</b>\n\n"
        f"Bot MEXC birjasida avtomatik ravishda arbitraj imkoniyatlarini qidiradi.\n\n"
        f"📍 Misol: USDT → BTC → ETH → USDT\n"
        f"💰 Foyda: 0.3% — 2% har trade\n\n"
        f"⚙️ Holat: {status}",
        reply_markup=arbitrage_main_kb(is_running)
    )


@router.callback_query(F.data == "arb_info")
async def cb_arb_info(call: CallbackQuery):
    await call.message.edit_text(
        "ℹ️ <b>Uchburchak Arbitraj nima?</b>\n\n"
        "Bu bir birja ichida 3 ta juftlik orqali foyda qilish:\n\n"
        "<b>Misol:</b>\n"
        "1️⃣ 100 USDT → BTC sotib olish\n"
        "2️⃣ BTC → ETH almashtirish\n"
        "3️⃣ ETH → USDT sotish\n"
        "💰 Natija: 100.5 USDT (+0.5%)\n\n"
        "<b>Afzalliklari:</b>\n"
        "✅ Bozor yo'nalishiga bog'liq emas\n"
        "✅ Juda tez (sekundlar ichida)\n"
        "✅ Kichik risk\n\n"
        "<b>Kamchiliklari:</b>\n"
        "⚠️ Komissiya xarajati bor (0.1% × 3)\n"
        "⚠️ Narx o'zgarib ketishi mumkin\n"
        "⚠️ Katta miqdor kerak (min 10 USDT)",
        reply_markup=arbitrage_main_kb()
    )


@router.callback_query(F.data == "arb_find")
async def cb_arb_find(call: CallbackQuery):
    await call.answer("⏳ Arbitraj izlanmoqda, kuting...")
    await call.message.edit_text("🔍 <b>MEXC da arbitraj imkoniyatlari izlanmoqda...</b>\n\n⏳ 10-30 soniya kuting...")
    
    opportunities = await find_triangular_opportunities(min_profit=0.1)
    
    if not opportunities:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="🔄 Qayta izlash", callback_data="arb_find"))
        kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="arb_back"))
        kb.adjust(2)
        await call.message.edit_text(
            "😔 <b>Hozircha foydali arbitraj topilmadi</b>\n\n"
            "Bu normal holat — bozor muvozanatda.\n"
            "Biroz kutib qayta izlang.",
            reply_markup=kb.as_markup()
        )
        return
    
    text = f"✅ <b>{len(opportunities)} ta arbitraj topildi!</b>\n\n"
    for i, opp in enumerate(opportunities[:5], 1):
        text += (
            f"{i}. 📍 {opp['path']}\n"
            f"   💰 Foyda: <b>+{opp['profit_pct']}%</b> (1 USDT uchun)\n\n"
        )
    
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Qayta izlash", callback_data="arb_find"))
    kb.add(InlineKeyboardButton(text="▶️ Avtomatik bajarish", callback_data="arb_start"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="arb_back"))
    kb.adjust(2)
    
    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "arb_start")
async def cb_arb_start(call: CallbackQuery, state: FSMContext):
    user = get_user(call.from_user.id)
    
    if not user or not user.get('mexc_api_key'):
        await call.answer("❌ Avval MEXC API kalitini ulang!", show_alert=True)
        return
    
    if not user.get('tariff'):
        await call.answer("❌ Tarif kerak!", show_alert=True)
        return
    
    await call.message.edit_text(
        "💰 <b>Arbitraj uchun miqdor</b>\n\n"
        "Har bir arbitraj uchun necha USDT ishlatsin?\n\n"
        "Minimal: 10 USDT\n"
        "Tavsiya: 50-100 USDT\n\n"
        "Miqdorni kiriting:"
    )
    await state.set_state(ArbState.waiting_amount)


@router.message(ArbState.waiting_amount)
async def process_arb_amount(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    
    try:
        amount = float(message.text.replace(",", "."))
        if amount < 10:
            await message.answer("❌ Minimal 10 USDT kiriting.")
            return
        
        await state.update_data(arb_amount=amount)
        await message.answer(
            f"✅ Miqdor: <b>{amount} USDT</b>\n\n"
            "📊 Minimal foyda foizini kiriting:\n\n"
            "Tavsiya: <b>0.3</b>\n"
            "(0.3 = 0.3% foydadan past bo'lsa bajarmaydi)"
        )
        await state.set_state(ArbState.waiting_min_profit)
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


@router.message(ArbState.waiting_min_profit)
async def process_arb_min_profit(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    
    try:
        min_profit = float(message.text.replace(",", "."))
        if min_profit < 0.1 or min_profit > 10:
            await message.answer("❌ 0.1 dan 10 gacha kiriting.")
            return
        
        data = await state.get_data()
        amount = data['arb_amount']
        user = get_user(message.from_user.id)
        
        await state.clear()
        
        # Eski taskni to'xtatish
        user_id = message.from_user.id
        if user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done():
            arbitrage_tasks[user_id].cancel()
        
        # Yangi task yaratish
        task = asyncio.create_task(
            monitor_arbitrage_loop(
                message.bot, user_id,
                user['mexc_api_key'], user['mexc_secret_key'],
                amount, min_profit
            )
        )
        arbitrage_tasks[user_id] = task
        
        await message.answer(
            f"✅ <b>Arbitraj monitor ishga tushdi!</b>\n\n"
            f"💰 Miqdor: {amount} USDT\n"
            f"📊 Min foyda: {min_profit}%\n"
            f"🔄 Har 30 soniyada tekshiradi\n\n"
            f"Arbitraj topilganda xabar olasiz!",
            reply_markup=main_menu()
        )
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


@router.callback_query(F.data == "arb_stop")
async def cb_arb_stop(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done():
        arbitrage_tasks[user_id].cancel()
        del arbitrage_tasks[user_id]
        await call.message.edit_text(
            "⏹ <b>Arbitraj monitor to'xtatildi!</b>",
            reply_markup=arbitrage_main_kb(False)
        )
    else:
        await call.answer("Monitor allaqachon to'xtatilgan.", show_alert=True)


@router.callback_query(F.data == "arb_back")
async def cb_arb_back(call: CallbackQuery):
    user_id = call.from_user.id
    is_running = user_id in arbitrage_tasks and not arbitrage_tasks[user_id].done()
    await call.message.edit_text(
        f"🔺 <b>Uchburchak Arbitraj</b>\n\nBo'limni tanlang:",
        reply_markup=arbitrage_main_kb(is_running)
    )
