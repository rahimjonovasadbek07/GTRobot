import asyncio
import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from typing import Callable, Dict, Any, Awaitable

from config import BOT_TOKEN, REQUIRED_CHANNELS
from database.db import init_db, get_channels
from handlers.user import router as user_router
from keyboards.kb import check_sub_keyboard
from handlers.trading import router as trading_router, auto_tasks, auto_trading_loop
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


class SubscriptionMiddleware(BaseMiddleware):
    SKIP_CALLBACKS = {
        "check_sub", "lang_uz", "lang_ru", "lang_en",
        "guide_mexc_api", "guide_auto_trading", "guide_copy_trading",
        "guide_arbitrage", "guide_signals", "guide_balance",
        "guide_referral", "guide_faq", "guide_back",
    }

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]

        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
            if event.text and (event.text.startswith("/start") or event.text.startswith("/admin")):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if event.data and event.data in self.SKIP_CALLBACKS:
                return await handler(event, data)

        if user_id is None:
            return await handler(event, data)

        channels_to_check = list(REQUIRED_CHANNELS)
        try:
            db_channels = get_channels()
            for ch in db_channels:
                channels_to_check.append({"id": ch[1], "name": ch[2]})
        except Exception:
            pass

        if not channels_to_check:
            return await handler(event, data)

        for ch in channels_to_check:
            ch_id = ch["id"] if isinstance(ch, dict) else ch[1]
            try:
                member = await bot.get_chat_member(ch_id, user_id)
                if member.status in ["left", "kicked", "restricted"]:
                    text = "🔔 <b>Botdan foydalanish uchun kanalga obuna bo'ling:</b>"
                    kb = check_sub_keyboard(channels_to_check)
                    if isinstance(event, Message):
                        await event.answer(text, reply_markup=kb)
                    elif isinstance(event, CallbackQuery):
                        await event.message.answer(text, reply_markup=kb)
                        await event.answer()
                    return
            except Exception:
                pass

        return await handler(event, data)


async def restore_active_traders(bot: Bot):
    try:
        from database.db import get_all_active_traders
        active_users = get_all_active_traders()
        if not active_users:
            return
        logger.info(f"🔄 {len(active_users)} ta faol trader qayta tiklanmoqda...")
        for user in active_users:
            user_id = user["tg_id"]
            api_key = user.get("mexc_api_key")
            secret_key = user.get("mexc_secret_key")
            if not api_key or not secret_key:
                continue
            trade_amount = float(user.get("trade_amount", 10))
            min_profit = float(user.get("min_profit", 0.3))
            task = asyncio.create_task(
                auto_trading_loop(bot, user_id, api_key, secret_key, trade_amount, min_profit)
            )
            auto_tasks[user_id] = task
            try:
                await bot.send_message(
                    user_id,
                    f"🔄 <b>Bot qayta ishga tushdi!</b>\n\n"
                    f"✅ Trading avtomatik davom etmoqda\n"
                    f"💰 Har trade: <b>{trade_amount} USDT</b>"
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"restore_active_traders xatosi: {e}")


async def main():
    init_db()
    logger.info("✅ Ma'lumotlar bazasi tayyor.")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # MUHIM: guide_router COPY TRADING DAN OLDIN bo'lishi kerak!
    dp.include_router(cancel_router)
    dp.include_router(admin_router)
    dp.include_router(signals_router)
    dp.include_router(arbitrage_router)
    dp.include_router(guide_router)      # ← guide avval
    dp.include_router(settings_router)
    dp.include_router(mining_router)
    dp.include_router(copy_trading_router)  # ← copy trading keyin
    dp.include_router(trading_router)
    dp.include_router(referral_router)
    dp.include_router(history_router)
    dp.include_router(user_router)

    logger.info("🤖 GTRobot ishga tushdi!")
    asyncio.create_task(mining_payout_loop(bot))
    asyncio.create_task(restore_active_traders(bot))

    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())