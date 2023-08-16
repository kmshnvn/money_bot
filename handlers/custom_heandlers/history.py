from datetime import datetime, date
from typing import Tuple, Dict

from aiogram import F
from loguru import logger

from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.states import UserState
from database.database import (
    db_get_history,
    db_get_transaction,
    db_delete_transaction,
    db_get_history_transaction, db_get_custom_date_history,
)
from functions import simple_cal_callback, SimpleCalendar
from functions.functions import create_history_text, text_of_stat
from handlers.default_heandlers.start import router
from keyboards.inline_keyboards import (
    change_date,
    main_history_inline_kb,
    transaction_history,
    delete_history_kb,

)


@router.message(Command('history'))
@router.message(F.text.contains('История'))
async def history(message: Message, state: FSMContext) -> None:
    """
    Функция, отлавливает команду /history
    """
    try:
        logger.info(f'{message.chat.id} - history.py | выбор команды /history')
        await state.set_data({})

        if not history:
            await message.answer(f'Истории пользования еще нет, выберите другую команду')
        else:
            await message.answer(
                f'*Это меню различной статистики.*\n\n'
                f'Здесь можно посмотреть последние операции и удалить их при необходимости. '
                f'Если нажать на кнопку 📊*Статисика*, '
                f'то сможешь посмотреть свои обобщенные траты за различный период '
                f'и понять куда уходит больше всего денег',
                parse_mode='Markdown',
                reply_markup=main_history_inline_kb()
            )

            await state.set_state(UserState.main_history)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при выборе пункта истории {ex}')
        await message.edit_text('🤕Возникла ошибка при просмотре истории. Скоро меня починят')


@router.callback_query(Text('back_to_main_history'))
async def callback_history(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        logger.info(f'{callback.message.chat.id} - history.py | возврат в меню history')
        await state.set_data({})

        await callback.message.edit_text(
            f'*Это меню различной статистики.*\n\n'
            f'Здесь можно посмотреть последние операции и удалить их при необходимости. '
            f'Если нажать на кнопку 📊*Статисика*, '
            f'то сможешь посмотреть свои обобщенные траты за различный период '
            f'и понять куда уходит больше всего денег',
            parse_mode='Markdown',
            reply_markup=main_history_inline_kb()
        )

        await state.set_state(UserState.main_history)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при выборе пункта истории {ex}')
        await callback.message.edit_text('🤕Возникла ошибка при просмотре истории. Скоро меня починят')


@router.callback_query(Text('history_of_transactions'))
async def user_transaction_history(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        logger.info(f'{callback.message.chat.id} - Выводим пользовательcкую дату пользователя')
        await state.set_state(UserState.transaction_history)

        start_date, end_date = create_date(await state.get_data())

        if start_date and end_date:
            history = db_get_custom_date_history(callback.message.chat.id, start_date, end_date)
            text = create_history_text('', list(history))
            if text == '':
                full_text = f'Транзакции в периоде с {start_date} по {end_date} отсутствуют'
            else:
                full_text = f'Транзакции в выбранном периоде {start_date} - {end_date}\n\n' + text

        else:
            history = db_get_history(callback.message.chat.id)
            text = 'Последние операции\n\n'
            full_text = create_history_text(text, list(history))

        await callback.message.edit_text(
            f'{full_text}',
            parse_mode='Markdown',
            reply_markup=transaction_history()
        )
    except Exception as ex:
        logger.error(f'Что-то пошло не так при формировании истории {ex}')
        await callback.message.edit_text('🤕Возникла ошибка при выводе истории. Скоро меня починят')


@router.message(F.text.startswith('/del'))
async def check_delete_transaction(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды удаления операции.
    """
    try:
        logger.info(f'{message.chat.id} - Уточняем удаление операции')

        transaction_id = message.text[4:]
        transaction = db_get_transaction(transaction_id)

        amount = float(transaction.get("amount"))
        summ = amount if amount >= 0 else -amount

        await state.set_data({
            'id': transaction_id,
            'user_id': message.chat.id,
            'summ': amount,
        })

        text = (
            f'Выбрана операция\n\n'
            f'Дата операции: {transaction["transaction_date"]}\n'
            f'{summ} ₽ в категории {transaction["category_name"]}\n'
            f'Описание: {transaction["description"]}\n\n'
            f'Удаляем операцию?'
        )

        await message.answer(
            f'{text}',
            parse_mode='Markdown',
            reply_markup=delete_history_kb()
        )

        await state.set_state(UserState.delete_transaction)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при уточнении удаления операции: {ex}')
        await message.answer('🤕 Возникла ошибка при уточнении удаления операции. Скоро меня починят')


@router.callback_query(UserState.delete_transaction, Text('delete_transaction'))
async def delete_transaction(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик подтверждения удаления операции.
    """
    try:
        logger.info(f'{callback.message.chat.id} - Уточняем удаление операции')

        user_dict = await state.get_data()
        db_delete_transaction(user_dict)

        await callback.message.edit_text(text=f'Удалил', parse_mode='Markdown')
        await state.set_state(UserState.default)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при удалении операции: {ex}')
        await callback.message.edit_text(
            '🤕 Возникла ошибка при подтверждении удаления операции. Скоро меня починят'
        )


@router.callback_query(Text('user_statistic'))
async def month_statistic(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды "Статистика".
    """
    try:
        logger.info(f'{callback.message.chat.id} - Вывод команды статистики')

        history_list, start_date, end_date = db_get_history_transaction(
            tg_id=callback.message.chat.id,
        )
        text = text_of_stat(history_list)

        await callback.message.edit_text(
            text=f'История с {start_date} по {end_date}:\n{text}',
            parse_mode='Markdown',
            reply_markup=change_date()
        )
        await state.set_state(UserState.statistic_history)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при выводе статистики: {ex}')
        await callback.message.edit_text(
            '🤕 Возникла ошибка при выводе статистики. Скоро меня починят'
        )


@router.callback_query(Text('change_date'))
async def date_statistic(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды выбора даты для статистики.
    """
    try:
        await callback.message.edit_text(
            text='Выберите дату начала',
            reply_markup=await SimpleCalendar().start_calendar()
        )
        await state.update_data({'user_state': await state.get_state()})
        await state.set_state(UserState.start_date_history)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при выборе даты для статистики: {ex}')
        await callback.message.edit_text('🤕 Возникла ошибка при выборе даты. Скоро меня починят')


@router.callback_query(UserState.start_date_history, simple_cal_callback.filter())
@router.callback_query(UserState.end_date_history, simple_cal_callback.filter())
async def process_simple_calendar_history(
        callback_query: CallbackQuery,
        callback_data: dict,
        state: FSMContext):
    """
    Обработчик выбора даты через календарь для статистики.
    """
    try:

        my_state = await state.get_state()
        selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)

        if selected and my_state == 'UserState:start_date_history':
            new_date = date.strftime("%d.%m.%Y")
            await callback_query.message.edit_text(
                f'Выбранная дата {new_date}\n'
                f'Выберите дату конца периода',
                reply_markup=await SimpleCalendar().start_calendar()
            )
            await state.update_data({'start_date': new_date})
            await state.set_state(UserState.end_date_history)

        elif selected and my_state == 'UserState:end_date_history':

            new_date = date.strftime("%d.%m.%Y")
            user_dict = await state.get_data()
            start_date = user_dict.get("start_date")

            if new_date < start_date:
                start_date, new_date = new_date, start_date
                await state.update_data({'start_date': start_date, 'end_date': new_date})
                print(f'поменял данные {start_date}, {new_date}')
            else:
                await state.update_data({'end_date': new_date})

            await callback_query.message.edit_text(
                f'Выбранная дата {start_date} - {new_date}\n'
            )

            user_state = user_dict.get('user_state')
            print(user_state)
            if user_state == 'UserState:transaction_history':
                await user_transaction_history(callback_query, state)
            elif user_state == 'UserState:statistic_history':
                await month_custom_date_statistic(callback_query.message, state)
            else:
                await callback_query.message.edit_text(
                    f'Что-то пошло не так при выборе даты, скоро все исправим😵‍💫',
                )
                await history(callback_query.message, state)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при обработке календаря для статистики: {ex}')
        await callback_query.message.edit_text(
            '🤕 Возникла ошибка при выборе даты. Скоро меня починят'
        )


def create_date(user_dict: Dict) -> Tuple[date | None, date | None]:
    """
    Создание объектов даты начала и даты конца из данных пользователя.
    """
    start_date = datetime.strptime(user_dict.get('start_date'), '%d.%m.%Y').date() \
        if user_dict.get('start_date') \
        else None

    end_date = datetime.strptime(user_dict.get('end_date'), '%d.%m.%Y').date() \
        if user_dict.get('end_date') \
        else None

    return start_date, end_date


async def month_custom_date_statistic(message: Message, state: FSMContext) -> None:
    """
    Вывод статистики за пользовательский период с датами пользователя.
    """
    try:
        logger.info(f'{message.chat.id} - Выводим транзакции с датами пользователя')

        begin_history, end_history = create_date(await state.get_data())

        history_list, start_date, end_date = db_get_history_transaction(
            tg_id=message.chat.id,
            start_date=begin_history,
            end_date=end_history
        )
        text = text_of_stat(history_list)
        await message.edit_text(
            text=f'История с {start_date} по {end_date}:\n{text}',
            parse_mode='Markdown',
            reply_markup=change_date()
        )
        await state.set_state(UserState.statistic_history)
    except Exception as ex:
        logger.error(f'Что-то пошло не так при выводе статистики за пользовательский период: {ex}')
        await message.edit_text('🤕 Возникла ошибка при выводе статистики. Скоро меня починят')
