from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import (
    get_all_users, get_user_count, get_active_users, update_balance,
    set_tariff, get_tariff_prices, update_tariff_price,
    get_channels, add_channel, remove_channel,
    get_revenue_stats, confirm_payment, get_user,
    get_payment_settings, update_payment_settings,
    get_mining_plans_db, update_mining_plan,
    get_bot_settings, set_bot_setting
)
from keyboards.kb import admin_menu, main_menu, cancel_keyboard, channels_keyboard
from config import ADMIN_IDS

router = Router()


def is_admin(user_id):
    return user_id in ADMIN_IDS


class AdminState(StatesGroup):
    waiting_tariff_type = State()
    waiting_tariff_price = State()
    waiting_channel_id = State()
    waiting_channel_name = State()
    waiting_broadcast = State()
    waiting_wallet = State()
    waiting_network = State()
    waiting_card = State()
    waiting_card_owner = State()
    waiting_mining_field = State()
    waiting_mining_value = State()
    waiting_referral_bonus = State()
    waiting_support_text = State()
    waiting_signal_name = State()


# ===== ADMIN MENYU =====
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    await state.clear()
    if not is_admin(message.from_user.id):
        await message.answer("❌ Ruxsat yo'q.")
        return
    await message.answer("🔐 <b>Admin panel</b>", reply_markup=admin_menu())


@router.message(F.text == "🔙 Asosiy menyu")
async def back_main(message: Message, state: FSMContext):
    await state.clear()
    from database.db import get_user
    user = get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    await message.answer("Asosiy menyu:", reply_markup=main_menu(lang))


# ===== 1. TARIF NARXI =====
@router.message(F.text == "💵 Tarif narxi")
async def change_tariff(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    prices = get_tariff_prices()
    await message.answer(
        f"💵 <b>Joriy narxlar:</b>\n\n"
        f"📅 Kunlik: {prices.get('daily', 5.0):.2f} USDT\n"
        f"📆 Oylik: {prices.get('monthly', 50.0):.2f} USDT\n\n"
        "<b>daily</b> yoki <b>monthly</b> yozing:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminState.waiting_tariff_type)


@router.message(AdminState.waiting_tariff_type)
async def proc_tariff_type(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    t = message.text.strip().lower()
    if t not in ["daily", "monthly"]:
        await message.answer("❌ <b>daily</b> yoki <b>monthly</b> yozing:")
        return
    await state.update_data(tariff_type=t)
    await message.answer("💰 Yangi narx (USDT):", reply_markup=cancel_keyboard())
    await state.set_state(AdminState.waiting_tariff_price)


@router.message(AdminState.waiting_tariff_price)
async def proc_tariff_price(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    try:
        price = float(message.text.replace(" ", "").replace(",", ""))
        data = await state.get_data()
        update_tariff_price(data["tariff_type"], price)
        label = "Kunlik" if data["tariff_type"] == "daily" else "Oylik"
        await message.answer(f"✅ {label}: <b>{price:.4f} USDT</b>", reply_markup=admin_menu())
        await state.clear()
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


# ===== 2. TO'LOV REKVIZITLARI =====
@router.message(F.text == "💳 To'lov rekvizit")
async def payment_settings_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    s = get_payment_settings()
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="💎 USDT Hamyon", callback_data="set_wallet"))
    kb.add(InlineKeyboardButton(text="🌐 Tarmoq", callback_data="set_network"))
    kb.add(InlineKeyboardButton(text="💳 Karta raqami", callback_data="set_card"))
    kb.add(InlineKeyboardButton(text="👤 Karta egasi", callback_data="set_card_owner"))
    kb.adjust(2)
    await message.answer(
        f"💳 <b>To'lov rekvizitlari</b>\n\n"
        f"💎 USDT Hamyon: <code>{s['wallet_address'] or 'Kiritilmagan'}</code>\n"
        f"🌐 Tarmoq: <b>{s['network']}</b>\n"
        f"💳 Karta: <code>{s['card_number'] or 'Kiritilmagan'}</code>\n"
        f"👤 Egasi: <b>{s['card_owner']}</b>",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "set_wallet")
async def cb_set_wallet(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("💎 USDT hamyon manzilini kiriting:")
    await state.set_state(AdminState.waiting_wallet)


@router.message(AdminState.waiting_wallet)
async def proc_wallet(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    update_payment_settings(wallet_address=message.text.strip())
    await state.clear()
    await message.answer("✅ Hamyon yangilandi!", reply_markup=admin_menu())


@router.callback_query(F.data == "set_network")
async def cb_set_network(call: CallbackQuery):
    kb = InlineKeyboardBuilder()
    for net in ["TRC20", "ERC20", "BEP20", "SOL"]:
        kb.add(InlineKeyboardButton(text=net, callback_data=f"network_{net}"))
    kb.adjust(2)
    await call.message.edit_text("🌐 Tarmoqni tanlang:", reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("network_"))
async def cb_network(call: CallbackQuery):
    network = call.data.split("_")[1]
    update_payment_settings(network=network)
    await call.answer(f"✅ {network}")
    await call.message.edit_text(f"✅ Tarmoq: <b>{network}</b>")


@router.callback_query(F.data == "set_card")
async def cb_set_card(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("💳 Karta raqamini kiriting:")
    await state.set_state(AdminState.waiting_card)


@router.message(AdminState.waiting_card)
async def proc_card(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    update_payment_settings(card_number=message.text.strip())
    await state.clear()
    await message.answer("✅ Karta yangilandi!", reply_markup=admin_menu())


@router.callback_query(F.data == "set_card_owner")
async def cb_set_card_owner(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("👤 Karta egasini kiriting:")
    await state.set_state(AdminState.waiting_card_owner)


@router.message(AdminState.waiting_card_owner)
async def proc_card_owner(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    update_payment_settings(card_owner=message.text.strip())
    await state.clear()
    await message.answer("✅ Karta egasi yangilandi!", reply_markup=admin_menu())


# ===== 3. MINING SOZLAMALARI =====
@router.message(F.text == "⛏️ Mining sozlama")
async def mining_settings(message: Message):
    if not is_admin(message.from_user.id):
        return
    plans = get_mining_plans_db()
    text = "⛏️ <b>Mining sozlamalari</b>\n\n"
    kb = InlineKeyboardBuilder()
    for p in plans:
        text += (
            f"<b>{p['name']}</b>\n"
            f"  Soatlik: {p['hourly_usdt']} USDT\n"
            f"  Kunlik: {p['daily_price']} → {p['daily_earn']} USDT\n"
            f"  Oylik: {p['monthly_price']} → {p['monthly_earn']} USDT\n\n"
        )
        kb.add(InlineKeyboardButton(text=f"✏️ {p['name']}", callback_data=f"edit_mining_{p['id']}"))
    kb.adjust(1)
    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("edit_mining_"))
async def cb_edit_mining(call: CallbackQuery, state: FSMContext):
    plan_id = int(call.data.split("_")[-1])
    plans = get_mining_plans_db()
    plan = next((p for p in plans if p["id"] == plan_id), None)
    if not plan:
        await call.answer("❌ Topilmadi!")
        return
    await state.update_data(mining_plan_id=plan_id)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="💰 Soatlik", callback_data=f"mfield_hourly_{plan_id}"))
    kb.add(InlineKeyboardButton(text="📅 Kunlik narx", callback_data=f"mfield_dprice_{plan_id}"))
    kb.add(InlineKeyboardButton(text="📅 Kunlik daromad", callback_data=f"mfield_dearn_{plan_id}"))
    kb.add(InlineKeyboardButton(text="📆 Oylik narx", callback_data=f"mfield_mprice_{plan_id}"))
    kb.add(InlineKeyboardButton(text="📆 Oylik daromad", callback_data=f"mfield_mearn_{plan_id}"))
    kb.adjust(2)
    await call.message.edit_text(
        f"✏️ <b>{plan['name']}</b>\n\nQaysi maydonni o'zgartirmoqchisiz?",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("mfield_"))
async def cb_mining_field(call: CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    field = parts[1]
    plan_id = int(parts[2])
    field_names = {
        "hourly": "soatlik daromad (USDT)",
        "dprice": "kunlik narx (USDT)",
        "dearn": "kunlik daromad (USDT)",
        "mprice": "oylik narx (USDT)",
        "mearn": "oylik daromad (USDT)",
    }
    await state.update_data(mining_field=field, mining_plan_id=plan_id)
    await call.message.edit_text(f"💰 Yangi {field_names.get(field, field)} kiriting:")
    await state.set_state(AdminState.waiting_mining_value)


@router.message(AdminState.waiting_mining_value)
async def proc_mining_value(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    try:
        value = float(message.text.replace(" ", "").replace(",", ""))
        data = await state.get_data()
        field_map = {
            "hourly": "hourly_USDT", "dprice": "daily_price",
            "dearn": "daily_earn", "mprice": "monthly_price", "mearn": "monthly_earn",
        }
        update_mining_plan(data["mining_plan_id"], **{field_map[data["mining_field"]]: value})
        await state.clear()
        await message.answer(f"✅ Yangilandi: {value} USDT", reply_markup=admin_menu())
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


# ===== 4. BOT SOZLAMALARI =====
@router.message(F.text == "🔧 Bot sozlama")
async def bot_settings_menu(message: Message):
    if not is_admin(message.from_user.id):
        return
    s = get_bot_settings()
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🎁 Referral bonus", callback_data="set_referral"))
    kb.add(InlineKeyboardButton(text="🆘 Qo'llab-quvvatlash", callback_data="set_support"))
    kb.add(InlineKeyboardButton(text="👤 Signal nomi", callback_data="set_signal_name"))
    kb.adjust(1)
    await message.answer(
        f"🔧 <b>Bot sozlamalari</b>\n\n"
        f"🎁 Referral bonus: <b>{s.get('referral_bonus', '0.5')} USDT</b>\n"
        f"👤 Signal nomi: <b>{s.get('signal_name', 'Ai Trading Bot Signal')}</b>\n"
        f"🆘 Qo'llab-quvvatlash:\n{s.get('support_text', '@grandtrade_admin')}",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "set_referral")
async def cb_set_referral(call: CallbackQuery, state: FSMContext):
    s = get_bot_settings()
    await call.message.edit_text(
        f"🎁 Referral bonus miqdorini kiriting (USDT):\n\nJoriy: {s.get('referral_bonus', '0.5')} USDT"
    )
    await state.set_state(AdminState.waiting_referral_bonus)


@router.message(AdminState.waiting_referral_bonus)
async def proc_referral_bonus(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    try:
        bonus = float(message.text.replace(" ", "").replace(",", ""))
        set_bot_setting("referral_bonus", str(bonus))
        await state.clear()
        await message.answer(f"✅ Referral bonus: <b>{bonus} USDT</b>", reply_markup=admin_menu())
    except ValueError:
        await message.answer("❌ Raqam kiriting.")


@router.callback_query(F.data == "set_support")
async def cb_set_support(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("🆘 Qo'llab-quvvatlash matnini kiriting:")
    await state.set_state(AdminState.waiting_support_text)


@router.message(AdminState.waiting_support_text)
async def proc_support_text(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    set_bot_setting("support_text", message.text.strip())
    await state.clear()
    await message.answer("✅ Qo'llab-quvvatlash matni yangilandi!", reply_markup=admin_menu())


@router.callback_query(F.data == "set_signal_name")
async def cb_set_signal_name(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "👤 Signal yuborilganda ko'rinadigan treyder nomini kiriting:\n\nMisol: Grand Trade"
    )
    await state.set_state(AdminState.waiting_signal_name)


@router.message(AdminState.waiting_signal_name)
async def proc_signal_name(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    set_bot_setting("signal_name", message.text.strip())
    await state.clear()
    await message.answer(f"✅ Signal nomi: <b>{message.text.strip()}</b>", reply_markup=admin_menu())


# ===== 5. KANAL BOSHQARUVI =====
@router.message(F.text == "📢 Kanal boshqaruv")
async def manage_channels(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    channels = get_channels()
    text = "📢 <b>Kanallar boshqaruvi</b>\n\n"
    if channels:
        for ch in channels:
            text += f"• {ch[2]} ({ch[1]})\n"
    else:
        text += "Hozircha kanallar yo'q.\n"
    await message.answer(text, reply_markup=channels_keyboard(channels))


@router.callback_query(F.data == "add_channel")
async def cb_add_channel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "➕ Kanal ID kiriting:\n\n"
        "• Public kanal: <code>@kanalingiz</code>\n"
        "• Private kanal: <code>-1002519689075</code>\n\n"
        "<b>Muhim:</b> Bot kanalga admin bo'lishi kerak!"
    )
    await state.set_state(AdminState.waiting_channel_id)


@router.message(AdminState.waiting_channel_id)
async def proc_channel_id(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    await state.update_data(channel_id=message.text.strip())
    await message.answer("📝 Kanal nomini kiriting:", reply_markup=cancel_keyboard())
    await state.set_state(AdminState.waiting_channel_name)


@router.message(AdminState.waiting_channel_name)
async def proc_channel_name(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    data = await state.get_data()
    success = add_channel(data["channel_id"], message.text.strip())
    if success:
        await message.answer(f"✅ Kanal qo'shildi: <b>{message.text}</b>", reply_markup=admin_menu())
    else:
        await message.answer("❌ Allaqachon mavjud.", reply_markup=admin_menu())
    await state.clear()


@router.callback_query(F.data.startswith("del_channel_"))
async def cb_del_channel(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    ch_id = int(call.data.split("_")[-1])
    remove_channel(ch_id)
    await call.answer("✅ O'chirildi!")
    channels = get_channels()
    await call.message.edit_text("📢 <b>Kanallar:</b>", reply_markup=channels_keyboard(channels))


# ===== 6. BROADCAST =====
@router.message(F.text == "📨 Xabar yuborish")
async def broadcast_menu(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "📨 Barcha foydalanuvchilarga xabar kiriting:\n\n"
        "✅ Rasm, video, matn — hammasi yuboriladi!",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminState.waiting_broadcast)


@router.message(AdminState.waiting_broadcast)
async def proc_broadcast(message: Message, state: FSMContext):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "❌ Cancel"]:
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return
    users = get_all_users()
    sent = 0
    failed = 0
    for user in users:
        try:
            # Rasm, video yoki matn
            if message.photo:
                await message.bot.send_photo(
                    user[0], message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            elif message.video:
                await message.bot.send_video(
                    user[0], message.video.file_id,
                    caption=message.caption or ""
                )
            elif message.document:
                await message.bot.send_document(
                    user[0], message.document.file_id,
                    caption=message.caption or ""
                )
            else:
                await message.bot.send_message(
                    user[0], f"📢 <b>Ai Trading Bot:</b>\n\n{message.text}"
                )
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"✅ Yuborildi: {sent} | ❌ Xato: {failed}", reply_markup=admin_menu())
    await state.clear()


# ===== 7. STATISTIKA =====
@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    total = get_user_count()
    active = get_active_users()
    revenue = get_revenue_stats()
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami: <b>{total}</b>\n"
        f"🤖 Faol bot: <b>{active}</b>\n\n"
        f"💰 Daromad: <b>{revenue['total']:.4f} USDT</b>\n"
        f"✅ To'lovlar: <b>{revenue['count']}</b>"
    )


# ===== 8. FOYDALANUVCHILAR =====
@router.message(F.text == "👥 Foydalanuvchilar")
async def show_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = get_all_users()
    if not users:
        await message.answer("Foydalanuvchilar yo'q.")
        return
    lines = [f"👥 <b>Foydalanuvchilar ({len(users)} ta)</b>\n"]
    for u in users[:20]:
        tg_id, username, full_name, balance, tariff, tariff_exp, api_key, secret_key, bot_active = u[:9]
        api_show = f"{api_key[:6]}...{api_key[-4:]}" if api_key else "—"
        sk_show = f"{secret_key[:4]}...{secret_key[-4:]}" if secret_key else "—"
        lines.append(
            f"━━━━━━━━━━━━━━━\n"
            f"👤 {full_name} | {username or '—'}\n"
            f"🆔 <code>{tg_id}</code>\n"
            f"💰 {balance:.4f} USDT | 📋 {tariff or '—'}\n"
            f"🤖 {'✅' if bot_active else '⏹'} | 🔑 <code>{api_show}</code>\n"
            f"🔐 <code>{sk_show}</code>"
        )
    if len(users) > 20:
        lines.append(f"\n... va yana {len(users)-20} ta")
    await message.answer("\n".join(lines))


# ===== 9. TO'LOV TASDIQLASH =====
@router.message(F.text == "✅ To'lov tasdiqlash")
async def payment_info(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("✅ Foydalanuvchi chek yuborganda tasdiqlash tugmasi chiqadi.")


@router.callback_query(F.data.startswith("confirm_pay_"))
async def cb_confirm_pay(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return
    parts = call.data.split("_")
    payment_id = int(parts[2])
    tg_id = int(parts[3])
    tariff_type = parts[4]
    row = confirm_payment(payment_id)
    if not row:
        await call.answer("❌ Topilmadi.", show_alert=True)
        return
    user_tg_id, amount, t_type = row
    if tariff_type == "balance":
        update_balance(tg_id, amount)
        try:
            await call.bot.send_message(tg_id, f"✅ <b>Balans to'ldirildi!</b>\n\n💰 +{amount:.4f} USDT")
        except Exception:
            pass
    else:
        expires = (datetime.now() + timedelta(days=1 if tariff_type == "daily" else 30)).isoformat()
        set_tariff(tg_id, tariff_type, expires)
        label = "Kunlik" if tariff_type == "daily" else "Oylik"
        try:
            await call.bot.send_message(tg_id, f"✅ <b>{label} tarif faollashtirildi!</b>")
        except Exception:
            pass
    new_caption = (call.message.caption or "") + f"\n\n✅ TASDIQLANDI ({call.from_user.full_name})"
    try:
        await call.message.edit_caption(caption=new_caption)
    except Exception:
        await call.answer("✅ Tasdiqlandi!")


@router.callback_query(F.data.startswith("reject_pay_"))
async def cb_reject_pay(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q.", show_alert=True)
        return
    parts = call.data.split("_")
    tg_id = int(parts[3])
    try:
        await call.bot.send_message(tg_id, "❌ <b>To'lovingiz rad etildi.</b>")
    except Exception:
        pass
    new_caption = (call.message.caption or "") + "\n\n❌ RAD ETILDI"
    try:
        await call.message.edit_caption(caption=new_caption)
    except Exception:
        await call.answer("❌ Rad etildi!")