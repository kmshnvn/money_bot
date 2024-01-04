from loguru import logger
from aiogram.filters import Text, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram import F

from handlers.default_heandlers.start import router


from database.database import db_create_category, db_get_category, db_change_category
from database.states import UserState
from keyboards.inline_keyboards import (
    user_category_kb,
    save_category_kb,
    exist_category_kb,
    group_category_kb,
)

from keyboards.reply_keyboards import (
    default_category_kb,
    main_kb,
)


@router.message(F.text.contains("Настройки"))
@router.message(Command("settings"))
@router.message(
    UserState.transaction_new_category, F.text.contains("Настройки категорий")
)
async def category_settings(message: Message, state: FSMContext):
    """
    Обработка команды /Setting для настройки категорий трат пользователя.
    """
    try:
        logger.info("Начало /Setting")
        await state.set_state(UserState.settings)

        user_category = db_get_category(
            tg_id=message.chat.id, user_name=message.from_user.full_name
        )

        if not user_category:
            logger.info("Категорий нет")

            await message.answer(
                text="Для быстрой настройки у меня есть стандартные категории трат, "
                "чтобы использовать их просто нажми на кнопку 'Использовать стандартный набор'"
                "\n\n*Стандартный набор расходов:*"
                "\nТранспорт🚌"
                "\nПродукты🥦"
                "\nКафе🍕"
                "\nДом🏡"
                "\nПутешествия✈️"
                "\nОдежда👕"
                "\nКрасота💆‍"
                "\n\n*Категории дохода:*"
                "\nЗарплата💰",
                reply_markup=default_category_kb(),
            )
        else:
            logger.info("Категорий есть")
            await state.set_data(user_category)

            text = ""

            for key, value in user_category.items():
                if key == "Expense":
                    text += "*Категории расходов:*\n"
                    for elem in value:
                        text += f"{elem}\n"
                else:
                    text += "\n*Категории доходов:*\n"
                    for elem in value:
                        text += f"{elem}\n"

            await message.answer(
                text=f"Настройки категорий.\n"
                f"Сейчас у тебя установлены следующие категории:\n\n"
                f"{text}"
                f"\nЧто делаем?",
                reply_markup=exist_category_kb(),
            )
    except Exception as ex:
        logger.error(f"Что-то пошло не так при настройке категорий: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при настройке категорий. Скоро меня починят"
        )


@router.message(
    UserState.settings, F.text.contains("Использовать стандартные категории")
)
async def default_category_settings(message: Message, state: FSMContext):
    """
    Обработка выбора использования стандартных категорий трат.
    """
    try:
        logger.info("Настройки по стандартным категориям")

        default_category = {
            "Expense": [
                "Транспорт🚌",
                "Продукты🥦",
                "Кафе🍕",
                "Дом🏡",
                "Путешествия✈️",
                "Одежда👕",
                "Красота💆‍",
            ],
            "Income": ["Зарплата💰"],
        }

        db_create_category(message.chat.id, default_category)
        await message.answer(
            text="Отлично, мы настроили категории. "
            "В дальнейшем их можно будет редактировать в /settings\n"
            "Сейчас создадим свою первую операцию\n"
            "Для этого нажми на кнопку '🧮Новая операция'",
            reply_markup=main_kb(),
        )
        await state.set_state(UserState.default)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при настройке стандартных категорий: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при настройке категорий. Скоро меня починят"
        )


@router.callback_query(UserState.settings, Text("add_new_category"))
@router.callback_query(UserState.save_category, Text("change_transaction"))
async def custom_category_settings(callback: CallbackQuery, state: FSMContext):
    """
    Обработка начала настройки своих категорий трат. Пользователь выбирает группу категории.
    """
    try:
        logger.info("Начинаем настройку своих категорий. Выбираем группы категории")

        await state.set_state(UserState.custom_category_group)
        await callback.message.edit_text(
            "К чему относится категория?",
            reply_markup=group_category_kb(),
        )
    except Exception as ex:
        logger.error(f"Что-то пошло не так при начале настройки своих категорий: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при начале настройки категорий. Скоро меня починят"
        )


@router.callback_query(
    UserState.custom_category_group, Text(text=["income", "expense"])
)
async def add_new_category_settings(callback: CallbackQuery, state: FSMContext):
    """
    Обработка выбора группы категории и ожидание ввода названия новой категории.
    """
    try:
        logger.info("Ловим группу и ждем названия категории")

        if callback.data == "income":
            await state.update_data({"group": "Income"})
        else:
            await state.update_data({"group": "Expense"})

        await callback.message.edit_text(
            "Введите название категории",
        )

        await state.set_state(UserState.custom_category)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при выборе группы категории: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при выборе группы категории. Скоро меня починят"
        )


@router.callback_query(UserState.custom_category_group, Text("ready"))
async def category_settings_complete(callback: CallbackQuery, state: FSMContext):
    """
    Завершение настройки категорий и переход к созданию операции.
    """
    try:
        logger.info("Категории настроены.")

        await state.set_state(UserState.default)

        await callback.message.edit_text(
            "Отлично, категории настроены",
        )
        await category_settings(callback.message, state)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при завершении настройки категорий: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при завершении настройки категорий. Скоро меня починят"
        )


@router.message(UserState.custom_category)
async def add_new_category_settings(message: Message, state: FSMContext):
    """
    Обработчик добавления новой пользовательской категории.
    """
    try:
        logger.info("Уточняем сохранение категории + запись во временное хранилище")

        if len(message.text) > 20:
            await message.answer("Название категории не может превышать 20 символов")
        else:
            data = await state.get_data()
            group = data["group"]
            another_group = "Income" if group == "Expense" else "Expense"

            category = message.text

            if category.title() in data[group]:
                await message.answer(
                    "Категория уже есть\n" f"Нужно ввести другую",
                )
            elif category.title() in data[another_group]:
                text_another_name = (
                    "дохода" if another_group == "Income" else "расходных операций"
                )

                await message.answer(
                    f"Категория уже есть в категориях {text_another_name}\n"
                    f"Добавьте смайлик ➕,➖, (Д), (Р) или любое другое обозначение, "
                    f"чтобы можно было легко отличить их",
                )
            else:
                await state.update_data({"new_category": {group: category}})
                group_name = "Доход" if group == "Income" else "Расход"

                await message.answer(
                    f"Проверим:\n"
                    f"Категория - *{group_name}*\n"
                    f"Название - *{message.text}*\n",
                    reply_markup=save_category_kb(),
                )
                await state.set_state(UserState.save_category)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при добавлении новой категории: {ex}")
        await message.edit_text(
            "🤕 Возникла ошибка при добавлении новой категории. Скоро меня починят"
        )


@router.callback_query(UserState.save_category, Text("add_transaction"))
async def add_new_category_settings(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик сохранения новой пользовательской категории в базе данных.
    """
    try:
        logger.info("Запись категории в БД")

        category_dict = await state.get_data()

        if category_dict.get("new_category"):
            new_category = category_dict["new_category"]
            group = category_dict["group"]

            new_category_list = category_dict[group]
            new_category_list.append(new_category[group].title())

            db_create_category(callback.message.chat.id, new_category)
            await state.update_data({group: new_category_list})
        else:
            db_create_category(callback.message.chat.id, category_dict)

        await callback.message.edit_text(
            f"✅Сохранил",
        )
        await callback.message.answer(
            "Теперь следующая. \nК чему относится категория?",
            reply_markup=group_category_kb(),
        )
        await state.set_state(UserState.custom_category_group)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при сохранении новой категории: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при сохранении новой категории. Скоро меня починят"
        )


@router.callback_query(
    UserState.settings, Text(["delete_category", "change_category_name"])
)
async def default_category_settings(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для редактирования категорий пользователя.
    """
    try:
        logger.info("Зашли в редактор категории")

        user_dict = await state.get_data()
        category_list = []

        for key, value in user_dict.items():
            if key in ("Expense", "Income"):
                category_list.extend(value)

        await state.update_data({"all_categories": category_list})

        await callback.message.edit_text(
            text="Выберите категорию для редактирования",
            reply_markup=user_category_kb(category_list),
        )
        if callback.data == "delete_category":
            await state.set_state(UserState.delete_category)
        else:
            await state.set_state(UserState.rename_category)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при редактировании категорий: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при редактировании категорий. Скоро меня починят"
        )


@router.callback_query(
    UserState.rename_category, Text(startswith="transaction_category:")
)
async def default_category_settings(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для редактирования категорий пользователя.
    """
    try:
        logger.info("Изменяем категорию")

        category = callback.data.split(":")[1]
        await callback.message.edit_text(
            text="Напиши новое название для категории. Смайлики приветствуются🤩",
        )

        await state.update_data({"last_name": category})
        await state.set_state(UserState.edit_category)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при редактировании категорий: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при редактировании категорий. Скоро меня починят"
        )


@router.message(UserState.edit_category)
async def default_category_settings(message: Message, state: FSMContext):
    """
    Обработчик для изменения названия категории пользователя.
    """
    try:
        logger.info("Изменяем название категории")

        user_dict = await state.get_data()

        db_change_category(
            tg_id=message.chat.id,
            category_name=user_dict["last_name"],
            new_name=message.text,
        )

        await message.answer(
            text=f'Категорию обновил с *{user_dict["last_name"]}* на *{message.text}*',
        )

        await category_settings(message, state)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при изменении названия категории: {ex}")
        await message.edit_text(
            "🤕 Возникла ошибка при изменении названия категории. Скоро меня починят"
        )


@router.callback_query(
    UserState.delete_category, Text(startswith="transaction_category:")
)
async def delete_category(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для удаления категории пользователя.
    """
    try:
        logger.info("Удаляем категорию")
        category = callback.data.split(":")[1]
        db_change_category(
            tg_id=callback.message.chat.id,
            category_name=category,
        )

        await callback.message.edit_text(
            text=f"Категория *{category}* удалена",
        )

        await category_settings(callback.message, state)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при удалении категории: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при удалении категории. Скоро меня починят"
        )
