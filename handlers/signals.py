from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    save_signal, get_active_signals, get_all_signals,
    close_signal, get_all_users, get_user
)
from keyboards.kb import signal_keyboard, cancel_keyboard, main_menu, admin_menu
from utils.mexc_api import place_spot_order, get_market_price
from config import ADMIN_IDS

router = Router()

SIG_TX = {
    "uz": {
        "no_signals": "📡 <b>Faol signallar yo'q</b>\n\nAdmin signal yuborganda bu yerda ko'rinadi.",
        "signals_title": "📡 <b>Faol signallar ({n} ta)</b>",
        "entry": "📥 Kirish", "tp": "🎯 TP", "sl": "🛑 SL",
    },
    "ru": {
        "no_signals": "📡 <b>Нет активных сигналов</b>\n\nКогда админ пришлёт сигнал, он появится здесь.",
        "signals_title": "📡 <b>Активные сигналы ({n} шт.)</b>",
        "entry": "📥 Вход", "tp": "🎯 TP", "sl": "🛑 SL",
    },
    "en": {
        "no_signals": "📡 <b>No active signals</b>\n\nSignals from admin will appear here.",
        "signals_title": "📡 <b>Active signals ({n})</b>",
        "entry": "📥 Entry", "tp": "🎯 TP", "sl": "🛑 SL",
    },
}


def get_user_lang(tg_id):
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


def format_signal_message(symbol, direction, leverage, entry, tp, sl, trader_name=None):
    if trader_name is None:
        from database.db import get_bot_settings
        s = get_bot_settings()
        trader_name = s.get("signal_name", "GTRobot Signal")
    dir_emoji = "🟢" if direction == "LONG" else "🔴"
    formatted = f"{symbol[:-4]}/USDT" if symbol.endswith("USDT") else symbol
    msg = (
        f"📡 <b>Signal!</b>\n\n"
        f"👤 <b>Treder: {trader_name}</b>\n\n"
        f"{dir_emoji} <b>{formatted}</b>\n"
        f"{'LONG' if direction == 'LONG' else 'SHORT'}: {entry}\n"
        f"TP: {tp}\nSL: {sl}\n"
    )
    if leverage > 1:
        msg += f"⚡️ Leverage: x{leverage}\n"
    return msg


@router.message(F.text.in_(["📡 Signallar", "📡 Сигналы", "📡 Signals"]))
async def show_signals(message: Message):
    lang = get_user_lang(message.from_user.id)
    tx = SIG_TX.get(lang, SIG_TX["uz"])
    signals = get_active_signals()
    if not signals:
        await message.answer(tx["no_signals"])
        return
    text = f"{tx['signals_title'].format(n=len(signals))}\n\n"
    for s in signals:
        sid, admin_id, symbol, direction, leverage, entry, tp, sl, status, msg, created = s
        dir_emoji = "🟢" if direction == "LONG" else "🔴"
        formatted = f"{symbol[:-4]}/USDT" if symbol.endswith("USDT") else symbol
        text += (
            f"{dir_emoji} <b>{formatted}</b> {direction}\n"
            f"{tx['entry']}: {entry} | {tx['tp']}: {tp} | {tx['sl']}: {sl}\n"
            f"🕐 {created[:16]}\n\n"
        )
    await message.answer(text)


@router.message(F.text == "📡 Signal yuborish")
async def admin_send_signal(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    await message.answer(
        "📡 <b>Signal yuborish</b>\n\n"
        "Quyidagi formatda yozing:\n\n"
        "<code>BTCUSDT LONG 10 50000 52000 49000</code>\n\n"
        "• <b>BTCUSDT</b> — juftlik\n"
        "• <b>LONG</b> yoki <b>SHORT</b> — yo'nalish\n"
        "• <b>10</b> — leverage\n"
        "• <b>50000</b> — kirish narxi\n"
        "• <b>52000</b> — TP\n"
        "• <b>49000</b> — SL",
        reply_markup=cancel_keyboard()
    )
    from aiogram.fsm.state import State, StatesGroup
    await state.set_state(SignalState.waiting_signal)


class SignalState(StatesGroup):
    waiting_signal = State()


@router.message(SignalState.waiting_signal)
async def process_signal(message: Message, state: FSMContext):
    from keyboards.kb import CANCEL_TEXTS
    if message.text in CANCEL_TEXTS:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return
    try:
        parts = message.text.strip().upper().split()
        if len(parts) != 6:
            raise ValueError("Format noto'g'ri")
        symbol, direction = parts[0], parts[1]
        leverage, entry, tp, sl = int(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])
        if direction not in ["LONG", "SHORT"]:
            raise ValueError
    except Exception:
        await message.answer("❌ <b>Noto'g'ri format!</b>\n\nTo'g'ri: <code>BTCUSDT LONG 10 50000 52000 49000</code>")
        return

    signal_id = save_signal(message.from_user.id, symbol, direction, leverage, entry, tp, sl, message.text)
    signal_msg = format_signal_message(symbol, direction, leverage, entry, tp, sl)
    all_users = get_all_users()
    sent = 0
    for u in all_users:
        try:
            await message.bot.send_message(u[0], signal_msg)
            sent += 1
        except Exception:
            pass

    traded = 0
    from database.db import get_users_with_active_bot
    active_users = get_users_with_active_bot()
    for user in active_users:
        tg_id, api_key, secret_key = user
        if not api_key:
            continue
        try:
            price_result = await get_market_price(symbol)
            if not price_result["success"]:
                continue
            side = "BUY" if direction == "LONG" else "SELL"
            qty = round(10 / price_result["price"], 6)
            if qty > 0:
                result = await place_spot_order(api_key, secret_key, symbol, side, qty)
                if result["success"]:
                    traded += 1
                    try:
                        await message.bot.send_message(
                            tg_id,
                            f"✅ <b>Trade ochildi!</b>\n\n{'🟢' if side == 'BUY' else '🔴'} {symbol} {side}\n📋 Order: {result['order'].get('orderId', '?')}"
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    await state.clear()
    await message.answer(
        f"✅ <b>Signal yuborildi!</b>\n\n📨 Xabar: {sent} ta\n🤖 Avtomatik trade: {traded} ta\n🆔 Signal: #{signal_id}",
        reply_markup=signal_keyboard(signal_id)
    )
    await message.answer("Admin menyu:", reply_markup=admin_menu())


@router.callback_query(F.data.startswith("close_signal_"))
async def cb_close_signal(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    signal_id = int(call.data.split("_")[-1])
    close_signal(signal_id)
    all_users = get_all_users()
    for u in all_users:
        try:
            await call.bot.send_message(u[0], f"🔒 <b>Signal #{signal_id} yopildi!</b>")
        except Exception:
            pass
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("✅ Signal yopildi!")
    await call.message.answer(f"✅ Signal #{signal_id} yopildi.", reply_markup=admin_menu())