from aiogram import Router, F
from aiogram.types import Message
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user_trades, get_trade_stats

router = Router()


@router.message(F.text == "📈 Savdo tarixi")
async def show_trade_history(message: Message):
    trades = get_user_trades(message.from_user.id, limit=15)
    stats = get_trade_stats(message.from_user.id)

    if not trades:
        await message.answer(
            "📈 <b>Savdo tarixi</b>\n\n"
            "Hozircha savdolar yo'q.\n\n"
            "🤖 Auto Trading ni yoqing va signal kelishini kuting!"
        )
        return

    # Statistika
    win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
    pnl_emoji = "📈" if stats['pnl'] >= 0 else "📉"

    text = (
        f"📈 <b>Savdo tarixi</b>\n\n"
        f"📊 <b>Umumiy statistika:</b>\n"
        f"• Jami savdolar: <b>{stats['total']}</b>\n"
        f"• Foydali savdolar: <b>{stats['wins']}</b>\n"
        f"• Win rate: <b>{win_rate:.1f}%</b>\n"
        f"{pnl_emoji} Umumiy PNL: <b>{stats['pnl']:.4f}</b>\n\n"
        f"─────────────────\n"
        f"📋 <b>So'nggi savdolar:</b>\n\n"
    )

    for t in trades:
        symbol, direction, leverage, entry, tp, sl, status, pnl, created = t
        dir_emoji = "🟢" if direction == "LONG" else "🔴"
        status_emoji = "✅" if status == "closed" else "⏳"
        pnl_str = f" | PNL: {pnl:.4f}" if pnl != 0 else ""

        text += (
            f"{dir_emoji} <b>{symbol}</b> {direction} x{leverage} {status_emoji}\n"
            f"📥 {entry} → 🎯 {tp} | 🛑 {sl}{pnl_str}\n"
            f"🕐 {created[:16]}\n\n"
        )

    await message.answer(text)
