import asyncio

from loguru import logger
from flowers.loader_flower import main

if __name__ == "__main__":
    logger.info("Запуск бота")
    asyncio.run(main())
