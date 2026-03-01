import io

import aiohttp
from aiogram import Bot
from aiogram.types import BufferedInputFile, InputMediaPhoto
from loguru import logger
from fastapi import Request

from flowers.bot_app import app
from flowers.config import INFO_CHANNEL, BOT_TOKEN_FL
from flowers.database.queries.query import get_all_products_from_db

bot = Bot(token=BOT_TOKEN_FL)


@app.post("/tilda-webhook")
async def tilda_webhook(request: Request):
    data = await request.json()
    logger.debug(f"WEBHOOK DATA: {data}")
    if "test" in data:
        return {"status": "ok"}

    product_dict = await parse_tilda_webhook_data(data)
    await send_info_about_tilda_order(product_dict)
    return {"status": "ok"}


async def parse_tilda_webhook_data(data: dict) -> dict:
    logger.debug("parse_tilda_webhook_data")
    product_dict: dict = {}
    products = data.get("payment").get("products")

    for product in products:
        product_dict[product["externalid"]] = {"name": product["name"]}
    return product_dict
    # Заказ №[‘payment’][‘orderid’]
    #
    # for num, product in enumerate([‘payment’][‘products’])
    # num. product[‘name’]: product[‘price’] (product[‘price’] x product[‘amount’])
    # add [E0NLNnxYmH7DBfJ6HjHF]
    #
    # payment/delivery
    # Сумма платежа - payment/amount
    # Платежная система - payment/sys
    #
    # Телефон: [‘Телефон’]
    # Дата доставки: [‘Когда_нужен_букет’]
    # Вид доставки: [’Вид_доставки’]
    # Время самовывоза: [‘Желаемое_время_самовывоза’]
    # Где связаться с клиентом: [‘Как_связаться_с_клиентом’]
    # Бонусная система: [‘Бонусная_система’]
    # если да [Копим_или_списываем]
    #
    #


async def send_info_about_tilda_order(product_dict: dict):
    logger.debug("send_info_about_tilda_order")

    try:
        for external_id, product in product_dict.items():
            media_group: list = []
            product_info = get_all_products_from_db(external_id)

            logger.debug(product_info)
            photos: str = product_info["photo_link"]
            name: str = product["name"]
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
                            media_group.append(InputMediaPhoto(media=img, caption=name))
                        else:
                            logger.error("Ошибка загрузки файла. Код:", response.status)

            await bot.send_media_group(
                chat_id=INFO_CHANNEL,
                media=media_group,
            )
    except IndexError:
        pass
