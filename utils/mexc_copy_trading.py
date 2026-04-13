"""
MEXC Copy Trading - Top treyderlar savdosini kuzatish
ccxt kutubxonasi orqali
"""
import ccxt.async_support as ccxt
import asyncio
from typing import Optional


async def get_mexc_exchange(api_key: str = None, secret_key: str = None):
    """MEXC exchange obyektini yaratish"""
    config = {
        'enableRateLimit': True,
        'timeout': 10000,
    }
    if api_key and secret_key:
        config['apiKey'] = api_key
        config['secret'] = secret_key
    
    exchange = ccxt.mexc(config)
    return exchange


async def get_top_tickers(limit: int = 20) -> list:
    """MEXC da eng ko'p trade qilingan juftliklar"""
    exchange = await get_mexc_exchange()
    try:
        tickers = await exchange.fetch_tickers()
        # Volume bo'yicha saralash
        sorted_tickers = sorted(
            [(k, v) for k, v in tickers.items() if '/USDT' in k and v.get('quoteVolume')],
            key=lambda x: x[1].get('quoteVolume', 0),
            reverse=True
        )[:limit]
        
        result = []
        for symbol, ticker in sorted_tickers:
            result.append({
                'symbol': symbol,
                'price': ticker.get('last', 0),
                'change': ticker.get('percentage', 0),
                'volume': ticker.get('quoteVolume', 0),
                'high': ticker.get('high', 0),
                'low': ticker.get('low', 0),
            })
        return result
    except Exception as e:
        return []
    finally:
        await exchange.close()


async def get_market_analysis(symbol: str) -> dict:
    """Juftlik uchun batafsil tahlil"""
    exchange = await get_mexc_exchange()
    try:
        # OHLCV ma'lumotlari (1 soatlik)
        ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=24)
        ticker = await exchange.fetch_ticker(symbol)
        
        if not ohlcv:
            return {}
        
        closes = [c[4] for c in ohlcv]
        volumes = [c[5] for c in ohlcv]
        
        # Oddiy RSI hisoblash
        rsi = calculate_rsi(closes)
        
        # Trend aniqlash
        avg_short = sum(closes[-5:]) / 5
        avg_long = sum(closes[-20:]) / 20 if len(closes) >= 20 else sum(closes) / len(closes)
        trend = "BULLISH 📈" if avg_short > avg_long else "BEARISH 📉"
        
        # Signal
        signal = "KUTING ⏳"
        if rsi < 30:
            signal = "BUY 🟢 (Oversold)"
        elif rsi > 70:
            signal = "SELL 🔴 (Overbought)"
        elif avg_short > avg_long:
            signal = "BUY 🟢 (Trend yuqori)"
        
        return {
            'symbol': symbol,
            'price': ticker.get('last', 0),
            'change_24h': ticker.get('percentage', 0),
            'volume_24h': ticker.get('quoteVolume', 0),
            'high_24h': ticker.get('high', 0),
            'low_24h': ticker.get('low', 0),
            'rsi': round(rsi, 2),
            'trend': trend,
            'signal': signal,
        }
    except Exception as e:
        return {}
    finally:
        await exchange.close()


async def get_top_gainers(limit: int = 10) -> list:
    """Eng ko'p o'sgan kriptolar"""
    exchange = await get_mexc_exchange()
    try:
        tickers = await exchange.fetch_tickers()
        gainers = sorted(
            [(k, v) for k, v in tickers.items() 
             if '/USDT' in k and v.get('percentage') is not None and v.get('quoteVolume', 0) > 100000],
            key=lambda x: x[1].get('percentage', 0),
            reverse=True
        )[:limit]
        
        result = []
        for symbol, ticker in gainers:
            result.append({
                'symbol': symbol,
                'price': ticker.get('last', 0),
                'change': ticker.get('percentage', 0),
                'volume': ticker.get('quoteVolume', 0),
            })
        return result
    except Exception as e:
        return []
    finally:
        await exchange.close()


async def get_top_losers(limit: int = 10) -> list:
    """Eng ko'p tushgan kriptolar"""
    exchange = await get_mexc_exchange()
    try:
        tickers = await exchange.fetch_tickers()
        losers = sorted(
            [(k, v) for k, v in tickers.items() 
             if '/USDT' in k and v.get('percentage') is not None and v.get('quoteVolume', 0) > 100000],
            key=lambda x: x[1].get('percentage', 0)
        )[:limit]
        
        result = []
        for symbol, ticker in losers:
            result.append({
                'symbol': symbol,
                'price': ticker.get('last', 0),
                'change': ticker.get('percentage', 0),
                'volume': ticker.get('quoteVolume', 0),
            })
        return result
    except Exception as e:
        return []
    finally:
        await exchange.close()


async def place_order_ccxt(api_key: str, secret_key: str, symbol: str, 
                            side: str, amount: float, order_type: str = 'market') -> dict:
    """ccxt orqali order berish"""
    exchange = await get_mexc_exchange(api_key, secret_key)
    try:
        order = await exchange.create_order(
            symbol=symbol,
            type=order_type,
            side=side.lower(),
            amount=amount
        )
        return {'success': True, 'order': order}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        await exchange.close()


async def get_user_balance_ccxt(api_key: str, secret_key: str) -> dict:
    """ccxt orqali balans olish"""
    exchange = await get_mexc_exchange(api_key, secret_key)
    try:
        balance = await exchange.fetch_balance()
        non_zero = {
            asset: {'free': data['free'], 'total': data['total']}
            for asset, data in balance['total'].items()
            if data > 0
        }
        return {'success': True, 'balances': non_zero}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        await exchange.close()


async def get_open_orders_ccxt(api_key: str, secret_key: str, symbol: str = None) -> dict:
    """ccxt orqali ochiq orderlar"""
    exchange = await get_mexc_exchange(api_key, secret_key)
    try:
        orders = await exchange.fetch_open_orders(symbol)
        return {'success': True, 'orders': orders}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        await exchange.close()


def calculate_rsi(closes: list, period: int = 14) -> float:
    """RSI hisoblash"""
    if len(closes) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
