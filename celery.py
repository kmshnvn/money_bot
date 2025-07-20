import os

from aiogram.types import FSInputFile
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from config_data.config import DUMP_CHANNEL
from files.dump_file import create_db_dump
from handlers.custom_heandlers.transaction import bot


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def daily_db_dump():
    logger.debug("Запуск задачи для создания и отправки дампа базы данных")
    dump_file = await create_db_dump()
    if dump_file:
        try:
            await bot.send_document(
                chat_id=DUMP_CHANNEL,
                document=FSInputFile(dump_file),
                caption="Ежедневный дамп базы данных Money Bot",
            )
        except Exception as ex:
            logger.error(f"Не удалось отправить дамп БД - {ex}")
        finally:
            os.remove(dump_file)
    else:
        logger.error("Не удалось создать дамп БД")


def start_scheduler():
    scheduler.add_job(daily_db_dump, "cron", hour=4, minute=0)

    scheduler.start()


def job_listener(event):
    if event.exception:
        logger.error(f"Задача {event.job_id} не выполнена из-за ошибки.")
    else:
        logger.info(f"Задача {event.job_id} выполнена успешно.")


scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
