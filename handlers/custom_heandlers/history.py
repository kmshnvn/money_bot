import calendar
from datetime import datetime, date
from typing import Tuple, Dict

from aiogram import F
from aiogram.exceptions import TelegramBadRequest
from dateutil.relativedelta import relativedelta
from loguru import logger
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.states import UserState
from database.database import (
    db_get_history,
    db_get_transaction,
    db_delete_transaction,
    db_get_history_transaction,
    db_get_custom_date_history,
    db_get_first_date_transaction,
    db_get_all_date_transaction,
    db_get_all_transactions_by_day,
    db_get_all_month_transaction,
    db_get_category_transaction_by_date,
)
from functions import simple_cal_callback, SimpleCalendar
from functions.functions import create_history_text, text_of_stat, get_start_date
from functions.graphics import generate_standard_graphics
from handlers.default_heandlers.start import router
from keyboards.inline_keyboards import (
    change_date,
    main_history_inline_kb,
    transaction_history,
    delete_history_kb,
    transaction_history_by_day,
    category_history_kb,
    CreateCallbackData,
    back_to_category_history_kb,
)


@router.message(Command("history"))
@router.message(F.text.contains("История"))
async def history(message: Message, state: FSMContext) -> None:
    """
    Функция, отлавливает команду /history
    """
    try:
        logger.info(f"{message.chat.id} - history.py | выбор команды /history")
        user_dict = await state.get_data()
        logger.debug(user_dict)

        await state.set_data(
            {
                "last_msg": user_dict.get("last_msg"),
                "not_changed_msg": user_dict.get("not_changed_msg"),
            }
        )

        if not history:
            await message.answer(
                f"Истории пользования еще нет, выберите другую команду"
            )
        else:
            await message.answer(
                f"*Это меню различной статистики.*\n\n"
                f"Здесь можно посмотреть последние операции и удалить их при необходимости. "
                f"Если нажать на кнопку 📊*Статисика*, "
                f"то сможешь посмотреть свои обобщенные траты за различный период "
                f"и понять куда уходит больше всего денег",
                reply_markup=main_history_inline_kb(),
            )

            await state.set_state(UserState.main_history)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при выборе пункта истории {ex}")
        await message.edit_text(
            "🤕Возникла ошибка при просмотре истории. Скоро меня починят"
        )


@router.callback_query(Text("back_to_main_history"))
@router.callback_query(Text("main_history_menu"))
async def callback_history(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        logger.info(f"{callback.message.chat.id} - history.py | возврат в меню history")
        user_dict = await state.get_data()
        logger.debug(user_dict)

        await state.set_data(
            {
                "last_msg": user_dict.get("last_msg"),
                "not_changed_msg": user_dict.get("not_changed_msg"),
            }
        )
        user_dict = await state.get_data()
        logger.debug(user_dict)

        await callback.message.edit_text(
            f"*Это меню различной статистики.*\n\n"
            f"Здесь можно посмотреть последние операции и удалить их при необходимости. "
            f"Если нажать на кнопку 📊*Статисика*, "
            f"то сможешь посмотреть свои обобщенные траты за различный период "
            f"и понять куда уходит больше всего денег",
            reply_markup=main_history_inline_kb(),
        )

        await state.set_state(UserState.main_history)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при выборе пункта истории {ex}")
        await callback.message.edit_text(
            "🤕Возникла ошибка при просмотре истории. Скоро меня починят"
        )


@router.callback_query(Text("history_of_transactions"))
@router.callback_query(UserState.transaction_history, Text("change_for_past_history"))
@router.callback_query(UserState.transaction_history, Text("change_for_next_history"))
@router.callback_query(UserState.transaction_history, Text("last_transaction_history"))
async def user_transaction_history(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Вывод истории транзакций пользователя
    """
    try:
        logger.info(
            f"{callback.message.chat.id} - Вывод истории транзакций пользователя"
        )

        user_dict = await state.get_data()
        logger.debug(user_dict)

        period_flag = False
        await state.set_state(UserState.transaction_history)
        user_dict = await state.get_data()

        if callback.data == "last_transaction_history":
            if user_dict.get("start_date"):
                user_dict.pop("start_date")
            if user_dict.get("end_date"):
                user_dict.pop("end_date")
            await state.set_data(user_dict)

        start_date, end_date = create_date(user_dict)
        history_limit = 0

        if start_date and end_date:
            period_flag = True
            history = db_get_custom_date_history(
                callback.message.chat.id, start_date, end_date
            )
            start_date = date.strftime(start_date, "%d.%m.%Y")
            end_date = date.strftime(end_date, "%d.%m.%Y")
            text = create_history_text("", list(history))
            if text == "":
                full_text = (
                    f"Транзакции в периоде с {start_date} по {end_date} отсутствуют"
                )
            else:
                full_text = (
                    f"Транзакции в выбранном периоде {start_date} - {end_date}\n\n"
                    + text
                )

        else:
            user_data = await state.get_data()
            if user_data.get("history_transaction_lim"):
                history_limit = user_data.get("history_transaction_lim")

                if callback.data == "change_for_past_history":
                    history_limit += 30
                elif callback.data == "change_for_next_history":
                    history_limit -= 30
            else:
                history_limit = 30

            await state.update_data({"history_transaction_lim": history_limit})
            history = db_get_history(callback.message.chat.id, history_limit)
            text = "Последние операции\n\n"
            for e in history:
                logger.debug(e)
            full_text = create_history_text(text, list(history))

        last_transaction_list = True if history_limit <= 30 else False

        await callback.message.edit_text(
            f"{full_text}",
            reply_markup=transaction_history(last_transaction_list, period_flag),
            disable_web_page_preview=True,
        )
    except Exception as ex:
        logger.error(f"Что-то пошло не так при формировании истории {ex}")
        await callback.message.edit_text(
            "🤕Возникла ошибка при выводе истории. Скоро меня починят"
        )


@router.callback_query(UserState.transaction_history, Text("show_day_history"))
@router.callback_query(
    UserState.transaction_history, Text("change_for_past_day_history")
)
@router.callback_query(
    UserState.transaction_history, Text("change_for_next_day_history")
)
async def user_transaction_history_by_day(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Вывод истории транзакций пользователя
    """
    try:
        logger.info(
            f"{callback.message.chat.id} - Вывод истории транзакций пользователя за день"
        )
        logger.debug(callback.data)
        text = "❗️Важно. Я вывожу только те дни, в которые были операции. Если операций не было, то день будет пропущен❗️\n\n"
        await state.set_state(UserState.transaction_history)
        user_data = await state.get_data()
        if user_data.get("limit_days"):
            limit_days = user_data.get("limit_days")

            if callback.data == "change_for_past_day_history":
                limit_days += 1
            elif callback.data == "change_for_next_day_history":
                limit_days -= 1
        else:
            limit_days = 1
        keyboard_flag = True if limit_days == 1 else False
        dates_list = db_get_all_date_transaction(callback.message.chat.id, limit_days)

        logger.debug(dates_list)
        logger.debug(limit_days)

        await state.update_data({"limit_days": limit_days})

        history = db_get_all_transactions_by_day(
            callback.message.chat.id, dates_list[-1]
        )
        full_text = create_history_text(text=text, history=list(history))

        await callback.message.edit_text(
            f"{full_text}",
            reply_markup=transaction_history_by_day(keyboard_flag),
        )
    except Exception as ex:
        logger.error(f"Что-то пошло не так при формировании истории по дням {ex}")
        await callback.message.edit_text(
            "🤕Возникла ошибка при выводе истории. Скоро меня починят"
        )


@router.message(F.text.startswith("/del"))
async def check_delete_transaction(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды удаления операции.
    """
    try:
        logger.info(f"{message.chat.id} - Уточняем удаление операции")

        transaction_id = message.text[4:]
        transaction = db_get_transaction(transaction_id, message.chat.id)

        if transaction:
            amount = float(transaction.get("amount"))
            summ = amount if amount >= 0 else -amount
            transaction_date = date.strftime(
                transaction["transaction_date"], "%d.%m.%Y"
            )

            await state.set_data(
                {
                    "delete_transaction": {
                        "id": transaction_id,
                        "user_id": message.chat.id,
                        "summ": amount,
                    },
                    "transaction_info": {
                        "transaction_date": transaction_date,
                        "category_name": transaction.get("category_name"),
                        "summ": summ,
                        "description": transaction.get("description"),
                    },
                }
            )

            text = (
                f"Выбрана операция\n\n"
                f"*Дата операции: {transaction_date}*\n"
                f'{summ} ₽ в категории {transaction["category_name"]}\n'
                f'Описание: {transaction["description"]}\n\n'
                f"Удаляем операцию?"
            )

            await message.answer(f"{text}", reply_markup=delete_history_kb())
        else:
            await message.answer(
                text=f"Операция уже удалена или не существует",
            )

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении удаления операции: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при уточнении удаления операции. Скоро меня починят"
        )


@router.callback_query(Text(startswith="delete_success_transaction"))
async def callback_change_descr(callback: CallbackQuery, state: FSMContext):
    """
    Удаление операции через callback кнопку
    """
    try:
        logger.info(f"{callback.message.chat.id} - Уточняем удаление операции")

        transaction_id = callback.data.split("-")[1]
        transaction = db_get_transaction(int(transaction_id), callback.message.chat.id)

        if transaction:
            amount = float(transaction.get("amount"))
            summ = amount if amount >= 0 else -amount
            transaction_date = date.strftime(
                transaction["transaction_date"], "%d.%m.%Y"
            )

            await state.update_data(
                {
                    "delete_transaction": {
                        "id": transaction_id,
                        "user_id": callback.message.chat.id,
                        "summ": amount,
                    },
                    "transaction_info": {
                        "transaction_date": transaction_date,
                        "category_name": transaction.get("category_name"),
                        "summ": summ,
                        "description": transaction.get("description"),
                    },
                }
            )

            text = (
                f"Выбрана операция\n\n"
                f"*Дата операции: {transaction_date}*\n"
                f'{summ} ₽ в категории {transaction["category_name"]}\n'
                f'Описание: {transaction["description"]}\n\n'
                f"Удаляем операцию?"
            )

            await callback.message.answer(f"{text}", reply_markup=delete_history_kb())
        else:
            await callback.message.answer(
                text=f"Операция уже удалена или не существует",
            )

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении удаления операции: {ex}")
        await callback.message.answer(
            "🤕 Возникла ошибка при уточнении удаления операции. Скоро меня починят"
        )


@router.callback_query(Text("delete_transaction"))
async def delete_transaction(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик подтверждения удаления операции.
    """
    try:
        logger.info(f"{callback.message.chat.id} - Уточняем удаление операции")

        user_dict = await state.get_data()

        if db_delete_transaction(user_dict["delete_transaction"]):
            transaction_info = user_dict["transaction_info"]
            text = (
                f"✅Операция успешно удалена\n\n"
                f'*Дата операции: {transaction_info["transaction_date"]}*\n'
                f'{transaction_info["summ"]} ₽ в категории {transaction_info["category_name"]}\n'
                f'Описание: {transaction_info["description"]}'
            )

            user_dict.pop("delete_transaction")
            user_dict.pop("transaction_info")
            await state.set_data(user_dict)

            await callback.message.edit_text(text=text, parse_mode="Markdown")

        else:
            await callback.message.edit_text(
                text=f"Что-то пошло не так при удалении", parse_mode="Markdown"
            )

    except Exception as ex:
        logger.error(f"Что-то пошло не так при удалении операции: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при подтверждении удаления операции. Скоро меня починят"
        )


@router.callback_query(Text("user_statistic"))
async def month_statistic(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды "Статистика".
    """
    try:
        logger.info(f"{callback.message.chat.id} - Вывод команды статистики")
        user_dict = await state.get_data()
        logger.debug(user_dict)

        history_list, start_date, end_date = db_get_history_transaction(
            tg_id=callback.message.chat.id,
        )
        await state.update_data({"start_date": start_date, "end_date": end_date})
        text = f"История с {start_date} по {end_date}:\n"

        text_list, data_for_graphic, data_for_keyboard = text_of_stat(history_list)
        for new_text in text_list:
            text += new_text

        await callback.message.edit_text(
            text=text,
            reply_markup=change_date(),
        )

        await state.set_state(UserState.statistic_history)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при выводе статистики: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при выводе статистики. Скоро меня починят"
        )


@router.callback_query(Text("change_date"))
async def date_statistic(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды выбора даты для статистики.
    """
    try:
        logger.info(
            f"{callback.message.chat.id} - Выбираем дату начала для вывода истории"
        )

        await callback.message.edit_text(
            text="Выберите дату начала",
            reply_markup=await SimpleCalendar().start_calendar(),
        )
        await state.update_data({"user_state": await state.get_state()})
        await state.set_state(UserState.start_date_history)
    except Exception as ex:
        logger.error(f"Что-то пошло не так при выборе даты для статистики: {ex}")
        await callback.message.edit_text(
            "🤕 Возникла ошибка при выборе даты. Скоро меня починят"
        )


@router.callback_query(UserState.start_date_history, simple_cal_callback.filter())
@router.callback_query(UserState.end_date_history, simple_cal_callback.filter())
async def process_simple_calendar_history(
    callback_query: CallbackQuery, callback_data: dict, state: FSMContext
):
    """
    Обработчик выбора даты через календарь для статистики.
    """
    try:
        logger.info(
            f"{callback_query.message.chat.id} - Выбираем дату конца для вывода истории"
        )

        my_state = await state.get_state()
        selected, date = await SimpleCalendar().process_selection(
            callback_query, callback_data
        )

        if selected and my_state == "UserState:start_date_history":
            new_date = date.strftime("%d.%m.%Y")
            await callback_query.message.edit_text(
                f"Выбранная дата {new_date}\n" f"Выберите дату конца периода",
                reply_markup=await SimpleCalendar().start_calendar(),
            )
            await state.update_data({"start_date": new_date})
            await state.set_state(UserState.end_date_history)

        elif selected and my_state == "UserState:end_date_history":
            second_date = date.strftime("%d.%m.%Y")
            user_dict = await state.get_data()
            first_date = user_dict.get("start_date")
            start_date, end_date = create_date(
                {"start_date": first_date, "end_date": second_date}
            )
            if end_date < start_date:
                first_date, second_date = second_date, first_date
                await state.update_data(
                    {"start_date": first_date, "end_date": second_date}
                )
            else:
                await state.update_data({"end_date": second_date})

            await callback_query.message.edit_text(
                f"Выбранная дата {first_date} - {second_date}\n"
            )

            user_state = user_dict.get("user_state")
            if user_state == "UserState:transaction_history":
                await user_transaction_history(callback_query, state)
            elif user_state == "UserState:statistic_history":
                await month_custom_date_statistic(callback_query.message, state)
            else:
                await callback_query.message.edit_text(
                    f"Что-то пошло не так при выборе даты, скоро все исправим😵‍💫",
                )
                await history(callback_query.message, state)
    except Exception as ex:
        logger.error(
            f"Что-то пошло не так при обработке календаря для статистики: {ex}"
        )
        await callback_query.message.edit_text(
            "🤕 Возникла ошибка при выборе даты. Скоро меня починят"
        )


def create_date(user_dict: Dict) -> Tuple[date | None, date | None]:
    """
    Создание объектов даты начала и даты конца из данных пользователя.
    """

    _start_date = (
        user_dict.get("start_date")
        if user_dict.get("start_date")
        else user_dict.get("date")
    )
    _end_date = (
        user_dict.get("end_date")
        if user_dict.get("end_date")
        else user_dict.get("date")
    )

    start_date = (
        datetime.strptime(_start_date, "%d.%m.%Y").date() if _start_date else None
    )

    end_date = datetime.strptime(_end_date, "%d.%m.%Y").date() if _end_date else None

    return start_date, end_date


async def month_custom_date_statistic(message: Message, state: FSMContext) -> None:
    """
    Вывод статистики за пользовательский период с датами пользователя.
    """
    try:
        logger.info(f"{message.chat.id} - Выводим транзакции с датами пользователя")
        text_length = 4000
        long_message = False
        user_data = await state.get_data()
        begin_history, end_history = create_date(user_data)
        history_list, start_date, end_date = db_get_history_transaction(
            tg_id=message.chat.id, start_date=begin_history, end_date=end_history
        )
        month_flag = False
        all_history_flag = False
        last_month_flag = False

        if user_data.get("change_date_current_month"):
            month_flag = True

        if user_data.get("change_date_all_history"):
            all_history_flag = True

        if user_data.get("last_month"):
            last_month_flag = True

        text = f"История с {start_date} по {end_date}:\n"

        text_list, data_for_graphic, data_for_keyboard = text_of_stat(history_list)
        for new_text in text_list:
            if len(text) + len(new_text) > text_length:
                await message.answer(text=text)
                long_message = True

                text = ""

            text += new_text

        if long_message:
            await message.answer(
                text=text,
                reply_markup=change_date(
                    start_date=False,
                    month_flag=month_flag,
                    all_period=all_history_flag,
                    last_month=last_month_flag,
                ),
            )
        else:
            await message.edit_text(
                text=text,
                reply_markup=change_date(
                    start_date=False,
                    month_flag=month_flag,
                    all_period=all_history_flag,
                    last_month=last_month_flag,
                ),
            )

        await state.set_state(UserState.statistic_history)
    except TelegramBadRequest:
        await message.answer(
            text="Только что вывел информацию по выбранному критерию, выбери другой параметр"
        )


@router.callback_query(Text(["show_category_history"]))
@router.callback_query(Text(["back_to_category_history"]))
async def category_history_statistic(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Вывод статистики за пользовательский период с датами пользователя и цифрами категорий.
    """
    try:
        logger.info(f"{callback.message.chat.id} - Траты по категориям")
        text_length = 4000
        long_message = False
        user_data = await state.get_data()
        begin_history, end_history = create_date(user_data)
        history_list, start_date, end_date = db_get_history_transaction(
            tg_id=callback.message.chat.id,
            start_date=begin_history,
            end_date=end_history,
        )

        text = f"История с {start_date} по {end_date}:\n"

        text_list, data_for_graphic, data_for_keyboard = text_of_stat(
            history_list=history_list, category_flag=True
        )
        for new_text in text_list:
            if len(text) + len(new_text) > text_length:
                await callback.message.answer(text=text)
                long_message = True

                text = ""

            text += new_text

        if long_message:
            await callback.message.answer(
                text=text, reply_markup=category_history_kb(data_for_keyboard)
            )
        else:
            await callback.message.edit_text(
                text=text, reply_markup=category_history_kb(data_for_keyboard)
            )

        await state.set_state(UserState.statistic_history)
    except TelegramBadRequest:
        await callback.message.answer(
            text="Только что вывел информацию по выбранному критерию, выбери другой параметр"
        )


@router.callback_query(CreateCallbackData.filter(F.foo == "category_history"))
async def show_category_transactions(
    callback: CallbackQuery, state: FSMContext, callback_data: CreateCallbackData
) -> None:
    """ """
    logger.debug("Show category transactions")

    user_dict = await state.get_data()

    start_date = datetime.strptime(user_dict.get("start_date"), "%d.%m.%Y").date()
    end_date = datetime.strptime(user_dict.get("end_date"), "%d.%m.%Y").date()
    category_id = callback_data.bar

    history = db_get_category_transaction_by_date(
        callback.message.chat.id, start_date, end_date, category_id
    )
    full_text = create_history_text("", history)

    await callback.message.edit_text(
        text=full_text, reply_markup=back_to_category_history_kb()
    )


@router.callback_query(Text("show_graphics"))
async def show_graphics(callback: CallbackQuery, state: FSMContext) -> None:
    begin_history, end_history = create_date(await state.get_data())

    history_list, start_date, end_date = db_get_history_transaction(
        tg_id=callback.message.chat.id, start_date=begin_history, end_date=end_history
    )
    text, data_for_graphic, data_for_keyboard = text_of_stat(history_list)
    new_text = f"Графики в период с {start_date} по {end_date}"

    if data_for_graphic:
        media_graph = generate_standard_graphics(
            history_list=history_list,
            data_for_graphic=data_for_graphic,
            text=new_text,
        )

        await callback.message.answer_media_group(media=media_graph)
    else:
        await callback.message.answer(
            text="Данных для формирования графиков еще нет❌\n\n"
            "Нажми /transaction , чтобы записать новую операцию в данный период",
        )


@router.callback_query(
    Text(
        [
            "change_date_all_history",
            "change_date_current_month",
            "change_date_three_month",
            "change_for_past_month",
            "change_for_next_month",
            "back_to_user_month_statistics",
        ]
    )
)
async def callback_change_date_of_static(
    callback: CallbackQuery, state: FSMContext
) -> None:
    user_dict = await state.get_data()
    if user_dict.get("change_date_all_history"):
        user_dict.pop("change_date_all_history")
    if user_dict.get("change_date_current_month"):
        user_dict.pop("change_date_current_month")
    if user_dict.get("last_month"):
        user_dict.pop("last_month")
    await state.set_data(user_dict)

    if callback.data == "change_date_three_month":
        await month_statistic(callback, state)
    else:
        if callback.data == "change_date_all_history":
            start_date = db_get_first_date_transaction(tg_id=callback.message.chat.id)
            await state.update_data(
                {"change_date_all_history": True, "start_date": start_date}
            )

        elif callback.data == "change_date_current_month":
            date_list = get_start_date()
            start_date = date_list["start_month"].strftime("%d.%m.%Y")
            await state.update_data(
                {"change_date_current_month": True, "start_date": start_date}
            )

        elif callback.data == "change_for_past_month":
            new_date = datetime.strptime(user_dict.get("start_date"), "%d.%m.%Y").date()
            new_date -= relativedelta(months=1)
            start_date = new_date.strftime("%d.%m.%Y")

            last_day = calendar.monthrange(new_date.year, new_date.month)[1]
            end_date = datetime(new_date.year, new_date.month, last_day)
            end_date_str = end_date.strftime("%d.%m.%Y")

            await state.update_data(
                {
                    "change_date_current_month": True,
                    "start_date": start_date,
                    "end_date": end_date_str,
                }
            )

        elif callback.data == "change_for_next_month":
            new_date = datetime.strptime(user_dict.get("start_date"), "%d.%m.%Y").date()
            new_date += relativedelta(months=1)
            start_date = new_date.strftime("%d.%m.%Y")

            last_day = calendar.monthrange(new_date.year, new_date.month)[1]
            end_date = datetime(new_date.year, new_date.month, last_day)
            end_date_str = end_date.strftime("%d.%m.%Y")

            await state.update_data(
                {
                    "change_date_current_month": True,
                    "start_date": start_date,
                    "end_date": end_date_str,
                }
            )

        elif callback.data == "back_to_user_month_statistics":
            start_date = user_dict.get("start_date")
            await state.update_data(
                {
                    "change_date_current_month": True,
                }
            )

        if datetime.strptime(start_date, "%d.%m.%Y").date().month == date.today().month:
            await state.update_data({"last_month": True})
        await month_custom_date_statistic(callback.message, state)
