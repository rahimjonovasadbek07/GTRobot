from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user
from utils.mexc_copy_trading import get_top_tickers, get_top_gainers, get_top_losers, get_market_analysis
from utils.mexc_copy_leaders import (
    get_top_traders_formatted, get_trader_positions_formatted,
    format_trader_signal, monitor_copy_traders
)
from keyboards.kb import main_menu, cancel_keyboard

router = Router()
copy_tasks = {}
_cached_traders = []


def copy_main_kb(is_running=False):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="👑 Top 100 Treyderlar", callback_data="ct_top_traders"))
    kb.add(InlineKeyboardButton(text="📋 Treyderlar Pozitsiyasi", callback_data="ct_positions"))
    kb.add(InlineKeyboardButton(text="🔥 Top 20 Volume", callback_data="ct_top_volume"))
    kb.add(InlineKeyboardButton(text="📈 Top Gainers", callback_data="ct_gainers"))
    kb.add(InlineKeyboardButton(text="📉 Top Losers", callback_data="ct_losers"))
    kb.add(InlineKeyboardButton(text="🔍 Juftlik tahlili", callback_data="ct_analyze"))
    if is_running:
        kb.add(InlineKeyboardButton(text="⏹ Copy Tradingni to'xtatish", callback_data="ct_stop"))
    else:
        kb.add(InlineKeyboardButton(text="▶️ Avtomatik Copy Trading", callback_data="ct_auto_start"))
    kb.adjust(1)
    return kb.as_markup()


class CopyState(StatesGroup):
    waiting_amount = State()
    waiting_symbol = State()


@router.message(F.text == "📊 Copy Trading")
async def show_copy_trading(message: Message):
    from database.db import has_active_tariff
    from utils.lang import t
    from database.db import get_user as _get_user
    _u = _get_user(message.from_user.id)
    _lang = _u.get("lang", "uz") if _u else "uz"
    if not has_active_tariff(message.from_user.id):
        await message.answer(t(_lang, "no_tariff"))
        return
    user_id = message.from_user.id
    is_running = user_id in copy_tasks and not copy_tasks[user_id].done()
    status = "✅ Avtomatik nusxalash yoqiq" if is_running else "⏹ Avtomatik nusxalash o'chiq"
    await message.answer(
        f"📊 <b>Copy Trading</b>\n\n"
        f"⚙️ Holat: {status}\n\n"
        "Bo'limni tanlang:",
        reply_markup=copy_main_kb(is_running)
    )


# ===== TOP 100 TREYDERLAR (1-50) =====
@router.callback_query(F.data == "ct_top_traders")
async def cb_top_traders(call: CallbackQuery):
    global _cached_traders
    await call.answer("⏳ Olinmoqda...")
    await call.message.edit_text("⏳ <b>MEXC Top 100 treyderlar olinmoqda...</b>")

    traders = await get_top_traders_formatted(limit=100)
    _cached_traders = traders

    if not traders:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ct_top_traders"))
        kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
        kb.adjust(2)
        await call.message.edit_text("❌ Ma'lumot olishda xato.", reply_markup=kb.as_markup())
        return

    text = "👑 <b>MEXC Top 100 Treyderlar (1—50)</b>\n\n"
    for t in traders[:50]:
        i = t.get("rank", 0)
        roi = t.get("roi", 0)
        win = t.get("win_rate", 0)
        name = t.get("name", "Trader")
        followers = t.get("followers", 0)
        direction = t.get("direction", "")
        symbol = t.get("symbol", "")
        change = t.get("change", 0)
        dir_emoji = "🟢" if (direction == "LONG" or change >= 0) else "🔴"

        if symbol:
            cs = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
            text += f"{i}. {dir_emoji} <b>{symbol}</b> {cs} | ROI:{roi:.1f}% | Win:{win:.0f}%\n"
        else:
            medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}."))
            text += f"{medal} <b>{name}</b> | ROI:{roi:.1f}% | Win:{win:.0f}% | 👥{followers}\n"

    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="📄 51—100 ko'rish", callback_data="ct_top_traders_2"))
    kb.add(InlineKeyboardButton(text="📋 Pozitsiyalarni ko'rish", callback_data="ct_positions"))
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ct_top_traders"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


# ===== TOP 100 (51-100) =====
@router.callback_query(F.data == "ct_top_traders_2")
async def cb_top_traders_2(call: CallbackQuery):
    global _cached_traders
    await call.answer("⏳ Olinmoqda...")
    traders = _cached_traders if _cached_traders else await get_top_traders_formatted(limit=100)
    if len(traders) < 51:
        await call.answer("Ma'lumot yetarli emas!", show_alert=True)
        return

    text = "👑 <b>MEXC Top 100 Treyderlar (51—100)</b>\n\n"
    for t in traders[50:100]:
        i = t.get("rank", 0)
        roi = t.get("roi", 0)
        win = t.get("win_rate", 0)
        name = t.get("name", "Trader")
        followers = t.get("followers", 0)
        direction = t.get("direction", "")
        symbol = t.get("symbol", "")
        change = t.get("change", 0)
        dir_emoji = "🟢" if (direction == "LONG" or change >= 0) else "🔴"

        if symbol:
            cs = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
            text += f"{i}. {dir_emoji} <b>{symbol}</b> {cs} | ROI:{roi:.1f}% | Win:{win:.0f}%\n"
        else:
            text += f"{i}. <b>{name}</b> | ROI:{roi:.1f}% | Win:{win:.0f}% | 👥{followers}\n"

    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="⬅️ 1—50 ga qaytish", callback_data="ct_top_traders"))
    kb.add(InlineKeyboardButton(text="📋 Pozitsiyalarni ko'rish", callback_data="ct_positions"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


# ===== TREYDERLAR POZITSIYASI - KLIENT FORMATI =====
@router.callback_query(F.data == "ct_positions")
async def cb_positions(call: CallbackQuery):
    global _cached_traders
    await call.answer("⏳ Pozitsiyalar olinmoqda...")
    await call.message.edit_text("⏳ <b>Top treyderlar pozitsiyalari olinmoqda...</b>")

    traders = _cached_traders if _cached_traders else await get_top_traders_formatted(limit=100)
    positions = await get_trader_positions_formatted(traders, limit=10)

    if not positions:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ct_positions"))
        kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
        kb.adjust(2)
        await call.message.edit_text("❌ Pozitsiyalar topilmadi.", reply_markup=kb.as_markup())
        return

    # Har bir pozitsiyani alohida xabar sifatida yuborish
    await call.message.edit_text(f"📋 <b>Top 10 Treyderlar Pozitsiyasi</b>\n\n⏳ Yuborilmoqda...")

    for pos in positions[:10]:
        msg = format_trader_signal(pos)
        try:
            await call.message.answer(msg)
            await asyncio.sleep(0.3)
        except Exception:
            pass

    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ct_positions"))
    kb.add(InlineKeyboardButton(text="▶️ Avtomatik nusxalash", callback_data="ct_auto_start"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await call.message.answer("✅ <b>Barcha pozitsiyalar yuborildi!</b>", reply_markup=kb.as_markup())


# ===== AVTOMATIK COPY TRADING =====
@router.callback_query(F.data == "ct_auto_start")
async def cb_auto_start(call: CallbackQuery, state: FSMContext):
    user = get_user(call.from_user.id)
    if not user or not user.get("mexc_api_key"):
        await call.answer("❌ Avval MEXC API ulang! 🤖 Auto Trading bo'limidan.", show_alert=True)
        return
    if not user.get("tariff"):
        await call.answer("❌ Tarif kerak! 📋 Tarif bo'limidan sotib oling.", show_alert=True)
        return
    await call.message.edit_text(
        "▶️ <b>Avtomatik Copy Trading</b>\n\n"
        "Har bir trade uchun necha USDT?\n\n"
        "• Minimal: 5 USDT\n"
        "• Tavsiya: 10-50 USDT\n\n"
        "Miqdorni kiriting:"
    )
    await state.set_state(CopyState.waiting_amount)


@router.message(CopyState.waiting_amount)
async def process_copy_amount(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    try:
        amount = float(message.text.replace(",", "."))
        if amount < 5:
            await message.answer("❌ Minimal 5 USDT kiriting.")
            return
        user = get_user(message.from_user.id)
        user_id = message.from_user.id
        if user_id in copy_tasks and not copy_tasks[user_id].done():
            copy_tasks[user_id].cancel()
        task = asyncio.create_task(
            monitor_copy_traders(
                message.bot, user_id,
                user["mexc_api_key"], user["mexc_secret_key"],
                copy_amount=amount, top_n=20
            )
        )
        copy_tasks[user_id] = task
        await state.clear()
        await message.answer(
            f"✅ <b>Avtomatik Copy Trading yoqildi!</b>\n\n"
            f"💰 Har trade: <b>{amount} USDT</b>\n"
            f"👑 Top 20 treyderlar kuzatilmoqda\n"
            f"🔄 Har daqiqada yangilanadi\n\n"
            f"Signal kelganda klient formatida xabar olasiz! 📱",
            reply_markup=main_menu()
        )
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


@router.callback_query(F.data == "ct_stop")
async def cb_ct_stop(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id in copy_tasks and not copy_tasks[user_id].done():
        copy_tasks[user_id].cancel()
        del copy_tasks[user_id]
        await call.message.edit_text("⏹ <b>Copy Trading to'xtatildi!</b>", reply_markup=copy_main_kb(False))
    else:
        await call.answer("Allaqachon to'xtatilgan.", show_alert=True)


# ===== TOP VOLUME =====
@router.callback_query(F.data == "ct_top_volume")
async def cb_top_volume(call: CallbackQuery):
    await call.answer("⏳ Olinmoqda...")
    await call.message.edit_text("⏳ Top juftliklar olinmoqda...")
    tickers = await get_top_tickers(20)
    if not tickers:
        await call.message.edit_text("❌ Xato.", reply_markup=copy_main_kb())
        return
    text = "🔥 <b>MEXC Top 20 — Savdo Hajmi</b>\n\n"
    for i, t in enumerate(tickers, 1):
        ce = "📈" if t['change'] >= 0 else "📉"
        cs = f"+{t['change']:.2f}%" if t['change'] >= 0 else f"{t['change']:.2f}%"
        v = t['volume']
        vs = f"${v/1_000_000:.1f}M" if v > 1_000_000 else f"${v/1000:.1f}K"
        text += f"{i}. <b>{t['symbol']}</b> — ${t['price']:.4f} {ce}{cs} | {vs}\n"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ct_top_volume"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


# ===== GAINERS =====
@router.callback_query(F.data == "ct_gainers")
async def cb_gainers(call: CallbackQuery):
    await call.answer("⏳ Olinmoqda...")
    await call.message.edit_text("⏳ Top gainers olinmoqda...")
    gainers = await get_top_gainers(15)
    if not gainers:
        await call.message.edit_text("❌ Xato.", reply_markup=copy_main_kb())
        return
    text = "📈 <b>MEXC Top Gainers (24h)</b>\n\n"
    for i, t in enumerate(gainers, 1):
        text += f"{i}. <b>{t['symbol']}</b> — ${t['price']:.6f} 🚀 +{t['change']:.2f}%\n"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ct_gainers"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


# ===== LOSERS =====
@router.callback_query(F.data == "ct_losers")
async def cb_losers(call: CallbackQuery):
    await call.answer("⏳ Olinmoqda...")
    await call.message.edit_text("⏳ Top losers olinmoqda...")
    losers = await get_top_losers(15)
    if not losers:
        await call.message.edit_text("❌ Xato.", reply_markup=copy_main_kb())
        return
    text = "📉 <b>MEXC Top Losers (24h)</b>\n\n"
    for i, t in enumerate(losers, 1):
        text += f"{i}. <b>{t['symbol']}</b> — ${t['price']:.6f} 💥 {t['change']:.2f}%\n"
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="ct_losers"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


# ===== TAHLIL =====
@router.callback_query(F.data == "ct_analyze")
async def cb_analyze(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "🔍 <b>Juftlik tahlili</b>\n\n"
        "Juftlikni yozing:\nMisol: <code>BTC/USDT</code>"
    )
    await state.set_state(CopyState.waiting_symbol)


@router.message(CopyState.waiting_symbol)
async def process_analyze(message: Message, state: FSMContext):
    symbol = message.text.strip().upper()
    if "/" not in symbol:
        symbol += "/USDT"
    await message.answer(f"⏳ {symbol} tahlil qilinmoqda...")
    result = await get_market_analysis(symbol)
    if not result:
        await message.answer("❌ Topilmadi. To'g'ri format: BTC/USDT")
        await state.clear()
        return
    change = result["change_24h"]
    cs = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
    ce = "📈" if change >= 0 else "📉"
    rsi = result["rsi"]
    rs = "Oversold 🟢" if rsi < 30 else ("Overbought 🔴" if rsi > 70 else "Normal ⚪")
    v = result["volume_24h"]
    vs = f"${v/1_000_000:.2f}M" if v > 1_000_000 else f"${v/1000:.2f}K"
    text = (
        f"🔍 <b>{result['symbol']} Tahlil</b>\n\n"
        f"💵 Narx: <b>${result['price']:.6f}</b>\n"
        f"{ce} 24h: <b>{cs}</b>\n"
        f"📊 Hajm: {vs}\n"
        f"⬆️ Max: ${result['high_24h']:.6f}\n"
        f"⬇️ Min: ${result['low_24h']:.6f}\n\n"
        f"📉 RSI: <b>{rsi}</b> — {rs}\n"
        f"📈 Trend: <b>{result['trend']}</b>\n\n"
        f"🎯 Signal: <b>{result['signal']}</b>"
    )
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"refresh_analyze_{symbol}"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await message.answer(text, reply_markup=kb.as_markup())
    await state.clear()


@router.callback_query(F.data.startswith("refresh_analyze_"))
async def cb_refresh(call: CallbackQuery):
    symbol = call.data.replace("refresh_analyze_", "")
    await call.answer("⏳ Yangilanmoqda...")
    result = await get_market_analysis(symbol)
    if not result:
        await call.answer("❌ Xato!", show_alert=True)
        return
    change = result["change_24h"]
    cs = f"+{change:.2f}%" if change >= 0 else f"{change:.2f}%"
    ce = "📈" if change >= 0 else "📉"
    rsi = result["rsi"]
    rs = "Oversold 🟢" if rsi < 30 else ("Overbought 🔴" if rsi > 70 else "Normal ⚪")
    text = (
        f"🔍 <b>{result['symbol']} Tahlil</b>\n\n"
        f"💵 Narx: <b>${result['price']:.6f}</b>\n"
        f"{ce} 24h: <b>{cs}</b>\n"
        f"📉 RSI: <b>{rsi}</b> — {rs}\n"
        f"📈 Trend: <b>{result['trend']}</b>\n\n"
        f"🎯 Signal: <b>{result['signal']}</b>"
    )
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"refresh_analyze_{symbol}"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="ct_back"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "ct_back")
async def cb_back(call: CallbackQuery):
    user_id = call.from_user.id
    is_running = user_id in copy_tasks and not copy_tasks[user_id].done()
    await call.message.edit_text(
        "📊 <b>Copy Trading</b>\n\nBo'limni tanlang:",
        reply_markup=copy_main_kb(is_running)
    )
