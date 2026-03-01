import io

import aiohttp
from aiogram import F, Bot
from aiogram.types import Message, BufferedInputFile, InputMediaPhoto
from loguru import logger

from flowers.config import INFO_CHANNEL, BOT_TOKEN_FL
from flowers.database.queries.query import get_all_products_from_db
from flowers.handlers_fl.start import router

bot = Bot(token=BOT_TOKEN_FL)


@router.message(F.chat.id == int(INFO_CHANNEL), F.text.startswith("Заказ"))
async def send_info_about_tilda_order(message: Message):
    logger.debug("send_info_about_tilda_order")
    product_dict = get_all_products_from_db()

    try:
        text_split = message.text.splitlines()
        for line in text_split[1:]:
            if "." not in line:
                break

            media_group: list = []
            name = line.split(". ")[1].split(":")[0]
            for product in product_dict:
                if product["product_name"] == name:
                    logger.debug(name)
                    photos: str = product["photo_link"]
                    photo_list = photos.split(" ")
                    for photo_link in photo_list[:2]:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(photo_link) as response:
                                logger.debug(response.status)
                                if response.status == 200:
                                    file_bytes = io.BytesIO(await response.read())
                                    file_bytes.seek(0)
                                    img = BufferedInputFile(
                                        file=file_bytes.read(), filename="photo.jpg"
                                    )
                                    media_group.append(
                                        InputMediaPhoto(media=img, caption=name)
                                    )
                                else:
                                    logger.error(
                                        "Ошибка загрузки файла. Код:", response.status
                                    )

                    await bot.send_media_group(
                        chat_id=INFO_CHANNEL,
                        media=media_group,
                        reply_to_message_id=message.message_id,
                    )
                    break
    except IndexError:
        pass
