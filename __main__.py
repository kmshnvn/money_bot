import asyncio

from loguru import logger
from loader import main


logger.add('logs/user_logger.log', format='{time:HH:mm:ss DD-MM-YY} {level} {message}', level='INFO', rotation="2 MB")
logger.add('logs/logger.log', format='{time:HH:mm:ss DD-MM-YY} {level} {message}', level='ERROR')


if __name__ == "__main__":
    logger.info('Запуск бота')
    asyncio.run(main())
