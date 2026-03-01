from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from flowers.config import BOT_TOKEN_FL, DEFAULT_COMMANDS_FL
from flowers.database.states import storage_fl
from flowers.handlers_fl import start


async def main():
    bot = Bot(token=BOT_TOKEN_FL)

    await bot.set_my_commands(
        [BotCommand(command=i[0], description=i[1]) for i in DEFAULT_COMMANDS_FL]
    )

    dp = Dispatcher(storage=storage_fl)
    dp.include_routers(start.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Настройка бота прошла успешно")

    await dp.start_polling(bot)
