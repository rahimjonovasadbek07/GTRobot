from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = Router()


def guide_main_kb():
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔑 MEXC API olish", callback_data="guide_mexc_api"))
    kb.add(InlineKeyboardButton(text="🤖 Auto Trading", callback_data="guide_auto_trading"))
    kb.add(InlineKeyboardButton(text="📊 Copy Trading", callback_data="guide_copy_trading"))
    kb.add(InlineKeyboardButton(text="🔺 Arbitraj", callback_data="guide_arbitrage"))
    kb.add(InlineKeyboardButton(text="📡 Signallar", callback_data="guide_signals"))
    kb.add(InlineKeyboardButton(text="💰 Balans & Tarif", callback_data="guide_balance"))
    kb.add(InlineKeyboardButton(text="👥 Referral", callback_data="guide_referral"))
    kb.add(InlineKeyboardButton(text="❓ FAQ", callback_data="guide_faq"))
    kb.adjust(2)
    return kb.as_markup()


def back_kb():
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔙 Qo'llanmaga qaytish", callback_data="guide_back"))
    return kb.as_markup()


@router.message(F.text == "📖 Qo'llanma")
async def show_guide(message: Message):
    await message.answer(
        "📖 <b>GTRobot Qo'llanma</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:\n\n"
        "🔑 MEXC API olish\n"
        "🤖 Auto Trading ishlatish\n"
        "📊 Copy Trading\n"
        "🔺 Arbitraj\n"
        "📡 Signallar\n"
        "💰 Balans & Tarif\n"
        "👥 Referral tizimi\n"
        "❓ Ko'p so'raladigan savollar",
        reply_markup=guide_main_kb()
    )


# ===== MEXC API OLISH =====
@router.callback_query(F.data == "guide_mexc_api")
async def guide_mexc_api(call: CallbackQuery):
    text = (
        "🔑 <b>MEXC API olish — Qadamma-qadam</b>\n\n"

        "<b>1-qadam: MEXC ga kiring</b>\n"
        "• mexc.com saytiga yoki ilovasiga kiring\n"
        "• Hisobingizga login qiling\n"
        "• Hisob yo'q bo'lsa — ro'yxatdan o'ting\n\n"

        "<b>2-qadam: KYC tasdiqlash</b>\n"
        "• Profile → Verification ga o'ting\n"
        "• Basic Verification bosing\n"
        "• Pasport yoki ID karta rasmini yuklang\n"
        "• Selfie oling\n"
        "• 10-30 daqiqada tasdiqlanadi\n\n"

        "<b>3-qadam: API Management</b>\n"
        "• Profile ikonkasi → API Management\n"
        "• Create API tugmasini bosing\n"
        "• HMAC turini tanlang\n\n"

        "<b>4-qadam: Ruxsatlar</b>\n"
        "✅ Spot → View Account Details\n"
        "✅ Spot → View Order Details\n"
        "✅ Spot → Trade\n"
        "✅ Futures → View Account Details\n"
        "✅ Futures → Order Placing\n"
        "❌ Withdraw — BELGILAMANG!\n"
        "❌ Transfer — BELGILAMANG!\n\n"

        "<b>5-qadam: Nom kiriting</b>\n"
        "• Notes ga: GTRobot yozing\n"
        "• Link IP Address — bo'sh qoldiring\n"
        "• Create bosing\n\n"

        "<b>6-qadam: Kalitlarni saqlang</b>\n"
        "• Access Key — nusxalab oling\n"
        "• Secret Key — nusxalab oling\n"
        "⚠️ Secret Key faqat 1 marta ko'rinadi!\n\n"

        "<b>7-qadam: Botga ulash</b>\n"
        "• 🤖 Auto Trading → 🔑 MEXC API ulash\n"
        "• Access Key yuboring\n"
        "• Secret Key yuboring\n"
        "• Bot avtomatik tekshiradi ✅"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== AUTO TRADING =====
@router.callback_query(F.data == "guide_auto_trading")
async def guide_auto_trading(call: CallbackQuery):
    text = (
        "🤖 <b>Auto Trading — Qo'llanma</b>\n\n"

        "<b>Auto Trading nima?</b>\n"
        "Admin signal yuborganda bot sizning MEXC hisobingizda "
        "avtomatik ravishda order ochadi. Siz hech narsa qilmasangiz ham bot ishlaydi.\n\n"

        "<b>Ishlatish uchun:</b>\n\n"

        "<b>1-qadam: API ulash</b>\n"
        "• 🤖 Auto Trading → 🔑 MEXC API ulash\n"
        "• MEXC Access Key va Secret Key kiriting\n"
        "• Bot tekshirib ✅ tasdiqlaydi\n\n"

        "<b>2-qadam: Tarif sotib olish</b>\n"
        "• 📋 Tarif bo'limiga o'ting\n"
        "• Kunlik yoki Oylik tanlang\n"
        "• Balansdan to'lanadi\n\n"

        "<b>3-qadam: Botni faollashtirish</b>\n"
        "• 🤖 Auto Trading → ▶️ Botni faollashtirish\n"
        "• Bot MEXC ga ulanadi\n"
        "• Signal kelganda avtomatik trade ochiladi\n\n"

        "<b>Signal kelganda nima bo'ladi?</b>\n"
        "1. Admin signal yuboradi\n"
        "2. Siz xabar olasiz\n"
        "3. Bot avtomatik order ochadi\n"
        "4. Order ochildi deb xabar keladi\n\n"

        "<b>Botni to'xtatish:</b>\n"
        "• 🤖 Auto Trading → ⏹ Botni to'xtatish\n\n"

        "⚠️ <b>Eslatma:</b>\n"
        "• MEXC hisobingizda USDT bo'lishi kerak\n"
        "• Minimal 10 USDT tavsiya etiladi"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== COPY TRADING =====
@router.callback_query(F.data == "guide_copy_trading")
async def guide_copy_trading(call: CallbackQuery):
    text = (
        "📊 <b>Copy Trading — Qo'llanma</b>\n\n"

        "<b>Copy Trading nima?</b>\n"
        "MEXC birjasidagi real vaqt bozor ma'lumotlarini "
        "ko'rish va tahlil qilish imkoniyati.\n\n"

        "<b>Bo'limlar:</b>\n\n"

        "🔥 <b>Top 20 Volume</b>\n"
        "• Eng ko'p savdo qilinayotgan 20 ta juftlik\n"
        "• Narx, 24 soatlik o'zgarish, hajm ko'rsatiladi\n"
        "• Qaysi coin aktiv ekanini bilish uchun\n\n"

        "📈 <b>Top Gainers</b>\n"
        "• 24 soatda eng ko'p o'sgan kriptolar\n"
        "• Trend ustivorligini topish uchun\n\n"

        "📉 <b>Top Losers</b>\n"
        "• 24 soatda eng ko'p tushgan kriptolar\n"
        "• Potensial qayta o'sish imkoniyatini topish uchun\n\n"

        "🔍 <b>Juftlik tahlili</b>\n"
        "• Istalgan juftlikni kiriting (masalan: BTC/USDT)\n"
        "• RSI indikatori ko'rsatiladi\n"
        "• Trend: Bullish yoki Bearish\n"
        "• Signal: BUY / SELL / KUTING\n\n"

        "<b>RSI nima?</b>\n"
        "• RSI < 30 → Oversold (sotib olish vaqti) 🟢\n"
        "• RSI > 70 → Overbought (sotish vaqti) 🔴\n"
        "• RSI 30-70 → Normal holat ⚪"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== ARBITRAJ =====
@router.callback_query(F.data == "guide_arbitrage")
async def guide_arbitrage(call: CallbackQuery):
    text = (
        "🔺 <b>Uchburchak Arbitraj — Qo'llanma</b>\n\n"

        "<b>Arbitraj nima?</b>\n"
        "Bir birja ichida 3 ta juftlik orqali narx farqidan foyda qilish.\n\n"

        "<b>Misol:</b>\n"
        "1️⃣ 100 USDT → BTC sotib olamiz\n"
        "2️⃣ BTC → ETH ga almashtiramiz\n"
        "3️⃣ ETH → USDT sotamiz\n"
        "💰 Natija: 100.5 USDT (+0.5% foyda)\n\n"

        "<b>Ishlatish:</b>\n\n"

        "<b>1. Arbitraj izlash</b>\n"
        "• 🔺 Arbitraj → 🔍 Arbitraj izlash\n"
        "• Bot MEXC da barcha juftliklarni tekshiradi\n"
        "• Foydali yo'l topilsa ko'rsatadi\n"
        "• 10-30 soniya vaqt ketadi\n\n"

        "<b>2. Avtomatik monitor</b>\n"
        "• ▶️ Avtomatik monitor bosing\n"
        "• Miqdor kiriting (masalan: 50 USDT)\n"
        "• Minimal foyda % kiriting (masalan: 0.3)\n"
        "• Bot har 30 soniyada tekshirib turadi\n"
        "• Foyda topilganda avtomatik bajaradi\n\n"

        "<b>Tavsiyalar:</b>\n"
        "• Minimal 10 USDT ishlatish kerak\n"
        "• 0.3-0.5% minimal foyda tavsiya etiladi\n"
        "• Komissiya: 0.1% × 3 ta trade = 0.3%\n\n"

        "⚠️ <b>Xavf:</b>\n"
        "• Narx tez o'zgarishi mumkin\n"
        "• Har doim foyda kafolatlanmaydi\n"
        "• Kichik miqdordan boshlang"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== SIGNALLAR =====
@router.callback_query(F.data == "guide_signals")
async def guide_signals(call: CallbackQuery):
    text = (
        "📡 <b>Signallar — Qo'llanma</b>\n\n"

        "<b>Signal nima?</b>\n"
        "Admin yuborgan savdo tavsiyasi. "
        "Bot faol bo'lsa signal kelganda avtomatik trade ochiladi.\n\n"

        "<b>Signal formati:</b>\n"
        "<code>BTCUSDT LONG 10 50000 52000 49000</code>\n\n"

        "• <b>BTCUSDT</b> — savdo juftligi\n"
        "• <b>LONG</b> — yo'nalish (LONG=yuqori, SHORT=pastga)\n"
        "• <b>10</b> — leverage (kaldıraç)\n"
        "• <b>50000</b> — kirish narxi\n"
        "• <b>52000</b> — Take Profit (foyda olish)\n"
        "• <b>49000</b> — Stop Loss (zarar to'xtatish)\n\n"

        "<b>Signal kelganda:</b>\n"
        "1. Xabar olasiz 🔔\n"
        "2. Bot avtomatik order ochadi 🤖\n"
        "3. Order ochildi deb tasdiqlaydi ✅\n\n"

        "<b>Faol signallar:</b>\n"
        "• 📡 Signallar bo'limida ko'rish mumkin\n"
        "• Admin yopguncha aktiv qoladi\n\n"

        "<b>Signal ishlashi uchun:</b>\n"
        "✅ MEXC API ulangan bo'lishi kerak\n"
        "✅ Bot faollashtirilgan bo'lishi kerak\n"
        "✅ MEXC da yetarli balans bo'lishi kerak"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== BALANS & TARIF =====
@router.callback_query(F.data == "guide_balance")
async def guide_balance(call: CallbackQuery):
    text = (
        "💰 <b>Balans & Tarif — Qo'llanma</b>\n\n"

        "<b>Balans nima?</b>\n"
        "Bu GTRobot ichidagi hisobingiz. "
        "Tarif sotib olish uchun ishlatiladi.\n\n"

        "<b>Balansni to'ldirish:</b>\n"
        "1. 💰 Balans → 💳 Balansni to'ldirish\n"
        "2. Miqdorni tanlang\n"
        "3. Karta raqamiga pul o'tkazing\n"
        "4. Chek rasmini yuboring\n"
        "5. Admin tasdiqlaydi → balans to'ldiriladi\n\n"

        "<b>Tarif rejalari:</b>\n\n"
        "📅 <b>Kunlik tarif</b>\n"
        "• 24 soat foydalanish\n"
        "• Barcha funksiyalar\n\n"

        "📆 <b>Oylik tarif</b>\n"
        "• 30 kun foydalanish\n"
        "• Barcha funksiyalar\n"
        "• Kunlikdan arzonroq\n\n"

        "<b>Tarif sotib olish:</b>\n"
        "1. 📋 Tarif bo'limiga o'ting\n"
        "2. Reja tanlang\n"
        "3. Balansdan avtomatik to'lanadi\n\n"

        "⚠️ <b>Eslatma:</b>\n"
        "• Tarif tugasa bot to'xtaydi\n"
        "• Yangilash uchun qayta sotib oling"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== REFERRAL =====
@router.callback_query(F.data == "guide_referral")
async def guide_referral(call: CallbackQuery):
    text = (
        "👥 <b>Referral tizimi — Qo'llanma</b>\n\n"

        "<b>Referral nima?</b>\n"
        "Do'stingizni botga taklif qiling va bonus oling!\n\n"

        "<b>Qanday ishlaydi:</b>\n"
        "1. 👥 Referral bo'limiga o'ting\n"
        "2. Shaxsiy havolangizni nusxalab oling\n"
        "3. Do'stlaringizga yuboring\n"
        "4. Do'stingiz havola orqali botga kirsa\n"
        "5. Balansingizga bonus tushadi 🎁\n\n"

        "<b>Bonus miqdori:</b>\n"
        "• Har bir do'st uchun: 5,000 USDT\n"
        "• Cheksiz miqdorda do'st taklif qilish mumkin\n"
        "• Bonus darhol balansingizga tushadi\n\n"

        "<b>Statistika:</b>\n"
        "• Nechta do'st taklif qilganingiz\n"
        "• Jami referral bonus\n"
        "• Barchasini 👥 Referral bo'limida ko'ring\n\n"

        "<b>Havola formati:</b>\n"
        "<code>t.me/gtrobot?start=ref_SIZNINGKODINGIZ</code>"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== FAQ =====
@router.callback_query(F.data == "guide_faq")
async def guide_faq(call: CallbackQuery):
    text = (
        "❓ <b>Ko'p so'raladigan savollar (FAQ)</b>\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>Bot kompyuter o'chsa ishlayaptimi?</b>\n"
        "❌ Yo'q. Kompyuter yoqiq bo'lishi kerak. "
        "24/7 ishlash uchun VPS server kerak.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>MEXC KYC nima uchun kerak?</b>\n"
        "✅ API orqali trade qilish uchun MEXC KYC talab qiladi. "
        "Pasport yoki ID karta bilan 10-30 daqiqada bo'ladi.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>API kalitim o'g'irlanib ketadimi?</b>\n"
        "✅ Withdraw va Transfer ruxsatini bermasangiz xavfsiz. "
        "Kimdir kalitni olsa ham pul chiqara olmaydi.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>Minimal qancha pul bilan boshlash mumkin?</b>\n"
        "✅ MEXC da minimal 10 USDT bilan boshlash mumkin.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>Arbitraj har doim foyda beradimi?</b>\n"
        "❌ Kafolat yo'q. Narx tez o'zgaradi. "
        "Lekin bot faqat foydali bo'lganda bajaradi.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>Balans to'ldirilmasa nima qilaman?</b>\n"
        "✅ Admin bilan bog'laning: 🆘 Qo'llab-quvvatlash\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>API kalitim 90 kundan keyin nima bo'ladi?</b>\n"
        "✅ MEXC da yangilab (Renew) qilish kerak yoki "
        "yangi API yaratib botga qayta ulash kerak.\n\n"

        "━━━━━━━━━━━━━━━\n"
        "❓ <b>Boshqa savol bo'lsa?</b>\n"
        "✅ 🆘 Qo'llab-quvvatlash bo'limidan admin bilan bog'laning!"
    )
    await call.message.edit_text(text, reply_markup=back_kb())


# ===== ORQAGA =====
@router.callback_query(F.data == "guide_back")
async def guide_back(call: CallbackQuery):
    await call.message.edit_text(
        "📖 <b>GTRobot Qo'llanma</b>\n\nBo'limni tanlang:",
        reply_markup=guide_main_kb()
    )
