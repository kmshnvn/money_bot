from loguru import logger

from flowers.database.model import db, User, TildaProducts, Customer

if not db.get_tables():
    try:
        with db:
            db.create_tables(
                [
                    User,
                    Customer,
                    TildaProducts
                ]
            )
        logger.info("Создал продукты")
    except Exception as ex:
        logger.exception(f"database.py | Ошибка при создании БД - {ex}")
