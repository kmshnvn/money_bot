from datetime import date, timedelta
import re

from fuzzywuzzy import fuzz
from loguru import logger

from aiogram.filters import Command, Text
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.types import CallbackQuery

from database.database import (
    db_get_category,
    db_create_transaction,
    db_create_category,
    db_get_balance,
    db_get_transaction,
    db_update_transaction,
)

from database.states import UserState
from handlers.default_heandlers.start import router
from functions import simple_cal_callback, SimpleCalendar
from keyboards.inline_keyboards import (
    transaction_main_kb,
    user_category_kb,
    transaction_descr_kb,
    transaction_save_kb,
    save_category_kb,
    change_transaction_details_kb,
    change_success_transaction,
    change_success_transaction_details_kb,
    update_category_kb,
)
from keyboards.reply_keyboards import default_category_kb


async def check_regexp_summ(text: str) -> str:
    pattern = r"\d+(,\d{1,2})?"
    match = re.findall(pattern, text)[0]
    if match:
        corrected_number = match.replace(",", ".")
        text = text.replace(match, corrected_number)
        return text
    else:
        return text


async def calculate_sum(text: str):
    num_list = text.split("+")
    summ = 0
    for elem in num_list:
        num = await check_regexp_summ(elem)
        summ += float(num)
    return str(summ)


async def check_change_transaction(user_data: dict):
    user_dict = user_data["old_transaction_info"]
    description = (
        user_data["change_descr"]
        if user_data["change_descr"] != ""
        else user_dict["old_descr"]
    )
    text_descr = "(Без описания)" if description == "" else description

    category = (
        user_data["change_category"]
        if user_data["change_category"] != ""
        else user_dict["old_category"]
    )
    user_date = (
        user_data["change_date"]
        if user_data["change_date"] != ""
        else user_dict["old_date"]
    )

    if user_dict["old_group"] == "Expense":
        if user_data["change_summ"] == "":
            amount = user_dict["old_summ"]
            summ = -user_dict["old_summ"]
        else:
            amount = -user_data["change_summ"]
            summ = user_data["change_summ"]
    else:
        amount, summ = user_data["change_summ"]

    transaction_dict = {
        "id": user_data["id"],
        "date": user_date,
        "summ": summ,
        "category": category,
        "descr": description,
        "amount": amount,
        "text_descr": text_descr,
    }

    return transaction_dict


@router.message(F.text.contains("Новая операция"))
@router.message(Command("transaction"))
@router.message(UserState.save_transaction, F.text.contains("Изменить"))
async def new_transaction(message: Message, state: FSMContext):
    """
    Обработчик для начала записи новой операции пользователя.
    """
    try:
        logger.debug("Начинаем запись операции пользователя и спрашиваем дату")

        user_category = db_get_category(
            tg_id=message.chat.id, user_name=message.from_user.full_name
        )

        if not user_category:
            logger.info("Категорий нет")

            await message.answer(
                text=f"*Категории еще не установлены, сначала нужно их настроить.*\n\n"
                f"Для быстрой настройки у меня есть стандартные категории трат, "
                f"чтобы использовать их просто нажми на кнопку 'Использовать стандартный набор'"
                f"\n\n*Стандартный набор расходов:*"
                f"\nТранспорт🚌"
                f"\nПродукты🥦"
                f"\nКафе🍕"
                f"\nДом🏡"
                f"\nПутешествия✈️"
                f"\nОдежда👕"
                f"\nКрасота💆‍"
                f"\n\n*Категории дохода:*"
                f"\nЗарплата💰",
                reply_markup=default_category_kb(),
            )
            await state.set_state(UserState.settings)

        else:
            balance = db_get_balance(message.chat.id)
            default_group = "Expense"

            await state.set_data(
                {
                    "date": date.today().strftime("%d.%m.%Y"),
                    "group": default_group,
                    "summ": "",
                    "category": "",
                    "descr": "",
                    "balance": float(balance),
                }
            )
            await state.update_data(user_category)

            text = ""

            await message.answer(
                text=(
                    text + f"Записываю *расходную операцию.*\n"
                    f"Дата - Сегодня\n\n"
                    f"Сколько денег потратили?"
                ),
                reply_markup=transaction_main_kb(default_group),
            )
            await state.set_state(UserState.transaction_summ)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при начале записи новой операции: {ex}")
        await message.edit_text(
            "🤕 Возникла ошибка в начале записи операции. Скоро меня починят"
        )


@router.callback_query(
    UserState.transaction_summ,
    Text(
        text=["income", "expense", "change_for_today_date", "change_for_yesterday_date"]
    ),
)
@router.callback_query(UserState.transaction_category, Text("back"))
async def transaction_summ(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик для уточнения суммы операции.
    """
    try:
        logger.debug(
            f"Пользователь {callback.message.chat.id}. Уточняем сумму операции"
        )
        await state.set_state(UserState.transaction_summ)

        not_today = True
        if callback.data == "change_for_today_date":
            await state.update_data({"date": date.today().strftime("%d.%m.%Y")})
        elif callback.data == "change_for_yesterday_date":
            yesterday = date.today() - timedelta(days=1)
            await state.update_data({"date": yesterday.strftime("%d.%m.%Y")})

        group_name = callback.data.title()

        user_dict = await state.get_data()

        user_date = user_dict.get("date")
        balance = user_dict.get("balance")
        if group_name not in ["Income", "Expense"]:
            group_name = user_dict.get("group")
        else:
            await state.update_data({"group": group_name})

        if user_date == date.today().strftime("%d.%m.%Y"):
            user_date = "Сегодня"
            not_today = False

        text = ""
        if group_name == "Expense":
            await callback.message.edit_text(
                text=(
                    text + f"Записываю расходную операцию.\n"
                    f"Дата - *{user_date}*\n\n"
                    f"Сколько денег потратили?"
                ),
                reply_markup=transaction_main_kb(group_name, not_today),
            )
        else:
            await callback.message.edit_text(
                text=(
                    text + f"Записываю пополнение.\n"
                    f"Дата - *{user_date}*\n\n"
                    f"Сколько денег получили?"
                ),
                reply_markup=transaction_main_kb(group_name, not_today),
            )

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении суммы операции: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при уточнении суммы операции. Скоро меня починят"
        )


@router.callback_query(UserState.transaction_summ, Text("change_transaction_date"))
@router.callback_query(
    UserState.change_transaction_details, Text("change_transaction_date")
)
@router.callback_query(
    UserState.change_success_transaction_details, Text("change_transaction_date")
)
async def transaction_user_date(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды выбора даты для статистики.
    """
    try:
        await callback.message.edit_text(
            text="Выберите дату начала",
            reply_markup=await SimpleCalendar().start_calendar(),
        )
        await state.update_data({"user_state": await state.get_state()})
    except Exception as ex:
        logger.error(f"Что-то пошло не так при выборе даты для статистики: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при выборе даты. Скоро меня починят"
        )


@router.callback_query(UserState.transaction_summ, simple_cal_callback.filter())
@router.callback_query(
    UserState.change_transaction_details, simple_cal_callback.filter()
)
@router.callback_query(
    UserState.change_success_transaction_details, simple_cal_callback.filter()
)
async def process_simple_calendar(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    """
    Обработчик для выбора даты с помощью календаря.
    """
    try:
        selected, date = await SimpleCalendar().process_selection(
            callback_query, callback_data
        )

        if selected:
            user_state = await state.get_state()

            if user_state == "UserState:change_success_transaction_details":
                await state.update_data({"change_date": date.strftime("%d.%m.%Y")})
                await callback_change_success_transaction_check(callback_query, state)
            else:
                await state.update_data({"date": date.strftime("%d.%m.%Y")})

                if user_state == "UserState:transaction_summ":
                    await transaction_summ(callback_query, state)
                elif user_state == "UserState:change_transaction_details":
                    await callback_transaction_check(callback_query, state)
                else:
                    await callback_query.message.edit_text(
                        f"Что-то пошло не так при выборе даты, скоро все исправим😵‍💫",
                    )

    except Exception as ex:
        logger.error(f"Что-то пошло не так при обработке календаря: {ex}")
        await callback_query.message.edit_text(
            "🤕 Возникла ошибка при выборе даты. Скоро меня починят"
        )


@router.message(
    UserState.transaction_summ,
    F.text.regexp(r"\d+(?:[,.]\d{1,2})?(?:\s*[-+]\s*\d+(?:[,.]\d{1,2})?)*"),
)
async def transaction_category(message: Message, state: FSMContext):
    """
    Функция. Проверяем вводимое число пользователя и уточняем категорию операции
    """
    try:
        logger.debug(
            f"Пользователь {message.chat.id} - Сумма {message.text}. "
            f"Уточняем категорию операции"
        )
        pattern = "\d+(?:[,.]\d{1,2})?(?:\s*[-+]\s*\d+(?:[,.]\d{1,2})?)*"
        match = re.search(pattern, message.text)

        if match:
            user_text = await calculate_sum(message.text)
        else:
            user_text = await check_regexp_summ(message.text)
        await state.update_data({"summ": float(user_text)})
        user_state = await state.get_state()

        user_dict = await state.get_data()

        group_name = "Expense" if user_dict["group"] == "Expense" else "Income"

        user_category = user_dict.get(group_name)

        if user_category is not None:
            await message.answer(
                f"Сумма - {user_text}\n\n"
                f"В какой категории была операция?\n"
                f"\nЕсли операции нет и нужно добавить - "
                f"просто введи новую категорию",
                reply_markup=user_category_kb(sorted(user_category), group_name),
            )

        else:
            await message.answer(
                f"Категорий еще нет. Введите новую",
            )
        await state.set_state(UserState.transaction_category)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке: {ex}")
        await message.answer(
            f"🔰Ожидаю сумму операции. Нужно ввести число в формате:\n\n"
            f"🔸100\n"
            f"🔸100.0\n"
            f"🔸100,0\n"
            f"🔸100.00\n"
            f"🔸100,00\n\n"
            f"Также можно ввести сумму для калькулятора в формате:\n"
            f"🔹100+100,0+..",
        )


@router.callback_query(UserState.transaction_new_category, Text("back"))
@router.callback_query(
    UserState.change_transaction_details, Text("change_transaction_category")
)
@router.callback_query(
    UserState.change_success_transaction_details, Text("change_transaction_category")
)
@router.callback_query(UserState.transaction_category, Text(text=["income", "expense"]))
async def transaction_category_back(callback: CallbackQuery, state: FSMContext):
    """
    Функция. Проверяем вводимое число пользователя и уточняем категорию операции.
    Сюда можно попасть только в том случае, если пользователь ввел новую категорию и нажал "Назад".
    Либо при изменении операции перед записью, либо смена Доход/расход во время выбора категории
    """
    try:
        logger.debug(
            f"Пользователь {callback.message.chat.id} - Сумма {callback.message.text}. "
            f"Уточняем категорию операции"
        )

        if callback.data in ["income", "expense"]:
            await state.update_data({"group": callback.data.title()})

        user_dict = await state.get_data()
        user_state = await state.get_state()
        await state.update_data({"user_state": user_state})

        if user_state == "UserState:change_success_transaction_details":
            group_name = user_dict["old_transaction_info"]["old_group"]
            user_category = user_dict.get(group_name)

            if user_category is not None:
                await callback.message.edit_text(
                    f"В какой категории была операция?\n"
                    f"\nЕсли операции нет и нужно добавить - "
                    f"просто введи новую категорию",
                    reply_markup=user_category_kb(sorted(user_category)),
                )

            else:
                await callback.message.edit_text(
                    f"Категорий еще нет. Введите новую",
                )
            await state.set_state(UserState.change_transaction_category)

        else:
            group_name = "Expense" if user_dict["group"] == "Expense" else "Income"
            user_category = user_dict.get(group_name)

            if user_category is not None:
                await callback.message.edit_text(
                    f"В какой категории была операция?\n"
                    f"\nЕсли операции нет и нужно добавить - "
                    f"просто введи новую категорию",
                    reply_markup=user_category_kb(sorted(user_category), group_name),
                )
            else:
                await callback.message.edit_text(
                    f"Категорий еще нет. Введите новую",
                )
            await state.set_state(UserState.transaction_category)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении категории операции: {ex}")
        await callback.message.answer(
            "🤕 Возникла ошибка при уточнении категории операции. Скоро меня починят"
        )


@router.message(UserState.transaction_category)
@router.message(UserState.change_transaction_category)
async def transaction_description(message: Message, state: FSMContext):
    """
    Функция. Уточненяем описание операции.
    """
    try:
        logger.debug(f"Пользователь {message.chat.id}. Уточняем описание операции")
        category = message.text.title()
        user_dict = await state.get_data()

        group_name = "Expense" if user_dict["group"] == "Expense" else "Income"

        matching_category = None
        if user_dict.get(group_name) is not None:
            matching_category = next(
                (
                    elem
                    for elem in user_dict[group_name]
                    if fuzz.ratio(category, elem) > 80
                ),
                None,
            )

        if matching_category is None:
            await state.update_data({"category": category})

            await message.answer(
                f"К сожалению, такой категории не было в вашем списке.\n"
                f"\nГруппа категории: {group_name}\n"
                f"Категория: {category}\n"
                f"\nДобавим категорию",
                reply_markup=transaction_save_kb(),
            )
            await state.set_state(UserState.transaction_new_category)
        elif (
            user_dict.get("user_state")
            == "UserState:change_success_transaction_details"
        ):
            await state.update_data({"change_category": matching_category})
            await change_success_transaction_check(message, state)
        else:
            await state.update_data({"category": matching_category})
            if user_dict.get("user_state") == "UserState:change_transaction_details":
                await transaction_check_without_descr(message, state)
            else:
                await message.answer(
                    f"Такая категория уже есть в вашем списке\n"
                    f"Добавьте описание операции (необязательно)",
                    reply_markup=transaction_descr_kb(),
                )

                await state.set_state(UserState.transaction_description)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении описания операции: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при уточнении описания операции. Скоро меня починят"
        )


@router.callback_query(
    UserState.transaction_category, Text(startswith="transaction_category:")
)
@router.callback_query(
    UserState.change_transaction_category, Text(startswith="transaction_category:")
)
async def transaction_callback_description(callback: CallbackQuery, state: FSMContext):
    """
    Функция. Уточненяем описание операции.
    """
    try:
        logger.debug(
            f"Пользователь {callback.message.chat.id}. Уточняем описание операции"
        )
        category = callback.data.split(":")[1]
        user_dict = await state.get_data()

        if (
            user_dict.get("user_state")
            == "UserState:change_success_transaction_details"
        ):
            await state.update_data({"change_category": category})
            await callback_change_success_transaction_check(callback, state)
        elif user_dict.get("user_state") == "UserState:change_transaction_details":
            await state.update_data({"category": category})
            await callback_transaction_check(callback, state)
        else:
            await state.update_data({"category": category})
            await callback.message.edit_text(
                f"Добавьте описание операции (необязательно)",
                reply_markup=transaction_descr_kb(),
            )

            await state.set_state(UserState.transaction_description)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении описания операции: {ex}")
        await callback.message.answer(
            "🤕 Возникла ошибка при уточнении описания операции. Скоро меня починят"
        )


@router.callback_query(UserState.transaction_new_category, Text("add_category"))
async def transaction_new_category(callback: CallbackQuery, state: FSMContext):
    """
    Запись новой категории операции и переход к уточнению описания.
    """
    try:
        logger.debug(f"Пользователь {callback.message.chat.id}. Запись новой категории")

        user_dict = await state.get_data()
        print(user_dict)

        group_name = "Expense" if user_dict["group"] == "Expense" else "Income"
        new_category = {group_name: user_dict["category"]}

        category_list = user_dict.get(group_name)
        if category_list is not None:
            category_list.append(new_category[group_name])
        else:
            category_list = [new_category[group_name]]

        await state.update_data({group_name: category_list})

        db_create_category(callback.message.chat.id, new_category)
        if user_dict.get("user_state") == "UserState:change_transaction_details":
            await transaction_check_without_descr(callback.message, state)
        else:
            await callback.message.edit_text(
                f'Записал новую категорию {user_dict["category"]}\n\n'
                f"Добавьте описание операции (необязательно)",
                reply_markup=transaction_descr_kb(),
            )

            await state.set_state(UserState.transaction_description)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при записи новой категории: {ex}")
        await callback.message.answer(
            "🤕 Возникла ошибка при записи новой категории. Скоро меня починят"
        )


@router.callback_query(UserState.transaction_description)
@router.callback_query(UserState.change_transaction_details, Text("back"))
async def callback_transaction_check(callback: CallbackQuery, state: FSMContext):
    """
    Проверка операции перед сохранением.
    """
    try:
        logger.debug(f"Пользователь {callback.message.chat.id}. Проверка операции")
        user_dict = await state.get_data()
        description = user_dict.get("descr")
        text_descr = "(Без описания)" if description == "" else description

        await callback.message.edit_text(
            f"Проверим операцию:\n"
            f'Дата - *{user_dict["date"]}*\n'
            f'Сумма - *{user_dict["summ"]}*\n'
            f'Категория - *{user_dict["category"]}*\n'
            f"Описание - {text_descr}\n",
            reply_markup=save_category_kb(),
        )
        await state.set_state(UserState.save_transaction)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        await callback.message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )


async def change_success_transaction_check(message: Message, state: FSMContext):
    """
    Проверка уже сохраненной операции перед обновлением информации в БД.
    """
    try:
        logger.debug(
            f"Пользователь {message.chat.id}. Проверка операции перед обновлением информации в БД"
        )

        user_data = await state.get_data()

        transaction_dict = await check_change_transaction(user_data)

        await state.update_data({"transaction_dict": transaction_dict})

        await message.answer(
            f"Сейчас операция будет выглядеть так:\n"
            f'Дата - *{transaction_dict["date"]}*\n'
            f'Сумма - *{transaction_dict["summ"]}*\n'
            f'Категория - *{transaction_dict["category"]}*\n'
            f'Описание - {transaction_dict["descr"]}\n',
            reply_markup=update_category_kb(),
        )
        await state.set_state(UserState.update_transaction)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )


@router.callback_query(UserState.change_success_transaction_details, Text("back"))
async def callback_change_success_transaction_check(
    callback: CallbackQuery, state: FSMContext
):
    """
    Проверка уже сохраненной операции перед обновлением информации в БД.
    """
    try:
        logger.debug(
            f"Пользователь {callback.message.chat.id}. Проверка операции перед обновлением информации в БД"
        )

        user_data = await state.get_data()

        transaction_dict = await check_change_transaction(user_data)

        await state.update_data({"transaction_dict": transaction_dict})

        await callback.message.edit_text(
            f"Сейчас операция будет выглядеть так:\n"
            f'Дата - *{transaction_dict["date"]}*\n'
            f'Сумма - *{transaction_dict["summ"]}*\n'
            f'Категория - *{transaction_dict["category"]}*\n'
            f'Описание - {transaction_dict["descr"]}\n',
            reply_markup=update_category_kb(),
        )
        await state.set_state(UserState.update_transaction)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        await callback.message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )


async def transaction_check_without_descr(message: Message, state: FSMContext):
    """
    Проверка операции перед сохранением.
    """
    try:
        logger.debug(f"Пользователь {message.chat.id}. Проверка операции")

        user_dict = await state.get_data()
        description = user_dict.get("descr")
        text_descr = "(Без описания)" if description == "" else description

        await message.answer(
            f"Проверим операцию:\n"
            f'Дата - *{user_dict["date"]}*\n'
            f'Сумма - *{user_dict["summ"]}*\n'
            f'Категория - *{user_dict["category"]}*\n'
            f"Описание - {text_descr}\n",
            reply_markup=save_category_kb(),
        )
        await state.set_state(UserState.save_transaction)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )


@router.message(UserState.transaction_description)
@router.message(UserState.change_transaction_details_descr)
@router.message(UserState.change_success_transaction_details_descr)
async def transaction_check(message: Message, state: FSMContext):
    """
    Проверка операции перед сохранением.
    """
    try:
        logger.debug(f"Пользователь {message.chat.id}. Проверка операции")

        description = message.text
        user_state = await state.get_state()

        if user_state == "UserState:change_success_transaction_details_descr":
            await state.update_data({"change_descr": description})
            await change_success_transaction_check(message, state)
        else:
            await state.update_data({"descr": description})
            user_dict = await state.get_data()

            await message.answer(
                f"Проверим операцию:\n"
                f'Дата - *{user_dict["date"]}*\n'
                f'Сумма - *{user_dict["summ"]}*\n'
                f'Категория - *{user_dict["category"]}*\n'
                f"Описание - *{description}*\n",
                reply_markup=save_category_kb(),
            )
            await state.set_state(UserState.save_transaction)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )


@router.callback_query(UserState.update_transaction, Text("update_transaction"))
async def add_new_category_settings(callback: CallbackQuery, state: FSMContext):
    """
    Функция обновления транзакции в БД.
    """
    try:
        logger.debug(
            f"Пользователь {callback.message.chat.id}. Обновление транзакции в БД"
        )

        user_dict = await state.get_data()

        transaction_dict = user_dict["transaction_dict"]

        if db_update_transaction(transaction_dict, callback.message.chat.id):
            balance = db_get_balance(callback.message.chat.id)

            await callback.message.edit_text(
                text=(
                    f"✅Операцию обновил\n\n"
                    f"Дата - *{transaction_dict['date']}*\n"
                    f"Сумма - *{transaction_dict['summ']}*\n"
                    f"Категория - *{transaction_dict['category']}*\n"
                    f"Описание - {transaction_dict['text_descr']}\n"
                ),
            )

            user_dict.pop("transaction_dict")
            user_dict.pop("old_transaction_info")
            user_dict.pop("change_category")
            user_dict.pop("change_date")
            user_dict.pop("change_descr")
            user_dict.pop("change_summ")
            user_dict.pop("id")

            await state.set_data(user_dict)

            user_dict = await state.get_data()

            await state.set_state(UserState.transaction_summ)
        else:
            await callback.message.edit_text(
                text=(
                    f"🤕 Произошла ошибка при обновлении транзакции. Мы скоро все исправим!"
                ),
            )
            await state.set_state(UserState.transaction_summ)
    #
    except Exception as ex:
        logger.error(f"Ошибка при записи транзакции в БД: {ex}")
        await callback.message.answer(
            "🤕 Произошла ошибка при обновлении транзакции. Мы скоро все исправим!"
        )


@router.callback_query(UserState.save_transaction, Text("add_transaction"))
async def add_new_category_settings(callback: CallbackQuery, state: FSMContext):
    """
    Запись новой транзакции в базу данных.
    """
    try:
        logger.debug(f"Пользователь {callback.message.chat.id}. Запись транзакции в БД")

        user_dict = await state.get_data()

        summ = (
            user_dict["summ"] if user_dict["group"] == "Income" else -user_dict["summ"]
        )

        transaction_dict = {
            "id": callback.message.chat.id,
            "date": user_dict["date"],
            "summ": summ,
            "category": user_dict["category"],
            "descr": user_dict["descr"],
        }

        transaction_id = db_create_transaction(transaction_dict)

        if transaction_id:
            balance = db_get_balance(callback.message.chat.id)
            default_group = "Expense"

            await state.update_data(
                {
                    "group": default_group,
                    "summ": "",
                    "category": "",
                    "descr": "",
                    "balance": float(balance),
                    "user_state": "",
                }
            )

            await callback.message.edit_text(
                text=(
                    f"Операцию записал✅\n\n"
                    f'Дата - *{user_dict["date"]}*\n'
                    f'Сумма - *{user_dict["summ"]}*\n'
                    f'Категория - *{user_dict["category"]}*\n'
                    f'Описание - *{user_dict["descr"]}*\n'
                ),
                reply_markup=change_success_transaction(transaction_id),
            )

            user_dict = await state.get_data()

            if user_dict.get("date") == date.today().strftime("%d.%m.%Y"):
                str_date = "Сегодня"
                not_today = False
            else:
                str_date = user_dict.get("date")
                not_today = True

            await callback.message.answer(
                text=(
                    f"Записываю новую *расходную операцию.*\n"
                    f"Дата - {str_date}\n\n"
                    f"Сколько денег потратили?"
                ),
                reply_markup=transaction_main_kb(default_group, not_today),
            )
            await state.set_state(UserState.transaction_summ)
        else:
            await callback.message.edit_text(
                text=(
                    f"🤕 Произошла ошибка при записи транзакции. Мы скоро все исправим!"
                ),
            )
            await state.set_state(UserState.transaction_summ)

    except Exception as ex:
        logger.error(f"Ошибка при записи транзакции в БД: {ex}")
        await callback.message.answer(
            "🤕 Произошла ошибка при записи транзакции. Мы скоро все исправим!"
        )


@router.callback_query(UserState.change_transaction_category, Text("back"))
@router.callback_query(UserState.save_transaction, Text("change_transaction"))
@router.callback_query(UserState.update_transaction, Text("change_transaction"))
@router.callback_query(
    UserState.transaction_summ, Text(startswith="change_success_transaction")
)
async def callback_change_unwritten_category(
    callback: CallbackQuery, state: FSMContext
):
    """
    Функция. Уточняем перед записью какие данные изменить
    """
    logger.debug(
        f"Пользователь {callback.message.chat.id} - "
        f"Уточняем какие данные изменить перед сохранением"
    )

    user_state = await state.get_state()

    if user_state == "UserState:save_transaction":
        await state.set_state(UserState.change_transaction_details)

        await callback.message.edit_text(
            text=f"Что будем менять?",
            reply_markup=change_transaction_details_kb(),
        )

    elif (
        user_state == "UserState:update_transaction"
        or user_state == "UserState:change_transaction_category"
    ):
        await state.set_state(UserState.change_success_transaction_details)

        await callback.message.edit_text(
            text=f"Что будем менять?",
            reply_markup=change_transaction_details_kb(),
        )

    else:
        transaction_id = callback.data.split("-")[1]

        transaction = db_get_transaction(int(transaction_id))
        if transaction:
            amount = float(transaction.get("amount"))
            summ = amount if amount >= 0 else -amount
            group = "Income" if amount >= 0 else "Expense"
            transaction_date = date.strftime(
                transaction["transaction_date"], "%d.%m.%Y"
            )

            await state.update_data(
                {
                    "id": transaction_id,
                    "change_summ": "",
                    "change_descr": "",
                    "change_date": "",
                    "change_category": "",
                    "old_transaction_info": {
                        "old_date": transaction_date,
                        "old_summ": float(transaction["amount"]),
                        "old_category": transaction["category_name"],
                        "old_descr": transaction["description"],
                        "old_group": group,
                    },
                }
            )

            text = (
                f"Выбрана операция\n\n"
                f"*Дата операции: {transaction_date}*\n"
                f'{summ} ₽ в категории {transaction["category_name"]}\n'
                f'Описание: {transaction["description"]}\n\n'
            )

            await callback.message.answer(
                text=f"{text}Что будем менять?",
                reply_markup=change_success_transaction_details_kb(),
            )

            await state.set_state(UserState.change_success_transaction_details)
        else:
            await callback.message.answer(
                text=f"Операция уже удалена или не существует",
            )


@router.callback_query(
    UserState.change_transaction_details, Text("change_transaction_summ")
)
@router.callback_query(
    UserState.change_success_transaction_details, Text("change_transaction_summ")
)
async def callback_change_unwritten_category(
    callback: CallbackQuery, state: FSMContext
):
    """
    Функция. Меняем сумму операции перед записью
    """
    logger.debug(
        f"Пользователь {callback.message.chat.id} - "
        f"запрашиваем новую сумму операции перед сохранением"
    )

    user_state = await state.get_state()

    if user_state == "UserState:change_success_transaction_details":
        await state.set_state(UserState.change_success_transaction_details_summ)
    elif user_state == "UserState:change_transaction_details":
        await state.set_state(UserState.change_transaction_details_summ)

    await callback.message.edit_text(
        text=f"Введите новую сумму",
    )


@router.message(
    UserState.change_transaction_details_summ,
    F.text.regexp(r"\d+(?:[,.]\d{1,2})?(?:\s*[-+]\s*\d+(?:[,.]\d{1,2})?)*"),
)
@router.message(
    UserState.change_success_transaction_details_summ,
    F.text.regexp(r"\d+(?:[,.]\d{1,2})?(?:\s*[-+]\s*\d+(?:[,.]\d{1,2})?)*"),
)
async def transaction_category(message: Message, state: FSMContext):
    """
    Функция. Проверяем вводимое число пользователя и возвращаемся на проверку
    """
    try:
        logger.debug(
            f"Пользователь {message.chat.id} - Сумма {message.text}. "
            f"Уточняем категорию операции"
        )

        pattern = "\d+(?:[,.]\d{1,2})?(?:\s*[-+]\s*\d+(?:[,.]\d{1,2})?)*"
        match = re.search(pattern, message.text)
        if match:
            user_text = await calculate_sum(message.text)
        else:
            user_text = await check_regexp_summ(message.text)

        user_state = await state.get_state()

        if user_state == "UserState:change_success_transaction_details_summ":
            await state.update_data({"change_summ": float(user_text)})
            await change_success_transaction_check(message, state)

        elif user_state == "UserState:change_transaction_details_summ":
            await state.update_data({"summ": float(user_text)})
            await transaction_check_without_descr(message, state)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке: {ex}")
        await message.answer(
            f"🔰Ожидаю сумму операции. Нужно ввести число в формате:\n\n"
            f"🔸100\n"
            f"🔸100.0\n"
            f"🔸100,0\n"
            f"🔸100.00\n"
            f"🔸100,00\n\n"
            f"Также можно ввести сумму для калькулятора в формате:\n"
            f"🔹100+100,0+..",
        )


@router.callback_query(
    UserState.change_transaction_details, Text("change_transaction_descr")
)
@router.callback_query(
    UserState.change_success_transaction_details, Text("change_transaction_descr")
)
async def callback_change_descr(callback: CallbackQuery, state: FSMContext):
    """
    Функция. Уточняем новое описание операии
    """
    logger.debug(
        f"Пользователь {callback.message.chat.id} - Уточняем новое описание операии"
    )
    await callback.message.edit_text(
        text=f"Введите описание операции",
    )

    user_state = await state.get_state()

    if user_state == "UserState:change_success_transaction_details":
        await state.set_state(UserState.change_success_transaction_details_descr)
    elif user_state == "UserState:change_transaction_details":
        await state.set_state(UserState.change_transaction_details_descr)
