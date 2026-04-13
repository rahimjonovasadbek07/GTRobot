import hmac
import hashlib
import time
import aiohttp
import json
from config import MEXC_API_BASE, MEXC_FUTURES_BASE


def _sign(secret_key: str, params: dict) -> str:
    """MEXC HMAC SHA256 imzo yaratish"""
    query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(
        secret_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return signature


def _timestamp():
    return str(int(time.time() * 1000))


async def test_api_connection(api_key: str, secret_key: str) -> dict:
    """API kalitlarini tekshirish - account info olish"""
    ts = _timestamp()
    params = {"timestamp": ts}
    sig = hmac.new(
        secret_key.encode("utf-8"),
        f"timestamp={ts}".encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = sig

    headers = {
        "X-MEXC-APIKEY": api_key,
        "Content-Type": "application/json"
    }

    url = f"{MEXC_API_BASE}/api/v3/account"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return {"success": True, "data": data}
                else:
                    return {"success": False, "error": data.get("msg", "API xatosi")}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_spot_balance(api_key: str, secret_key: str) -> dict:
    """SPOT balansni olish"""
    ts = _timestamp()
    query = f"timestamp={ts}"
    sig = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()

    headers = {"X-MEXC-APIKEY": api_key}
    url = f"{MEXC_API_BASE}/api/v3/account"
    params = {"timestamp": ts, "signature": sig}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if resp.status == 200:
                    balances = {
                        b["asset"]: {"free": float(b["free"]), "locked": float(b["locked"])}
                        for b in data.get("balances", [])
                        if float(b["free"]) > 0 or float(b["locked"]) > 0
                    }
                    return {"success": True, "balances": balances}
                return {"success": False, "error": data.get("msg", "Xato")}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def place_spot_order(api_key: str, secret_key: str, symbol: str, side: str,
                           quantity: float, order_type: str = "MARKET") -> dict:
    """SPOT buyurtma berish
    side: BUY yoki SELL
    symbol: BTCUSDT kabi
    """
    ts = _timestamp()
    params = {
        "symbol": symbol.upper(),
        "side": side.upper(),
        "type": order_type,
        "quantity": str(quantity),
        "timestamp": ts
    }

    query = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    sig = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig

    headers = {
        "X-MEXC-APIKEY": api_key,
        "Content-Type": "application/json"
    }

    url = f"{MEXC_API_BASE}/api/v3/order"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return {"success": True, "order": data}
                return {"success": False, "error": data.get("msg", "Buyurtma xatosi")}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_futures_balance(api_key: str, secret_key: str) -> dict:
    """Futures balansni olish"""
    ts = _timestamp()
    query = f"timestamp={ts}"
    sig = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()

    headers = {"X-MEXC-APIKEY": api_key}
    url = f"{MEXC_API_BASE}/api/v3/account"
    params = {"timestamp": ts, "signature": sig}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if resp.status == 200:
                    usdt_balance = next(
                        (b for b in data.get("balances", []) if b["asset"] == "USDT"), None
                    )
                    return {
                        "success": True,
                        "usdt": float(usdt_balance["free"]) if usdt_balance else 0
                    }
                return {"success": False, "error": data.get("msg", "Xato")}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_market_price(symbol: str) -> dict:
    """Bozor narxini olish (API key shart emas)"""
    url = f"{MEXC_API_BASE}/api/v3/ticker/price"
    params = {"symbol": symbol.upper()}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return {"success": True, "price": float(data["price"]), "symbol": data["symbol"]}
                return {"success": False, "error": "Narx topilmadi"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_open_orders(api_key: str, secret_key: str, symbol: str = None) -> dict:
    """Ochiq buyurtmalarni olish"""
    ts = _timestamp()
    params_dict = {"timestamp": ts}
    if symbol:
        params_dict["symbol"] = symbol.upper()

    query = "&".join([f"{k}={v}" for k, v in sorted(params_dict.items())])
    sig = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
    params_dict["signature"] = sig

    headers = {"X-MEXC-APIKEY": api_key}
    url = f"{MEXC_API_BASE}/api/v3/openOrders"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params_dict, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return {"success": True, "orders": data}
                return {"success": False, "error": data.get("msg", "Xato")}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def cancel_order(api_key: str, secret_key: str, symbol: str, order_id: str) -> dict:
    """Buyurtmani bekor qilish"""
    ts = _timestamp()
    params_dict = {"symbol": symbol.upper(), "orderId": order_id, "timestamp": ts}

    query = "&".join([f"{k}={v}" for k, v in sorted(params_dict.items())])
    sig = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
    params_dict["signature"] = sig

    headers = {"X-MEXC-APIKEY": api_key}
    url = f"{MEXC_API_BASE}/api/v3/order"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers, params=params_dict, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                if resp.status == 200:
                    return {"success": True, "data": data}
                return {"success": False, "error": data.get("msg", "Xato")}
    except Exception as e:
        return {"success": False, "error": str(e)}
