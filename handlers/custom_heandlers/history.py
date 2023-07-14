from aiogram import F
from loguru import logger

from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config_data.config import MONTH_NAME
from database.states import UserState
from database.database import (
    db_get_history,
    db_get_transaction,
    db_delete_transaction,
    db_get_history_transaction,
)
from functions.functions import create_history_text
from handlers.default_heandlers.start import router
from keyboards.reply_keyboards import (
    history_kb,
    delete_history_kb,
    main_kb,
)


@router.message(Command('history'))
@router.message(F.text.contains('История'))
async def history(message: Message, state: FSMContext) -> None:
    """    Функция, отлавливает команду /history

    Смотрит текущую дату, и получает данные из БД, ищет все даты пользователя;
    Если дат нет, то выводит информацию об этом, если в списке дат найдено сегодняшнее число -
    показывает историю за сегодняшний день, иначе выводит историю за последние 3 дня,
    в который пользователь использовал бота
    """
    try:
        logger.info(f'{message.chat.id} - history.py | выбор команды /history')

        history = db_get_history(message.chat.id)

        if not history:
            await message.answer(f'Истории пользования еще нет, выберите другую команду')
        else:
            text = 'Последние 5 операций\n\n'

            text = create_history_text(text, list(history))

            await message.answer(
                f'{text}',
                parse_mode='Markdown',
                reply_markup=history_kb()
            )

            await state.set_state(UserState.main_history)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при формировании истории {ex}')
        await message.answer('🤕Возникла ошибка при выводе истории. Скоро меня починят')


@router.message(F.text.startswith('/del'))
async def check_delete_transaction(message: Message, state: FSMContext) -> None:
    transaction_id = message.text[4:]
    transaction = db_get_transaction(transaction_id)

    await state.set_data({'id': transaction_id})

    amount = float(transaction.get("amount"))
    summ = amount if amount >= 0 else -amount

    text = f'Выбрана операция\n\n' \
           f'Дата операции: {transaction["transaction_date"]}\n' \
           f'{summ} ₽ в категории {transaction["category_name"]}\n' \
           f'Описание: {transaction["description"]}\n\n' \
           f'Удаляем операцию?'

    await message.answer(
        f'{text}',
        parse_mode='Markdown',
        reply_markup=delete_history_kb()
    )

    await state.set_state(UserState.delete_transaction)


@router.message(UserState.delete_transaction, F.text.contains('Удаляем'))
async def delete_transaction(message: Message, state: FSMContext) -> None:
    user_dict = await state.get_data()
    db_delete_transaction(user_dict.get('id'))

    await message.answer(text=f'Удалил', parse_mode='Markdown', reply_markup=main_kb())
    await state.set_state(UserState.default)


@router.message(UserState.main_history, F.text.contains('Статистика'))
async def month_statistic(message: Message, state: FSMContext) -> None:
    income = 0
    expenses = 0
    date_list = []
    date_dict = {}
    text = 'История пользования за 3 месяца:\n'

    history_list = db_get_history_transaction(message.chat.id)

    for history in history_list[::-1]:
        summ = float(history['amount'])
        year_month = history['year_month']
        year, month = year_month.split('-')
        month_name = MONTH_NAME[int(month)]

        if year_month not in date_list:
            text += f'\n🔹*{month_name} {year}*\n\n'
            date_list.append(year_month)

        text += f"  🔸{history['category_name']}: {summ} ₽\n"

    await message.answer(text)
