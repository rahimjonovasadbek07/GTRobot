import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "837837025").split(",")]

# Majburiy kanallar - bu yerga o'zingizning kanalingizni yozing
REQUIRED_CHANNELS = [
    {"id": "-1002519689075", "name": "Grand Trade"}
]

MEXC_API_BASE = "https://api.mexc.com"
MEXC_FUTURES_BASE = "https://contract.mexc.com"

TARIFF_PRICES = {
    "daily": 5.0,      # 5 USDT kunlik
    "monthly": 50.0    # 50 USDT oylik
}

DB_PATH = "gtrobot.db"
