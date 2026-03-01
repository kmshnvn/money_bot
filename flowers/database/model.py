from datetime import datetime

from peewee import (
    Model,
    PostgresqlDatabase,
    DateTimeField,
    BigIntegerField,
    CharField,
    TextField,
    IntegerField,
    ForeignKeyField,
)

from flowers.config import (
    POSTGRES_DATABASE_FL,
    POSTGRES_USER_FL,
    POSTGRES_PASSWORD_FL,
    POSTGRES_HOST_FL,
    POSTGRES_PORT_FL,
)
from flowers.database.static_models import UserRole

db = PostgresqlDatabase(
    POSTGRES_DATABASE_FL,
    user=POSTGRES_USER_FL,
    password=POSTGRES_PASSWORD_FL,
    host=POSTGRES_HOST_FL,
    port=POSTGRES_PORT_FL,
)


class BaseModel(Model):
    """Базовая модель, включающая общие поля и настройки."""

    class Meta:
        database = db


class TimestampedModel(BaseModel):
    """Абстрактная модель для добавления временных меток создания и обновления."""

    created_at = DateTimeField(default=datetime.now, verbose_name="Дата создания")
    updated_at = DateTimeField(default=datetime.now, verbose_name="Дата обновления")

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super(TimestampedModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class User(TimestampedModel):
    """Модель пользователя, включающая поля для хранения информации о нем."""

    telegram_id = BigIntegerField(null=False, unique=True, verbose_name="Телеграм ID")
    username = CharField(
        max_length=32, null=True, unique=False, verbose_name="Имя пользователя"
    )
    first_name = TextField(null=True, unique=False, verbose_name="Имя")
    second_name = TextField(null=True, unique=False, verbose_name="Фамилия")
    user_role = IntegerField(default=UserRole.USER, verbose_name="Роль пользователя")

    class Meta:
        table_name = "users"


class Customer(TimestampedModel):
    """Модель клиента, связанная с пользователем."""

    user = ForeignKeyField(User, backref="customers", null=True, on_delete="CASCADE")
    name = CharField(max_length=255, null=False, verbose_name="Имя клиента")
    phone_number = BigIntegerField(null=False, verbose_name="Номер телефона")

    class Meta:
        table_name = "customers"

    def __str__(self):
        return self.name


class TildaProducts(TimestampedModel):
    """Модель контрагентов, на которых оформляются заказы"""

    external_id = CharField(null=False, unique=True, verbose_name="External ID Tilda")
    product_name = CharField(max_length=255, null=True, verbose_name="Название товара")
    photo_link = TextField(null=True, verbose_name="Ссылка на фото")

    class Meta:
        table_name = "tilda_products"
