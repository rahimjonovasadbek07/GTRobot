from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user, set_user_lang
from utils.lang import t, get_lang_keyboard, LANGS
from keyboards.kb import main_menu

router = Router()


@router.message(F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"]))
async def show_settings(message: Message):
    user = get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    lang_names = {"uz": "🇺🇿 O'zbek", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🌐 Tilni o'zgartirish", callback_data="change_lang"))
    kb.adjust(1)

    await message.answer(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"🌐 Joriy til: <b>{lang_names.get(lang, '🇺🇿 O\'zbek')}</b>\n\n"
        f"Sozlamani o'zgartirish uchun tugmani bosing:",
        reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "change_lang")
async def cb_change_lang(call: CallbackQuery):
    await call.message.edit_text(
        "🌐 Tilni tanlang / Выберите язык / Choose language:",
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
    await call.message.edit_text(t(lang, "lang_set"))
    await call.message.answer(
        f"✅ <b>Til o'zgartirildi!</b>",
        reply_markup=main_menu(lang)
    )
