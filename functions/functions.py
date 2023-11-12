from datetime import date, datetime, timedelta
from typing import List, Dict, Union

from loguru import logger

from config_data.config import MONTH_NAME

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
    for day_history in history[:HISTORY_DISPLAY_LIMIT]:
        print(day_history)
        user_date = day_history.get("transaction_date")
        if user_date not in date_list:
            date_list.append(user_date)
            user_date = "Сегодня" if user_date == today_date else user_date
            text += f"📆*{user_date}*\n\n"

        summ = day_history.get("amount")
        descr = day_history.get("description")
        history_id = day_history.get("id")
        category = day_history.get("category_name")

        text += (
            f"{float(summ)} ₽ | *{category}*\n"
            f"Описание: {descr}\n"
            f"(Удалить /del{history_id})\n\n"
        )

        history_to_remove.append(day_history)

    for item in history_to_remove:
        history.remove(item)

    return text


def text_of_stat(history_list: Dict) -> str:
    """
    Создает текст статистики на основе списка истории.

    :param history_list: Словарь данных истории транзакций.
    :return: Итоговый текст статистики.
    """
    date_list = []
    text = ""

    sorted_data = sorted(
        history_list, key=lambda x: datetime.strptime(x["year_month"], "%Y-%m")
    )

    for history in sorted_data:
        summ = float(history["amount"])
        year_month = history["year_month"]
        year, month = year_month.split("-")
        month_name = MONTH_NAME[int(month)]

        if year_month not in date_list:
            text += f"\n🔹*{month_name} {year}*\n\n"
            date_list.append(year_month)

        text += f"  🔸{history['category_name']}: {summ} ₽\n"

    if not text:
        text = f"\nВ этот период трат не было"

    return text
