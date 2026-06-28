"""
Foydalanuvchilar ma'lumotlarini export qilish va Telegram kanalga
backup qilish/qaytarish tizimi.

QO'SHISH UCHUN:
1. Bu faylni handlers/ papkasiga qo'shing
2. config.py ga BACKUP_CHANNEL_ID qo'shing
3. bot.py ga quyidagilarni qo'shing (pastdagi misolga qarang)
"""
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
import csv
import io
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_all_users
from config import ADMIN_IDS

router = Router()


def is_admin(user_id):
    return user_id in ADMIN_IDS


@router.message(Command("export"))
@router.message(F.text == "📥 Export foydalanuvchilar")
async def export_users(message: Message):
    if not is_admin(message.from_user.id):
        return

    users = get_all_users()
    if not users:
        await message.answer("❌ Foydalanuvchilar yo'q.")
        return

    # CSV yaratish
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Telegram ID", "Username", "To'liq ism", "Balans (USDT)",
        "Tarif", "Tarif tugashi", "MEXC API Key", "MEXC Secret Key",
        "Bot faol", "Referral kod", "Referal qilgan ID", "Referral bonus"
    ])

    for u in users:
        writer.writerow(list(u))

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM - Excelda to'g'ri ochilishi uchun
    filename = f"gtrobot_users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    file = BufferedInputFile(csv_bytes, filename=filename)

    await message.answer_document(
        file,
        caption=f"📥 <b>Foydalanuvchilar export</b>\n\n👥 Jami: {len(users)} ta\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )


@router.message(Command("backup_now"))
async def manual_backup(message: Message):
    """Qo'lda backup yuborish - test uchun"""
    if not is_admin(message.from_user.id):
        return

    from config import BACKUP_CHANNEL_ID, DB_PATH
    from utils.backup import backup_to_channel

    if not BACKUP_CHANNEL_ID:
        await message.answer("❌ BACKUP_CHANNEL_ID config.py da kiritilmagan!")
        return

    await message.answer("⏳ Backup yuborilmoqda...")
    success = await backup_to_channel(message.bot, BACKUP_CHANNEL_ID, DB_PATH)
    if success:
        await message.answer("✅ Backup muvaffaqiyatli yuborildi!")
    else:
        await message.answer("❌ Backup xato berdi. Bot kanalga admin ekanligini tekshiring.")


@router.message(Command("restore_now"))
async def manual_restore(message: Message):
    """Qo'lda restore qilish - test uchun"""
    if not is_admin(message.from_user.id):
        return

    from config import BACKUP_CHANNEL_ID, DB_PATH
    from utils.backup import restore_from_channel

    if not BACKUP_CHANNEL_ID:
        await message.answer("❌ BACKUP_CHANNEL_ID config.py da kiritilmagan!")
        return

    await message.answer("⏳ Backup qaytarilmoqda...")
    success = await restore_from_channel(message.bot, BACKUP_CHANNEL_ID, DB_PATH)
    if success:
        await message.answer("✅ Ma'lumotlar muvaffaqiyatli qaytarildi!")
    else:
        await message.answer("❌ Restore xato berdi. Kanalda pin qilingan backup yo'q yoki bot admin emas.")
