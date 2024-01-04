from typing import List, Dict, Union

import plotly.graph_objects as go
from aiogram.types import BufferedInputFile, InputMediaPhoto
from plotly.io import to_image
from pydantic.types import Decimal

from functions.functions import generate_dict_for_graphics, generate_media_message


def generate_standard_graphics(
    history_list: List[Dict[str, Union[str, Decimal]]],
    data_for_graphic: Dict[str, Dict[str, int]],
    text: str,
) -> List[InputMediaPhoto]:
    """
    Создает список графиков для аналитики трат

    history_list: История транзакций из БД пользователя
    data_for_graphic: Отобранные ранее данные из операций пользователя {Месяц: {Расход: сумма; Доход: сумма}}
    text: Текст, который будет прикреплен к медиа группе
    return: Возвращает список из InputMediaPhoto для передачи в бота
    """
    media = []
    month_list = []
    expense = []
    income = []

    dict_for_graphics = generate_dict_for_graphics(history_list)

    for month, value in data_for_graphic.items():
        month_list.append(month)
        for elem, amount in value.items():
            if elem == "Expense":
                expense.append(-amount)
            elif elem == "Income":
                income.append(amount)

    if len(month_list) == 1:
        graph_file = bar_char_history(expense, income)
    else:
        graph_file = line_graph_history(month_list, expense, income)

    media = generate_media_message(media_list=media, photos=graph_file, text=text)

    for title, elem in dict_for_graphics.items():
        labels = []
        values = []
        if elem == {}:
            continue
        for key, value in elem.items():
            labels.append(key)
            values.append(value)
        graph_file = pie_graph_history(title, labels, values)
        media = generate_media_message(media_list=media, photos=graph_file, text=text)

    return media


def pie_graph_history(
    title: str, labels: List[str], values: List[str | Decimal]
) -> BufferedInputFile:
    """
    Создает круговую диаграмму трат пользователя за период

    title:
    labels:
    values:
    return:
    """
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_traces(
        textinfo="percent+label", marker=dict(line=dict(color="#000000", width=1.5))
    )
    fig.update_layout(title_text=title)
    img_byte = to_image(fig=fig, format="png", scale=2.5)
    graph_file = BufferedInputFile(file=img_byte, filename="graph.webp")

    return graph_file


def line_graph_history(
    month_list: List[str], expense: List[int], income: List[int]
) -> BufferedInputFile:
    """
    Создает линейную график пользователя для сравнения от 2х месяцев

    month_list:
    expense:
    income:
    return:
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=month_list,
            y=expense,
            name="Расходы",
            line=dict(color="firebrick", width=4),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=month_list, y=income, name="Доходы", line=dict(color="royalblue", width=4)
        )
    )
    fig.update_layout(title_text="Динамика расходов и доходов", plot_bgcolor="white")

    img_byte = to_image(fig=fig, format="png", scale=2.5)
    graph_file = BufferedInputFile(file=img_byte, filename="graph.webp")

    return graph_file


def bar_char_history(expense: List[int], income: List[int]) -> BufferedInputFile:
    """
    Создает график баров пользователя для сравнения дохода и расхода в месяце

    month_list:
    expense:
    income:
    return:
    """
    colors = ["royalblue", "crimson"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=["Доход", "Расход"],
                y=[income[0], expense[0]],
                marker_color=colors,
            )
        ]
    )
    fig.update_layout(title_text="Сравнение дохода и расхода за выбранный период ")
    img_byte = to_image(fig=fig, format="png", scale=2.5)
    graph_file = BufferedInputFile(file=img_byte, filename="graph.webp")

    return graph_file
