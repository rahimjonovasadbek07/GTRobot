import sqlite3
from datetime import datetime
from config import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # Foydalanuvchilar
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 0,
            tariff TEXT DEFAULT NULL,
            tariff_expires TEXT DEFAULT NULL,
            mexc_api_key TEXT DEFAULT NULL,
            mexc_secret_key TEXT DEFAULT NULL,
            bot_active INTEGER DEFAULT 0,
            referral_code TEXT UNIQUE,
            referred_by INTEGER DEFAULT NULL,
            referral_bonus REAL DEFAULT 0,
            lang TEXT DEFAULT 'uz',
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tarif narxlari
    c.execute("""
        CREATE TABLE IF NOT EXISTS tariff_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tariff_type TEXT UNIQUE,
            price REAL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # To'lov rekvizitlari
    c.execute("""
        CREATE TABLE IF NOT EXISTS payment_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT DEFAULT '',
            network TEXT DEFAULT 'TRC20',
            currency TEXT DEFAULT 'USDT',
            card_number TEXT DEFAULT '',
            card_owner TEXT DEFAULT 'Grand Trade',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Kanallar
    c.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE,
            channel_name TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # To'lovlar
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            amount REAL,
            tariff_type TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Signallar
    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            symbol TEXT,
            direction TEXT,
            leverage INTEGER,
            entry_price REAL,
            take_profit REAL,
            stop_loss REAL,
            status TEXT DEFAULT 'active',
            message_text TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Savdo tarixi
    c.execute("""
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            signal_id INTEGER,
            symbol TEXT,
            direction TEXT,
            leverage INTEGER,
            entry_price REAL,
            take_profit REAL,
            stop_loss REAL,
            order_id TEXT,
            status TEXT DEFAULT 'open',
            pnl REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            closed_at TEXT DEFAULT NULL
        )
    """)

    # Mining
    c.execute("""
        CREATE TABLE IF NOT EXISTS mining_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER UNIQUE,
            plan_name TEXT,
            hourly_uzs INTEGER,
            daily_price INTEGER,
            weekly_price INTEGER,
            monthly_price INTEGER,
            daily_earn INTEGER,
            weekly_earn INTEGER,
            monthly_earn INTEGER,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_mining (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            plan_id INTEGER,
            plan_name TEXT,
            hourly_income REAL,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            total_earned REAL DEFAULT 0,
            last_payout TEXT DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mining_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            amount REAL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Standart narxlar
    c.execute("INSERT OR IGNORE INTO tariff_prices (tariff_type, price) VALUES (?, ?)", ("daily", 5.0))
    c.execute("INSERT OR IGNORE INTO tariff_prices (tariff_type, price) VALUES (?, ?)", ("monthly", 50.0))

    # Standart to'lov rekvizitlari
    c.execute("INSERT OR IGNORE INTO payment_settings (id, wallet_address, network, currency) VALUES (1, '', 'TRC20', 'USDT')")

    # Standart mining sozlamalari
    # Mining USDT da: (plan_id, name, hourly, daily_price, weekly_price, monthly_price, daily_earn, weekly_earn, monthly_earn)
    default_plans = [
        (1, "⛏️ Miner v1", 0.0005, 1.0, 6.0, 20.0, 0.012, 0.084, 0.36),
        (2, "⛏️ Miner v2", 0.002, 3.0, 18.0, 60.0, 0.048, 0.336, 1.44),
        (3, "⛏️ Miner v3", 0.008, 10.0, 60.0, 200.0, 0.192, 1.344, 5.76),
    ]
    for p in default_plans:
        c.execute("""
            INSERT OR IGNORE INTO mining_settings
            (plan_id, plan_name, hourly_uzs, daily_price, weekly_price, monthly_price, daily_earn, weekly_earn, monthly_earn)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, p)

    conn.commit()
    conn.close()


# ===== USER =====
def get_user(tg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,))
    row = c.fetchone()
    conn.close()
    if row:
        cols = ["tg_id","username","full_name","balance","tariff","tariff_expires",
                "mexc_api_key","mexc_secret_key","bot_active","referral_code",
                "referred_by","referral_bonus","lang","registered_at"]
        return dict(zip(cols, row))
    return None


def register_user(tg_id, username, full_name, referred_by=None):
    import random, string
    ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO users (tg_id, username, full_name, referral_code, referred_by)
        VALUES (?, ?, ?, ?, ?)
    """, (tg_id, username, full_name, ref_code, referred_by))
    c.execute("UPDATE users SET username=?, full_name=? WHERE tg_id=?", (username, full_name, tg_id))
    conn.commit()
    conn.close()


def set_user_lang(tg_id, lang):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE tg_id=?", (lang, tg_id))
    conn.commit()
    conn.close()


def update_balance(tg_id, amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE tg_id=?", (amount, tg_id))
    conn.commit()
    conn.close()


def set_tariff(tg_id, tariff_type, expires):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET tariff=?, tariff_expires=? WHERE tg_id=?", (tariff_type, expires, tg_id))
    conn.commit()
    conn.close()


def save_api_keys(tg_id, api_key, secret_key):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET mexc_api_key=?, mexc_secret_key=? WHERE tg_id=?", (api_key, secret_key, tg_id))
    conn.commit()
    conn.close()


def set_bot_active(tg_id, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET bot_active=? WHERE tg_id=?", (status, tg_id))
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id,username,full_name,balance,tariff,tariff_expires,mexc_api_key,mexc_secret_key,bot_active,referral_code,referred_by,referral_bonus FROM users")
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_count():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_active_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE bot_active=1")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_users_with_active_bot():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id, mexc_api_key, mexc_secret_key FROM users WHERE bot_active=1 AND mexc_api_key IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_by_referral(ref_code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id FROM users WHERE referral_code=?", (ref_code,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def get_referral_stats(tg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE referred_by=?", (tg_id,))
    count = c.fetchone()[0]
    c.execute("SELECT referral_bonus FROM users WHERE tg_id=?", (tg_id,))
    row = c.fetchone()
    bonus = row[0] if row else 0
    conn.close()
    return {"count": count, "bonus": bonus}


def has_active_tariff(tg_id):
    """Foydalanuvchi faol tarifi bormi"""
    user = get_user(tg_id)
    if not user or not user.get("tariff") or not user.get("tariff_expires"):
        return False
    try:
        exp = datetime.fromisoformat(user["tariff_expires"])
        return exp > datetime.now()
    except Exception:
        return False


# ===== TARIF =====
def get_tariff_prices():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tariff_type, price FROM tariff_prices")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def update_tariff_price(tariff_type, price):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE tariff_prices SET price=? WHERE tariff_type=?", (price, tariff_type))
    conn.commit()
    conn.close()


# ===== TO'LOV REKVIZITLARI =====
def get_payment_settings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT wallet_address, network, currency, card_number, card_owner FROM payment_settings WHERE id=1")
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "wallet_address": row[0],
            "network": row[1],
            "currency": row[2],
            "card_number": row[3],
            "card_owner": row[4],
        }
    return {"wallet_address": "", "network": "TRC20", "currency": "USDT", "card_number": "", "card_owner": "Grand Trade"}


def update_payment_settings(wallet_address=None, network=None, currency=None, card_number=None, card_owner=None):
    conn = get_conn()
    c = conn.cursor()
    if wallet_address is not None:
        c.execute("UPDATE payment_settings SET wallet_address=? WHERE id=1", (wallet_address,))
    if network is not None:
        c.execute("UPDATE payment_settings SET network=? WHERE id=1", (network,))
    if currency is not None:
        c.execute("UPDATE payment_settings SET currency=? WHERE id=1", (currency,))
    if card_number is not None:
        c.execute("UPDATE payment_settings SET card_number=? WHERE id=1", (card_number,))
    if card_owner is not None:
        c.execute("UPDATE payment_settings SET card_owner=? WHERE id=1", (card_owner,))
    conn.commit()
    conn.close()


# ===== KANALLAR =====
def get_channels():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, channel_id, channel_name FROM channels")
    rows = c.fetchall()
    conn.close()
    return rows


def add_channel(channel_id, channel_name):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO channels (channel_id, channel_name) VALUES (?, ?)", (channel_id, channel_name))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False


def remove_channel(channel_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM channels WHERE id=?", (channel_id,))
    conn.commit()
    conn.close()


# ===== TO'LOV =====
def create_payment(tg_id, amount, tariff_type):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO payments (tg_id, amount, tariff_type) VALUES (?, ?, ?)", (tg_id, amount, tariff_type))
    pid = c.lastrowid
    conn.commit()
    conn.close()
    return pid


def confirm_payment(payment_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE payments SET status='confirmed' WHERE id=?", (payment_id,))
    c.execute("SELECT tg_id, amount, tariff_type FROM payments WHERE id=?", (payment_id,))
    row = c.fetchone()
    conn.commit()
    conn.close()
    return row


def get_revenue_stats():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM payments WHERE status='confirmed'")
    total = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM payments WHERE status='confirmed'")
    count = c.fetchone()[0] or 0
    conn.close()
    return {"total": total, "count": count}


# ===== SIGNAL =====
def save_signal(admin_id, symbol, direction, leverage, entry_price, take_profit, stop_loss, message_text):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO signals (admin_id, symbol, direction, leverage, entry_price, take_profit, stop_loss, message_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (admin_id, symbol, direction, leverage, entry_price, take_profit, stop_loss, message_text))
    sid = c.lastrowid
    conn.commit()
    conn.close()
    return sid


def get_active_signals():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM signals WHERE status='active' ORDER BY created_at DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_signals(limit=20):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM signals ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows


def close_signal(signal_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE signals SET status='closed' WHERE id=?", (signal_id,))
    conn.commit()
    conn.close()


# ===== SAVDO TARIXI =====
def save_trade(tg_id, signal_id, symbol, direction, leverage, entry_price, take_profit, stop_loss, order_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO trade_history (tg_id, signal_id, symbol, direction, leverage, entry_price, take_profit, stop_loss, order_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tg_id, signal_id, symbol, direction, leverage, entry_price, take_profit, stop_loss, order_id))
    conn.commit()
    conn.close()


def get_user_trades(tg_id, limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT symbol, direction, leverage, entry_price, take_profit, stop_loss, status, pnl, created_at
        FROM trade_history WHERE tg_id=? ORDER BY created_at DESC LIMIT ?
    """, (tg_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


def get_trade_stats(tg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM trade_history WHERE tg_id=?", (tg_id,))
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trade_history WHERE tg_id=? AND status='closed' AND pnl>0", (tg_id,))
    wins = c.fetchone()[0]
    c.execute("SELECT SUM(pnl) FROM trade_history WHERE tg_id=?", (tg_id,))
    total_pnl = c.fetchone()[0] or 0
    conn.close()
    return {"total": total, "wins": wins, "pnl": total_pnl}


# ===== MINING =====
def get_mining_plans_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM mining_settings ORDER BY plan_id")
    rows = c.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "id": r[1],
            "name": r[2],
            "hourly_uzs": r[3],
            "daily_price": r[4],
            "weekly_price": r[5],
            "monthly_price": r[6],
            "daily_earn": r[7],
            "weekly_earn": r[8],
            "monthly_earn": r[9],
        })
    return result


def update_mining_plan(plan_id, hourly_uzs=None, daily_price=None, weekly_price=None,
                       monthly_price=None, daily_earn=None, weekly_earn=None, monthly_earn=None):
    conn = get_conn()
    c = conn.cursor()
    fields = []
    values = []
    if hourly_uzs is not None:
        fields.append("hourly_uzs=?"); values.append(hourly_uzs)
    if daily_price is not None:
        fields.append("daily_price=?"); values.append(daily_price)
    if weekly_price is not None:
        fields.append("weekly_price=?"); values.append(weekly_price)
    if monthly_price is not None:
        fields.append("monthly_price=?"); values.append(monthly_price)
    if daily_earn is not None:
        fields.append("daily_earn=?"); values.append(daily_earn)
    if weekly_earn is not None:
        fields.append("weekly_earn=?"); values.append(weekly_earn)
    if monthly_earn is not None:
        fields.append("monthly_earn=?"); values.append(monthly_earn)
    if fields:
        values.append(plan_id)
        c.execute(f"UPDATE mining_settings SET {', '.join(fields)} WHERE plan_id=?", values)
        conn.commit()
    conn.close()


def get_user_mining(tg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM user_mining WHERE tg_id=? AND is_active=1 ORDER BY started_at DESC LIMIT 1", (tg_id,))
    row = c.fetchone()
    conn.close()
    if row:
        cols = ["id","tg_id","plan_id","plan_name","hourly_income","started_at","expires_at","total_earned","last_payout","is_active"]
        return dict(zip(cols, row))
    return None


def start_mining(tg_id, plan_id, plan_name, hourly_income, expires_at):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE user_mining SET is_active=0 WHERE tg_id=?", (tg_id,))
    c.execute("""
        INSERT INTO user_mining (tg_id, plan_id, plan_name, hourly_income, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (tg_id, plan_id, plan_name, hourly_income, expires_at))
    conn.commit()
    conn.close()


def add_mining_earnings(tg_id, amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE user_mining SET total_earned=total_earned+?, last_payout=CURRENT_TIMESTAMP WHERE tg_id=? AND is_active=1", (amount, tg_id))
    c.execute("UPDATE users SET balance=balance+? WHERE tg_id=?", (amount, tg_id))
    c.execute("INSERT INTO mining_history (tg_id, amount, description) VALUES (?, ?, ?)", (tg_id, amount, "Mining daromad"))
    conn.commit()
    conn.close()


def stop_mining(tg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE user_mining SET is_active=0 WHERE tg_id=?", (tg_id,))
    conn.commit()
    conn.close()


def get_all_active_miners():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT tg_id, hourly_income, last_payout, expires_at FROM user_mining WHERE is_active=1")
    rows = c.fetchall()
    conn.close()
    return rows


def get_mining_stats(tg_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT plan_name, hourly_income, started_at, expires_at, total_earned, last_payout FROM user_mining WHERE tg_id=? AND is_active=1", (tg_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"plan_name": row[0], "hourly_income": row[1], "started_at": row[2], "expires_at": row[3], "total_earned": row[4], "last_payout": row[5]}
    return None

# Mining plan functions for backward compat
def get_mining_plans():
    return get_mining_plans_db()


# ===== SOZLAMALAR (Admin) =====
def get_bot_settings():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    defaults = {
        "referral_bonus": "5000",
        "support_username": "@grandtrade_admin",
        "support_text": "📱 Admin: @grandtrade_admin\n⏰ 9:00 — 22:00",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()

    c.execute("SELECT key, value FROM bot_settings")
    rows = c.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def set_bot_setting(key: str, value: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    c.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
