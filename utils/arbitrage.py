"""
Uchburchak Arbitraj - MEXC birjasi ichida
Misol: USDT → BTC → ETH → USDT
Bot o'zi topib avtomatik bajaradi
"""
import ccxt.async_support as ccxt
import asyncio
import itertools
from typing import Optional


async def get_exchange(api_key: str = None, secret_key: str = None):
    config = {'enableRateLimit': True, 'timeout': 10000}
    if api_key and secret_key:
        config['apiKey'] = api_key
        config['secret'] = secret_key
    return ccxt.mexc(config)


async def find_triangular_opportunities(min_profit: float = 0.3) -> list:
    """
    Uchburchak arbitraj imkoniyatlarini topish
    min_profit: minimal foydalilik % (0.3 = 0.3%)
    """
    exchange = await get_exchange()
    opportunities = []
    
    try:
        # Barcha bozor ma'lumotlarini olish
        tickers = await exchange.fetch_tickers()
        markets = await exchange.load_markets()
        
        # USDT juftliklarini olish
        usdt_pairs = {
            k: v for k, v in tickers.items() 
            if k.endswith('/USDT') and v.get('ask') and v.get('bid')
        }
        
        # Asosiy kriptolar (likvidligi yuqori)
        base_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'MATIC', 'LINK', 'AVAX']
        
        # Uchburchak topish: USDT → A → B → USDT
        for coin_a in base_coins:
            for coin_b in base_coins:
                if coin_a == coin_b:
                    continue
                
                pair_a = f"{coin_a}/USDT"  # USDT → A
                pair_b = f"{coin_b}/USDT"  # B → USDT
                pair_ab = f"{coin_a}/{coin_b}"  # A → B yoki
                pair_ba = f"{coin_b}/{coin_a}"  # B → A
                
                # 1-yo'l: USDT → A → B → USDT
                if pair_a in tickers and pair_b in tickers and pair_ab in tickers:
                    try:
                        ask_a = tickers[pair_a].get('ask', 0)   # A sotib olish narxi
                        bid_b = tickers[pair_b].get('bid', 0)   # B sotish narxi
                        bid_ab = tickers[pair_ab].get('bid', 0)  # A → B
                        
                        if ask_a > 0 and bid_b > 0 and bid_ab > 0:
                            # 1 USDT bilan hisoblash
                            amount_a = 1.0 / ask_a          # Qancha A olamiz
                            amount_b = amount_a * bid_ab     # Qancha B olamiz  
                            final_usdt = amount_b * bid_b    # Necha USDT qaytadi
                            
                            # Komissiya (0.1% * 3 = 0.3%)
                            commission = 0.003
                            net_profit = (final_usdt - 1.0) - commission
                            profit_pct = net_profit * 100
                            
                            if profit_pct > min_profit:
                                opportunities.append({
                                    'path': f"USDT → {coin_a} → {coin_b} → USDT",
                                    'profit_pct': round(profit_pct, 4),
                                    'profit_usdt': round(net_profit, 6),
                                    'pairs': [pair_a, pair_ab, pair_b],
                                    'sides': ['buy', 'sell', 'sell'],
                                    'details': {
                                        f'{pair_a} ask': ask_a,
                                        f'{pair_ab} bid': bid_ab,
                                        f'{pair_b} bid': bid_b,
                                    }
                                })
                    except Exception:
                        continue
                
                # 2-yo'l: USDT → B → A → USDT
                if pair_b in tickers and pair_a in tickers and pair_ba in tickers:
                    try:
                        ask_b = tickers[pair_b].get('ask', 0)
                        bid_a = tickers[pair_a].get('bid', 0)
                        bid_ba = tickers[pair_ba].get('bid', 0)
                        
                        if ask_b > 0 and bid_a > 0 and bid_ba > 0:
                            amount_b = 1.0 / ask_b
                            amount_a = amount_b * bid_ba
                            final_usdt = amount_a * bid_a
                            
                            commission = 0.003
                            net_profit = (final_usdt - 1.0) - commission
                            profit_pct = net_profit * 100
                            
                            if profit_pct > min_profit:
                                opportunities.append({
                                    'path': f"USDT → {coin_b} → {coin_a} → USDT",
                                    'profit_pct': round(profit_pct, 4),
                                    'profit_usdt': round(net_profit, 6),
                                    'pairs': [pair_b, pair_ba, pair_a],
                                    'sides': ['buy', 'sell', 'sell'],
                                    'details': {
                                        f'{pair_b} ask': ask_b,
                                        f'{pair_ba} bid': bid_ba,
                                        f'{pair_a} bid': bid_a,
                                    }
                                })
                    except Exception:
                        continue
        
        # Foydalilik bo'yicha saralash
        opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
        return opportunities[:10]  # Top 10
        
    except Exception as e:
        return []
    finally:
        await exchange.close()


async def execute_triangular_arbitrage(api_key: str, secret_key: str, 
                                        opportunity: dict, usdt_amount: float) -> dict:
    """Arbitrajni bajarish"""
    exchange = await get_exchange(api_key, secret_key)
    results = []
    
    try:
        pairs = opportunity['pairs']
        sides = opportunity['sides']
        path = opportunity['path']
        
        # 1-trade
        ticker1 = await exchange.fetch_ticker(pairs[0])
        price1 = ticker1['ask'] if sides[0] == 'buy' else ticker1['bid']
        amount1 = usdt_amount / price1 if sides[0] == 'buy' else usdt_amount
        
        order1 = await exchange.create_market_order(pairs[0], sides[0], amount1)
        results.append({'pair': pairs[0], 'side': sides[0], 'order': order1.get('id', '?')})
        
        await asyncio.sleep(0.5)
        
        # 2-trade
        filled1 = order1.get('filled', amount1)
        ticker2 = await exchange.fetch_ticker(pairs[1])
        price2 = ticker2['ask'] if sides[1] == 'buy' else ticker2['bid']
        amount2 = filled1
        
        order2 = await exchange.create_market_order(pairs[1], sides[1], amount2)
        results.append({'pair': pairs[1], 'side': sides[1], 'order': order2.get('id', '?')})
        
        await asyncio.sleep(0.5)
        
        # 3-trade
        filled2 = order2.get('filled', amount2)
        order3 = await exchange.create_market_order(pairs[2], sides[2], filled2)
        results.append({'pair': pairs[2], 'side': sides[2], 'order': order3.get('id', '?')})
        
        return {
            'success': True,
            'path': path,
            'trades': results,
            'expected_profit': opportunity['profit_pct']
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e), 'completed_trades': results}
    finally:
        await exchange.close()


async def monitor_arbitrage_loop(bot, user_id: int, api_key: str, secret_key: str,
                                  usdt_amount: float = 10.0, min_profit: float = 0.5):
    """
    Doimiy arbitraj monitoring
    Foyda topilsa avtomatik bajaradi va foydalanuvchiga xabar beradi
    """
    while True:
        try:
            opportunities = await find_triangular_opportunities(min_profit)
            
            if opportunities:
                best = opportunities[0]
                
                # Foydalanuvchiga xabar
                msg = (
                    f"🔺 <b>Arbitraj topildi!</b>\n\n"
                    f"📍 Yo'l: {best['path']}\n"
                    f"💰 Foyda: <b>+{best['profit_pct']}%</b>\n"
                    f"💵 {usdt_amount} USDT → +{usdt_amount * best['profit_usdt']:.4f} USDT\n\n"
                    f"⚡️ Bajarilmoqda..."
                )
                await bot.send_message(user_id, msg)
                
                # Avtomatik bajarish
                result = await execute_triangular_arbitrage(
                    api_key, secret_key, best, usdt_amount
                )
                
                if result['success']:
                    await bot.send_message(
                        user_id,
                        f"✅ <b>Arbitraj muvaffaqiyatli!</b>\n\n"
                        f"📍 {result['path']}\n"
                        f"💰 Kutilgan foyda: +{result['expected_profit']}%"
                    )
                else:
                    await bot.send_message(
                        user_id,
                        f"❌ <b>Arbitraj xatosi:</b>\n{result['error']}"
                    )
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            pass
        
        # 30 soniyada bir tekshirish
        await asyncio.sleep(30)
