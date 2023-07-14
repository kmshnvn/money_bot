from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers.default_heandlers import start, echo, help

from database.states import storage
from config_data.config import BOT_TOKEN, DEFAULT_COMMANDS


async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode='HTML')

    await bot.set_my_commands(
        [BotCommand(command=i[0], description=i[1]) for i in DEFAULT_COMMANDS]
    )

    dp = Dispatcher(storage=storage)
    dp.include_routers(
        start.router,
        help.router,
        echo.router
    )

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info('Настройка бота прошла успешно')

    await dp.start_polling(bot)


