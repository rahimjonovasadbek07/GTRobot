"""
Ko'p tilli tizim - O'zbek, Rus, Ingliz
"""

LANGS = {
    "uz": {
        "start_welcome": "👋 Salom, <b>{name}</b>!\n\n🤖 <b>GTRobot</b> — MEXC birjasida professional savdo roboti\n\n💰 Balans: <b>{balance:,.0f} UZS</b>\n📋 Tarif: <b>{tariff}</b>\n\n📌 Bo'limni tanlang:",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_set": "✅ Til o'zgartirildi!",
        "subscribe_required": "🔔 <b>Botdan foydalanish uchun kanalga obuna bo'ling:</b>",
        "check_sub": "✅ Obunani tekshirish",
        "sub_confirmed": "✅ Obuna tasdiqlandi!\n\n👋 Xush kelibsiz, <b>{name}</b>!",
        "sub_not_done": "❌ Hali kanalga obuna bo'lmadingiz!",
        "no_tariff": "⚠️ <b>Bu funksiya uchun tarif kerak!</b>\n\n📋 Tarif sotib olish uchun '📋 Tarif' ga o'ting.",
        "balance": "💰 Balans",
        "tariff": "📋 Tarif",
        "cloud_mining": "⛏️ Cloud Mining",
        "signals": "📡 Signallar",
        "auto_trading": "🤖 Auto Trading",
        "copy_trading": "📊 Copy Trading",
        "arbitraj": "🔺 Arbitraj",
        "history": "📈 Savdo tarixi",
        "referral": "👥 Referral",
        "guide": "📖 Qo'llanma",
        "support": "🆘 Qo'llab-quvvatlash",
        "settings": "⚙️ Sozlamalar",
        "topup": "💳 Balansni to'ldirish",
        "tariff_no": "❌ Yo'q",
        "admin_panel": "🔐 Admin panel",
    },
    "ru": {
        "start_welcome": "👋 Привет, <b>{name}</b>!\n\n🤖 <b>GTRobot</b> — профессиональный торговый робот на MEXC\n\n💰 Баланс: <b>{balance:,.0f} UZS</b>\n📋 Тариф: <b>{tariff}</b>\n\n📌 Выберите раздел:",
        "choose_lang": "🌐 Выберите язык:",
        "lang_set": "✅ Язык изменён!",
        "subscribe_required": "🔔 <b>Для использования бота подпишитесь на канал:</b>",
        "check_sub": "✅ Проверить подписку",
        "sub_confirmed": "✅ Подписка подтверждена!\n\n👋 Добро пожаловать, <b>{name}</b>!",
        "sub_not_done": "❌ Вы ещё не подписались на канал!",
        "no_tariff": "⚠️ <b>Для этой функции нужен тариф!</b>\n\n📋 Купите тариф в разделе '📋 Тариф'.",
        "balance": "💰 Баланс",
        "tariff": "📋 Тариф",
        "cloud_mining": "⛏️ Cloud Mining",
        "signals": "📡 Сигналы",
        "auto_trading": "🤖 Авто Трейдинг",
        "copy_trading": "📊 Копи Трейдинг",
        "arbitraj": "🔺 Арбитраж",
        "history": "📈 История сделок",
        "referral": "👥 Реферал",
        "guide": "📖 Руководство",
        "support": "🆘 Поддержка",
        "settings": "⚙️ Настройки",
        "topup": "💳 Пополнить баланс",
        "tariff_no": "❌ Нет",
        "admin_panel": "🔐 Панель админа",
    },
    "en": {
        "start_welcome": "👋 Hello, <b>{name}</b>!\n\n🤖 <b>GTRobot</b> — Professional trading robot on MEXC\n\n💰 Balance: <b>{balance:,.0f} UZS</b>\n📋 Tariff: <b>{tariff}</b>\n\n📌 Choose a section:",
        "choose_lang": "🌐 Choose language:",
        "lang_set": "✅ Language changed!",
        "subscribe_required": "🔔 <b>Please subscribe to the channel to use the bot:</b>",
        "check_sub": "✅ Check subscription",
        "sub_confirmed": "✅ Subscription confirmed!\n\n👋 Welcome, <b>{name}</b>!",
        "sub_not_done": "❌ You haven't subscribed to the channel yet!",
        "no_tariff": "⚠️ <b>This feature requires a tariff!</b>\n\nBuy a tariff in the '📋 Tariff' section.",
        "balance": "💰 Balance",
        "tariff": "📋 Tariff",
        "cloud_mining": "⛏️ Cloud Mining",
        "signals": "📡 Signals",
        "auto_trading": "🤖 Auto Trading",
        "copy_trading": "📊 Copy Trading",
        "arbitraj": "🔺 Arbitrage",
        "history": "📈 Trade history",
        "referral": "👥 Referral",
        "guide": "📖 Guide",
        "support": "🆘 Support",
        "settings": "⚙️ Settings",
        "topup": "💳 Top up balance",
        "tariff_no": "❌ None",
        "admin_panel": "🔐 Admin panel",
    }
}


def t(lang: str, key: str, **kwargs) -> str:
    """Tarjima olish"""
    lang = lang if lang in LANGS else "uz"
    text = LANGS[lang].get(key, LANGS["uz"].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def get_lang_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"))
    kb.add(InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"))
    kb.add(InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"))
    kb.adjust(3)
    return kb.as_markup()
