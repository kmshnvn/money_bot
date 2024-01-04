from datetime import date, datetime, timedelta
from typing import List, Dict, Union, Tuple

from aiogram.types import InputMediaPhoto
from loguru import logger
from pydantic.types import Decimal

from config_data.config import MONTH_NAME, BOT_NAME

HISTORY_DISPLAY_LIMIT = 15


def get_start_date() -> Dict[str, date]:
    """
    Возвращает даты начала периода для рассчета статистики в команде /start.
    Например, сегодня 2 число (сб), то нужно вернуть данные с начала недели, а не с начала месяца.

    :return: Словарь с датами начала периодов.
    """
    try:
        today = date.today()
        week_number = today.isocalendar()[1]
        month = today.month
        year = today.year

        first_day_of_week = datetime.strptime(
            f"{year}-W{week_number}-1", "%Y-W%W-%w"
        ).date()
        first_day_of_month = datetime.strptime(f"{year}-{month}-1", "%Y-%m-%d").date()
        last_day_of_week = first_day_of_week + timedelta(days=6)

        end_date = (
            first_day_of_month
            if first_day_of_month < first_day_of_week
            else first_day_of_week
        )

        logger.debug(f"Собрали даты")

        return {
            "today": today,
            "end_date": end_date,
            "start_week": first_day_of_week,
            "end_week": last_day_of_week,
            "start_month": first_day_of_month,
        }

    except Exception as e:
        logger.error(f"Ошибка при вычислении статистики: {e}")


def calculate_statistics(
    query: List[Dict[str, Union[str, float]]],
    first_day_of_week: date,
    last_day_of_week: date,
    first_day_of_month: date,
) -> Dict[str, List[float]]:
    """
    Функция рассчитывает статистику на основе полученных данных.

    :param query: Список данных о транзакциях.
    :param first_day_of_week: Дата начала текущей недели.
    :param last_day_of_week: Дата окончания текущей недели.
    :param first_day_of_month: Дата начала текущего месяца.
    :return: Словарь с рассчитанной статистикой.
    """
    try:
        today = date.today()

        today_result = []
        week_result = []
        month_result = []

        for elem in query:
            if elem.get("transaction_date") >= first_day_of_month:
                month_result.append(float(elem.get("amount")))
                if elem.get("transaction_date") == today:
                    today_result.append(float(elem.get("amount")))

        for elem in query:
            if first_day_of_week <= elem.get("transaction_date") <= last_day_of_week:
                week_result.append(float(elem.get("amount")))

        result = {
            "today": today_result,
            "week": week_result,
            "month": month_result,
        }

        logger.debug(f"Собрали текст статистики")

        return result
    except Exception as ex:
        logger.error(f"Ошибка при вычислении статистики: {ex}")
        return {}


def create_history_text(text: str, history: List[Dict[str, Union[str, float]]]) -> str:
    """
    Создает текст истории транзакций.

    :param text: Исходный текст.
    :param history: Список данных о транзакциях.
    :return: Итоговый текст истории транзакций.
    """
    today_date = date.today()
    date_list = []

    history_to_remove = []
    for day_history in reversed(history[:HISTORY_DISPLAY_LIMIT]):
        user_date = day_history["transaction_date"]
        if user_date not in date_list:
            date_list.append(user_date)
            user_date = (
                "Сегодня" if user_date == today_date else user_date.strftime("%d.%m.%Y")
            )
            text += f"📆*{user_date}*\n-----------\n"

        summ = day_history.get("amount")
        descr = day_history.get("description")
        history_id = day_history.get("id")
        category = day_history.get("category_name")

        text += f"   {float(summ)} ₽ | *{category}*\n"
        if descr != "":
            text += f"   Описание: {descr}\n"

        text += (
            f"   ✏️\n"
            f"   [Изменить](https://telegram.me/{BOT_NAME}?start=change{history_id})\n"
            f"   [Удалить](https://telegram.me/{BOT_NAME}?start=del{history_id})\n"
            f"-----------\n"
        )

        history_to_remove.append(day_history)

    for item in history_to_remove:
        history.remove(item)
    return text


def text_of_stat(history_list: Dict) -> Tuple[str, Dict[str, Dict[str, int]]]:
    """
    Создает текст статистики на основе списка истории.

    :param history_list: Словарь данных истории транзакций.
    :return: Итоговый текст статистики.
    """
    date_list = []
    data_for_graphic = {}
    text = ""

    sorted_data = sorted(
        history_list, key=lambda x: datetime.strptime(x["year_month"], "%Y-%m")
    )

    for history in sorted_data:
        year_month = history["year_month"]
        year, month = year_month.split("-")
        month_name = MONTH_NAME[int(month)]

        if year_month not in date_list:
            if text != "":
                text = text_of_stat_generate(text, income_stat, expense_stat)

            text += f"\n🔹*{month_name} {year}*\n\n"
            date_list.append(year_month)
            income_stat = 0
            expense_stat = 0

        summ = float(history["amount"])
        if summ > 0:
            income_stat += summ
        else:
            expense_stat += summ

        text += f"  🔸{history['category_name']}: {summ} ₽\n"
        data_for_graphic[month_name] = {"Income": income_stat, "Expense": expense_stat}

    text = text_of_stat_generate(text, income_stat, expense_stat)

    if not text:
        text = f"\nВ этот период трат не было"

    return text, data_for_graphic


def text_of_stat_generate(text, income_stat, expense_stat):
    text += (
        f"\n  💰Всего доход: {income_stat}\n"
        f"  🔻Всего расход: {expense_stat}\n"
        f"  🔰Осталось: {income_stat + expense_stat}\n"
    )
    return text


def generate_media_message(media_list, photos, text):
    if len(media_list) == 0:
        media_list.append(InputMediaPhoto(media=photos, caption=text))
    else:
        media_list.append(InputMediaPhoto(media=photos))

    return media_list


def generate_dict_for_graphics(
    history_list: List[Dict[str, Union[str, Decimal]]]
) -> Dict[str, Dict[str, Union[str, Decimal]]]:
    graph_dict_expense = {}
    graph_dict_income = {}

    for elem in history_list:
        summ = elem["amount"]
        category_name = elem["category_name"]

        if summ < 0:
            amount = -summ

            if not category_name in graph_dict_expense:
                graph_dict_expense[category_name] = amount
            else:
                graph_dict_expense[category_name] += amount
        else:
            amount = summ

            if not category_name in graph_dict_income:
                graph_dict_income[category_name] = amount
            else:
                graph_dict_income[category_name] += amount

    return {"Доход": graph_dict_income, "Расход": graph_dict_expense}
