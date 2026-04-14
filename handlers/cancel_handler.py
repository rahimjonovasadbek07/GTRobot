"""
Universal cancel handler - har qanday holatda ishlaydi
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_user
from keyboards.kb import main_menu, CANCEL_TEXTS

router = Router()


@router.message(F.text.in_(CANCEL_TEXTS))
async def universal_cancel(message: Message, state: FSMContext):
    """Har qanday holatda bekor qilish"""
    current_state = await state.get_state()
    await state.clear()
    
    user = get_user(message.from_user.id)
    lang = user.get("lang", "uz") if user else "uz"
    
    await message.answer(
        "❌ Bekor qilindi.",
        reply_markup=main_menu(lang)
    )
