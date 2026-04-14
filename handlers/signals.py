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


class SignalState(StatesGroup):
    waiting_signal = State()


def format_signal_message(symbol: str, direction: str, leverage: int,
                           entry: float, tp: float, sl: float,
                           trader_name: str = None) -> str:
    if trader_name is None:
        from database.db import get_bot_settings
        s = get_bot_settings()
        trader_name = s.get("signal_name", "GTRobot Signal")
    """Klient formatida signal xabari"""
    dir_emoji = "🟢" if direction == "LONG" else "🔴"

    # Juftlikni formatlash: BTCUSDT → BTC/USDT
    if symbol.endswith("USDT"):
        base = symbol[:-4]
        formatted = f"{base}/USDT"
    else:
        formatted = symbol

    msg = (
        f"📡 <b>Signal!</b>\n\n"
        f"👤 <b>Treder: {trader_name}</b>\n\n"
        f"{dir_emoji} <b>{formatted}</b>\n"
        f"{'LONG' if direction == 'LONG' else 'SHORT'}: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n"
    )

    if leverage > 1:
        msg += f"⚡️ Leverage: x{leverage}\n"

    return msg


# ===== SIGNALLAR RO'YXATI =====
@router.message(F.text == "📡 Signallar")
async def show_signals(message: Message):
    signals = get_active_signals()
    if not signals:
        await message.answer(
            "📡 <b>Faol signallar yo'q</b>\n\n"
            "Admin signal yuborganda bu yerda ko'rinadi."
        )
        return

    text = f"📡 <b>Faol signallar ({len(signals)} ta)</b>\n\n"
    for s in signals:
        sid, admin_id, symbol, direction, leverage, entry, tp, sl, status, msg, created = s
        dir_emoji = "🟢" if direction == "LONG" else "🔴"

        if symbol.endswith("USDT"):
            formatted = f"{symbol[:-4]}/USDT"
        else:
            formatted = symbol

        text += (
            f"{dir_emoji} <b>{formatted}</b> {direction}\n"
            f"📥 Kirish: {entry} | 🎯 TP: {tp} | 🛑 SL: {sl}\n"
            f"🕐 {created[:16]}\n\n"
        )
    await message.answer(text)


# ===== ADMIN: SIGNAL YUBORISH =====
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
        "• <b>49000</b> — SL\n\n"
        "Misol:\n"
        "<code>BTCUSDT LONG 10 50000 52000 49000</code>\n"
        "<code>ETHUSDT SHORT 5 3000 2800 3100</code>",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(SignalState.waiting_signal)


@router.message(SignalState.waiting_signal)
async def process_signal(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu())
        return

    try:
        parts = message.text.strip().upper().split()
        if len(parts) != 6:
            raise ValueError("Format noto'g'ri")
        symbol = parts[0]
        direction = parts[1]
        leverage = int(parts[2])
        entry = float(parts[3])
        tp = float(parts[4])
        sl = float(parts[5])
        if direction not in ["LONG", "SHORT"]:
            raise ValueError("LONG yoki SHORT bo'lishi kerak")
    except Exception:
        await message.answer(
            "❌ <b>Noto'g'ri format!</b>\n\n"
            "To'g'ri format:\n"
            "<code>BTCUSDT LONG 10 50000 52000 49000</code>"
        )
        return

    # Signalni saqlash
    signal_id = save_signal(
        message.from_user.id, symbol, direction, leverage,
        entry, tp, sl, message.text
    )

    # Klient formatida signal xabari
    signal_msg = format_signal_message(symbol, direction, leverage, entry, tp, sl)

    # Barcha foydalanuvchilarga yuborish
    all_users = get_all_users()
    sent = 0
    traded = 0

    for u in all_users:
        try:
            await message.bot.send_message(u[0], signal_msg)
            sent += 1
        except Exception:
            pass

    # Bot faol foydalanuvchilar uchun avtomatik trade
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
                            f"✅ <b>Trade ochildi!</b>\n\n"
                            f"{'🟢' if side == 'BUY' else '🔴'} {symbol} {side}\n"
                            f"📋 Order: {result['order'].get('orderId', '?')}"
                        )
                    except Exception:
                        pass
        except Exception:
            pass

    await state.clear()
    from keyboards.kb import admin_menu
    await message.answer(
        f"✅ <b>Signal yuborildi!</b>\n\n"
        f"📨 Xabar: {sent} ta\n"
        f"🤖 Avtomatik trade: {traded} ta\n"
        f"🆔 Signal: #{signal_id}",
        reply_markup=signal_keyboard(signal_id)
    )
    await message.answer("Admin menyu:", reply_markup=admin_menu())


# ===== SIGNALNI YOPISH =====
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
            await call.bot.send_message(
                u[0],
                f"🔒 <b>Signal #{signal_id} yopildi!</b>"
            )
        except Exception:
            pass

    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("✅ Signal yopildi!")
    await call.message.answer(f"✅ Signal #{signal_id} yopildi.", reply_markup=admin_menu())
