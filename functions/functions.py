from datetime import date, datetime, timedelta
from typing import List, Dict, Union

from loguru import logger


def get_start_date() -> Dict[str, date]:
    """
    Возвращает даты начала периода для рассчета статистики в команде /start.
    Например, сегодня 2 число (сб), то нужно вернуть данные с начала недели, а не с начала месяца.

    :return:
    """
    try:
        today = date.today()
        week_number = today.isocalendar()[1]
        month = today.month
        year = today.year

        first_day_of_week = datetime.strptime(f'{year}-W{week_number}-1', "%Y-W%W-%w").date()
        first_day_of_month = datetime.strptime(f'{year}-{month}-1', '%Y-%m-%d').date()
        last_day_of_week = first_day_of_week + timedelta(days=6)

        if first_day_of_month < first_day_of_week:
            end_date = first_day_of_month
        else:
            end_date = first_day_of_week

        logger.debug(f'Собрали даты')

        return {
            'today': today,
            'end_date': end_date,
            'start_week': first_day_of_week,
            'end_week': last_day_of_week,
            'start_month': first_day_of_month,
        }

    except Exception as e:
        logger.error(f'Ошибка при вычислении статистики: {e}')


def calculate_statistics(
    query: List[Dict[str, Union[str, float]]],
    first_day_of_week: date,
    last_day_of_week: date,
    first_day_of_month: date,
) -> Dict[str, List[float]]:
    """
    Функция рассчитывает статистику на основе полученных данных.

    :param query:
    :param first_day_of_week:
    :param first_day_of_month:
    :param last_day_of_week:
    :return:
    """
    try:
        today = date.today()

        today_result = []
        week_result = []
        month_result = []

        for elem in query:
            if elem.get('transaction_date') >= first_day_of_month:
                month_result.append(float(elem.get('amount')))
                if elem.get('transaction_date') == today:
                    today_result.append(float(elem.get('amount')))

        for elem in query:
            if first_day_of_week <= elem.get('transaction_date') <= last_day_of_week:
                week_result.append(float(elem.get('amount')))

        result = {
            'today': today_result,
            'week': week_result,
            'month': month_result,
        }

        logger.debug(f'Собрали текст статистики')

        return result
    except Exception as ex:
        logger.error(f'Ошибка при вычислении статистики: {ex}')
        return {}


def create_history_text(text: str, history: List) -> str:
    print(history)
    today_date = date.today()
    date_list = []
    category_list = []

    for day_history in history[:5]:
        user_date = day_history.get('transaction_date')
        if user_date not in date_list:
            date_list.append(user_date)
            user_date = 'Сегодня' if user_date == today_date else user_date
            text += f'📆*{user_date}*\n\n'
            category_list = []

        category = day_history.get('category_name')

        if category not in category_list:
            text += f'🔹*{category}*\n\n'
            category_list.append(category)

        summ = day_history.get('amount')
        descr = day_history.get('description')
        history_id = day_history.get('id')

        text += f"{float(summ)} ₽ | (Удалить /del{history_id})\n" \
                f"Описание: {descr}\n\n" \

        history.remove(day_history)

    return text

