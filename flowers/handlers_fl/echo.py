from aiogram import F
from aiogram.types import Message
from loguru import logger

from flowers.handlers_fl.start import router


@router.message(F.chat.type.in_("private"))
async def echo(message: Message):
    logger.debug("echo")
    logger.debug(message)

    await message.answer("Жду файл или вернись к изначальному сообщению, нажав /start")
