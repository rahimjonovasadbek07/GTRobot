# 🤖 GTRobot — MEXC Auto Trading Telegram Bot

## 📁 Loyiha tuzilmasi

```
gtrobot/
├── bot.py              # Asosiy fayl (ishga tushirish)
├── config.py           # Sozlamalar
├── requirements.txt    # Kutubxonalar
├── .env.example        # .env namunasi
├── database/
│   └── db.py           # SQLite ma'lumotlar bazasi
├── handlers/
│   ├── user.py         # Foydalanuvchi handlerlari
│   ├── trading.py      # Auto trading (MEXC API)
│   └── admin.py        # Admin panel
├── keyboards/
│   └── kb.py           # Tugmalar
└── utils/
    └── mexc_api.py     # MEXC birjasi API
```

---

## 🚀 O'rnatish va ishga tushirish

### 1. Python o'rnatish
```bash
python3 --version  # 3.9+ bo'lishi kerak
```

### 2. Virtual muhit yaratish (ixtiyoriy)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# yoki
venv\Scripts\activate  # Windows
```

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. .env faylini sozlash
```bash
cp .env.example .env
nano .env  # yoki notepad .env
```

`.env` faylini to'ldiring:
```env
BOT_TOKEN=sizning_bot_tokeningiz
ADMIN_IDS=sizning_telegram_id_ingiz
REQUIRED_CHANNEL=@sizning_kanalingiz
```

### 5. Botni ishga tushirish
```bash
python3 bot.py
```

---

## 🔑 Bot Token olish

1. Telegram da @BotFather ga yozing
2. `/newbot` yuboring
3. Bot nomini kiriting: `GTRobot`
4. Username kiriting: `gtrobot_savdo_bot`
5. Token ni nusxalab `.env` ga joylashtiring

---

## 🆔 Admin ID olish

1. @userinfobot ga `/start` yuboring
2. ID raqamni ko'ring: `Your id: 123456789`
3. `.env` dagi `ADMIN_IDS=` ga yozing

---

## 📋 Bot funksiyalari

### Foydalanuvchi uchun:
| Tugma | Vazifa |
|-------|--------|
| 💰 Balans | Balansni ko'rish va to'ldirish |
| 📋 Tarif | Kunlik/Oylik tarif sotib olish |
| 🤖 Auto Trading | MEXC API ulash va bot boshqarish |
| 📊 Copy Trading | Binance top treyderlar |
| 🆘 Qo'llab-quvvatlash | Admin bilan bog'lanish |

### Admin uchun (`/admin`):
| Tugma | Vazifa |
|-------|--------|
| 💵 Tarif narxini o'zgartirish | Narxlarni yangilash |
| 📢 Kanal qo'shish/o'chirish | Obuna kanallarni boshqarish |
| 📨 Xabar yuborish | Barcha foydalanuvchilarga broadcast |
| 📊 Statistika | Bot statistikasi |
| 👥 Foydalanuvchilar | Barchani ko'rish (API key bilan) |
| ✅ To'lovni tasdiqlash | Chek yuborilganda tasdiqlash |

---

## 💳 To'lov tizimi

Bot **qo'lda to'lov** (ruchnoy) tizimida ishlaydi:
1. Foydalanuvchi miqdorni tanlaydi
2. Karta raqami ko'rsatiladi
3. Foydalanuvchi chek rasmini yuboradi
4. Admin tasdiqlaydi → balans to'ldiriladi

**Karta raqamini o'zgartirish:** `handlers/user.py` da `process_receipt` funksiyasida `8600 1234 5678 9012` ni o'zgartiring.

---

## 🔗 MEXC API ulash

Foydalanuvchi uchun qadamlar:
1. `🤖 Auto Trading` → `🔑 API Kalitini kiriting`
2. mexc.com → Profile → API Management
3. `Create API` → HMAC tanlang
4. **Spot & Margin Trading** ruxsatini bering
5. API Key va Secret Key ni botga yuboring

---

## 🗄️ Ma'lumotlar bazasi

SQLite (`gtrobot.db`) - barcha ma'lumotlar:

**users jadvali:**
- `tg_id` — Telegram ID
- `username` — @username
- `full_name` — To'liq ism
- `balance` — UZS balance
- `tariff` / `tariff_expires` — Tarif ma'lumoti
- `mexc_api_key` / `mexc_secret_key` — MEXC API kalitlari
- `bot_active` — Bot holati

---

## 🔒 Xavfsizlik

- API kalitlar SQLite da saqlanadi
- Faqat admin `ADMIN_IDS` da ro'yxatga olinganlar panel ko'radi
- Har bir foydalanuvchi faqat o'z ma'lumotini ko'radi

---

## 📞 Yordam

Muammo yuzaga kelsa:
1. `gtrobot.db` ni o'chiring (yangi DB yaratiladi)
2. `requirements.txt` kutubxonalarini qayta o'rnating
3. `.env` faylini tekshiring
