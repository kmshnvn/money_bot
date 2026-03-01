from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

from flowers.config import ADMIN_LIST_FL
from flowers.database import first_create
from flowers.database.model import User
from flowers.database.static_models import UserRole

router = Router()


@router.message(Command("start"))
async def bot_start(message: Message) -> None:
    """
    Функция, приветствует пользователя.

    Активируется при получении от пользователя /start.
    Создает БД, если такого пользователя не было раньше
    """
    logger.debug("bot_start")
    telegram_id = message.chat.id
    logger.info(f"{telegram_id} - команда start")
    print(ADMIN_LIST_FL)
    role = UserRole.ADMINISTRATOR if telegram_id in ADMIN_LIST_FL else UserRole.USER
    print(role)
    if not User.get_or_none(telegram_id=telegram_id):
        username = message.from_user.username
        first_name = message.from_user.first_name
        second_name = message.from_user.last_name

        User.create(
            username=username,
            telegram_id=telegram_id,
            first_name=first_name,
            second_name=second_name,
            user_role=UserRole.ADMINISTRATOR if telegram_id in ADMIN_LIST_FL else UserRole.USER,
        )
        logger.info("Создал БД пользователя")

    if telegram_id in ADMIN_LIST_FL:
        await message.answer("Меню Администратора")
    else:
        await message.answer("Привет, в данный момент бот находится в разработке и используется администраторами")