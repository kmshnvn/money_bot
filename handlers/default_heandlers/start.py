from aiogram.fsm.context import FSMContext
from loguru import logger
from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.types import Message

from database.database import db_get_main_statistic
from database.model import User, Balance, Account
from database.states import UserState
from keyboards.reply_keyboards import main_kb, start_kb

router = Router()

@router.message(Command('start'))
@router.message(F.text.contains('Главное меню'))
async def bot_start(message: Message, state: FSMContext) -> None:
    """
    Функция, приветствует пользователя.

    Активируется при получении от пользователя /start.
    Создает БД, если такого пользователя не было раньше
    """

    logger.info(f'{message.chat.id} - команда start')

    if not User.get_or_none(telegram_id=message.from_user.id):
        user = User.create(username=message.from_user.full_name, telegram_id=message.chat.id)
        account = Account.create(user=user)
        Balance.create(user=user, account=account)
        logger.info('Создал БД пользователя')

        await message.answer(
            text=f"Привет, {message.from_user.first_name}!\n"
                 f"\nЯ бот, который поможет тебе держать финансы под контролем\n"
                 f"\nЧтобы начать работать нужно сделать несколько настроек\n"
                 f"\nНачнем с категорий трат",
            parse_mode='Markdown',
            reply_markup=start_kb()
        )
    else:
        logger.info('Такой id уже есть. Базы не стал создавать')

        user_transactions = db_get_main_statistic(message.chat.id)
        text = get_statistic_text(user_transactions)

        await message.answer(
            text=f"{message.from_user.first_name}, вот твоя статистика:\n"
                 f"{text}",
            parse_mode='Markdown',
            reply_markup=main_kb()
        )

    await state.set_state(UserState.default)


def get_statistic_text(user_transactions) -> str:
    text = ''
    for key, value in user_transactions.items():
        period = ''
        if key == 'today':
            period = 'За сегодня'
        elif key == 'week':
            period = 'С начала недели'
        elif key == 'month':
            period = 'С начала месяца'

        text += f'\n🔹*{period}*\n\n'

        if not value:
            text += 'Операций не было😛\n'
        else:
            income = 0
            expense = 0

            for elem in value:
                amount = float(elem)
                if amount < 0:
                    expense += amount
                else:
                    income += amount

            result = income + expense

            if income > 0:
                text += f'Доход: {income} ₽\n'
            if expense < 0:
                text += f'Расходы: {expense} ₽\n'
            text += f'Всего: {result} ₽\n'

    return text
