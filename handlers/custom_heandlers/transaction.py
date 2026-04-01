from datetime import date, timedelta, datetime
import re

from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from fuzzywuzzy import fuzz
from loguru import logger
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import F, Bot
from aiogram.types import CallbackQuery

from config_data.config import BOT_TOKEN
from database.database import (
    db_get_category,
    db_create_transaction,
    db_create_category,
    db_get_balance,
    db_get_transaction,
    db_update_transaction,
    db_get_category_id,
    db_delete_category,
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
    CreateCallbackData,
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
        amount = summ = (
            user_dict["old_summ"]
            if user_data["change_summ"] == ""
            else user_data["change_summ"]
        )

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


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))


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

            msg = await message.answer(
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

            text = ""

            msg = await message.answer(
                text=(
                    text + "Записываю операцию\n"
                    "Дата - *Сегодня*\n\n"
                    "Введите сумму.\n"
                    "Далее можно будет выбрать Расход/Доход"
                ),
                reply_markup=transaction_main_kb(),
            )
            await state.set_data(
                {
                    "date": date.today().strftime("%d.%m.%Y"),
                    "group": default_group,
                    "summ": "",
                    "category": "",
                    "descr": "",
                    "balance": float(balance),
                    "last_msg": msg.message_id,
                    "not_changed_msg": msg.message_id - 1,
                }
            )
            await state.update_data(user_category)
            await state.set_state(UserState.transaction_summ)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при начале записи новой операции: {ex}")
        msg = await message.edit_text(
            "🤕 Возникла ошибка в начале записи операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(
    UserState.transaction_summ,
    F.data.in_(
        {
            "income",
            "expense",
            "change_for_today_date",
            "change_for_yesterday_date",
            "change_for_next_date",
            "change_for_past_date",
        }
    ),
)
@router.callback_query(UserState.transaction_category, F.data == "back")
@router.callback_query(F.data == "new_transaction_callback")
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
        elif callback.data == "change_for_next_date":
            user_data = await state.get_data()
            user_date = datetime.strptime(user_data["date"], "%d.%m.%Y").date()
            past_day = user_date + timedelta(days=1)
            await state.update_data({"date": past_day.strftime("%d.%m.%Y")})
        elif callback.data == "change_for_past_date":
            user_data = await state.get_data()
            user_date = datetime.strptime(user_data["date"], "%d.%m.%Y").date()
            next_date = user_date - timedelta(days=1)
            await state.update_data({"date": next_date.strftime("%d.%m.%Y")})
        elif callback.data == "new_transaction_callback":
            user_category = db_get_category(
                tg_id=callback.message.chat.id,
                user_name=callback.message.from_user.full_name,
            )
            balance = db_get_balance(callback.message.chat.id)
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
        msg = await callback.message.edit_text(
            text=(
                text + f"Записываю операцию.\n"
                f"Дата - *{user_date}*\n\n"
                f"Введите сумму операции\n"
                f"Далее можно будет выбрать Расход/Доход"
            ),
            reply_markup=transaction_main_kb(not_today=not_today),
        )
        await state.update_data(
            {"last_msg": msg.message_id, "not_changed_msg": msg.message_id - 1}
        )

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении суммы операции: {ex}")
        msg = await callback.message.edit_text(
            "🤕 Возникла ошибка при уточнении суммы операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(UserState.transaction_summ, F.data == "change_transaction_date")
@router.callback_query(
    UserState.change_transaction_details, F.data == "change_transaction_date"
)
@router.callback_query(
    UserState.change_success_transaction_details, F.data == "change_transaction_date"
)
async def transaction_user_date(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик команды выбора даты для статистики.
    """
    try:
        msg = await callback.message.edit_text(
            text="Выберите дату начала",
            reply_markup=await SimpleCalendar().start_calendar(),
        )
        await state.update_data({"last_msg": msg.message_id})
        await state.update_data({"user_state": await state.get_state()})
    except Exception as ex:
        logger.error(f"Что-то пошло не так при выборе даты для статистики: {ex}")
        msg = await callback.message.edit_text(
            "🤕 Возникла ошибка при выборе даты. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


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
                        "Что-то пошло не так при выборе даты, скоро все исправим😵‍💫",
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
            user_text = float(await calculate_sum(message.text))
        else:
            user_text = float(await check_regexp_summ(message.text))
        await state.update_data({"summ": user_text})
        user_state = await state.get_state()

        user_dict = await state.get_data()

        group_name = "Expense" if user_dict["group"] == "Expense" else "Income"

        user_category = user_dict.get(group_name)

        if user_category is not None:
            msg = await message.answer(
                f"Сумма - {round(user_text, 2)}\n\n"
                f"В какой категории была операция?\n"
                f"\nЕсли операции нет и нужно добавить - "
                f"просто введи новую категорию",
                reply_markup=user_category_kb(sorted(user_category), group_name),
            )
            user_dict = await state.get_data()

        else:
            msg = await message.answer(
                "Категорий еще нет. Введите новую",
            )
        await state.set_state(UserState.transaction_category)
        await state.update_data({"last_msg": msg.message_id})

    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке: {ex}")
        msg = await message.answer(
            "🔰Ожидаю сумму операции. Нужно ввести число в формате:\n\n"
            "🔸100\n"
            "🔸100.0\n"
            "🔸100,0\n"
            "🔸100.00\n"
            "🔸100,00\n\n"
            "Также можно ввести сумму для калькулятора в формате:\n"
            "🔹100+100,0+..",
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(UserState.transaction_new_category, F.data == "back")
@router.callback_query(UserState.transaction_description, F.data == "back")
@router.callback_query(
    UserState.change_transaction_details, F.data == "change_transaction_category"
)
@router.callback_query(
    UserState.change_success_transaction_details,
    F.data == "change_transaction_category",
)
@router.callback_query(
    UserState.transaction_category, F.data.in_({"income", "expense"})
)
async def transaction_category_back(callback: CallbackQuery, state: FSMContext):
    """
    Функция. Проверяем вводимое число пользователя и уточняем категорию операции.
    Сюда можно попасть только в том случае, если пользователь ввел новую категорию и нажал "Назад".
    Либо при изменении операции перед записью, либо смена Доход/расход во время выбора категории
    """
    try:
        logger.debug(
            f"Пользователь {callback.message.chat.id}" f"Уточняем категорию операции"
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
                msg = await callback.message.edit_text(
                    "В какой категории была операция?\n"
                    "\nЕсли операции нет и нужно добавить - "
                    "просто введи новую категорию",
                    reply_markup=user_category_kb(sorted(user_category)),
                )

            else:
                msg = await callback.message.edit_text(
                    "Категорий еще нет. Введите новую",
                )
            await state.set_state(UserState.change_transaction_category)
            await state.update_data({"last_msg": msg.message_id})

        else:
            group_name = "Expense" if user_dict["group"] == "Expense" else "Income"
            user_category = user_dict.get(group_name)

            if user_category is not None:
                msg = await callback.message.edit_text(
                    "В какой категории была операция?\n"
                    "\nЕсли операции нет и нужно добавить - "
                    "просто введи новую категорию",
                    reply_markup=user_category_kb(sorted(user_category), group_name),
                )
            else:
                msg = await callback.message.edit_text(
                    "Категорий еще нет. Введите новую",
                )
            await state.set_state(UserState.transaction_category)
            await state.update_data({"last_msg": msg.message_id})

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении категории операции: {ex}")
        msg = await callback.message.answer(
            "🤕 Возникла ошибка при уточнении категории операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


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
            if len(message.text) > 20:
                msg = await message.answer(
                    "Название категории не может превышать 20 символов"
                )
            else:
                await state.update_data({"category": category})

                msg = await message.answer(
                    f"К сожалению, такой категории не было в вашем списке.\n"
                    f"\nГруппа категории: {group_name}\n"
                    f"Категория: {category}\n"
                    f"\nДобавим категорию",
                    reply_markup=transaction_save_kb(),
                )
                await state.set_state(UserState.transaction_new_category)
                await state.update_data({"last_msg": msg.message_id})

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
                msg = await message.answer(
                    text="Такая категория уже есть в вашем списке\n"
                    "Добавьте описание операции (необязательно)",
                    reply_markup=transaction_descr_kb(),
                )
                await state.update_data({"last_msg": msg.message_id})
                await state.set_state(UserState.transaction_description)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении описания операции: {ex}")
        msg = await message.answer(
            "🤕 Возникла ошибка при уточнении описания операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(
    UserState.transaction_category, F.data.startswith("transaction_category:")
)
@router.callback_query(
    UserState.change_transaction_category, F.data.startswith("transaction_category:")
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
            msg = await callback.message.edit_text(
                text="Добавьте описание операции (необязательно)",
                reply_markup=transaction_descr_kb(),
            )
            await state.update_data({"last_msg": msg.message_id})
            await state.set_state(UserState.transaction_description)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении описания операции: {ex}")
        msg = await callback.message.answer(
            "🤕 Возникла ошибка при уточнении описания операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(UserState.transaction_new_category, F.data == "add_category")
async def transaction_new_category(callback: CallbackQuery, state: FSMContext):
    """
    Запись новой категории операции и переход к уточнению описания.
    """
    try:
        logger.debug(f"Пользователь {callback.message.chat.id}. Запись новой категории")

        user_dict = await state.get_data()

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
            user_category = db_get_category_id(
                tg_id=callback.message.chat.id, category_name=user_dict["category"]
            )
            msg = await callback.message.edit_text(
                f'Записал новую категорию {user_dict["category"]}\n\n'
                f"Добавьте описание операции (необязательно)",
                reply_markup=transaction_descr_kb(
                    delete_flag=True, category_id=user_category["id"]
                ),
            )
            await state.update_data({"last_msg": msg.message_id})
            await state.set_state(UserState.transaction_description)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при записи новой категории: {ex}")
        msg = await callback.message.answer(
            "🤕 Возникла ошибка при записи новой категории. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(CreateCallbackData.filter(F.foo == "delete_category_from_db"))
async def delete_success_category_from_transacsions(
    callback: CallbackQuery, state: FSMContext, callback_data: CreateCallbackData
) -> None:
    """ """
    logger.info("delete_success_category_from_transacsions")

    data = await state.get_data()
    category_group = data["group"]
    category_list = data[category_group][:-1]

    await state.update_data({category_group: category_list})

    db_delete_category(callback_data.bar)
    await transaction_category_back(callback, state)


@router.callback_query(UserState.transaction_description)
@router.callback_query(UserState.change_transaction_details, F.data == "back")
async def callback_transaction_check(callback: CallbackQuery, state: FSMContext):
    """
    Проверка операции перед сохранением.
    """
    try:
        logger.debug(f"Пользователь {callback.message.chat.id}. Проверка операции")
        user_dict = await state.get_data()
        description = user_dict.get("descr")
        text_descr = "(Без описания)" if description == "" else description

        msg = await callback.message.edit_text(
            f"Проверим операцию:\n"
            f'Дата - *{user_dict["date"]}*\n'
            f'Сумма - *{round(user_dict["summ"], 2)}*\n'
            f'Категория - *{user_dict["category"]}*\n'
            f"Описание - {text_descr}\n",
            reply_markup=save_category_kb(),
        )
        await state.update_data({"last_msg": msg.message_id})
        await state.set_state(UserState.save_transaction)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        msg = await callback.message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


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

        msg = await message.answer(
            f"Сейчас операция будет выглядеть так:\n"
            f'Дата - *{transaction_dict["date"]}*\n'
            f'Сумма - *{round(transaction_dict["summ"], 2)}*\n'
            f'Категория - *{transaction_dict["category"]}*\n'
            f'Описание - {transaction_dict["descr"]}\n',
            reply_markup=update_category_kb(),
        )
        await state.update_data({"last_msg": msg.message_id})
        await state.set_state(UserState.update_transaction)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        msg = await message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(UserState.change_success_transaction_details, F.data == "back")
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

        logger.debug(transaction_dict)

        await state.update_data({"transaction_dict": transaction_dict})

        msg = await callback.message.edit_text(
            f"Сейчас операция будет выглядеть так:\n"
            f'Дата - *{transaction_dict["date"]}*\n'
            f'Сумма - *{round(transaction_dict["summ"], 2)}*\n'
            f'Категория - *{transaction_dict["category"]}*\n'
            f'Описание - {transaction_dict["descr"]}\n',
            reply_markup=update_category_kb(),
        )
        await state.update_data({"last_msg": msg.message_id})
        await state.set_state(UserState.update_transaction)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        msg = await callback.message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


async def transaction_check_without_descr(message: Message, state: FSMContext):
    """
    Проверка операции перед сохранением.
    """
    try:
        logger.debug(f"Пользователь {message.chat.id}. Проверка операции")

        user_dict = await state.get_data()
        description = user_dict.get("descr")
        text_descr = "(Без описания)" if description == "" else description

        msg = await message.answer(
            f"Проверим операцию:\n"
            f'Дата - *{user_dict["date"]}*\n'
            f'Сумма - *{round(user_dict["summ"], 2)}*\n'
            f'Категория - *{user_dict["category"]}*\n'
            f"Описание - {text_descr}\n",
            reply_markup=save_category_kb(),
        )
        await state.update_data({"last_msg": msg.message_id})
        await state.set_state(UserState.save_transaction)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        msg = await message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


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

            msg = await message.answer(
                f"Проверим операцию:\n"
                f'Дата - *{user_dict["date"]}*\n'
                f'Сумма - *{round(user_dict["summ"], 2)}*\n'
                f'Категория - *{user_dict["category"]}*\n'
                f"Описание - *{description}*\n",
                reply_markup=save_category_kb(),
            )
            await state.update_data({"last_msg": msg.message_id})
            await state.set_state(UserState.save_transaction)

    except Exception as ex:
        logger.error(f"Что-то пошло не так при проверке операции: {ex}")
        msg = await message.answer(
            "🤕 Возникла ошибка при проверке операции. Скоро меня починят"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(UserState.update_transaction, F.data == "update_transaction")
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
        user_state = user_dict.get("user_state_history")
        logger.debug(user_state)

        if db_update_transaction(transaction_dict, callback.message.chat.id):
            balance = db_get_balance(callback.message.chat.id)

            if (
                user_state != "UserState:statistic_history"
                and user_state != "UserState:transaction_history"
            ):
                not_changed_msg = (
                    user_dict["not_changed_msg"] + 1
                    if user_dict.get("del_early_msg")
                    else user_dict["not_changed_msg"]
                )

                for msg_id in range(not_changed_msg, user_dict["last_msg"]):
                    try:
                        await bot.delete_message(
                            chat_id=callback.message.chat.id, message_id=msg_id
                        )
                    except TelegramBadRequest:
                        pass

                msg = await callback.message.edit_text(
                    text=(
                        f"✅Операцию обновил\n\n"
                        f"Дата - *{transaction_dict['date']}*\n"
                        f"Сумма - *{round(transaction_dict['summ'], 2)}*\n"
                        f"Категория - *{transaction_dict['category']}*\n"
                        f"Описание - {transaction_dict['text_descr']}\n"
                    ),
                    reply_markup=change_success_transaction(
                        transaction_dict["id"], callback.message.message_id
                    ),
                )

                if user_dict.get("date") == date.today().strftime("%d.%m.%Y"):
                    str_date = "Сегодня"
                    not_today = False
                else:
                    str_date = user_dict.get("date")
                    not_today = True

                msg = await callback.message.answer(
                    text=(
                        f"Записываю новую *расходную операцию.*\n"
                        f"Дата - {str_date}\n\n"
                        f"Сколько денег потратили?"
                    ),
                    reply_markup=transaction_main_kb(not_today),
                )
                ll = msg.message_id
                await state.update_data(
                    {
                        "last_msg": ll,
                        "not_changed_msg": ll - 1,
                        "user_state": "",
                    }
                )
            else:
                msg = await callback.message.edit_text(
                    text=(
                        f"✅Операцию обновил\n\n"
                        f"Дата - *{transaction_dict['date']}*\n"
                        f"Сумма - *{round(transaction_dict['summ'], 2)}*\n"
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

            if user_state == "UserState:statistic_history":
                await state.set_state(UserState.statistic_history)
            elif user_state == "UserState:transaction_history":
                await state.set_state(UserState.transaction_history)
            else:
                await state.set_state(UserState.transaction_summ)
        else:
            msg = await callback.message.edit_text(
                text=(
                    "🤕 Произошла ошибка при обновлении транзакции. Мы скоро все исправим!"
                ),
            )
            if user_state == "UserState:statistic_history":
                await state.set_state(UserState.statistic_history)
            elif user_state == "UserState:transaction_history":
                await state.set_state(UserState.transaction_history)
            else:
                await state.set_state(UserState.transaction_summ)
    #
    except Exception as ex:
        logger.error(f"Ошибка при записи транзакции в БД: {ex}")
        msg = await callback.message.answer(
            "🤕 Произошла ошибка при обновлении транзакции. Мы скоро все исправим!"
        )


@router.callback_query(UserState.save_transaction, F.data == "add_transaction")
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

            for msg_id in range(
                user_dict["not_changed_msg"] + 1, user_dict["last_msg"]
            ):
                try:
                    await bot.delete_message(
                        chat_id=callback.message.chat.id, message_id=msg_id
                    )
                except TelegramBadRequest:
                    pass

            msg = await callback.message.edit_text(
                text=(
                    f"Операцию записал✅\n\n"
                    f'Дата - *{user_dict["date"]}*\n'
                    f'Сумма - *{round(user_dict["summ"], 2)}*\n'
                    f'Категория - *{user_dict["category"]}*\n'
                    f'Описание - *{user_dict["descr"]}*\n'
                ),
                reply_markup=change_success_transaction(
                    transaction_id, callback.message.message_id
                ),
            )
            await state.update_data({"last_msg": msg.message_id})
            user_dict = await state.get_data()

            if user_dict.get("date") == date.today().strftime("%d.%m.%Y"):
                str_date = "Сегодня"
                not_today = False
            else:
                str_date = user_dict.get("date")
                not_today = True

            msg = await callback.message.answer(
                text=(
                    f"Записываю новую *расходную операцию.*\n"
                    f"Дата - {str_date}\n\n"
                    f"Сколько денег потратили?"
                ),
                reply_markup=transaction_main_kb(not_today),
            )
            await state.update_data({"last_msg": msg.message_id})

            await state.update_data(
                {
                    "group": default_group,
                    "summ": "",
                    "category": "",
                    "descr": "",
                    "balance": float(balance),
                    "user_state": "",
                    "last_msg": msg.message_id,
                    "not_changed_msg": msg.message_id - 1,
                }
            )

            await state.set_state(UserState.transaction_summ)
        else:
            msg = await callback.message.edit_text(
                text=(
                    "🤕 Произошла ошибка при записи транзакции. Мы скоро все исправим!"
                ),
            )
            await state.update_data({"last_msg": msg.message_id})
            await state.set_state(UserState.transaction_summ)

    except Exception as ex:
        logger.error(f"Ошибка при записи транзакции в БД: {ex}")
        msg = await callback.message.answer(
            "🤕 Произошла ошибка при записи транзакции. Мы скоро все исправим!"
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(UserState.change_transaction_category, F.data == "back")
@router.callback_query(UserState.save_transaction, F.data == "change_transaction")
@router.callback_query(UserState.update_transaction, F.data == "change_transaction")
@router.callback_query(
    UserState.transaction_summ, F.data.startswith("change_success_transaction")
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
    logger.debug(f"user state - {user_state}")

    if user_state == "UserState:save_transaction":
        logger.debug("UserState:save_transaction")
        await state.set_state(UserState.change_transaction_details)

        msg = await callback.message.edit_text(
            text="Что будем менять?",
            reply_markup=change_transaction_details_kb(),
        )
        await state.update_data({"last_msg": msg.message_id})

    elif (
        user_state == "UserState:update_transaction"
        or user_state == "UserState:change_transaction_category"
    ):
        logger.debug(
            "UserState:update_transaction or UserState:change_transaction_category"
        )

        await state.set_state(UserState.change_success_transaction_details)

        msg = await callback.message.edit_text(
            text="Что будем менять?",
            reply_markup=change_transaction_details_kb(),
        )
        await state.update_data({"last_msg": msg.message_id})

    else:
        logger.debug("else")
        transaction_id = callback.data.split("-")[1]
        transaction_update_msg = int(callback.data.split("-")[2])
        transaction = db_get_transaction(int(transaction_id), callback.message.chat.id)
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
            user_dd = await state.get_data()
            logger.debug(f"user data - {user_dd}")
            msg_change_id = user_dd["not_changed_msg"]
            last_msg = user_dd["last_msg"]
            text = (
                f"Выбрана операция\n\n"
                f"*Дата операции: {transaction_date}*\n"
                f'{summ} ₽ в категории {transaction["category_name"]}\n'
                f'Описание: {transaction["description"]}\n\n'
            )

            for msg_id in range(msg_change_id + 1, last_msg + 1):
                try:
                    await bot.delete_message(
                        chat_id=callback.message.chat.id, message_id=msg_id
                    )
                except TelegramBadRequest:
                    pass

            if transaction_update_msg < msg_change_id + 1:
                try:
                    await bot.delete_message(
                        chat_id=callback.message.chat.id,
                        message_id=transaction_update_msg,
                    )
                except TelegramBadRequest:
                    pass
                msg = await callback.message.answer(
                    text=f"{text}Что будем менять?",
                    reply_markup=change_success_transaction_details_kb(),
                )
                await state.update_data(
                    {"last_msg": msg.message_id + 1, "del_early_msg": True}
                )

            else:
                msg = await callback.message.edit_text(
                    text=f"{text}Что будем менять?",
                    reply_markup=change_success_transaction_details_kb(),
                )
                await state.update_data({"last_msg": msg.message_id})
            await state.set_state(UserState.change_success_transaction_details)
        else:
            msg = await callback.message.answer(
                text="Операция уже удалена или не существует",
            )
            await state.update_data({"last_msg": msg.message_id})


@router.callback_query(
    UserState.change_transaction_details, F.data == "change_transaction_summ"
)
@router.callback_query(
    UserState.change_success_transaction_details, F.data == "change_transaction_summ"
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

    msg = await callback.message.edit_text(
        text="Введите новую сумму",
    )
    await state.update_data({"last_msg": msg.message_id})


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
        msg = await message.answer(
            "🔰Ожидаю сумму операции. Нужно ввести число в формате:\n\n"
            "🔸100\n"
            "🔸100.0\n"
            "🔸100,0\n"
            "🔸100.00\n"
            "🔸100,00\n\n"
            "Также можно ввести сумму для калькулятора в формате:\n"
            "🔹100+100,0+..",
        )
        await state.update_data({"last_msg": msg.message_id})


@router.callback_query(
    UserState.change_transaction_details, F.data == "change_transaction_descr"
)
@router.callback_query(
    UserState.change_success_transaction_details, F.data == "change_transaction_descr"
)
async def callback_change_descr(callback: CallbackQuery, state: FSMContext):
    """
    Функция. Уточняем новое описание операии
    """
    logger.debug(
        f"Пользователь {callback.message.chat.id} - Уточняем новое описание операии"
    )
    msg = await callback.message.edit_text(
        text="Введите описание операции",
    )
    await state.update_data({"last_msg": msg.message_id})

    user_state = await state.get_state()

    logger.debug(user_state)

    if user_state == "UserState:change_success_transaction_details":
        await state.set_state(UserState.change_success_transaction_details_descr)
    elif user_state == "UserState:change_transaction_details":
        await state.set_state(UserState.change_transaction_details_descr)
