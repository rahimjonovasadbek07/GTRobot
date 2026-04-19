from aiogram import Router, F
from aiogram.types import Message
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user_trades, get_trade_stats, get_user

router = Router()

HISTORY_TX = {
    "uz": {
        "title": "📈 <b>Savdo tarixi</b>",
        "no_trades": "Hozircha savdolar yo'q.\n\n🤖 Auto Trading ni yoqing va signal kelishini kuting!",
        "stats": "📊 <b>Umumiy statistika:</b>",
        "total": "• Jami savdolar",
        "wins": "• Foydali savdolar",
        "win_rate": "• Win rate",
        "pnl": "Umumiy PNL",
        "recent": "📋 <b>So'nggi savdolar:</b>",
        "entry": "📥", "tp": "🎯", "sl": "🛑", "pnl_label": "PNL",
    },
    "ru": {
        "title": "📈 <b>История сделок</b>",
        "no_trades": "Сделок пока нет.\n\n🤖 Включите Auto Trading и ждите сигнала!",
        "stats": "📊 <b>Общая статистика:</b>",
        "total": "• Всего сделок",
        "wins": "• Прибыльных",
        "win_rate": "• Win rate",
        "pnl": "Общий PNL",
        "recent": "📋 <b>Последние сделки:</b>",
        "entry": "📥", "tp": "🎯", "sl": "🛑", "pnl_label": "PNL",
    },
    "en": {
        "title": "📈 <b>Trade history</b>",
        "no_trades": "No trades yet.\n\n🤖 Enable Auto Trading and wait for a signal!",
        "stats": "📊 <b>Overall statistics:</b>",
        "total": "• Total trades",
        "wins": "• Profitable trades",
        "win_rate": "• Win rate",
        "pnl": "Total PNL",
        "recent": "📋 <b>Recent trades:</b>",
        "entry": "📥", "tp": "🎯", "sl": "🛑", "pnl_label": "PNL",
    },
}


def get_user_lang(tg_id):
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


@router.message(F.text.in_(["📈 Savdo tarixi", "📈 История сделок", "📈 Trade history"]))
async def show_trade_history(message: Message):
    lang = get_user_lang(message.from_user.id)
    tx = HISTORY_TX.get(lang, HISTORY_TX["uz"])
    trades = get_user_trades(message.from_user.id, limit=15)
    stats = get_trade_stats(message.from_user.id)

    if not trades:
        await message.answer(f"{tx['title']}\n\n{tx['no_trades']}")
        return

    win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
    pnl_emoji = "📈" if stats['pnl'] >= 0 else "📉"

    text = (
        f"{tx['title']}\n\n"
        f"{tx['stats']}\n"
        f"{tx['total']}: <b>{stats['total']}</b>\n"
        f"{tx['wins']}: <b>{stats['wins']}</b>\n"
        f"{tx['win_rate']}: <b>{win_rate:.1f}%</b>\n"
        f"{pnl_emoji} {tx['pnl']}: <b>{stats['pnl']:.4f}</b>\n\n"
        f"─────────────────\n"
        f"{tx['recent']}\n\n"
    )

    for t in trades:
        symbol, direction, leverage, entry, tp, sl, status, pnl, created = t
        dir_emoji = "🟢" if direction == "LONG" else "🔴"
        status_emoji = "✅" if status == "closed" else "⏳"
        pnl_str = f" | {tx['pnl_label']}: {pnl:.4f}" if pnl != 0 else ""
        text += (
            f"{dir_emoji} <b>{symbol}</b> {direction} x{leverage} {status_emoji}\n"
            f"{tx['entry']} {entry} → {tx['tp']} {tp} | {tx['sl']} {sl}{pnl_str}\n"
            f"🕐 {created[:16]}\n\n"
        )

    await message.answer(text)