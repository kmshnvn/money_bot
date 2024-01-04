import os
from datetime import datetime, date
from typing import Dict, List, Union, Tuple, Any
from decimal import Decimal

from loguru import logger
from peewee import fn, SQL

from functions.functions import (
    get_start_date,
    calculate_statistics,
)
from .model import User, Transaction, Category, Account, db, Balance


def start_table(name: str, tg_id: int) -> None:
    """
    Создание стартовых полей пользователя

    :param name:
    :param tg_id:
    :return:
    """
    try:
        with db.atomic():
            user = User.create(username=name, telegram_id=tg_id)
            account = Account.create(user=user)
            Balance.create(user=user, account=account)
            logger.debug(f"{tg_id} | Создание стартовых полей пользователя")
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при создании таблицы: {ex}")


def db_get_balance(tg_id: int) -> Union[float, None]:
    """
    Функция получает текущий баланс пользователя.

    :param tg_id:
    :return:
    """

    try:
        user = User.get_or_none(telegram_id=tg_id)
        query = Balance.select().where(Balance.user == user)
        for string in query.dicts().execute():
            logger.debug(f"{tg_id} | Получили баланс пользователя")
            return string["balance"]
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при получении баланса из БД: {ex}")
        return None


def db_create_category(
    tg_id: int, category_dict: Dict[str, Union[List[str], str]]
) -> None:
    """
    Функция создает новые категории для пользователя и сохраняет их в БД.

    :param tg_id:
    :param category_dict:
    :return:
    """
    try:
        with db.atomic():
            logger.debug(f"{tg_id} | Создание новой категории в БД")

            fields = [
                Category.user,
                Category.group_of_categories,
                Category.category_name,
                Category.archive,
            ]
            records = []
            user = User.get_or_none(telegram_id=tg_id)
            archived = False

            query = Category.select().where(
                Category.user == user, Category.archive == 0
            )
            bd_category = [elem["category_name"] for elem in query.dicts().execute()]

            for group, category_list in category_dict.items():
                if isinstance(category_list, list):
                    for category in category_list:
                        if category not in bd_category:
                            records.append(
                                (
                                    user,
                                    str(group).capitalize(),
                                    str(category).capitalize(),
                                    archived,
                                )
                            )
                else:
                    records.append(
                        (
                            user,
                            str(group).capitalize(),
                            str(category_list).capitalize(),
                            archived,
                        )
                    )
            logger.debug(f"{tg_id} | Собрали список категорий\n {records}\n")

            if records:
                Category.insert_many(records, fields=fields).execute()
                logger.debug(f"{tg_id} | Записал")
            else:
                logger.debug(f"{tg_id} | Категория уже существует")
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при создании категории: {ex}")


def db_get_category(
    tg_id: int, group: str = None, user_name: str = None
) -> Dict[str, List[str]]:
    """
    Функция получает категории пользователя из БД.

    :param tg_id:
    :param group:
    :param user_name:
    :return:
    """
    try:
        user = User.get_or_none(telegram_id=tg_id)
        if user is None:
            start_table(name=user_name, tg_id=tg_id)
        if group is None:
            query = Category.select().where(
                Category.user == user,
                Category.archive == 0,
            )
        else:
            query = Category.select().where(
                Category.user == user,
                Category.archive == 0,
                Category.group_of_categories == group,
            )

        category = {}

        for elem in query.dicts().execute():
            group = elem["group_of_categories"]
            if category.get(group, False) is False:
                category[group] = [elem["category_name"]]
            else:
                category[group].append(elem["category_name"])

        logger.debug(f"{tg_id} | Взял категории из БД")
        return category
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при получении категорий из БД: {ex}")
        return {}


def db_change_category(
    tg_id: int,
    category_name: str,
    new_name: str = None,
) -> None:
    """
    Функция изменяет название категории или помещает ее в архив.

    :param tg_id:
    :param category_name:
    :param new_name:
    :return:
    """
    try:
        with db.atomic():
            user = User.get_or_none(telegram_id=tg_id)
            category = Category.get(
                Category.user == user,
                Category.archive == 0,
                Category.category_name == category_name,
            )
            if new_name:
                category.category_name = new_name
                logger.debug(
                    f"{tg_id} | "
                    f"Изменил название категории в БД с {category_name} на {new_name}"
                )
            else:
                category.archive = True
                logger.debug(f"{tg_id} | Добавил категорию в архив {category_name}")
            category.save()
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при изменении категории: {ex}")


def db_create_transaction(user_dict: Dict[str, Union[int, str]]) -> int:
    """
    Функция создает новую транзакцию для пользователя и сохраняет ее в БД.

    :param user_dict:
    :return:
    """
    try:
        with db.atomic():
            user = User.get_or_none(telegram_id=user_dict["id"])
            category = Category.get(
                Category.user == user, Category.category_name == user_dict["category"]
            ).id
            user_date = datetime.strptime(user_dict["date"], "%d.%m.%Y").date()

            transaction_summ = user_dict["summ"]

            with db.atomic():
                transaction = {
                    "user": user,
                    "transaction_date": user_date,
                    "amount": transaction_summ,
                    "category": category,
                    "description": user_dict["descr"],
                }

                user_balance = Balance.get(Balance.user == user)
                user_balance.balance += Decimal(transaction_summ)
                user_balance.save()

                transaction_id = Transaction.insert(transaction).execute()
                logger.debug(f'{user_dict["id"]} | Записал новую транзакцию в БД')
        return transaction_id
    except Exception as ex:
        logger.error(f'{user_dict["id"]} | Ошибка при создании транзакции: {ex}')


def db_get_history(tg_id: int) -> List[Dict[str, Union[str, int, float]]]:
    """
    Функция получает историю последних транзакций пользователя из БД.

    :param tg_id:
    :return:
    """
    try:
        user = User.get_or_none(telegram_id=tg_id)
        query = (
            Transaction.select(Transaction, Category.category_name)
            .join(Category)
            .where(
                Transaction.user == user,
            )
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .limit(30)
        )

        logger.debug(f"{tg_id} | Получил последние 30 операций пользователя")
        return query.dicts().execute()
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при получении истории транзакций: {ex}")


def db_get_custom_date_history(
    tg_id: int, start_date: date, end_date: date
) -> List[Dict[str, Union[str, int, float]]]:
    """
    Функция, получает на вход идентификатор пользователя,
    начальную дату и конечную дату поиска операций.
    Возвращает транзакции пользователя за выбранный период
    """
    try:
        user = User.get_or_none(telegram_id=tg_id)
        query = (
            Transaction.select(Transaction, Category.category_name)
            .join(Category)
            .where(
                Transaction.user == user,
                Transaction.transaction_date.between(start_date, end_date),
            )
            .order_by(Transaction.transaction_date)
        )

        logger.debug(f"{tg_id} | Получил операции с {start_date} по {end_date}")
        return query.dicts().execute()
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при получении истории транзакций: {ex}")


def db_get_transaction(transaction_id: int, tg_id: int) -> Dict[str, Union[int, str]]:
    """
    Функция получает информацию о транзакции по ее идентификатору из БД.

    :param transaction_id: id транзакции
    :param tg_id: телеграм id пользователя
    :return:
    """
    try:
        user = User.get_or_none(telegram_id=tg_id)

        query = (
            Transaction.select(Transaction, Category.category_name)
            .join(Category)
            .where(
                Transaction.user == user,
                Transaction.id == transaction_id,
            )
            .dicts()
            .execute()
        )
        for query_dict in query:
            return query_dict
    except Exception as ex:
        logger.error(f"Ошибка при получении транзакции из БД: {ex}")
        return {}


def db_get_main_statistic(tg_id: int) -> Dict[str, List[float]]:
    """
    Функция получает основную статистику пользователя из БД.

    :param tg_id:
    :return:
    """
    try:
        user = User.get_or_none(telegram_id=tg_id)

        date_dict = get_start_date()

        query = (
            Transaction.select(
                Transaction.amount,
                Transaction.transaction_date,
            )
            .where(
                Transaction.user == user,
                Transaction.transaction_date.between(
                    date_dict.get("end_date"), date_dict.get("today")
                ),
            )
            .dicts()
            .execute()
        )

        logger.debug(f"{tg_id} | Переход в составление статистики")
        return calculate_statistics(
            query=query,
            first_day_of_week=date_dict.get("start_week"),
            last_day_of_week=date_dict.get("end_week"),
            first_day_of_month=date_dict.get("start_month"),
        )
    except Exception as ex:
        logger.error(f"{tg_id} | Ошибка при получении основной статистики: {ex}")
        return {}


def db_get_history_transaction(
    tg_id: int, start_date=None, end_date=None
) -> Tuple[Any, date | Any, date | Any]:
    """
    Функция получает информацию о транзакциях.
    Берет данные за опеределенный системой или пользователем период.

    :param:
    :return:
    """
    user = User.get_or_none(telegram_id=tg_id)

    today = date.today()
    if start_date is None:
        start_date = (
            date(today.year, today.month - 2, 1)
            if today.month > 2
            else date(today.year - 1, 12 - today.month, 1)
        )

    if end_date is None:
        end_date = today

    query = (
        Transaction.select(
            fn.CONCAT(
                fn.EXTRACT(SQL('YEAR FROM "t1"."transaction_date"')).cast("VARCHAR"),
                "-",
                fn.EXTRACT(SQL('MONTH FROM "t1"."transaction_date"')).cast("VARCHAR"),
            ).alias("year_month"),
            fn.SUM(Transaction.amount).alias("amount"),
            Category.category_name,
        )
        .join(Category)
        .where(
            Transaction.user == user,
            Transaction.transaction_date.between(start_date, end_date),
        )
        .group_by(
            fn.CONCAT(
                fn.EXTRACT(SQL('YEAR FROM "t1"."transaction_date"')).cast("VARCHAR"),
                "-",
                fn.EXTRACT(SQL('MONTH FROM "t1"."transaction_date"')).cast("VARCHAR"),
            ),
            Category.category_name,
        )
        .order_by(
            fn.CONCAT(
                fn.EXTRACT(SQL('YEAR FROM "t1"."transaction_date"')).cast("VARCHAR"),
                "-",
                fn.EXTRACT(SQL('MONTH FROM "t1"."transaction_date"')).cast("VARCHAR"),
            ),
            fn.SUM(Transaction.amount).desc(),
        )
        .dicts()
        .execute()
    )

    return (
        query,
        date.strftime(start_date, "%d.%m.%Y"),
        date.strftime(end_date, "%d.%m.%Y"),
    )


def db_delete_transaction(user_dict: Dict[str, int]) -> bool:
    """
    Функция удаляет транзакцию по ее идентификатору из БД.

    :param:
    :return: True or False
    """
    try:
        with db.atomic():
            tg_id = user_dict.get("user_id")
            transaction_id = user_dict.get("id")
            summ = float(user_dict.get("summ"))

            user = User.get_or_none(telegram_id=tg_id)

            Transaction.delete_by_id(transaction_id)

            user_balance = Balance.get(Balance.user == user)
            user_balance.balance -= Decimal(summ)
            user_balance.save()

            logger.debug(f"Операцию id-{transaction_id} удалили")

            return True
    except Exception as e:
        logger.error(f"Ошибка удаления операции в БД: {e}")
        return False


def db_update_transaction(
    transaction_dict: Dict[str, Union[str, int]], tg_id: int
) -> bool:
    """
    Функция обновляет транзакцию по ее идентификатору из БД.

    :param:
    :return: True or False
    """
    try:
        user = User.get_or_none(telegram_id=tg_id)
        category = Category.get(
            Category.user == user,
            Category.category_name == transaction_dict["category"],
        ).id
        user_date = datetime.strptime(transaction_dict["date"], "%d.%m.%Y").date()
        with db.atomic():
            Transaction.update(
                transaction_date=user_date,
                amount=transaction_dict["amount"],
                category=category,
                description=transaction_dict["descr"],
            ).where(Transaction.id == transaction_dict["id"]).execute()

            logger.debug(
                f'{transaction_dict["id"]} | Обновил запись в БД \n{transaction_dict}'
            )
        return True
    except Exception as e:
        logger.error(f"Ошибка обновления операции в БД: {e}")
        return False


if not os.path.exists("database/bot_database.db"):
    try:
        with db:
            db.create_tables([User, Transaction, Category, Account, Balance])
    except Exception as ex:
        logger.error(f"database.py | Ошибка при создании БД - {ex}")
