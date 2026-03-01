import csv
import os

from aiogram import F, Bot
from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message
from loguru import logger

from flowers.config import BOT_TOKEN_FL, INFO_CHANNEL
from flowers.database.queries.query import add_products_from_tilda_to_db
from flowers.handlers_fl.start import router, bot_start

bot = Bot(token=BOT_TOKEN_FL)


@router.callback_query(F.data == "refresh_instruction")
async def send_refresh_instruction(callback: CallbackQuery):
    logger.info("send_refresh_instruction")
    await callback.message.answer("Тут инструкция")
    await bot.send_message(chat_id=INFO_CHANNEL, text="text")


@router.message(F.content_type == ContentType.DOCUMENT)
async def parse_products_document(message: Message):
    logger.info("parse_products_document")
    document = message.document

    if document.mime_type != "text/csv":
        await message.answer("Нужно отправить файл в формате csv")
        return
    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="upload_document")
        directory = f"src/docs/file_reader"
        os.makedirs(directory, exist_ok=True)

        filename = os.path.join(directory, document.file_name)

        await bot.download(message.document.file_id, filename, 60)
        columns_to_keep = ["External ID", "Title", "Photo"]
        data_list = []

        with open(filename, newline="", encoding="utf-8") as f_in:
            reader = csv.DictReader(f_in, delimiter=";")
            for row in reader:
                filtered_row = {
                    col.lower().replace(" ", "_"): row.get(col)
                    for col in columns_to_keep
                }
                data_list.append(filtered_row)

        add_products_from_tilda_to_db(data_list)
        await message.answer("✅Добавил всю информацию в базу")
        await bot_start(message)
    except Exception as ex:
        logger.exception(ex)
        await message.answer(
            "🤕Произошла неизвестная ошибка. О ней никто не знает, кроме тебя🤕"
        )
