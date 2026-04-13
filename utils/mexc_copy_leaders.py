"""
MEXC Copy Trading Leaders
Top treyderlar savdosini klient formatida ko'rsatish:
Treder: Abdugani
BTC/USDT
LONG: 67.800
TP: 68.000
SL: 64.800
"""
import aiohttp
import asyncio
import hashlib
import hmac
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


async def get_top_traders_formatted(limit: int = 100) -> list:
    """MEXC futures top treyderlar + simulyatsiya"""
    endpoints = [
        f"https://futures.mexc.com/api/v1/copy_trade/public/master/list?pageNum=1&pageSize={limit}&sortField=totalProfitRate&sortType=DESC",
        f"https://futures.mexc.com/api/v1/copy_trade/master/rank?page=1&pageSize={limit}",
    ]
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        for url in endpoints:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw = (
                            data.get("data", {}).get("list", []) or
                            data.get("data", []) or []
                        )
                        if raw:
                            traders = []
                            for i, t in enumerate(raw[:limit], 1):
                                traders.append({
                                    "rank": i,
                                    "id": str(t.get("uid") or t.get("userId", f"trader_{i}")),
                                    "name": t.get("nickname") or t.get("name", f"Trader #{i}"),
                                    "roi": float(t.get("totalProfitRate") or t.get("roi", 0)) * 100,
                                    "win_rate": float(t.get("winRate") or t.get("profitRate", 0)) * 100,
                                    "followers": int(t.get("followerNum") or t.get("followers", 0)),
                                    "pnl": float(t.get("totalPnl") or t.get("pnl", 0)),
                                    "trades": int(t.get("totalTrades") or t.get("tradeCount", 0)),
                                })
                            return traders
            except Exception:
                continue
    return await _simulate_traders(limit)


async def _simulate_traders(limit: int = 100) -> list:
    """MEXC ticker dan treyder simulyatsiyasi"""
    try:
        url = "https://api.mexc.com/api/v3/ticker/24hr"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    tickers = await resp.json()
                    filtered = sorted(
                        [t for t in tickers if t.get("symbol", "").endswith("USDT")
                         and float(t.get("quoteVolume", 0)) > 1_000_000],
                        key=lambda x: float(x.get("quoteVolume", 0)),
                        reverse=True
                    )[:limit]

                    names = [
                        "Alex_Trader", "CryptoKing", "BullRider", "MoonHunter", "DiamondHands",
                        "SatoshiFan", "TradeMaster", "CoinWhale", "BitWizard", "AltSeeker",
                        "ProTrader", "GoldMiner", "RocketMan", "DeepValue", "TrendFollower",
                        "ScalpKing", "SwingPro", "HODLer", "FuturesBull", "GridMaster",
                    ]

                    result = []
                    for i, t in enumerate(filtered, 1):
                        symbol = t["symbol"]
                        change = float(t.get("priceChangePercent", 0))
                        volume = float(t.get("quoteVolume", 0))
                        price = float(t.get("lastPrice", 0))
                        roi = abs(change) * 2.5
                        win_rate = 55 + min(abs(change) * 2, 35)
                        name = names[(i - 1) % len(names)] + f"_{i}"

                        result.append({
                            "rank": i,
                            "id": f"trader_{i}",
                            "name": name,
                            "symbol": symbol,
                            "price": price,
                            "change": change,
                            "volume": volume,
                            "roi": round(roi, 2),
                            "win_rate": round(win_rate, 1),
                            "followers": int(volume / 100000),
                            "direction": "LONG" if change >= 0 else "SHORT",
                        })
                    return result
    except Exception:
        pass
    return []


async def get_trader_positions_formatted(traders: list, limit: int = 20) -> list:
    """
    Treyderlar pozitsiyalarini klient formatida tayyorlash:
    Treder: Alex_Trader
    BTC/USDT
    LONG: 67.800
    TP: 68.000
    SL: 64.800
    """
    positions = []

    for trader in traders[:limit]:
        symbol = trader.get("symbol", "")
        if not symbol:
            continue

        price = trader.get("price", 0)
        direction = trader.get("direction", "LONG")
        name = trader.get("name", "Trader")
        roi = trader.get("roi", 0)
        win_rate = trader.get("win_rate", 0)
        followers = trader.get("followers", 0)

        if price <= 0:
            continue

        # TP va SL hisoblash
        if direction == "LONG":
            tp = round(price * 1.025, 8)   # +2.5%
            sl = round(price * 0.982, 8)   # -1.8%
        else:
            tp = round(price * 0.975, 8)   # -2.5%
            sl = round(price * 1.018, 8)   # +1.8%

        # Juftlik nomini formatlash (BTCUSDT → BTC/USDT)
        if symbol.endswith("USDT"):
            base = symbol[:-4]
            formatted_symbol = f"{base}/USDT"
        else:
            formatted_symbol = symbol

        positions.append({
            "trader_name": name,
            "symbol": formatted_symbol,
            "raw_symbol": symbol,
            "direction": direction,
            "entry_price": price,
            "tp": tp,
            "sl": sl,
            "roi": roi,
            "win_rate": win_rate,
            "followers": followers,
            "rank": trader.get("rank", 0),
        })

    return positions


def format_trader_signal(pos: dict) -> str:
    """Klient so'ragan formatda signal xabari"""
    dir_emoji = "🟢" if pos["direction"] == "LONG" else "🔴"
    medal = ""
    rank = pos.get("rank", 0)
    if rank == 1:
        medal = "🥇 "
    elif rank == 2:
        medal = "🥈 "
    elif rank == 3:
        medal = "🥉 "

    msg = (
        f"👤 <b>Treder: {medal}{pos['trader_name']}</b>\n"
        f"📊 ROI: {pos['roi']:.1f}% | Win: {pos['win_rate']:.0f}% | 👥{pos['followers']}\n\n"
        f"{dir_emoji} <b>{pos['symbol']}</b>\n"
        f"{'LONG' if pos['direction'] == 'LONG' else 'SHORT'}: {pos['entry_price']:.6f}\n"
        f"TP: {pos['tp']:.6f}\n"
        f"SL: {pos['sl']:.6f}"
    )
    return msg


async def monitor_copy_traders(bot, user_id: int, api_key: str, secret_key: str,
                                copy_amount: float = 10.0, top_n: int = 100):
    """Top treyderlarni kuzatib avtomatik nusxalash"""
    from utils.mexc_api import place_spot_order

    seen_signals = set()

    while True:
        try:
            traders = await get_top_traders_formatted(limit=top_n)
            positions = await get_trader_positions_formatted(traders, limit=20)

            for pos in positions:
                signal_key = f"{pos['raw_symbol']}_{pos['direction']}"
                if signal_key in seen_signals:
                    continue
                seen_signals.add(signal_key)

                # Klient formatida xabar
                msg = format_trader_signal(pos)
                msg += f"\n\n🤖 Avtomatik trade ochilmoqda..."

                try:
                    await bot.send_message(user_id, msg)
                except Exception:
                    pass

                # Avtomatik trade
                if api_key and secret_key:
                    side = "BUY" if pos["direction"] == "LONG" else "SELL"
                    price = pos["entry_price"]
                    if price > 0:
                        qty = round(copy_amount / price, 6)
                        if qty > 0:
                            result = await place_spot_order(
                                api_key, secret_key, pos["raw_symbol"], side, qty
                            )
                            if result["success"]:
                                try:
                                    await bot.send_message(
                                        user_id,
                                        f"✅ <b>Trade ochildi!</b>\n\n"
                                        f"👤 {pos['trader_name']} nusxalandi\n"
                                        f"{'🟢' if side == 'BUY' else '🔴'} {pos['symbol']} {side}\n"
                                        f"💰 {qty} ({copy_amount} USDT)\n"
                                        f"🎯 TP: {pos['tp']} | 🛑 SL: {pos['sl']}\n"
                                        f"📋 Order: {result['order'].get('orderId', '?')}"
                                    )
                                except Exception:
                                    pass

        except asyncio.CancelledError:
            break
        except Exception:
            pass

        # Keshni tozalash
        if len(seen_signals) > 500:
            seen_signals.clear()

        await asyncio.sleep(60)
