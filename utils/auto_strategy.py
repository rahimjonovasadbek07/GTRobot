"""
Auto Trading Strategy
1. RSI + MACD signallar
2. Uchburchak arbitraj - klient formatida
"""
import asyncio
import aiohttp


async def get_klines(symbol: str, interval: str = "1h", limit: int = 50) -> list:
    url = "https://api.mexc.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        pass
    return []


async def get_all_tickers() -> list:
    url = "https://api.mexc.com/api/v3/ticker/24hr"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [t for t in data if t.get("symbol", "").endswith("USDT")]
    except Exception:
        pass
    return []


async def get_exchange_info() -> dict:
    """Barcha juftliklar info"""
    url = "https://api.mexc.com/api/v3/exchangeInfo"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        pass
    return {}


def calculate_rsi(closes: list, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 2)


def calculate_macd(closes: list) -> dict:
    if len(closes) < 26:
        return {"macd": 0, "signal": 0, "histogram": 0}
    def ema(data, period):
        k = 2 / (period + 1)
        val = data[0]
        for p in data[1:]:
            val = p * k + val * (1 - k)
        return val
    ema12 = ema(closes[-26:], 12)
    ema26 = ema(closes[-26:], 26)
    macd_line = ema12 - ema26
    signal_line = ema([macd_line], 9)
    return {
        "macd": round(macd_line, 8),
        "signal": round(signal_line, 8),
        "histogram": round(macd_line - signal_line, 8)
    }


async def analyze_symbol(symbol: str) -> dict:
    klines = await get_klines(symbol, "1h", 50)
    if not klines:
        return {}
    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    volumes = [float(k[5]) for k in klines]
    current_price = closes[-1]
    rsi = calculate_rsi(closes)
    macd = calculate_macd(closes)
    ma7 = sum(closes[-7:]) / 7
    ma25 = sum(closes[-25:]) / 25
    trend = "BULLISH" if ma7 > ma25 else "BEARISH"
    avg_volume = sum(volumes[-10:]) / 10
    volume_surge = volumes[-1] > avg_volume * 1.5
    signal = None
    reason = ""
    if rsi < 30 and macd["histogram"] > 0:
        signal = "BUY"
        reason = f"RSI={rsi} (Oversold) + MACD o'smoqda"
    elif rsi > 70 and macd["histogram"] < 0:
        signal = "SELL"
        reason = f"RSI={rsi} (Overbought) + MACD tushmoqda"
    elif rsi < 35 and trend == "BULLISH" and volume_surge:
        signal = "BUY"
        reason = f"RSI={rsi} + Bullish trend + Yuqori volume"
    elif rsi > 65 and trend == "BEARISH" and volume_surge:
        signal = "SELL"
        reason = f"RSI={rsi} + Bearish trend + Yuqori volume"
    if signal == "BUY":
        tp = round(current_price * 1.02, 8)
        sl = round(current_price * 0.985, 8)
    elif signal == "SELL":
        tp = round(current_price * 0.98, 8)
        sl = round(current_price * 1.015, 8)
    else:
        tp = sl = 0
    return {
        "symbol": symbol,
        "price": current_price,
        "rsi": rsi,
        "macd": macd,
        "trend": trend,
        "signal": signal,
        "reason": reason,
        "tp": tp,
        "sl": sl,
        "support": round(min(lows[-20:]), 8),
        "resistance": round(max(highs[-20:]), 8),
        "volume_surge": volume_surge,
    }


async def find_best_signals(symbols: list = None, limit: int = 5) -> list:
    if not symbols:
        tickers = await get_all_tickers()
        sorted_t = sorted(tickers, key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)[:30]
        symbols = [t["symbol"] for t in sorted_t]
    tasks = [analyze_symbol(s) for s in symbols[:20]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    signals = [r for r in results if isinstance(r, dict) and r.get("signal")]
    signals.sort(key=lambda x: abs(x["rsi"] - 50), reverse=True)
    return signals[:limit]


async def find_triangular_arbitrage_detailed(trade_amount: float = 100.0, min_profit: float = 0.3) -> list:
    """
    Uchburchak arbitraj - klient formatida
    LITH/BTC/USDT
    Покупка: X LITH → BTC
    Продажа: BTC → USDT
    Профит: XXX USDT
    Спред: XX%
    """
    # Barcha ticker lar
    url = "https://api.mexc.com/api/v3/ticker/bookTicker"
    ticker_dict = {}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    tickers = await resp.json()
                    for t in tickers:
                        ticker_dict[t["symbol"]] = {
                            "ask": float(t.get("askPrice", 0)),
                            "bid": float(t.get("bidPrice", 0)),
                        }
    except Exception:
        # Fallback - oddiy ticker
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.mexc.com/api/v3/ticker/24hr",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        tickers = await resp.json()
                        for t in tickers:
                            price = float(t.get("lastPrice", 0))
                            ticker_dict[t["symbol"]] = {
                                "ask": price * 1.001,
                                "bid": price * 0.999,
                            }
        except Exception:
            pass

    if not ticker_dict:
        return []

    # Asosiy coinlar
    base_coins = [
        "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE",
        "MATIC", "LINK", "AVAX", "DOT", "LTC", "TRX", "ATOM",
        "NEAR", "FTM", "SAND", "MANA", "AXS", "GALA"
    ]

    opportunities = []

    for coin_a in base_coins:
        for coin_b in base_coins:
            if coin_a == coin_b:
                continue

            # Yo'l: USDT → coin_a → coin_b → USDT
            pair_au = f"{coin_a}USDT"
            pair_bu = f"{coin_b}USDT"
            pair_ab = f"{coin_a}{coin_b}"
            pair_ba = f"{coin_b}{coin_a}"

            try:
                # 1-yo'l: USDT → A → B → USDT
                if pair_au in ticker_dict and pair_bu in ticker_dict and pair_ab in ticker_dict:
                    ask_a = ticker_dict[pair_au]["ask"]
                    bid_b = ticker_dict[pair_bu]["bid"]
                    bid_ab = ticker_dict[pair_ab]["bid"]
                    ask_ab = ticker_dict[pair_ab]["ask"]

                    if ask_a > 0 and bid_b > 0 and bid_ab > 0:
                        qty_a = trade_amount / ask_a
                        qty_b = qty_a * bid_ab
                        final_usdt = qty_b * bid_b
                        commission = trade_amount * 0.003
                        net_profit = final_usdt - trade_amount - commission
                        spread_pct = (net_profit / trade_amount) * 100

                        if spread_pct > min_profit:
                            # ERC20 komissiya simulyatsiya
                            gas_fee_usd = 5.967
                            gas_coin_qty = round(gas_fee_usd / ask_a, 4) if ask_a > 0 else 0

                            opportunities.append({
                                "path": f"{coin_a}/{coin_b}/USDT",
                                "coin_a": coin_a,
                                "coin_b": coin_b,
                                # Покупка
                                "buy_from_qty": round(qty_a, 2),
                                "buy_from_coin": coin_a,
                                "buy_to_qty": round(qty_b, 2),
                                "buy_to_coin": coin_b,
                                "buy_price_min": round(bid_ab, 8),
                                "buy_price_max": round(ask_ab, 8),
                                # Продажа
                                "sell_from_qty": round(qty_b, 2),
                                "sell_from_coin": coin_b,
                                "sell_to_qty": round(final_usdt, 2),
                                "sell_to_coin": "USDT",
                                "sell_price_min": round(ticker_dict[pair_bu]["bid"] * 0.999, 6),
                                "sell_price_max": round(ticker_dict[pair_bu]["bid"], 6),
                                # Natija
                                "profit": round(net_profit, 2),
                                "spread_pct": round(spread_pct, 2),
                                # Komissiya
                                "network": "ERC20",
                                "commission_coin_qty": round(gas_coin_qty, 4),
                                "commission_usd": gas_fee_usd,
                                # Pairs
                                "pairs": [pair_au, pair_ab, pair_bu],
                                "sides": ["buy", "sell", "sell"],
                                "trade_amount": trade_amount,
                            })

                # 2-yo'l: USDT → B → A → USDT
                if pair_bu in ticker_dict and pair_au in ticker_dict and pair_ba in ticker_dict:
                    ask_b = ticker_dict[pair_bu]["ask"]
                    bid_a = ticker_dict[pair_au]["bid"]
                    bid_ba = ticker_dict[pair_ba]["bid"]
                    ask_ba = ticker_dict[pair_ba]["ask"]

                    if ask_b > 0 and bid_a > 0 and bid_ba > 0:
                        qty_b = trade_amount / ask_b
                        qty_a = qty_b * bid_ba
                        final_usdt = qty_a * bid_a
                        commission = trade_amount * 0.003
                        net_profit = final_usdt - trade_amount - commission
                        spread_pct = (net_profit / trade_amount) * 100

                        if spread_pct > min_profit:
                            gas_fee_usd = 5.967
                            gas_coin_qty = round(gas_fee_usd / ask_b, 4) if ask_b > 0 else 0

                            opportunities.append({
                                "path": f"{coin_b}/{coin_a}/USDT",
                                "coin_a": coin_b,
                                "coin_b": coin_a,
                                "buy_from_qty": round(qty_b, 2),
                                "buy_from_coin": coin_b,
                                "buy_to_qty": round(qty_a, 2),
                                "buy_to_coin": coin_a,
                                "buy_price_min": round(bid_ba, 8),
                                "buy_price_max": round(ask_ba, 8),
                                "sell_from_qty": round(qty_a, 2),
                                "sell_from_coin": coin_a,
                                "sell_to_qty": round(final_usdt, 2),
                                "sell_to_coin": "USDT",
                                "sell_price_min": round(ticker_dict[pair_au]["bid"] * 0.999, 6),
                                "sell_price_max": round(ticker_dict[pair_au]["bid"], 6),
                                "profit": round(net_profit, 2),
                                "spread_pct": round(spread_pct, 2),
                                "network": "ERC20",
                                "commission_coin_qty": round(gas_coin_qty, 4),
                                "commission_usd": gas_fee_usd,
                                "pairs": [pair_bu, pair_ba, pair_au],
                                "sides": ["buy", "sell", "sell"],
                                "trade_amount": trade_amount,
                            })
            except Exception:
                continue

    opportunities.sort(key=lambda x: x["spread_pct"], reverse=True)
    return opportunities[:10]


def format_arbitrage_message(opp: dict) -> str:
    """
    Klient so'ragan formatda arbitraj xabari:
    LITH/BTC/USDT
    🛒 Покупка:
    Объем: 8034.06 LITH → 8148428 BTC
    Цена: 0.000949-0.001083$
    ...
    """
    msg = (
        f"🔺 <b>{opp['path']}</b>\n\n"

        f"🛒 <b>Покупка:</b>\n"
        f"Объем: {opp['buy_from_qty']} {opp['buy_from_coin']} → {opp['buy_to_qty']} {opp['buy_to_coin']}\n"
        f"Цена: {opp['buy_price_min']}-{opp['buy_price_max']}$\n\n"

        f"📈 <b>Продажа:</b>\n"
        f"Объем: {opp['sell_from_qty']} {opp['sell_from_coin']} → {opp['sell_to_qty']} {opp['sell_to_coin']}\n"
        f"Цена: {opp['sell_price_min']}-{opp['sell_price_max']}$\n\n"

        f"💰 <b>Профит: {opp['profit']} USDT</b>\n"
        f"📊 Спред: <b>{opp['spread_pct']}%</b>\n\n"

        f"📤 <b>Вывод:</b>\n"
        f"Сеть: {opp['network']}\n"
        f"Комиссия: {opp['commission_coin_qty']} {opp['coin_a']} ({opp['commission_usd']}$)"
    )
    return msg
