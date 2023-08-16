from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_history_inline_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(
        text="🗓️История операций",
        callback_data="history_of_transactions")
    )
    kb.add(InlineKeyboardButton(
        text="📊Статистика трат",
        callback_data="user_statistic")
    )
    return kb.as_markup()


def change_date() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(
        text="🗓️Другая дата",
        callback_data="change_date")
    )
    kb.add(InlineKeyboardButton(
        text="⬅️Назад",
        callback_data="back_to_main_history")
    )
    kb.adjust(1)
    return kb.as_markup()


def transaction_history() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(
        text="🗓️Другая дата",
        callback_data="change_date")
    )
    # kb.add(InlineKeyboardButton(
    #     text="➡️Другие недавние операции",
    #     callback_data="change_transaction")
    # )
    kb.add(InlineKeyboardButton(
        text="⬅️Назад",
        callback_data="back_to_main_history")
    )
    kb.adjust(1)
    return kb.as_markup()


def delete_history_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(
        text="💯Удаляем",
        callback_data="delete_transaction")
    )
    return kb.as_markup()
