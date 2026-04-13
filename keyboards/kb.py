from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu(lang="uz") -> ReplyKeyboardMarkup:
    from utils.lang import t
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text=t(lang,"balance")), KeyboardButton(text=t(lang,"tariff")))
    kb.row(KeyboardButton(text=t(lang,"cloud_mining")), KeyboardButton(text=t(lang,"signals")))
    kb.row(KeyboardButton(text=t(lang,"auto_trading")), KeyboardButton(text=t(lang,"copy_trading")))
    kb.row(KeyboardButton(text=t(lang,"arbitraj")), KeyboardButton(text=t(lang,"history")))
    kb.row(KeyboardButton(text=t(lang,"referral")), KeyboardButton(text=t(lang,"guide")))
    kb.row(KeyboardButton(text=t(lang,"support")), KeyboardButton(text=t(lang,"settings")))
    return kb.as_markup(resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="📡 Signal yuborish"), KeyboardButton(text="📢 Kanal boshqaruv"))
    kb.row(KeyboardButton(text="💵 Tarif narxi"), KeyboardButton(text="💳 To'lov rekvizit"))
    kb.row(KeyboardButton(text="⛏️ Mining sozlama"), KeyboardButton(text="🔧 Bot sozlama"))
    kb.row(KeyboardButton(text="📊 Statistika"), KeyboardButton(text="✅ To'lov tasdiqlash"))
    kb.row(KeyboardButton(text="👥 Foydalanuvchilar"), KeyboardButton(text="📨 Xabar yuborish"))
    kb.row(KeyboardButton(text="🔙 Asosiy menyu"))
    return kb.as_markup(resize_keyboard=True)


def tariff_keyboard(daily_price, monthly_price) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=f"📅 Kunlik — {int(daily_price):,} UZS", callback_data="buy_daily"))
    kb.add(InlineKeyboardButton(text=f"📆 Oylik — {int(monthly_price):,} UZS", callback_data="buy_monthly"))
    kb.adjust(1)
    return kb.as_markup()


def balance_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="💳 Balansni to'ldirish", callback_data="topup_balance"))
    return kb.as_markup()


def topup_amount_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for a in [10000, 20000, 50000, 100000, 200000, 500000]:
        kb.add(InlineKeyboardButton(text=f"{a:,} UZS", callback_data=f"topup_{a}"))
    kb.add(InlineKeyboardButton(text="✏️ Boshqa miqdor", callback_data="topup_custom"))
    kb.adjust(2)
    return kb.as_markup()


def payment_confirm_keyboard(payment_id, tg_id, tariff) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_pay_{payment_id}_{tg_id}_{tariff}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_pay_{payment_id}_{tg_id}")
    )
    return kb.as_markup()


def channels_keyboard(channels) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        kb.add(InlineKeyboardButton(text=f"❌ {ch[2]} ({ch[1]})", callback_data=f"del_channel_{ch[0]}"))
    kb.add(InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel"))
    kb.adjust(1)
    return kb.as_markup()


def check_sub_keyboard(channels) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for ch in channels:
        ch_id = ch["id"] if isinstance(ch, dict) else ch[1]
        ch_name = ch["name"] if isinstance(ch, dict) else ch[2]
        if ch_id.startswith("-100"):
            link = f"https://t.me/c/{ch_id[4:]}"
        else:
            link = f"https://t.me/{ch_id.lstrip('@')}"
        kb.add(InlineKeyboardButton(text=f"📢 {ch_name}", url=link))
    kb.add(InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub"))
    kb.adjust(1)
    return kb.as_markup()


def signal_keyboard(signal_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="✅ Signalni yopish", callback_data=f"close_signal_{signal_id}"))
    return kb.as_markup()


def copy_trading_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="📈 Binance Copy Trading", url="https://www.binance.com/en/copy-trading"))
    kb.add(InlineKeyboardButton(text="📊 MEXC Copy Trading", url="https://www.mexc.com/copy-trade"))
    kb.adjust(1)
    return kb.as_markup()


def cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="❌ Bekor qilish"))
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)
