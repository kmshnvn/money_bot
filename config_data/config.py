import os
from dotenv import load_dotenv, find_dotenv


if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME")

POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "3"))
DUMP_CHANNEL = os.getenv("DUMP_CHANNEL")
ADMIN_LIST = os.getenv("ADMIN_LIST")
if ADMIN_LIST:
    ADMIN_LIST = [int(admin_id) for admin_id in ADMIN_LIST.strip("[]").split(",")]
else:
    ADMIN_LIST = []


DEFAULT_COMMANDS = (
    ("start", "Главное меню"),
    ("help", "🛟Команды бота🛟"),
    ("transaction", "Совершить операцию"),
    ("history", "История"),
    ("settings", "Настройки"),
)

MONTH_NAME = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}
