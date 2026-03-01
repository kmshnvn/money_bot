import os
from dotenv import load_dotenv, find_dotenv


if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN_FL = os.getenv("BOT_TOKEN_FL")
BOT_NAME_FL = os.getenv("BOT_NAME_FL")

POSTGRES_DATABASE_FL = os.getenv("POSTGRES_DATABASE_FL")
POSTGRES_USER_FL = os.getenv("POSTGRES_USER_FL")
POSTGRES_PASSWORD_FL = os.getenv("POSTGRES_PASSWORD_FL")
POSTGRES_PORT_FL = os.getenv("POSTGRES_PORT_FL")
POSTGRES_HOST_FL = os.getenv("POSTGRES_HOST_FL")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
DUMP_CHANNEL = os.getenv("DUMP_CHANNEL")
ADMIN_LIST_FL = os.getenv("ADMIN_LIST_FL")
if ADMIN_LIST_FL:
    ADMIN_LIST_FL = [int(admin_id) for admin_id in ADMIN_LIST_FL.strip("[]").split(",")]
else:
    ADMIN_LIST_FL = []


DEFAULT_COMMANDS_FL = (
    ("start", "Главное меню"),
)
