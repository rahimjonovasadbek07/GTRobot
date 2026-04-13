from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user, set_user_lang, get_bot_settings
from utils.lang import t, get_lang_keyboard, LANGS, LANG_NAMES
from keyboards.kb import main_menu

router = Router()


class SettingsState(StatesGroup):
    waiting_lang = State()


@router.message(F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"]))
async def show_settings(message: Message):
    user = get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=t(lang, "change_lang"), callback_data="change_lang"))
    kb.adjust(1)

    await message.answer(
        f"{t(lang, 'settings_title')}\n\n"
        f"🌐 {t(lang, 'settings_lang')}: <b>{LANG_NAMES.get(lang, '🇺🇿 O\'zbek')}</b>",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "change_lang")
async def cb_change_lang(call: CallbackQuery):
    lang = get_user(call.from_user.id).get("lang", "uz") if get_user(call.from_user.id) else "uz"
    await call.message.edit_text(
        t(lang, "choose_lang"),
        reply_markup=get_lang_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def cb_lang(call: CallbackQuery):
    lang = call.data.split("_")[1]
    if lang not in LANGS:
        await call.answer("❌ Xato!")
        return
    set_user_lang(call.from_user.id, lang)
    await call.answer(t(lang, "lang_set"))

    user = get_user(call.from_user.id)
    balance = user["balance"] if user else 0

    tariff_status = t(lang, "tariff_no")
    if user and user.get("tariff") and user.get("tariff_expires"):
        from datetime import datetime
        try:
            exp = datetime.fromisoformat(user["tariff_expires"])
            if exp > datetime.now():
                days = (exp - datetime.now()).days
                tariff_status = f"✅ {user['tariff'].capitalize()} ({days} kun)"
        except Exception:
            pass

    await call.message.edit_text(t(lang, "lang_set"))
    await call.message.answer(
        t(lang, "start_welcome", name=call.from_user.full_name, balance=balance, tariff=tariff_status),
        reply_markup=main_menu(lang)
    )
