import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "837837025").split(",")]

# Majburiy kanallar
REQUIRED_CHANNELS = [
    {"id": "-1001908526934", "name": "Crypto Savdosi", "link": "https://t.me/crypto_savdosi"},
    {"id": "-1002519689075", "name": "IT Studio Uz", "link": "https://t.me/ITstudio_uz"},
]

MEXC_API_BASE = "https://api.mexc.com"
MEXC_FUTURES_BASE = "https://contract.mexc.com"

TARIFF_PRICES = {
    "daily": 5.0,
    "monthly": 50.0
}

DB_PATH = "gtrobot.db"