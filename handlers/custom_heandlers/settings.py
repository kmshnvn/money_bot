from loguru import logger
from aiogram.filters import Text, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import F

from handlers.default_heandlers.start import router


from database.database import db_create_category, db_get_category, db_change_category, start_table
from database.states import UserState
from keyboards.reply_keyboards import (
    default_category_kb,
    add_transaction_kb,
    exist_category_kb,
    group_category_kb,
    save_category_kb,
    user_category_kb,
)


@router.message(F.text.contains('Настройки'))
@router.message(Command('settings'))
@router.message(UserState.transaction_new_category, F.text.contains('Настройки категорий'))
async def category_settings(message: Message, state: FSMContext):
    logger.info('Начало /Setting')
    await state.set_state(UserState.settings)
    user_category = db_get_category(tg_id=message.chat.id, user_name=message.from_user.full_name)

    if not user_category:
        logger.info('Категорий нет')

        await message.answer(
            text=f"Для быстрой настройки у меня есть стандартные категории трат, "
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
    else:
        logger.info('Категорий есть')
        await state.set_data(user_category)

        text = ''

        for key, value in user_category.items():
            if key == 'Expense':
                text += '*Категории расходов:*\n'
                for elem in value:
                    text += f'{elem}\n'
            else:
                text += '\n*Категории доходов:*\n'
                for elem in value:
                    text += f'{elem}\n'

        await message.answer(
            text=f"Настройки категорий.\n"
                 f"Сейчас у тебя установлены следующие категории трат\n\n"
                 f"{text}"
                 f"\nЧто делаем?",
            parse_mode='Markdown',
            reply_markup=exist_category_kb(),
        )
    print(await state.get_data())

@router.message(UserState.settings, F.text.contains('Использовать стандартные категории'))
async def default_category_settings(message: Message, state: FSMContext):
    logger.info('Настройки по стандартным категориям')

    default_category = {
        'Expense': ['Транспорт', 'Продукты', 'Кафе', 'Дом', 'Путешествия', 'Одежда'],
        'Income': ['Зарплата']
    }
    db_create_category(message.chat.id, default_category)

    await message.answer(
        text=f'Отлично, мы настроили категории. '
             f'В дальнейшем их можно будет редактировать в /settings\n'
             f'Сейчас создадим свою первую операцию',
        parse_mode='Markdown',
        reply_markup=add_transaction_kb()
    )
    await state.set_state(UserState.default)
    print(await state.get_data())



@router.message(
    UserState.settings,
    F.text.contains("Свои категории") | F.text.contains("Добавить новую")
)
@router.message(UserState.save_category, Text('Изменить'))
async def custom_category_settings(message: Message, state: FSMContext):
    logger.info('Начинаем настройку своих категорий. Выбираем группы категории')

    await state.set_state(UserState.custom_category_group)
    await message.answer(
        f'К чему относится категория?',
        reply_markup=group_category_kb(),
    )
    print(await state.get_data())



@router.message(UserState.custom_category_group, F.text.contains("Доход") | F.text.contains("Расход"))
async def add_new_category_settings(message: Message, state: FSMContext):
    logger.info('Ловим группу и ждем названия категории')

    if message.text == "Доход":
        await state.update_data({'group': 'Income'})
    else:
        await state.update_data({'group': 'Expense'})

    await message.answer(
        f'Введите название категории',
        reply_markup=ReplyKeyboardRemove(),
    )

    await state.set_state(UserState.custom_category)
    print(await state.get_data())



@router.message(UserState.custom_category, F.text.contains('Готово'))
@router.message(UserState.custom_category_group, Text('Готово'))
async def add_new_category_settings(message: Message, state: FSMContext):
    logger.info('Категории настроены. Выход')

    await state.set_state(UserState.default)

    await message.answer(
        f'Отлично, мы настроили категории. '
        f'В дальнейшем их можно будет редактировать в /settings\n'
        f'Сейчас создадим свою первую операцию',
        parse_mode='Markdown',
        reply_markup=add_transaction_kb()
    )
    print(await state.get_data())


@router.message(UserState.custom_category)
async def add_new_category_settings(message: Message, state: FSMContext):
    logger.info('Уточняем сохранение категории + запись во временное хранилище')


    if len(message.text) > 20:
        await message.answer(f'Название категории не может превышать 20 символов')
    else:
        data = await state.get_data()
        group = data['group']
        category = message.text

        if category.title() in data[group]:
            await message.answer(
                f'Категория уже есть\n'
                f'Нужно ввести другую',
                parse_mode='Markdown',
            )

        else:
            await state.update_data({'new_category': {group: category}})

            group_name = 'Расход'
            if group == 'Income':
                group_name = 'Доход'

            await message.answer(
                f'Проверим:\n'
                f'Категория - *{group_name}*\n'
                f'Название - *{message.text}*\n',
                parse_mode='Markdown',
                reply_markup=save_category_kb()
            )
            await state.set_state(UserState.save_category)
    print(await state.get_data())


@router.message(UserState.save_category, F.text.contains('Записать'))
async def add_new_category_settings(message: Message, state: FSMContext):
    logger.info('Запись категории в БД')

    category_dict = await state.get_data()

    if category_dict.get('new_category'):
        new_category = category_dict['new_category']
        group = category_dict['group']

        new_category_list = category_dict[group]
        new_category_list.append(new_category[group].title())

        db_create_category(message.chat.id, new_category)
        await state.update_data({group: new_category_list})
    else:
        db_create_category(message.chat.id, category_dict)

    await message.answer(
        f'Сохранил. Теперь следующая. \nК чему относится категория?',
        parse_mode='Markdown',
        reply_markup=group_category_kb()
    )
    await state.set_state(UserState.custom_category_group)
    print(await state.get_data())


@router.message(
    UserState.settings,
    F.text.contains('Удалить категорию') | F.text.contains('Изменить категорию')
)
async def default_category_settings(message: Message, state: FSMContext):
    logger.info('Зашли в редактор категории')

    user_dict = await state.get_data()
    category_list = []
    for key, value in user_dict.items():
        if key == 'Expense' or 'Income':
            for elem in value:
                category_list.append(elem)
    await state.update_data({'all_categories': category_list})

    await message.answer(
        text=f'Выберите категорию для редактирования',
        parse_mode='Markdown',
        reply_markup=user_category_kb(category_list)
    )
    if message.text == 'Удалить категорию':
        await state.set_state(UserState.delete_category)
    else:
        await state.set_state(UserState.rename_category)

    print(await state.get_data())


@router.message(UserState.rename_category)
async def default_category_settings(message: Message, state: FSMContext):
    logger.info('Изменяем категорию')

    user_dict = await state.get_data()
    categories = user_dict['all_categories']
    if message.text not in user_dict['all_categories']:
        await message.answer(
            text=f'Такой категории нет, выбери категорию из списка',
            parse_mode='Markdown',
            reply_markup=user_category_kb(categories)
        )
    else:
        await message.answer(
            text=f'Напиши новое название для категории. Смайлики приветствуются🤩',
            parse_mode='Markdown',
            reply_markup=user_category_kb(categories)
        )

        await state.update_data({'last_name': message.text})
        await state.set_state(UserState.edit_category)


@router.message(UserState.edit_category)
async def default_category_settings(message: Message, state: FSMContext):
    logger.info('Изменяем название категорию')

    user_dict = await state.get_data()

    db_change_category(
        tg_id=message.chat.id,
        category_name=user_dict['last_name'],
        new_name=message.text
    )

    await message.answer(
        text=f'Категорию обновил с {user_dict["last_name"]} на {message.text}',
        parse_mode='Markdown',
    )

    await category_settings(message, state)



@router.message(UserState.delete_category)
async def default_category_settings(message: Message, state: FSMContext):
    logger.info('Удаляем категорию')

    db_change_category(
        tg_id=message.chat.id,
        category_name=message.text,
    )

    await message.answer(
        text=f'Категория *{message.text}* удалена',
        parse_mode='Markdown',
    )

    await category_settings(message, state)
