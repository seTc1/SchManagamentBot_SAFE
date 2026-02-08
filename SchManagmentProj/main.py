import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.handlers import router
from app.database.engine_base import async_main, engine
from app.bot import init_bot, close_bot

with open("BOT_API_TOKEN.yaml", encoding="utf-8") as key:
    TOKEN = key.read().strip()


async def main():
    await async_main()
    storage = MemoryStorage()
    bot = init_bot(TOKEN)
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await close_bot()
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("End")
