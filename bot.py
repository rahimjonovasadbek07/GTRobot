import asyncio
import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database.db import init_db
from handlers.user import router as user_router
from handlers.trading import router as trading_router
from handlers.admin import router as admin_router
from handlers.signals import router as signals_router
from handlers.referral import router as referral_router
from handlers.history import router as history_router
from handlers.copy_trading import router as copy_trading_router
from handlers.arbitrage import router as arbitrage_router
from handlers.guide import router as guide_router
from handlers.mining import router as mining_router, mining_payout_loop
from handlers.cancel_handler import router as cancel_router
from handlers.settings import router as settings_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main():
    init_db()
    logger.info("✅ Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(cancel_router)  # Eng birinchi!
    dp.include_router(admin_router)
    dp.include_router(signals_router)
    dp.include_router(arbitrage_router)
    dp.include_router(guide_router)
    dp.include_router(settings_router)
    dp.include_router(mining_router)
    dp.include_router(copy_trading_router)
    dp.include_router(trading_router)
    dp.include_router(referral_router)
    dp.include_router(history_router)
    dp.include_router(user_router)

    logger.info("🤖 GTRobot V3 ishga tushdi!")
    asyncio.create_task(mining_payout_loop(bot))
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
