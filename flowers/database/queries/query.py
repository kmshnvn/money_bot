from loguru import logger

from flowers.database.model import TildaProducts, db


def add_products_from_tilda_to_db(product_dict: list) -> None:
    logger.debug("add_products_from_tilda_to_db")
    with db.atomic():
        for elem in product_dict:
            external_id = elem["external_id"]
            title = elem["title"]
            photo = elem["photo"]

            product = TildaProducts.get_or_none(external_id=external_id)
            if product is None:
                TildaProducts.create(
                    external_id=external_id, product_name=title, photo_link=photo
                )
            else:
                product.product_name = title
                product.photo_link = photo
                product.save()


def get_all_products_from_db(external_id: str):
    logger.debug("get_all_products_from_db")
    query = (
        TildaProducts.select()
        .where(TildaProducts.external_id == external_id)
        .dicts()
        .execute()
    )

    return [elem for elem in query][0]
