from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CreateCallbackData(CallbackData, prefix="product"):
    foo: str
    bar: int


def main_history_inline_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="🗓️История операций", callback_data="history_of_transactions"
        )
    )
    kb.add(
        InlineKeyboardButton(text="📊Статистика трат", callback_data="user_statistic")
    )
    kb.row(
        InlineKeyboardButton(
            text="🧮Новая операция", callback_data="new_transaction_callback"
        )
    )
    return kb.as_markup()


def change_date(
    start_date: bool = True,
    month_flag: bool = False,
    all_period: bool = False,
    last_month: bool = False,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if not month_flag:
        kb.add(
            InlineKeyboardButton(
                text="Месяц", callback_data="change_date_current_month"
            )
        )
    else:
        kb.add(InlineKeyboardButton(text="✅Месяц", callback_data="0"))
    if not start_date:
        kb.add(
            InlineKeyboardButton(
                text="3 месяца", callback_data="change_date_three_month"
            )
        )
    else:
        kb.add(InlineKeyboardButton(text="✅3 месяца", callback_data="0"))
    if not all_period:
        kb.add(
            InlineKeyboardButton(
                text="Весь период", callback_data="change_date_all_history"
            )
        )
    else:
        kb.add(InlineKeyboardButton(text="✅Весь период", callback_data="0"))
    kb.adjust(3)

    if month_flag:
        kb.row(InlineKeyboardButton(text="⏪️", callback_data="change_for_past_month"))
        if not last_month:
            kb.add(
                InlineKeyboardButton(text="⏩️", callback_data="change_for_next_month")
            )
        else:
            kb.add(InlineKeyboardButton(text="×", callback_data="0"))

        kb.row(
            InlineKeyboardButton(
                text="💠Траты по категориям", callback_data="show_category_history"
            )
        )

    kb.row(InlineKeyboardButton(text="🗓️Другая дата", callback_data="change_date"))
    kb.row(
        InlineKeyboardButton(
            text="📉Графики (выбранный период)", callback_data="show_graphics"
        )
    )
    kb.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_main_history"))
    return kb.as_markup()


def transaction_history(last_history: bool, period: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🔍По дням", callback_data="show_day_history"))

    if not period:
        kb.add(
            InlineKeyboardButton(text="🗓️Выбрать период", callback_data="change_date")
        )

        if last_history:
            kb.add(
                InlineKeyboardButton(text="⏪️", callback_data="change_for_past_history")
            )
            kb.add(InlineKeyboardButton(text="✅Последние", callback_data="0"))
            kb.add(InlineKeyboardButton(text="×", callback_data="0"))
            kb.adjust(1, 1, 3)

        else:
            kb.add(
                InlineKeyboardButton(text="⏪️", callback_data="change_for_past_history")
            )
            kb.add(InlineKeyboardButton(text="✅Последние", callback_data="0"))
            kb.add(
                InlineKeyboardButton(text="⏩️", callback_data="change_for_next_history")
            )
            kb.adjust(1, 1, 3)
    else:
        kb.add(InlineKeyboardButton(text="✅По периоду", callback_data="change_date"))
        kb.add(
            InlineKeyboardButton(
                text="〽️Последние", callback_data="last_transaction_history"
            )
        )

    kb.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_main_history"))
    return kb.as_markup()


def transaction_history_by_day(last_history: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="〽️Последние", callback_data="last_transaction_history"
        )
    )
    kb.add(InlineKeyboardButton(text="🗓️Выбрать период", callback_data="change_date"))

    if last_history:
        kb.add(
            InlineKeyboardButton(text="⏪️", callback_data="change_for_past_day_history")
        )
        kb.add(InlineKeyboardButton(text="✅По дням", callback_data="0"))
        kb.add(InlineKeyboardButton(text="×", callback_data="0"))
        kb.adjust(1, 1, 3)

    else:
        kb.add(
            InlineKeyboardButton(text="⏪️", callback_data="change_for_past_day_history")
        )
        kb.add(InlineKeyboardButton(text="✅По дням", callback_data="0"))
        kb.add(
            InlineKeyboardButton(text="⏩️", callback_data="change_for_next_day_history")
        )
        kb.adjust(1, 1, 3)

    kb.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_main_history"))
    return kb.as_markup()


def category_history_kb(data_for_keyboard) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for key, value in data_for_keyboard.items():
        kb.add(
            InlineKeyboardButton(
                text=key,
                callback_data=CreateCallbackData(
                    foo="category_history", bar=value
                ).pack(),
            )
        )
    kb.adjust(5)
    kb.row(
        InlineKeyboardButton(
            text="⬅️Назад", callback_data="back_to_user_month_statistics"
        )
    )

    return kb.as_markup()


def back_to_category_history_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_category_history")
    )
    return kb.as_markup()


def delete_history_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="💯Удаляем", callback_data="delete_transaction"))
    return kb.as_markup()


def first_user_transaction_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="Использовать стандартные категории",
            callback_data="use_default_category",
        )
    )
    kb.add(
        InlineKeyboardButton(text="Свои категории", callback_data="use_custom_category")
    )
    kb.adjust(1)
    return kb.as_markup()


def new_transaction() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="🧮Новая операция", callback_data="new_transaction")
    )
    kb.adjust(1)
    return kb.as_markup()


def transaction_main_kb(not_today: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.add(
        InlineKeyboardButton(
            text="📆Выбрать другую дату", callback_data="change_transaction_date"
        )
    )
    if not_today:
        kb.add(InlineKeyboardButton(text="⏪️", callback_data="change_for_past_date"))
        kb.add(
            InlineKeyboardButton(
                text="⏱️Сегодня", callback_data="change_for_today_date"
            )
        )
        kb.add(InlineKeyboardButton(text="⏩️", callback_data="change_for_next_date"))
        kb.adjust(1, 3)
    else:
        kb.add(
            InlineKeyboardButton(
                text="⏱️Вчера", callback_data="change_for_yesterday_date"
            )
        )
        kb.adjust(2, 1)
    kb.row(
        InlineKeyboardButton(
            text="📊История и аналитика", callback_data="main_history_menu"
        )
    )
    return kb.as_markup()


def user_category_kb(category_list: list, group_name=None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for elem in category_list:
        kb.add(
            InlineKeyboardButton(
                text=elem, callback_data=f"transaction_category:{elem}"
            )
        )
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back"))
    if group_name is not None:
        if group_name == "Expense":
            kb.add(
                InlineKeyboardButton(text="💰Нет, это доход💰", callback_data="income")
            )
        else:
            kb.add(
                InlineKeyboardButton(text="📈Нет, это расход📈", callback_data="expense")
            )

    return kb.as_markup()


def user_category_for_settings_kb(category_dict: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, value in category_dict.items():
        if key in ("Income", "Expense"):
            text = "доходов" if key == "Income" else "расходов"
            kb.row(
                InlineKeyboardButton(text=f"⚠️ Категории {text} ⚠️", callback_data="0")
            )

            count = 0
            for elem in value:
                if count == 0 or count % 2 == 0:
                    kb.row(
                        InlineKeyboardButton(
                            text=elem, callback_data=f"transaction_category:{elem}"
                        )
                    )
                else:
                    kb.add(
                        InlineKeyboardButton(
                            text=elem, callback_data=f"transaction_category:{elem}"
                        )
                    )
                count += 1

    kb.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_main_settings"))
    return kb.as_markup()


def transaction_descr_kb(
    delete_flag: bool = False, category_id: int = None
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="⬅️Назад", callback_data="back"))
    kb.add(
        InlineKeyboardButton(
            text="Без описания", callback_data="transaction_without_descr"
        )
    )
    if delete_flag:
        kb.row(
            InlineKeyboardButton(
                text="❌Удалить",
                callback_data=CreateCallbackData(
                    foo="delete_category_from_db", bar=category_id
                ).pack(),
            )
        )
    return kb.as_markup()


def transaction_save_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="✅Записать", callback_data="add_category"))
    kb.add(InlineKeyboardButton(text="⬅️Назад", callback_data="back"))
    kb.adjust(1)
    return kb.as_markup()


def save_category_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="✅Записать", callback_data="add_transaction"))
    kb.add(InlineKeyboardButton(text="Изменить", callback_data="change_transaction"))
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def update_category_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="✅Обновить", callback_data="update_transaction"))
    kb.add(InlineKeyboardButton(text="Изменить", callback_data="change_transaction"))
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def change_transaction_details_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🗓️Дату", callback_data="change_transaction_date"))
    kb.add(InlineKeyboardButton(text="💰Сумму", callback_data="change_transaction_summ"))
    kb.add(
        InlineKeyboardButton(
            text="🗂️Категорию", callback_data="change_transaction_category"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="🖊️Описание", callback_data="change_transaction_descr"
        )
    )
    kb.add(InlineKeyboardButton(text="⬅️Назад", callback_data="back"))
    kb.adjust(2)
    return kb.as_markup()


def change_success_transaction_details_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🗓️Дату", callback_data="change_transaction_date"))
    kb.add(InlineKeyboardButton(text="💰Сумму", callback_data="change_transaction_summ"))
    kb.add(
        InlineKeyboardButton(
            text="🗂️Категорию", callback_data="change_transaction_category"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="🖊️Описание", callback_data="change_transaction_descr"
        )
    )
    kb.adjust(2)
    return kb.as_markup()


def exist_category_kb(admin: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="Добавить новую", callback_data="add_new_category")
    )
    kb.row(
        InlineKeyboardButton(text="Удалить категорию", callback_data="delete_category")
    )
    kb.add(
        InlineKeyboardButton(
            text="Изменить категорию", callback_data="change_category_name"
        )
    )
    if admin:
        kb.row(
            InlineKeyboardButton(
                text="Дамп", callback_data="create_dump_db"
            )
        )
    return kb.as_markup()


def group_category_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Доход", callback_data="income"))
    kb.add(InlineKeyboardButton(text="Расход", callback_data="expense"))
    kb.add(
        InlineKeyboardButton(
            text="В настройки🛠️", callback_data="back_to_main_settings"
        )
    )
    kb.adjust(2, 1)
    return kb.as_markup()


def change_success_transaction(id: int, msg_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="✏️Изменить", callback_data=f"change_success_transaction-{id}-{msg_id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="❌Удалить", callback_data=f"delete_success_transaction-{id}"
        )
    )
    return kb.as_markup()
