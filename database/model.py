from datetime import datetime

from peewee import *

from config_data.config import (
    POSTGRES_DATABASE,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT,
)


db = PostgresqlDatabase(
    POSTGRES_DATABASE,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
)


class BaseModel(Model):
    """Базовый класс моделей"""

    class Meta:
        database = db


class User(BaseModel):
    """Класс пользователя.

    Описывает пользовательские поля для хранения информации о том,
    что делает пользователь в данный момент
    """

    class Meta:
        table_name = "user"

    reg_date = DateField(default=datetime.now().date(), verbose_name="Дата создания")
    telegram_id = BigIntegerField(null=True, unique=True, verbose_name="Телеграм ID")
    username = CharField(
        max_length=32, null=True, unique=False, verbose_name="Username"
    )


class Account(BaseModel):
    """
    Класс Счёта
    """

    class Meta:
        table_name = "account"

    user = ForeignKeyField(User, backref="budget", verbose_name="ID пользователя")
    created_date = DateField(
        default=datetime.now().date(), verbose_name="Дата создания"
    )
    account_name = TextField(
        default="Личный", null=False, unique=False, verbose_name="Название счета"
    )


class Category(BaseModel):
    """
    Класс Категорий
    """

    class Meta:
        table_name = "category"

    user = ForeignKeyField(User, backref="category", verbose_name="ID пользователя")
    group_of_categories = CharField(
        max_length=32, null=False, unique=False, verbose_name="Группа категории"
    )
    category_name = CharField(
        max_length=32, null=False, unique=False, verbose_name="Категория"
    )
    archive = BooleanField(null=False, verbose_name="В архиве")
    category_date = DateField(default=datetime.now(), verbose_name="Дата создания")


class Transaction(BaseModel):
    """
    Класс операций
    """

    class Meta:
        table_name = "transaction"
        order_by = "transaction_date"

    user = ForeignKeyField(User, backref="transactions", verbose_name="ID пользователя")
    transaction_date = DateField(
        default=datetime.now().date(), verbose_name="Дата транзакции"
    )
    amount = DecimalField(null=False, verbose_name="Сумма")
    category = ForeignKeyField(Category, backref="category", verbose_name="Категория")
    description = CharField(null=True, max_length=200, verbose_name="Описания")


class Balance(BaseModel):
    """
    Класс баланса пользователя
    """

    class Meta:
        table_name = "balance"

    user = ForeignKeyField(User, backref="balance", verbose_name="ID пользователя")
    account = ForeignKeyField(Account, backref="account", verbose_name="Название счёта")
    balance = DecimalField(default=0, null=False, verbose_name="Баланс")
