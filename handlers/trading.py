from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user, save_api_keys, set_bot_active
from keyboards.kb import main_menu, cancel_keyboard
from utils.mexc_api import test_api_connection, get_spot_balance, get_open_orders, place_spot_order
from utils.auto_strategy import (
    find_best_signals, find_triangular_arbitrage_detailed,
    format_arbitrage_message
)

router = Router()
auto_tasks = {}


class ApiState(StatesGroup):
    waiting_api_key = State()
    waiting_secret_key = State()


class AutoState(StatesGroup):
    waiting_amount = State()
    waiting_min_profit = State()


def get_trading_lang(tg_id):
    from database.db import get_user
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


def trading_main_kb(is_running=False, lang="uz"):
    kb = InlineKeyboardBuilder()
    if lang == "ru":
        kb.add(InlineKeyboardButton(text="🔑 Подключить MEXC API", callback_data="set_api"))
        kb.add(InlineKeyboardButton(text="⏹ Остановить бота" if is_running else "▶️ Активировать бота", callback_data="stop_bot" if is_running else "activate_bot"))
        kb.add(InlineKeyboardButton(text="🔍 Проверить сигналы", callback_data="check_signals"))
        kb.add(InlineKeyboardButton(text="🔺 Найти арбитраж", callback_data="auto_find_arb"))
        kb.add(InlineKeyboardButton(text="💰 Баланс MEXC", callback_data="check_balance"))
        kb.add(InlineKeyboardButton(text="📋 Открытые ордера", callback_data="open_orders"))
    elif lang == "en":
        kb.add(InlineKeyboardButton(text="🔑 Connect MEXC API", callback_data="set_api"))
        kb.add(InlineKeyboardButton(text="⏹ Stop bot" if is_running else "▶️ Activate bot", callback_data="stop_bot" if is_running else "activate_bot"))
        kb.add(InlineKeyboardButton(text="🔍 Check signals", callback_data="check_signals"))
        kb.add(InlineKeyboardButton(text="🔺 Find arbitrage", callback_data="auto_find_arb"))
        kb.add(InlineKeyboardButton(text="💰 MEXC Balance", callback_data="check_balance"))
        kb.add(InlineKeyboardButton(text="📋 Open orders", callback_data="open_orders"))
    else:
        kb.add(InlineKeyboardButton(text="🔑 MEXC API ulash", callback_data="set_api"))
        kb.add(InlineKeyboardButton(text="⏹ Botni to'xtatish" if is_running else "▶️ Botni faollashtirish", callback_data="stop_bot" if is_running else "activate_bot"))
        kb.add(InlineKeyboardButton(text="🔍 Signallarni tekshirish", callback_data="check_signals"))
        kb.add(InlineKeyboardButton(text="🔺 Arbitraj izlash", callback_data="auto_find_arb"))
        kb.add(InlineKeyboardButton(text="💰 MEXC Balans", callback_data="check_balance"))
        kb.add(InlineKeyboardButton(text="📋 Ochiq buyurtmalar", callback_data="open_orders"))
    kb.adjust(1)
    return kb.as_markup()


@router.message(F.text.in_(["🤖 Auto Trading", "🤖 Авто Трейдинг", "🤖 Auto Trading"]))
async def show_auto_trading(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval /start bosing.")
        return
    lang = get_trading_lang(message.from_user.id)
    user_id = message.from_user.id
    is_running = user_id in auto_tasks and not auto_tasks[user_id].done()

    if lang == "ru":
        api_status = "✅ Подключён" if user.get("mexc_api_key") else "❌ Не подключён"
        bot_status = "✅ Активен" if is_running else "⏹ Остановлен"
        text = (
            f"🤖 <b>Авто Трейдинг (MEXC)</b>\n\n"
            f"🔑 API: {api_status}\n"
            f"⚙️ Бот: {bot_status}\n\n"
            f"<b>Что делает бот:</b>\n"
            f"📡 Ищет сигналы RSI+MACD\n"
            f"🔺 Ищет треугольный арбитраж\n"
            f"⚡️ Автоматически открывает BUY/SELL\n"
            f"🎯 Устанавливает TP и SL"
        )
    elif lang == "en":
        api_status = "✅ Connected" if user.get("mexc_api_key") else "❌ Not connected"
        bot_status = "✅ Active" if is_running else "⏹ Stopped"
        text = (
            f"🤖 <b>Auto Trading (MEXC)</b>\n\n"
            f"🔑 API: {api_status}\n"
            f"⚙️ Bot: {bot_status}\n\n"
            f"<b>What the bot does:</b>\n"
            f"📡 Finds RSI+MACD signals\n"
            f"🔺 Finds triangular arbitrage\n"
            f"⚡️ Auto opens BUY/SELL\n"
            f"🎯 Sets TP and SL"
        )
    else:
        api_status = "✅ Ulangan" if user.get("mexc_api_key") else "❌ Ulanmagan"
        bot_status = "✅ Faol" if is_running else "⏹ To'xtatilgan"
        text = (
            f"🤖 <b>Auto Trading (MEXC)</b>\n\n"
            f"🔑 API: {api_status}\n"
            f"⚙️ Bot: {bot_status}\n\n"
            f"<b>Bot nima qiladi:</b>\n"
            f"📡 RSI+MACD asosida signal topadi\n"
            f"🔺 Uchburchak arbitraj izlaydi\n"
            f"⚡️ Avtomatik BUY/SELL ochadi\n"
            f"🎯 TP va SL o'rnatadi"
        )
    await message.answer(text, reply_markup=trading_main_kb(is_running, lang))


# ===== SIGNALLARNI TEKSHIRISH =====
@router.callback_query(F.data == "check_signals")
async def cb_check_signals(call: CallbackQuery):
    await call.answer("⏳ Tahlil qilinmoqda...")
    await call.message.edit_text("⏳ <b>Top 30 juftlik tahlil qilinmoqda...</b>\n\n30-60 soniya kuting.")
    signals = await find_best_signals(limit=5)
    if not signals:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="🔄 Qayta", callback_data="check_signals"))
        kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_trading"))
        kb.adjust(2)
        await call.message.edit_text(
            "😔 <b>Hozircha kuchli signal yo'q</b>\n\nBozor neytral. Biroz kutib qayta tekshiring.",
            reply_markup=kb.as_markup()
        )
        return
    text = f"📡 <b>Topilgan signallar ({len(signals)} ta)</b>\n\n"
    for s in signals:
        de = "🟢" if s["signal"] == "BUY" else "🔴"
        text += (
            f"{de} <b>{s['symbol']}</b> — {s['signal']}\n"
            f"💵 ${s['price']:.6f} | RSI: {s['rsi']} | {s['trend']}\n"
            f"🎯 TP: ${s['tp']:.6f} | 🛑 SL: ${s['sl']:.6f}\n"
            f"📝 {s['reason']}\n\n"
        )
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Yangilash", callback_data="check_signals"))
    kb.add(InlineKeyboardButton(text="▶️ Avtomatik mode", callback_data="activate_bot"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_trading"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


# ===== ARBITRAJ IZLASH =====
@router.callback_query(F.data == "auto_find_arb")
async def cb_auto_find_arb(call: CallbackQuery):
    await call.answer("⏳ Arbitraj izlanmoqda...")
    await call.message.edit_text("⏳ <b>MEXC da uchburchak arbitraj izlanmoqda...</b>\n\n20-40 soniya kuting.")

    opportunities = await find_triangular_arbitrage_detailed(trade_amount=100, min_profit=0.1)

    if not opportunities:
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="🔄 Qayta izlash", callback_data="auto_find_arb"))
        kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_trading"))
        kb.adjust(2)
        await call.message.edit_text(
            "😔 <b>Hozircha foydali arbitraj yo'q</b>\n\nBozor muvozanatda. Biroz kutib qayta izlang.",
            reply_markup=kb.as_markup()
        )
        return

    # Eng yaxshi natijani klient formatida ko'rsatish
    best = opportunities[0]
    text = format_arbitrage_message(best)

    if len(opportunities) > 1:
        text += f"\n\n📋 Jami {len(opportunities)} ta imkoniyat topildi."

    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔄 Qayta izlash", callback_data="auto_find_arb"))
    kb.add(InlineKeyboardButton(text="▶️ Avtomatik mode", callback_data="activate_bot"))
    kb.add(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_trading"))
    kb.adjust(2)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


# ===== BOTNI FAOLLASHTIRISH =====
@router.callback_query(F.data == "activate_bot")
async def cb_activate_bot(call: CallbackQuery, state: FSMContext):
    user = get_user(call.from_user.id)
    if not user or not user.get("mexc_api_key"):
        await call.answer("❌ Avval API kalitni ulang!", show_alert=True)
        return
    if not user.get("tariff"):
        await call.answer("❌ Tarif kerak!", show_alert=True)
        return
    await call.message.edit_text(
        "▶️ <b>Avtomatik Trading</b>\n\n"
        "Har bir trade uchun necha USDT?\n\n"
        "• Minimal: 5 USDT\n"
        "• Tavsiya: 10-100 USDT\n\n"
        "Miqdorni kiriting:"
    )
    await state.set_state(AutoState.waiting_amount)


@router.message(AutoState.waiting_amount)
async def process_auto_amount(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    try:
        amount = float(message.text.replace(",", "."))
        if amount < 5:
            await message.answer("❌ Minimal 5 USDT.")
            return
        await state.update_data(trade_amount=amount)
        await message.answer(
            f"✅ Miqdor: <b>{amount} USDT</b>\n\n"
            "📊 Minimal arbitraj foydasi (%):\n"
            "Tavsiya: <b>0.3</b>"
        )
        await state.set_state(AutoState.waiting_min_profit)
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


@router.message(AutoState.waiting_min_profit)
async def process_min_profit(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    try:
        min_profit = float(message.text.replace(",", "."))
        if min_profit < 0.1 or min_profit > 10:
            await message.answer("❌ 0.1 dan 10 gacha.")
            return
        data = await state.get_data()
        amount = data["trade_amount"]
        user = get_user(message.from_user.id)
        user_id = message.from_user.id

        if user_id in auto_tasks and not auto_tasks[user_id].done():
            auto_tasks[user_id].cancel()

        task = asyncio.create_task(
            auto_trading_loop(
                message.bot, user_id,
                user["mexc_api_key"], user["mexc_secret_key"],
                amount, min_profit
            )
        )
        auto_tasks[user_id] = task
        set_bot_active(user_id, 1)
        await state.clear()
        await message.answer(
            f"✅ <b>Avtomatik Trading yoqildi!</b>\n\n"
            f"💰 Har trade: <b>{amount} USDT</b>\n"
            f"📊 Min arbitraj: <b>{min_profit}%</b>\n\n"
            f"🔍 Har 2 daqiqada signal izlaydi\n"
            f"🔺 Har 5 daqiqada arbitraj izlaydi\n"
            f"📊 Natija klient formatida keladi!\n\n"
            f"Signal kelganda xabar olasiz! 📱",
            reply_markup=main_menu()
        )
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


async def auto_trading_loop(bot, user_id, api_key, secret_key, trade_amount, min_profit):
    """Asosiy avtomatik trading loop"""
    traded_signals = set()
    cycle = 0

    while True:
        try:
            cycle += 1

            # RSI/MACD signallar - har 2 daqiqada
            if cycle % 2 == 0:
                signals = await find_best_signals(limit=3)
                for signal in signals:
                    key = f"{signal['symbol']}_{signal['signal']}"
                    if key in traded_signals:
                        continue
                    traded_signals.add(key)

                    de = "🟢" if signal["signal"] == "BUY" else "🔴"
                    try:
                        await bot.send_message(
                            user_id,
                            f"📡 <b>Auto Signal!</b>\n\n"
                            f"{de} <b>{signal['symbol']}</b> — {signal['signal']}\n"
                            f"💵 ${signal['price']:.6f}\n"
                            f"📊 RSI: {signal['rsi']} | {signal['trend']}\n"
                            f"🎯 TP: ${signal['tp']:.6f}\n"
                            f"🛑 SL: ${signal['sl']:.6f}\n"
                            f"📝 {signal['reason']}\n\n"
                            f"🤖 Trade ochilmoqda..."
                        )
                    except Exception:
                        pass

                    # Trade ochish
                    try:
                        qty = round(trade_amount / signal["price"], 6)
                        side = "BUY" if signal["signal"] == "BUY" else "SELL"
                        if qty > 0:
                            result = await place_spot_order(api_key, secret_key, signal["symbol"], side, qty)
                            if result["success"]:
                                try:
                                    await bot.send_message(
                                        user_id,
                                        f"✅ <b>Trade ochildi!</b>\n"
                                        f"{de} {signal['symbol']} {side}\n"
                                        f"💰 {qty} ({trade_amount} USDT)\n"
                                        f"🎯 TP: ${signal['tp']:.6f} | 🛑 SL: ${signal['sl']:.6f}"
                                    )
                                except Exception:
                                    pass
                    except Exception:
                        pass

            # Arbitraj - har 5 daqiqada
            if cycle % 5 == 0:
                opportunities = await find_triangular_arbitrage_detailed(
                    trade_amount=trade_amount,
                    min_profit=min_profit
                )
                if opportunities:
                    best = opportunities[0]
                    # Klient formatida xabar
                    msg = format_arbitrage_message(best)
                    msg += "\n\n⚡️ Bajarilmoqda..."
                    try:
                        await bot.send_message(user_id, msg)
                    except Exception:
                        pass

                    # Arbitraj bajarish
                    try:
                        from utils.arbitrage import execute_triangular_arbitrage
                        arb_result = await execute_triangular_arbitrage(
                            api_key, secret_key, best, trade_amount
                        )
                        if arb_result["success"]:
                            try:
                                await bot.send_message(
                                    user_id,
                                    f"✅ <b>Arbitraj bajarildi!</b>\n"
                                    f"📍 {best['path']}\n"
                                    f"💰 Profit: +{best['profit']} USDT\n"
                                    f"📊 Spred: {best['spread_pct']}%"
                                )
                            except Exception:
                                pass
                    except Exception:
                        pass

        except asyncio.CancelledError:
            break
        except Exception:
            pass

        await asyncio.sleep(60)
        if cycle >= 30:
            traded_signals.clear()
            cycle = 0


# ===== BOTNI TO'XTATISH =====
@router.callback_query(F.data == "stop_bot")
async def cb_stop_bot(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id in auto_tasks and not auto_tasks[user_id].done():
        auto_tasks[user_id].cancel()
        del auto_tasks[user_id]
    set_bot_active(user_id, 0)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="▶️ Qayta yoqish", callback_data="activate_bot"))
    await call.message.edit_text(
        "⏹ <b>Bot to'xtatildi!</b>",
        reply_markup=kb.as_markup()
    )


# ===== API ULASH =====
@router.callback_query(F.data == "set_api")
async def cb_set_api(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "🔑 <b>MEXC API Kalitini kiriting</b>\n\n"
        "mexc.com → Profile → API Management\n\n"
        "📋 Access Key ni yuboring:"
    )
    await state.set_state(ApiState.waiting_api_key)


@router.message(ApiState.waiting_api_key)
async def process_api_key(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    api_key = message.text.strip()
    if len(api_key) < 5:
        await message.answer("❌ Noto'g'ri. Qayta kiriting:")
        return
    await state.update_data(api_key=api_key)
    await message.answer("🔐 Secret Key ni kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(ApiState.waiting_secret_key)


@router.message(ApiState.waiting_secret_key)
async def process_secret_key(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    secret_key = message.text.strip()
    if len(secret_key) < 5:
        await message.answer("❌ Noto'g'ri. Qayta kiriting:")
        return
    data = await state.get_data()
    api_key = data["api_key"]
    await message.answer("⏳ API tekshirilmoqda...")
    result = await test_api_connection(api_key, secret_key)
    if result["success"]:
        save_api_keys(message.from_user.id, api_key, secret_key)
        await state.clear()
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="▶️ Botni yoqish", callback_data="activate_bot"))
        await message.answer("✅ <b>API ulandi!</b>\n\nBotni faollashtiring.", reply_markup=kb.as_markup())
    else:
        await state.clear()
        await message.answer(f"❌ <b>Ulanmadi!</b>\n\n{result['error']}", reply_markup=main_menu())


# ===== BALANS =====
@router.callback_query(F.data == "check_balance")
async def cb_check_balance(call: CallbackQuery):
    user = get_user(call.from_user.id)
    if not user or not user.get("mexc_api_key"):
        await call.answer("❌ API ulanmagan!", show_alert=True)
        return
    await call.answer("⏳ Olinmoqda...")
    result = await get_spot_balance(user["mexc_api_key"], user["mexc_secret_key"])
    if result["success"]:
        balances = result["balances"]
        if not balances:
            text = "💰 <b>MEXC Balans</b>\n\nAktiv topilmadi."
        else:
            lines = ["💰 <b>MEXC Spot Balans</b>\n"]
            for asset, data in list(balances.items())[:15]:
                lines.append(f"• <b>{asset}:</b> {data['free']:.6f}")
            text = "\n".join(lines)
    else:
        text = f"❌ Xato: {result['error']}"
    await call.message.answer(text)


# ===== OCHIQ ORDERLAR =====
@router.callback_query(F.data == "open_orders")
async def cb_open_orders(call: CallbackQuery):
    user = get_user(call.from_user.id)
    if not user or not user.get("mexc_api_key"):
        await call.answer("❌ API ulanmagan!", show_alert=True)
        return
    await call.answer("⏳ Olinmoqda...")
    result = await get_open_orders(user["mexc_api_key"], user["mexc_secret_key"])
    if result["success"]:
        orders = result["orders"]
        if not orders:
            text = "📋 <b>Ochiq buyurtmalar yo'q.</b>"
        else:
            lines = [f"📋 <b>Ochiq buyurtmalar ({len(orders)} ta)</b>\n"]
            for o in orders[:10]:
                e = "🟢" if o.get("side") == "BUY" else "🔴"
                lines.append(f"{e} <b>{o.get('symbol')}</b> — {o.get('side')} {o.get('origQty')}")
            text = "\n".join(lines)
    else:
        text = f"❌ Xato: {result['error']}"
    await call.message.answer(text)


@router.callback_query(F.data == "back_trading")
async def cb_back_trading(call: CallbackQuery):
    user = get_user(call.from_user.id)
    user_id = call.from_user.id
    is_running = user_id in auto_tasks and not auto_tasks[user_id].done()
    api_status = "✅ Ulangan" if user and user.get("mexc_api_key") else "❌ Ulanmagan"
    bot_status = "✅ Faol" if is_running else "⏹ To\'xtatilgan"
    await call.message.edit_text(
        f"🤖 <b>Auto Trading (MEXC)</b>\n\n"
        f"🔑 API: {api_status}\n"
        f"⚙️ Bot: {bot_status}",
        reply_markup=trading_main_kb(is_running)
    )