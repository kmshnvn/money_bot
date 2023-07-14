from datetime import date

from loguru import logger

from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.types import CallbackQuery

from database.database import (
    db_get_category,
    db_create_transaction,
    db_create_category,
    db_get_balance,
)

from database.states import UserState
from handlers.default_heandlers.start import router
from functions import simple_cal_callback, SimpleCalendar
from keyboards.reply_keyboards import (
    user_category_kb,
    transaction_descr_kb,
    transaction_main_kb,
    default_category_kb,
    save_category_kb,
    transaction_end_kb,
    transaction_save_kb,
)


@router.message(UserState.default, F.text.contains("Новая операция"))
@router.message(Command('transaction'))
@router.message(UserState.save_transaction, F.text.contains("Изменить"))
async def new_transaction(message: Message, state: FSMContext):
    logger.info('Начинаем запись операции пользователя и спрашиваем дату')

    user_category = db_get_category(tg_id=message.chat.id, user_name=message.from_user.full_name)

    if not user_category:
        logger.info('Категорий нет')

        await message.answer(
            text = f'*Категории еще не установлены, сначала нужно их настроить.*\n\n'
                 f"Для быстрой настройки у меня есть стандартные категории трат, "
                 f"чтобы использовать их просто нажми на кнопку 'Использовать стандартный набор'"
                 f"\n\n*Стандартный набор расходов:*"
                 f"\nТранспорт"
                 f"\nПродукты"
                 f"\nКафе"
                 f"\nДом"
                 f"\nПутешествия"
                 f"\nОдежда"
                 f"\n\n*Категории дохода:*"
                 f"\nЗарплата",
            parse_mode='Markdown',
            reply_markup=default_category_kb(),
        )
        await state.set_state(UserState.settings)

    else:
        balance = db_get_balance(message.chat.id)

        await state.set_data({
            'date': str(date.today()),
            'group': 'Expense',
            'summ': '',
            'category': '',
            'descr': '',
            'balance': float(balance),
        })
        await state.update_data(user_category)

        await state.set_state(UserState.transaction_group)
        await transaction_summ(message, state)


@router.message(UserState.transaction_summ, F.text.contains('Доход') | F.text.contains("Расход"))
async def transaction_summ(message: Message, state: FSMContext):
    logger.info(f'Пользователь {message.chat.id}. Уточняем сумму операции')
    text_handler = ['Расход', '/transaction']

    user_dict = await state.get_data()
    group_name = user_dict.get('group')
    user_date = user_dict.get('date')
    balance = user_dict.get('balance')

    if message.text in text_handler:
        group_name = 'Expense'
    elif message.text == '💰Доход💰':
        group_name = 'Income'

    await state.update_data({'group': group_name})

    if user_date == str(date.today()):
        user_date = 'Сегодня'

    text = f'Сейчас твой баланс: {balance}\n\n'

    if group_name == 'Expense':
        await message.answer(
            text=text+
                 f'Записываю расходную операцию.\n'
                 f'Дата - *{user_date}*\n\n'
                 f'Сколько денег потратили?',
            parse_mode='Markdown',
            reply_markup=transaction_main_kb(group_name)
        )
    else:
        await message.answer(
            text=text +
                 f'Записываю пополнение.\n'
                 f'Дата - *{user_date}*\n\n'
                 f'Сколько денег получили?',
            parse_mode='Markdown',
            reply_markup=transaction_main_kb(group_name)
        )
    await state.set_state(UserState.transaction_summ)



@router.message(
    UserState.transaction_summ,
    F.text.contains("Выбрать другую дату")
)
async def transaction_group(message: Message, state: FSMContext):
    logger.info(f'Пользователь {message.chat.id}. Уточняем группу операции')
    await message.answer(
        f'Когда была совершена покупка?',
        parse_mode='Markdown',
        reply_markup=await SimpleCalendar().start_calendar()
    )


@router.callback_query(simple_cal_callback.filter())
async def process_simple_calendar(
        callback_query: CallbackQuery,
        callback_data: dict,
        state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.edit_text(
            f'Выбранная дата {date.strftime("%d.%m.%Y")}',
        )
        await state.update_data({'date': date.strftime('%Y-%m-%d')})
        await transaction_summ(callback_query.message, state)


@router.message(UserState.transaction_summ, F.text.regexp(r"^(\d+)$").as_("digits"))
async def transaction_category(message: Message, state: FSMContext):
    logger.info(f'Пользователь {message.chat.id}. Уточняем категорию операции')

    await state.update_data({'summ': int(message.text)})

    user_dict = await state.get_data()
    group_name = 'Expense' if user_dict['group'] == 'Expense' else 'Income'

    await message.answer(
        f'В какой категории была операция',
        parse_mode='Markdown',
        reply_markup=user_category_kb(user_dict[group_name])
    )

    await state.set_state(UserState.transaction_category)


@router.message(UserState.transaction_category)
async def transaction_description(message: Message, state: FSMContext):
    logger.info(f'Пользователь {message.chat.id}. Уточняем описание операции')

    user_dict = await state.get_data()
    group_name = 'Expense' if user_dict['group'] == 'Expense' else 'Income'


    if message.text not in user_dict[group_name]:
        await state.update_data({'category': message.text})

        await message.answer(
            f'К сожалению, такой категории не было в вашем списке.\n'
            f'\nГруппа категории: {user_dict["group"]}\n'
            f'Категория: {message.text}\n'
            f'\nДобавим категорию',
            parse_mode='Markdown',
            reply_markup=transaction_save_kb()
        )
        await state.set_state(UserState.transaction_new_category)

    else:
        await state.update_data({'category': message.text})

        await message.answer(
            f'Добавьте описание операции (необязательно)',
            parse_mode='Markdown',
            reply_markup=transaction_descr_kb()
        )

        await state.set_state(UserState.transaction_description)


@router.message(UserState.transaction_new_category, F.text.contains('Записать'))
async def transaction_new_category(message: Message, state: FSMContext):
    logger.info(f'Пользователь {message.chat.id}. Запись новой категории')

    user_dict = await state.get_data()

    group_name = 'Expense' if user_dict['group'] == 'Expense' else 'Income'
    new_category = {group_name: user_dict['category']}

    db_create_category(message.chat.id, new_category)

    await message.answer(
        f'Добавьте описание операции (необязательно)',
        parse_mode='Markdown',
        reply_markup=transaction_descr_kb()
    )

    await state.set_state(UserState.transaction_description)


@router.message(UserState.transaction_description)
async def transaction_check(message: Message, state: FSMContext):
    logger.info(f'Пользователь {message.chat.id}. Проверка операции')

    description = '' if message.text == 'Без описания' else message.text
    await state.update_data({'descr': description})
    user_dict = await state.get_data()

    await message.answer(
        f'Проверим операцию:\n'
        f'Дата - *{user_dict["date"]}*\n'
        f'Сумма - *{user_dict["summ"]}*\n'
        f'Категория - *{user_dict["category"]}*\n'
        f'Описание - *{description}*\n',
        parse_mode='Markdown',
        reply_markup=save_category_kb()
    )
    await state.set_state(UserState.save_transaction)


@router.message(UserState.save_transaction, F.text.contains('Записать'))
async def add_new_category_settings(message: Message, state: FSMContext):
    logger.info(f'Пользователь {message.chat.id}. Запись транзакции в БД')

    user_dict = await state.get_data()

    summ = user_dict['summ'] if user_dict['group'] == 'Income' else -user_dict['summ']

    transaction_dict = {
        'id': message.chat.id,
        'date': user_dict['date'],
        'summ': summ,
        'category': user_dict['category'],
        'descr': user_dict['descr'],
    }

    db_create_transaction(transaction_dict)

    await message.answer(
        f'Сохранил. Добавить еще одну?',
        parse_mode='Markdown',
        reply_markup=transaction_end_kb()
    )
    await state.set_state(UserState.default)


