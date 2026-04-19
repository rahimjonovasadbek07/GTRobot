from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user

router = Router()

GUIDE_TX = {
    "uz": {
        "title": "📖 <b>GTRobot Qo'llanma</b>",
        "select": "Quyidagi bo'limlardan birini tanlang:",
        "back_btn": "🔙 Qo'llanmaga qaytish",
        "btn_api": "🔑 MEXC API olish",
        "btn_auto": "🤖 Auto Trading",
        "btn_copy": "📊 Copy Trading",
        "btn_arb": "🔺 Arbitraj",
        "btn_sig": "📡 Signallar",
        "btn_bal": "💰 Balans & Tarif",
        "btn_ref": "👥 Referral",
        "btn_faq": "❓ FAQ",
    },
    "ru": {
        "title": "📖 <b>Руководство GTRobot</b>",
        "select": "Выберите раздел:",
        "back_btn": "🔙 Назад к руководству",
        "btn_api": "🔑 Получить MEXC API",
        "btn_auto": "🤖 Auto Trading",
        "btn_copy": "📊 Copy Trading",
        "btn_arb": "🔺 Арбитраж",
        "btn_sig": "📡 Сигналы",
        "btn_bal": "💰 Баланс & Тариф",
        "btn_ref": "👥 Реферал",
        "btn_faq": "❓ FAQ",
    },
    "en": {
        "title": "📖 <b>GTRobot Guide</b>",
        "select": "Choose a section:",
        "back_btn": "🔙 Back to guide",
        "btn_api": "🔑 Get MEXC API",
        "btn_auto": "🤖 Auto Trading",
        "btn_copy": "📊 Copy Trading",
        "btn_arb": "🔺 Arbitrage",
        "btn_sig": "📡 Signals",
        "btn_bal": "💰 Balance & Tariff",
        "btn_ref": "👥 Referral",
        "btn_faq": "❓ FAQ",
    },
}

GUIDE_CONTENT = {
    "mexc_api": {
        "uz": "🔑 <b>MEXC API olish — Qadamma-qadam</b>\n\n<b>1-qadam: MEXC ga kiring</b>\n• mexc.com saytiga yoki ilovasiga kiring\n• Hisobingizga login qiling\n\n<b>2-qadam: KYC tasdiqlash</b>\n• Profile → Verification ga o'ting\n• Pasport yoki ID karta rasmini yuklang\n• 10-30 daqiqada tasdiqlanadi\n\n<b>3-qadam: API Management</b>\n• Profile → API Management\n• Create API bosing, HMAC tanlang\n\n<b>4-qadam: Ruxsatlar</b>\n✅ Spot → Trade\n✅ Futures → Order Placing\n❌ Withdraw — BELGILAMANG!\n❌ Transfer — BELGILAMANG!\n\n<b>5-qadam: Botga ulash</b>\n• 🤖 Auto Trading → 🔑 MEXC API ulash\n• Access Key va Secret Key yuboring",
        "ru": "🔑 <b>Получение MEXC API — Пошагово</b>\n\n<b>Шаг 1: Войдите в MEXC</b>\n• Перейдите на mexc.com или в приложение\n• Войдите в свой аккаунт\n\n<b>Шаг 2: KYC верификация</b>\n• Profile → Verification\n• Загрузите фото паспорта или ID\n• Подтверждение за 10-30 минут\n\n<b>Шаг 3: Управление API</b>\n• Profile → API Management\n• Create API, выберите HMAC\n\n<b>Шаг 4: Разрешения</b>\n✅ Spot → Trade\n✅ Futures → Order Placing\n❌ Withdraw — НЕ ОТМЕЧАЙТЕ!\n❌ Transfer — НЕ ОТМЕЧАЙТЕ!\n\n<b>Шаг 5: Подключение к боту</b>\n• 🤖 Auto Trading → 🔑 Подключить MEXC API\n• Введите Access Key и Secret Key",
        "en": "🔑 <b>Getting MEXC API — Step by Step</b>\n\n<b>Step 1: Log into MEXC</b>\n• Go to mexc.com or the app\n• Log into your account\n\n<b>Step 2: KYC Verification</b>\n• Profile → Verification\n• Upload passport or ID photo\n• Approved in 10-30 minutes\n\n<b>Step 3: API Management</b>\n• Profile → API Management\n• Create API, select HMAC\n\n<b>Step 4: Permissions</b>\n✅ Spot → Trade\n✅ Futures → Order Placing\n❌ Withdraw — DO NOT CHECK!\n❌ Transfer — DO NOT CHECK!\n\n<b>Step 5: Connect to bot</b>\n• 🤖 Auto Trading → 🔑 Connect MEXC API\n• Enter Access Key and Secret Key",
    },
    "auto_trading": {
        "uz": "🤖 <b>Auto Trading — Qo'llanma</b>\n\nAdmin signal yuborganda bot avtomatik order ochadi.\n\n<b>1-qadam:</b> MEXC API ulash\n<b>2-qadam:</b> Tarif sotib olish\n<b>3-qadam:</b> Botni faollashtirish\n\nSignal kelganda bot avtomatik ishlaydi! ✅\n\n⚠️ MEXC da yetarli USDT bo'lishi kerak.",
        "ru": "🤖 <b>Auto Trading — Руководство</b>\n\nКогда админ присылает сигнал, бот автоматически открывает ордер.\n\n<b>Шаг 1:</b> Подключить MEXC API\n<b>Шаг 2:</b> Купить тариф\n<b>Шаг 3:</b> Активировать бота\n\nСигнал пришёл — бот работает автоматически! ✅\n\n⚠️ На MEXC должно быть достаточно USDT.",
        "en": "🤖 <b>Auto Trading — Guide</b>\n\nWhen admin sends a signal, bot automatically opens an order.\n\n<b>Step 1:</b> Connect MEXC API\n<b>Step 2:</b> Buy a tariff\n<b>Step 3:</b> Activate the bot\n\nSignal arrives — bot works automatically! ✅\n\n⚠️ You need enough USDT on MEXC.",
    },
    "copy_trading": {
        "uz": "📊 <b>Copy Trading — Qo'llanma</b>\n\nMEXC birjasidagi real vaqt ma'lumotlarini ko'rish va tahlil qilish.\n\n🔥 <b>Top 20 Volume</b> — eng aktiv juftliklar\n📈 <b>Top Gainers</b> — eng ko'p o'sganlar\n📉 <b>Top Losers</b> — eng ko'p tushganlar\n🔍 <b>Juftlik tahlili</b> — RSI va trend\n\n<b>RSI:</b>\n• RSI < 30 → Sotib olish vaqti 🟢\n• RSI > 70 → Sotish vaqti 🔴",
        "ru": "📊 <b>Copy Trading — Руководство</b>\n\nПросмотр и анализ данных биржи MEXC в реальном времени.\n\n🔥 <b>Top 20 Volume</b> — самые активные пары\n📈 <b>Top Gainers</b> — наибольший рост\n📉 <b>Top Losers</b> — наибольшее падение\n🔍 <b>Анализ пары</b> — RSI и тренд\n\n<b>RSI:</b>\n• RSI < 30 → Время покупать 🟢\n• RSI > 70 → Время продавать 🔴",
        "en": "📊 <b>Copy Trading — Guide</b>\n\nView and analyze MEXC exchange data in real time.\n\n🔥 <b>Top 20 Volume</b> — most active pairs\n📈 <b>Top Gainers</b> — biggest gainers\n📉 <b>Top Losers</b> — biggest losers\n🔍 <b>Pair analysis</b> — RSI and trend\n\n<b>RSI:</b>\n• RSI < 30 → Time to buy 🟢\n• RSI > 70 → Time to sell 🔴",
    },
    "arbitrage": {
        "uz": "🔺 <b>Uchburchak Arbitraj — Qo'llanma</b>\n\nBir birja ichida 3 ta juftlik orqali narx farqidan foyda qilish.\n\n<b>Misol:</b>\n1️⃣ 100 USDT → BTC\n2️⃣ BTC → ETH\n3️⃣ ETH → USDT = 100.5 USDT (+0.5%)\n\n• Minimal 10 USDT kerak\n• 0.3% minimal foyda tavsiya etiladi\n• Komissiya: 0.1% × 3 = 0.3%",
        "ru": "🔺 <b>Треугольный Арбитраж — Руководство</b>\n\nПолучение прибыли из разницы цен через 3 пары.\n\n<b>Пример:</b>\n1️⃣ 100 USDT → BTC\n2️⃣ BTC → ETH\n3️⃣ ETH → USDT = 100.5 USDT (+0.5%)\n\n• Минимум 10 USDT\n• Рекомендуется мин. прибыль 0.3%\n• Комиссия: 0.1% × 3 = 0.3%",
        "en": "🔺 <b>Triangular Arbitrage — Guide</b>\n\nProfit from price differences through 3 pairs.\n\n<b>Example:</b>\n1️⃣ 100 USDT → BTC\n2️⃣ BTC → ETH\n3️⃣ ETH → USDT = 100.5 USDT (+0.5%)\n\n• Minimum 10 USDT needed\n• Recommended min profit: 0.3%\n• Commission: 0.1% × 3 = 0.3%",
    },
    "signals": {
        "uz": "📡 <b>Signallar — Qo'llanma</b>\n\nAdmin yuborgan savdo tavsiyasi.\n\n<b>Signal formati:</b>\n<code>BTCUSDT LONG 10 50000 52000 49000</code>\n\n• <b>BTCUSDT</b> — juftlik\n• <b>LONG/SHORT</b> — yo'nalish\n• <b>10</b> — leverage\n• <b>50000</b> — kirish\n• <b>52000</b> — TP\n• <b>49000</b> — SL\n\n✅ API ulangan bo'lishi kerak\n✅ Bot faol bo'lishi kerak",
        "ru": "📡 <b>Сигналы — Руководство</b>\n\nТорговая рекомендация от администратора.\n\n<b>Формат сигнала:</b>\n<code>BTCUSDT LONG 10 50000 52000 49000</code>\n\n• <b>BTCUSDT</b> — пара\n• <b>LONG/SHORT</b> — направление\n• <b>10</b> — плечо\n• <b>50000</b> — вход\n• <b>52000</b> — TP\n• <b>49000</b> — SL\n\n✅ API должен быть подключён\n✅ Бот должен быть активен",
        "en": "📡 <b>Signals — Guide</b>\n\nTrading recommendation from admin.\n\n<b>Signal format:</b>\n<code>BTCUSDT LONG 10 50000 52000 49000</code>\n\n• <b>BTCUSDT</b> — pair\n• <b>LONG/SHORT</b> — direction\n• <b>10</b> — leverage\n• <b>50000</b> — entry\n• <b>52000</b> — TP\n• <b>49000</b> — SL\n\n✅ API must be connected\n✅ Bot must be active",
    },
    "balance": {
        "uz": "💰 <b>Balans & Tarif — Qo'llanma</b>\n\n<b>Balansni to'ldirish:</b>\n1. 💰 Balans → 💳 Balansni to'ldirish\n2. Miqdorni tanlang\n3. Chek rasmini yuboring\n4. Admin tasdiqlaydi\n\n<b>Tarif rejalari:</b>\n📅 Kunlik — 24 soat\n📆 Oylik — 30 kun\n\n⚠️ Tarif tugasa bot to'xtaydi.",
        "ru": "💰 <b>Баланс & Тариф — Руководство</b>\n\n<b>Пополнение баланса:</b>\n1. 💰 Баланс → 💳 Пополнить\n2. Выберите сумму\n3. Отправьте чек\n4. Администратор подтвердит\n\n<b>Тарифы:</b>\n📅 Дневной — 24 часа\n📆 Месячный — 30 дней\n\n⚠️ Когда тариф истечёт, бот остановится.",
        "en": "💰 <b>Balance & Tariff — Guide</b>\n\n<b>Top up balance:</b>\n1. 💰 Balance → 💳 Top up\n2. Select amount\n3. Send receipt\n4. Admin will confirm\n\n<b>Plans:</b>\n📅 Daily — 24 hours\n📆 Monthly — 30 days\n\n⚠️ Bot stops when tariff expires.",
    },
    "referral": {
        "uz": "👥 <b>Referral tizimi — Qo'llanma</b>\n\nDo'stingizni taklif qiling va bonus oling!\n\n1. 👥 Referral → havolangizni nusxalang\n2. Do'stlaringizga yuboring\n3. Havola orqali kirsa — bonus 🎁\n\nBonus darhol balansingizga tushadi.",
        "ru": "👥 <b>Реферальная система — Руководство</b>\n\nПригласите друга и получите бонус!\n\n1. 👥 Реферал → скопируйте вашу ссылку\n2. Отправьте друзьям\n3. Если зайдут по ссылке — бонус 🎁\n\nБонус сразу зачисляется на баланс.",
        "en": "👥 <b>Referral System — Guide</b>\n\nInvite a friend and earn a bonus!\n\n1. 👥 Referral → copy your link\n2. Share with friends\n3. If they join via link — bonus 🎁\n\nBonus is instantly credited to your balance.",
    },
    "faq": {
        "uz": "❓ <b>Ko'p so'raladigan savollar</b>\n\n❓ <b>Bot doim ishlayaptimi?</b>\n❌ VPS server kerak 24/7 uchun.\n\n❓ <b>API xavfsizmi?</b>\n✅ Withdraw ruxsati bermasa — xavfsiz.\n\n❓ <b>Minimal boshlash miqdori?</b>\n✅ MEXC da 10 USDT.\n\n❓ <b>Arbitraj kafolatlanadimi?</b>\n❌ Kafolat yo'q, lekin bot faqat foydali bo'lganda ishlaydi.\n\n❓ <b>Savol bo'lsa?</b>\n✅ 🆘 Qo'llab-quvvatlash bo'limiga murojaat qiling!",
        "ru": "❓ <b>Часто задаваемые вопросы</b>\n\n❓ <b>Бот работает постоянно?</b>\n❌ Нужен VPS для 24/7 работы.\n\n❓ <b>API безопасен?</b>\n✅ Безопасно, если не давать разрешение Withdraw.\n\n❓ <b>Минимальная сумма для старта?</b>\n✅ 10 USDT на MEXC.\n\n❓ <b>Арбитраж гарантирован?</b>\n❌ Нет гарантий, но бот работает только при прибыли.\n\n❓ <b>Есть вопросы?</b>\n✅ Обратитесь в раздел 🆘 Поддержка!",
        "en": "❓ <b>Frequently Asked Questions</b>\n\n❓ <b>Is the bot always running?</b>\n❌ You need a VPS for 24/7 operation.\n\n❓ <b>Is the API safe?</b>\n✅ Safe if you don't grant Withdraw permission.\n\n❓ <b>Minimum starting amount?</b>\n✅ 10 USDT on MEXC.\n\n❓ <b>Is arbitrage guaranteed?</b>\n❌ No guarantee, but bot only runs when profitable.\n\n❓ <b>Have questions?</b>\n✅ Contact 🆘 Support section!",
    },
}


def get_user_lang(tg_id):
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


def guide_main_kb(lang="uz"):
    tx = GUIDE_TX.get(lang, GUIDE_TX["uz"])
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=tx["btn_api"], callback_data="guide_mexc_api"))
    kb.add(InlineKeyboardButton(text=tx["btn_auto"], callback_data="guide_auto_trading"))
    kb.add(InlineKeyboardButton(text=tx["btn_copy"], callback_data="guide_copy_trading"))
    kb.add(InlineKeyboardButton(text=tx["btn_arb"], callback_data="guide_arbitrage"))
    kb.add(InlineKeyboardButton(text=tx["btn_sig"], callback_data="guide_signals"))
    kb.add(InlineKeyboardButton(text=tx["btn_bal"], callback_data="guide_balance"))
    kb.add(InlineKeyboardButton(text=tx["btn_ref"], callback_data="guide_referral"))
    kb.add(InlineKeyboardButton(text=tx["btn_faq"], callback_data="guide_faq"))
    kb.adjust(2)
    return kb.as_markup()


def back_kb(lang="uz"):
    tx = GUIDE_TX.get(lang, GUIDE_TX["uz"])
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=tx["back_btn"], callback_data="guide_back"))
    return kb.as_markup()


@router.message(F.text.in_(["📖 Qo'llanma", "📖 Руководство", "📖 Guide"]))
async def show_guide(message: Message):
    lang = get_user_lang(message.from_user.id)
    tx = GUIDE_TX.get(lang, GUIDE_TX["uz"])
    await message.answer(f"{tx['title']}\n\n{tx['select']}", reply_markup=guide_main_kb(lang))


async def _send_guide_section(call: CallbackQuery, section: str):
    lang = get_user_lang(call.from_user.id)
    content = GUIDE_CONTENT.get(section, {}).get(lang) or GUIDE_CONTENT.get(section, {}).get("uz", "—")
    await call.message.edit_text(content, reply_markup=back_kb(lang))


@router.callback_query(F.data == "guide_mexc_api")
async def guide_mexc_api(call: CallbackQuery):
    await _send_guide_section(call, "mexc_api")

@router.callback_query(F.data == "guide_auto_trading")
async def guide_auto_trading(call: CallbackQuery):
    await _send_guide_section(call, "auto_trading")

@router.callback_query(F.data == "guide_copy_trading")
async def guide_copy_trading(call: CallbackQuery):
    await _send_guide_section(call, "copy_trading")

@router.callback_query(F.data == "guide_arbitrage")
async def guide_arbitrage(call: CallbackQuery):
    await _send_guide_section(call, "arbitrage")

@router.callback_query(F.data == "guide_signals")
async def guide_signals(call: CallbackQuery):
    await _send_guide_section(call, "signals")

@router.callback_query(F.data == "guide_balance")
async def guide_balance(call: CallbackQuery):
    await _send_guide_section(call, "balance")

@router.callback_query(F.data == "guide_referral")
async def guide_referral(call: CallbackQuery):
    await _send_guide_section(call, "referral")

@router.callback_query(F.data == "guide_faq")
async def guide_faq(call: CallbackQuery):
    await _send_guide_section(call, "faq")

@router.callback_query(F.data == "guide_back")
async def guide_back(call: CallbackQuery):
    lang = get_user_lang(call.from_user.id)
    tx = GUIDE_TX.get(lang, GUIDE_TX["uz"])
    await call.message.edit_text(f"{tx['title']}\n\n{tx['select']}", reply_markup=guide_main_kb(lang))