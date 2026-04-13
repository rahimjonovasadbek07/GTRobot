from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    get_user, register_user, get_tariff_prices,
    update_balance, set_tariff, create_payment,
    confirm_payment, get_user_by_referral, has_active_tariff,
    get_payment_settings, set_user_lang
)
from keyboards.kb import (
    main_menu, tariff_keyboard, balance_keyboard,
    topup_amount_keyboard, cancel_keyboard,
    check_sub_keyboard, payment_confirm_keyboard
)
from utils.lang import t, get_lang_keyboard, LANGS
from config import ADMIN_IDS, REQUIRED_CHANNELS

router = Router()
REFERRAL_BONUS = 5000


class TopupState(StatesGroup):
    waiting_amount = State()
    waiting_receipt = State()


def get_user_lang(tg_id):
    user = get_user(tg_id)
    return user.get("lang", "uz") if user else "uz"


async def check_subscribed(bot: Bot, user_id: int) -> bool:
    channels = REQUIRED_CHANNELS
    if not channels:
        return True
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status in ["left", "kicked", "restricted"]:
                return False
        except Exception:
            pass
    return True


# ===== TIL TANLASH =====
@router.message(F.text == "🌐 Til")
async def choose_lang(message: Message):
    await message.answer("🌐 Tilni tanlang / Выберите язык / Choose language:", reply_markup=get_lang_keyboard())


@router.callback_query(F.data.startswith("lang_"))
async def cb_lang(call: CallbackQuery):
    lang = call.data.split("_")[1]
    if lang not in LANGS:
        await call.answer("❌ Noto'g'ri til!")
        return
    set_user_lang(call.from_user.id, lang)
    await call.answer(t(lang, "lang_set"))
    user = get_user(call.from_user.id)
    balance = user["balance"] if user else 0
    await call.message.edit_text(t(lang, "lang_set"))
    await call.message.answer(
        t(lang, "start_welcome", name=call.from_user.full_name, balance=balance, tariff=t(lang, "tariff_no")),
        reply_markup=main_menu(lang)
    )


# ===== START =====
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    args = message.text.split()

    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1][4:]
        referrer_id = get_user_by_referral(ref_code)
        if referrer_id and referrer_id != user.id:
            referred_by = referrer_id

    existing = get_user(user.id)
    register_user(user.id, f"@{user.username}" if user.username else "—", user.full_name, referred_by)

    if not existing and referred_by:
        update_balance(referred_by, REFERRAL_BONUS)
        try:
            ref_lang = get_user_lang(referred_by)
            await message.bot.send_message(
                referred_by,
                f"🎁 <b>Referral bonus!</b>\n\n{user.full_name} qo'shildi!\n💰 +{REFERRAL_BONUS:,} UZS"
            )
        except Exception:
            pass

    # Kanal tekshirish
    subscribed = await check_subscribed(message.bot, user.id)
    if not subscribed:
        lang = get_user_lang(user.id)
        await message.answer(
            t(lang, "subscribe_required"),
            reply_markup=check_sub_keyboard(REQUIRED_CHANNELS)
        )
        return

    # Til tanlash (yangi foydalanuvchi)
    if not existing:
        await message.answer(
            "🌐 Tilni tanlang / Выберите язык / Choose language:",
            reply_markup=get_lang_keyboard()
        )
        return

    db_user = get_user(user.id)
    lang = db_user.get("lang", "uz")
    tariff_status = t(lang, "tariff_no")
    if db_user and db_user.get("tariff") and db_user.get("tariff_expires"):
        try:
            exp_dt = datetime.fromisoformat(db_user["tariff_expires"])
            if exp_dt > datetime.now():
                days_left = (exp_dt - datetime.now()).days
                tariff_status = f"✅ {db_user['tariff'].capitalize()} ({days_left} kun)"
            else:
                tariff_status = "⏰ Tugagan"
        except Exception:
            pass

    await message.answer(
        t(lang, "start_welcome", name=user.full_name, balance=db_user["balance"], tariff=tariff_status),
        reply_markup=main_menu(lang)
    )
    if user.id in ADMIN_IDS:
        await message.answer("🔐 Admin: /admin")


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery):
    subscribed = await check_subscribed(call.bot, call.from_user.id)
    lang = get_user_lang(call.from_user.id)
    if subscribed:
        await call.message.delete()
        # Yangi foydalanuvchi bo'lsa til tanlat
        user = get_user(call.from_user.id)
        if not user or not user.get("lang"):
            await call.message.answer(
                "🌐 Tilni tanlang / Выберите язык / Choose language:",
                reply_markup=get_lang_keyboard()
            )
            return
        await call.message.answer(
            t(lang, "sub_confirmed", name=call.from_user.full_name),
            reply_markup=main_menu(lang)
        )
    else:
        await call.answer(t(lang, "sub_not_done"), show_alert=True)


# ===== TARIF TEKSHIRISH DECORATOR =====
def check_tariff_required(func):
    async def wrapper(message: Message, *args, **kwargs):
        lang = get_user_lang(message.from_user.id)
        if not has_active_tariff(message.from_user.id):
            await message.answer(t(lang, "no_tariff"))
            return
        return await func(message, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


# ===== BALANS =====
@router.message(F.text.in_(["💰 Balans", "💰 Баланс", "💰 Balance"]))
async def show_balance(message: Message):
    user = get_user(message.from_user.id)
    lang = get_user_lang(message.from_user.id)
    if not user:
        await message.answer("❌ Avval /start bosing.")
        return

    tariff_info = t(lang, "tariff_no")
    if user["tariff"] and user["tariff_expires"]:
        try:
            exp_dt = datetime.fromisoformat(user["tariff_expires"])
            if exp_dt > datetime.now():
                days_left = (exp_dt - datetime.now()).days
                hours_left = (exp_dt - datetime.now()).seconds // 3600
                tariff_info = f"✅ {user['tariff'].capitalize()} ({days_left}k {hours_left}s)"
            else:
                tariff_info = "⏰ Tugagan"
        except Exception:
            pass

    bot_status = "✅ Faol" if user["bot_active"] else "⏹ Off"
    api_status = "✅" if user.get("mexc_api_key") else "❌"

    await message.answer(
        f"💰 <b>Hisob</b>\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"💵 Balans: <b>{user['balance']:,.0f} UZS</b>\n"
        f"🎁 Referral: <b>{user.get('referral_bonus', 0):,.0f} UZS</b>\n\n"
        f"📋 Tarif: {tariff_info}\n"
        f"🔑 API: {api_status}\n"
        f"🤖 Bot: {bot_status}",
        reply_markup=balance_keyboard()
    )


@router.callback_query(F.data == "topup_balance")
async def cb_topup(call: CallbackQuery):
    await call.message.edit_text("💳 Miqdorni tanlang:", reply_markup=topup_amount_keyboard())


@router.callback_query(F.data.regexp(r'^topup_\d+$'))
async def cb_topup_amount(call: CallbackQuery, state: FSMContext):
    amount = int(call.data.split("_")[1])
    await state.update_data(topup_amount=amount)

    # To'lov rekvizitlarini olish
    s = get_payment_settings()

    text = f"💳 <b>To'lov: {amount:,} UZS</b>\n\n"
    if s["wallet_address"]:
        text += f"💎 <b>USDT ({s['network']}):</b>\n<code>{s['wallet_address']}</code>\n\n"
    if s["card_number"]:
        text += f"💳 <b>Karta:</b>\n<code>{s['card_number']}</code>\n👤 {s['card_owner']}\n\n"
    if not s["wallet_address"] and not s["card_number"]:
        text += "⚠️ Admin rekvizitlarni hali kiritilmagan. /admin → 💳 To'lov rekvizit\n\n"

    text += "📸 To'lovdan so'ng <b>chek rasmini</b> yuboring:"
    await call.message.edit_text(text)
    await state.set_state(TopupState.waiting_receipt)


@router.callback_query(F.data == "topup_custom")
async def cb_topup_custom(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("✏️ Miqdorni kiriting (UZS):")
    await state.set_state(TopupState.waiting_amount)


@router.message(TopupState.waiting_amount)
async def proc_custom_amount(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    try:
        amount = int(message.text.replace(" ", "").replace(",", ""))
        if amount < 5000:
            await message.answer("❌ Minimal 5,000 UZS")
            return
        await state.update_data(topup_amount=amount)
        s = get_payment_settings()
        text = f"💳 <b>{amount:,} UZS</b>\n\n"
        if s["wallet_address"]:
            text += f"💎 USDT ({s['network']}):\n<code>{s['wallet_address']}</code>\n\n"
        if s["card_number"]:
            text += f"💳 Karta: <code>{s['card_number']}</code>\n\n"
        text += "📸 Chek yuboring:"
        await message.answer(text, reply_markup=cancel_keyboard())
        await state.set_state(TopupState.waiting_receipt)
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


@router.message(TopupState.waiting_receipt)
async def proc_receipt(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu())
        return
    if not message.photo and not message.document:
        await message.answer("❌ Chek rasmini yuboring.")
        return

    data = await state.get_data()
    amount = data.get("topup_amount", 0)
    payment_id = create_payment(message.from_user.id, amount, "balance")

    for admin_id in ADMIN_IDS:
        try:
            caption = (
                f"💳 <b>Yangi to'lov</b>\n\n"
                f"👤 {message.from_user.full_name}\n"
                f"🆔 <code>{message.from_user.id}</code>\n"
                f"📱 @{message.from_user.username or '—'}\n"
                f"💰 <b>{amount:,} UZS</b>\n#{payment_id}"
            )
            kb = payment_confirm_keyboard(payment_id, message.from_user.id, "balance")
            if message.photo:
                await message.bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption, reply_markup=kb)
            else:
                await message.bot.send_document(admin_id, message.document.file_id, caption=caption, reply_markup=kb)
        except Exception:
            pass

    lang = get_user_lang(message.from_user.id)
    await message.answer("✅ So'rov adminga yuborildi. ⏳ Tez orada balans to'ldiriladi.", reply_markup=main_menu(lang))
    await state.clear()


# ===== TARIF =====
@router.message(F.text.in_(["📋 Tarif", "📋 Тариф", "📋 Tariff"]))
async def show_tariff(message: Message):
    prices = get_tariff_prices()
    daily = prices.get("daily", 10000)
    monthly = prices.get("monthly", 200000)
    user = get_user(message.from_user.id)
    balance = user["balance"] if user else 0
    lang = get_user_lang(message.from_user.id)

    await message.answer(
        f"📋 <b>Tarif rejalari</b>\n\n"
        f"💰 Balans: <b>{balance:,.0f} UZS</b>\n\n"
        f"📅 <b>Kunlik</b> — {int(daily):,} UZS (24 soat)\n"
        f"📆 <b>Oylik</b> — {int(monthly):,} UZS (30 kun)\n\n"
        f"💳 Avval balansni to'ldiring.",
        reply_markup=tariff_keyboard(daily, monthly)
    )


@router.callback_query(F.data.startswith("buy_"))
async def cb_buy_tariff(call: CallbackQuery):
    tariff_type = call.data.split("_")[1]
    user = get_user(call.from_user.id)
    prices = get_tariff_prices()
    price = prices.get(tariff_type, 0)
    balance = user["balance"] if user else 0

    if balance < price:
        await call.answer(f"❌ Balans yetarli emas!\nKerak: {price:,} UZS\nBalans: {balance:,} UZS", show_alert=True)
        return

    update_balance(call.from_user.id, -price)
    days = 1 if tariff_type == "daily" else 30
    expires = (datetime.now() + timedelta(days=days)).isoformat()
    set_tariff(call.from_user.id, tariff_type, expires)
    label = "Kunlik (1 kun)" if tariff_type == "daily" else "Oylik (30 kun)"
    lang = get_user_lang(call.from_user.id)
    await call.message.edit_text(
        f"✅ <b>Tarif faollashtirildi!</b>\n\n📋 {label}\n💰 {price:,} UZS\n📅 {expires[:10]} gacha"
    )
    await call.message.answer("✅ Barcha funksiyalardan foydalanishingiz mumkin!", reply_markup=main_menu(lang))


# ===== SUPPORT =====
@router.message(F.text.in_(["🆘 Qo'llab-quvvatlash", "🆘 Поддержка", "🆘 Support"]))
async def show_support(message: Message):
    await message.answer(
        "🆘 <b>Qo'llab-quvvatlash / Поддержка / Support</b>\n\n"
        "📱 Admin: @grandtrade_admin\n"
        "⏰ 9:00 — 22:00"
    )
