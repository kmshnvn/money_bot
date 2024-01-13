from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


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
    kb.row(InlineKeyboardButton(text="🧮Новая операция", callback_data="new_transaction_callback"))
    return kb.as_markup()


def change_date(start_date: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Месяц", callback_data="change_date_current_month"))
    if not start_date:
        kb.add(InlineKeyboardButton(text="3 месяца", callback_data="change_date_three_month"))
    kb.add(InlineKeyboardButton(text="Весь период", callback_data="change_date_all_history"))
    kb.adjust(3)

    kb.row(InlineKeyboardButton(text="🗓️Другая дата", callback_data="change_date"))
    kb.row(InlineKeyboardButton(text="📉Графики (выбранный период)", callback_data="show_graphics"))
    kb.row(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_main_history"))
    return kb.as_markup()


def transaction_history() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="🗓️Другая дата", callback_data="change_date"))
    kb.add(InlineKeyboardButton(text="⬅️Назад", callback_data="back_to_main_history"))
    kb.adjust(1)
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


def transaction_main_kb(
    group_name: str, not_today: bool = False
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if group_name == "Expense":
        kb.add(InlineKeyboardButton(text="💰Нет, это доход💰", callback_data="income"))
    else:
        kb.add(InlineKeyboardButton(text="📈Нет, это расход📈", callback_data="expense"))

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
        kb.adjust(1, 1, 3)
    else:
        kb.add(
            InlineKeyboardButton(
                text="⏱️Вчера", callback_data="change_for_yesterday_date"
            )
        )
        kb.adjust(1, 2)
    kb.row(InlineKeyboardButton(text="📊История и аналитика", callback_data="main_history_menu"))
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


def transaction_descr_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="⬅️Назад", callback_data="back"))
    kb.add(
        InlineKeyboardButton(
            text="Без описания", callback_data="transaction_without_descr"
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


def exist_category_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="Добавить новую", callback_data="add_new_category")
    )
    kb.add(
        InlineKeyboardButton(text="Удалить категорию", callback_data="delete_category")
    )
    kb.add(
        InlineKeyboardButton(
            text="Изменить категорию", callback_data="change_category_name"
        )
    )
    kb.adjust(1, 2)
    return kb.as_markup()


def group_category_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Доход", callback_data="income"))
    kb.add(InlineKeyboardButton(text="Расход", callback_data="expense"))
    kb.add(InlineKeyboardButton(text="В настройки🛠️", callback_data="ready"))
    kb.adjust(2, 1)
    return kb.as_markup()


def change_success_transaction(id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(
            text="✏️Изменить", callback_data=f"change_success_transaction-{id}"
        )
    )
    kb.add(
        InlineKeyboardButton(
            text="❌Удалить", callback_data=f"delete_success_transaction-{id}"
        )
    )
    return kb.as_markup()
