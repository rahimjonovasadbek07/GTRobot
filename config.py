import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "837837025").split(",")]

# Majburiy kanallar - env dan o'qiladi yoki hardcode
_ch_env = os.getenv("REQUIRED_CHANNEL", "")
if _ch_env:
    REQUIRED_CHANNELS = [
        {"id": ch_id.strip(), "name": f"Grand Trade {i+1}"}
        for i, ch_id in enumerate(_ch_env.split(","))
        if ch_id.strip()
    ]
else:
    REQUIRED_CHANNELS = [
        {"id": "-1001908526934", "name": "Grand Trade 1"},
        {"id": "-1002519689075", "name": "Grand Trade 2"},
    ]

MEXC_API_BASE = "https://api.mexc.com"
MEXC_FUTURES_BASE = "https://contract.mexc.com"

TARIFF_PRICES = {
    "daily": 5.0,
    "monthly": 50.0
}

DB_PATH = "gtrobot.db"