import subprocess
from datetime import datetime
import os

from loguru import logger

from config_data.config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE


async def create_db_dump():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"db_dump_{timestamp}.sql"
    directory = "src/dumps"
    os.makedirs(directory, exist_ok=True)
    filename = os.path.join(directory, filename)

    command = [
        "pg_dump",
        f"--dbname=postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}",
        "-f",
        str(filename),
    ]

    try:
        subprocess.run(command, check=True)
        return filename
    except subprocess.CalledProcessError as e:
        logger.exception("Ошибка при создании дампа базы данных: {}", e)
        return None