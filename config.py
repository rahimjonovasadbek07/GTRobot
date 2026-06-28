import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "837837025").split(",")]

REQUIRED_CHANNELS = [
    {"id": "@cryptosavdosi", "name": "Crypto Savdosi"},
    {"id": "@crypto_savdosi", "name": "Crypto Savdosi 2"},
]

MEXC_API_BASE = "https://api.mexc.com"
MEXC_FUTURES_BASE = "https://contract.mexc.com"

TARIFF_PRICES = {
    "daily": 5.0,
    "monthly": 50.0
}

DB_PATH = "ai_trading_bot.db"

BACKUP_CHANNEL_ID = os.getenv("BACKUP_CHANNEL_ID", "")