from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def start_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🛠️Настройки")
    return kb.as_markup(resize_keyboard=True)


def main_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧮Новая операция")
    kb.button(text="📋История")
    kb.button(text="🛠️Настройки")
    kb.button(text="📚Помощь")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def default_category_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Использовать стандартные категории")
    kb.button(text="Свои категории")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def exist_category_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Добавить новую")
    kb.button(text="Удалить категорию")
    kb.button(text="Изменить категорию")
    kb.button(text="⬅️Главное меню")
    kb.button(text="🧮Новая операция")
    kb.adjust(1, 2, 2)
    return kb.as_markup(resize_keyboard=True)


def save_category_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Записать")
    kb.button(text="Изменить")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def group_category_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Доход")
    kb.button(text="Расход")
    kb.button(text="Готово")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def add_transaction_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧮Новая операция")
    return kb.as_markup(resize_keyboard=True)


def user_category_kb(category_list: list) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for elem in category_list:
        kb.button(text=elem)
    kb.adjust(3)
    return kb.as_markup(resize_keyboard=True)


# Клавиатуры операций

def transaction_main_kb(group_name: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    if group_name == 'Expense':
        kb.button(text="💰Доход💰")
    else:
        kb.button(text="Расход")

    kb.button(text="📆Выбрать другую дату")
    kb.button(text="⬅️Главное меню")
    kb.adjust(1)

    return kb.as_markup(resize_keyboard=True)


def transaction_descr_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Без описания")
    return kb.as_markup(resize_keyboard=True)


def transaction_end_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🧮Новая операция")
    kb.button(text="⬅️Главное меню")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def transaction_save_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="✅Записать")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)


def history_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊Статистика")
    kb.button(text="⬅️Главное меню")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)
