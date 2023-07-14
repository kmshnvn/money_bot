from aiogram.fsm.context import FSMContext
from loguru import logger
from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.types import Message

from config_data.config import DEFAULT_COMMANDS
from database.states import UserState

router = Router()


@router.message(Command('help'))
@router.message(F.text.contains('Помощь'))
async def bot_help(message: Message, state: FSMContext) -> None:
    """
    Функция, дает справочную информацию по работе бота

    Активируется в момент написания пользователем /help.

    """
    await state.set_state(UserState.default)
    logger.info(f'{message.chat.id} - команда help')
    text = [f'/{command} - {desk}' for command, desk in DEFAULT_COMMANDS]
    await message.answer(
        'Я бот, который поможет тебе вести твои финансы\n\n'
        + '\n'.join(text)
    )

