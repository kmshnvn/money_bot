from loguru import logger

from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def bot_echo(message: Message):
    """    Функция, отлавливает текст, который не относится ни к одному состоянию    """
    await message.answer(
        text=f"Чтобы узнать подробнее о боте: /help"
        )
    logger.info(f'{message.chat.id} - echo.py | команда echo {message.text}')
